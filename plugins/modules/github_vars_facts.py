"""Ansible module to read variables from YAML and JSON files on GitHub"""

from __future__ import absolute_import, division, print_function

import base64
import json
import os.path
import re

import requests
import yaml
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nsls2.general.plugins.module_utils.github_file_reader import (
    GitHubFileReader,
)

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
    prefix:
        description: String to prefix the root keys in the dictionary
        required: false
        type: string
    varname:
        description: Name of variable to use for variables read from GitHub
        required: false
        type: string

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
filtered_keys:
    description: A list of keys which were filtered by the regular expressions
    type: list
    returned: always
    sample: ['key1', 'key2']
"""


def main():
    """Run the Ansible module"""
    module_args = {
        "owner": {"type": "str", "required": True},
        "repo": {"type": "str", "required": True},
        "branch": {"type": "str", "required": False, "default": "main"},
        "path": {"type": "str", "required": False, "default": None},
        "token": {"type": "str", "required": False, "no_log": True, "default": None},
        "filters": {"type": "list", "required": False, "default": []},
        "recursive": {"type": "bool", "required": False, "default": False},
        "prefix": {"type": "str", "required": False, "default": None},
        "varname": {"type": "str", "required": False, "default": None},
    }

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        ghfr = GitHubFileReader(
            module.params["owner"], module.params["repo"], module.params["token"]
        )
        c = ghfr.get_tree(
            module.params["branch"],
            path=module.params["path"],
            recursive=module.params["recursive"],
        )

    except requests.HTTPError as e:
        code = e.response.status_code
        reason = e.response.reason
        module.fail_json(msg=f'HTTP Error. Status code {code} Reason "{reason}"')

    data = {}
    for n in c:
        if os.path.splitext(n["name"])[1].lower() in [".yaml", ".yml"]:
            data.update(yaml.safe_load(n["content"]))
        if os.path.splitext(n["name"])[1].lower() in [".json"]:
            data.update(json.loads(n["content"]))

    # Now if needed we apply regex to the list
    filtered_keys = []
    if len(module.params["filters"]) > 0:
        filtered_data = {}
        for f in module.params["filters"]:
            for key, value in data.items():
                if re.match(f, key):
                    filtered_data[key] = value

        filtered_keys = [k for k in data if k not in filtered_data]

        data = filtered_data

    if module.params["varname"] is not None:
        _data = {}
        _data[module.params["varname"]] = data
        data = _data

    if module.params["prefix"] is not None:
        _data = {(module.params["prefix"] + key): value for key, value in data.items()}
        data = _data

    module.exit_json(ansible_facts=data, filtered_keys=filtered_keys, changed=False)


if __name__ == "__main__":
    main()
