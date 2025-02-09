#!/usr/bin/python
import base64
import json
import os.path
import re
import requests
import yaml
from __future__ import absolute_import, division, print_function
from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = r"""
---
module: github_vars_facts

short_description: Module to read GitHub repository and set facts
version_added: "1.0.0"
description:
    - Module to read GitHub repository, parse yaml or json files
    - and insert the contents into ansible facts

options:
    owner:
        description: The GitHub owner name
        required: true
        type: str
    repo:
        description: The GitHub repository name
        required: true
        type: string
    branch:
        description: The git branch to fetch
        required: false
        default: main
        type: string
    path:
        description: If present, only process files down from this path
        required: false
        type: string
    recursive:
        description: If true, recursively fetch files
        required: false
        type: bool
    token:
        description: The GitHub API Token for authentication
        required: false
        type: string
    filters:
        description: A list of regular expressions to filter variables on
        required: false
        type: list

author:
    - Stuart B. Wilkins (@stuwilkins)
"""

EXAMPLES = r"""
# Read tree from GitHub API
- name: Get variables from host vars
  nsls2.general.github_vars_facts:
    owner: 'nsls2'
    repo: 'my_repository'
    path: 'host_vars/some.host.com'
    branch: 'main'
    token: '<Redacted>'

# Read tree from GitHub API and filter results
- name: Get variables from host vars
  nsls2.general.github_vars_facts:
    owner: 'nsls2'
    repo: 'my_repository'
    path: 'host_vars/some.host.com'
    branch: 'main'
    token: '<Redacted>'
    recursive: true
    filters:
      - '^beamline'
"""

RETURN = r"""
filteed_keys:
    description: A list of keys which were filtered by the regular expressions
    type: list
    returned: always
    sample: ['key1', 'key2']
"""


class GitHubFileReader:
    def __init__(self, owner, repo, token=None):
        self._owner = owner
        self._repo = repo

        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/vnd.github+json"})
        self._session.headers.update({"X-GitHub-Api-Version": "2022-11-28"})

        if token is not None:
            self._session.headers.update({"Authorization": f"Bearer {token}"})

        self._contents = list()

    def get_tree(self, branch, path=None, recursive=None):
        sha = self._get_branch_sha(branch)
        files = self._get_tree(sha, path=path, recursive=recursive)
        for file in files:
            if file["type"] == "blob":
                blob = self._get_blob(file["url"])
                self._process_file(blob, file["path"])

        return self._contents

    def _get_json(self, url):
        r = self._session.get(url)
        r.raise_for_status()
        j = r.json()
        return j

    def _get_branch_sha(self, branch):
        # Get from here
        j = self._get_json(
            f"https://api.github.com/repos/{self._owner}/{self._repo}/branches/{branch}"
        )
        head_tree_sha = j["commit"]["commit"]["tree"]["sha"]
        return head_tree_sha

    def _get_tree(self, sha, path=None, recursive=None):
        _recursive = bool(recursive)
        j = self._get_json(
            f"https://api.github.com/repos/{self._owner}/{self._repo}/git/trees/{sha}?recursive=f{_recursive}"
        )

        if path is not None:
            # We now select only part of the path
            files = [leaf for leaf in j["tree"] if leaf["path"].startswith(path)]
        else:
            files = j["tree"]

        return files

    def _get_blob(self, blob_url):
        j = self._get_json(blob_url)
        return j

    def _process_file(self, j, name=None):
        # if we have content, then we can process
        if "content" in j:
            if j["encoding"] == "base64":
                _content = base64.b64decode(j["content"])
            else:
                raise RuntimeError("Invalid encoding")

            if name is None:
                if "name" in j:
                    name = j["name"]
                else:
                    name = ""

            self._contents.append(
                dict(
                    content=_content,
                    name=name,
                )
            )

    def get_content(self):
        return self._contents


def run_module():
    module_args = dict(
        owner=dict(type="str", required=True),
        repo=dict(type="str", required=True),
        branch=dict(type="str", required=False, default="main"),
        path=dict(type="str", required=False, default=None),
        token=dict(type="str", required=False, no_log=True, default=None),
        filters=dict(type="list", required=False, default=list()),
        recursive=dict(type="bool", required=False, default=False),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    owner = module.params["owner"]
    repo = module.params["repo"]
    branch = module.params["branch"]
    path = module.params["path"]
    recursive = module.params["recursive"]

    try:
        ghfr = GitHubFileReader(owner, repo, module.params.get("token"))
        c = ghfr.get_tree(branch, path=path, recursive=recursive)
    except requests.HTTPError as e:
        code = e.response.status_code
        reason = e.response.reason
        module.fail_json(msg=f'HTTP Error. Status code {code} Reason "{reason}"')

    data = dict()
    for n in c:
        if os.path.splitext(n["name"])[1].lower() in [".yaml", ".yml"]:
            data.update(yaml.safe_load(n["content"]))
        if os.path.splitext(n["name"])[1].lower() in [".json"]:
            data.update(json.loads(n["content"]))

    # Now if needed we apply regex to the list
    if len(module.params["filters"]) > 0:
        filtered_data = dict()
        for filter in module.params["filters"]:
            for key in data:
                if re.match(filter, key):
                    filtered_data[key] = data[key]

        filtered_keys = [k for k in data if k not in filtered_data]

        module.exit_json(
            ansible_facts=filtered_data, filtered_keys=filtered_keys, changed=False
        )

    module.exit_json(ansible_facts=data, filtered_keys=list(), changed=False)


def main():
    run_module()


if __name__ == "__main__":
    main()
