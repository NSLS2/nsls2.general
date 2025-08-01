"""Ansible module to read contents of files with a given ext from a GitHub repo."""

from __future__ import absolute_import, division, print_function

import os.path

import requests
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nsls2.general.plugins.module_utils.github_file_reader import (
    GitHubFileReader,
)

DOCUMENTATION = r"""
---
module: github_read_files_given_ext

short_description: Module to read files given extension from GitHub repository
version_added: "1.0.1"
description:
    - Module to find list of files with given extension in a GitHub repository,
    - read them, and return a dictionary mapping file names to their contents.

options:
    owner:
        description: The GitHub owner name
        required: true
        type: str
    repo:
        description: The GitHub repository name
        required: true
        type: string
    varname:
        description: Name of variable to use for variables read from GitHub
        required: true
        type: string
    extension:
        description: The file extension to filter by
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
    token:
        description: The GitHub API Token for authentication
        required: false
        type: string

author:
    - Jakub Wlodek (@jwlodek)
"""

EXAMPLES = r"""
# Read tree from GitHub API
- name: Get all files with the .txt extension
  nsls2.general.github_read_files_given_ext:
    owner: 'nsls2'
    repo: 'my_repository'
    path: 'host_vars/some.host.com'
    branch: 'main'
    token: '<Redacted>'
    extension: ['.txt']
"""


def main():
    """Run the Ansible module"""
    module_args = {
        "owner": {"type": "str", "required": True},
        "repo": {"type": "str", "required": True},
        "extensions": {"type": "list", "required": True},
        "varname": {"type": "str", "required": True},
        "branch": {"type": "str", "required": False, "default": "main"},
        "path": {"type": "str", "required": False, "default": None},
        "token": {"type": "str", "required": False, "no_log": True, "default": None},
    }

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        ghfr = GitHubFileReader(
            module.params["owner"], module.params["repo"], module.params["token"]
        )
        c = ghfr.get_tree(
            module.params["branch"],
            path=module.params["path"],
            recursive=True,
        )

    except requests.HTTPError as e:
        code = e.response.status_code
        reason = e.response.reason
        module.fail_json(msg=f'HTTP Error. Status code {code} Reason "{reason}"')

    data = {module.params["varname"]: {}}
    for n in c:
        if os.path.splitext(n["name"])[1].lower() in module.params["extensions"]:
            data[module.params["varname"]][os.path.basename(n["name"])] = n["content"]

    module.exit_json(ansible_facts=data, changed=False)


if __name__ == "__main__":
    main()
