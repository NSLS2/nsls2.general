"""Ansible vars plugin for NSLS2Network"""
from __future__ import absolute_import, division, print_function

from ansible.plugins.vars import BaseVarsPlugin  # type: ignore
from nsls2network import nsls2network_sanitized  # type: ignore[attr-defined]

DOCUMENTATION = """
    name: nsls2network
    author: Stuart B. Wilkins (@stuwilkins) <swilkins@bnl.gov>
    version_added: "0.1"
    short_description: Loads the variables from NSLS2 Network
    description:
        - Loads information about the NSLS2 Network config
"""


class VarsModule(BaseVarsPlugin):  # [too-few-public-methods]
    """NSLS2Network Ansible vars module"""

    def get_vars(self, loader, path, entities):
        """Parses the inventory file"""

        if not isinstance(entities, list):
            entities = [entities]

        super().get_vars(loader, path, entities)

        data = {}
        data["nsls2network"] = nsls2network_sanitized

        return data
