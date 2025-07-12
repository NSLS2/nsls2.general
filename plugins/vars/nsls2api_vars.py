"""Ansible vars plugin for NSLS2Network"""

from __future__ import absolute_import, division, print_function

import json

import requests
from ansible.plugins.vars import BaseVarsPlugin  # type: ignore

DOCUMENTATION = """
    name: nsls2api
    author: Stuart B. Wilkins (@stuwilkins) <swilkins@bnl.gov>
    version_added: "0.1"
    short_description: Loads facts and vaiable from NSLS2 API
    description:
        - Loads information about the NSLS2 from the NSLS2 API
"""


class VarsModule(BaseVarsPlugin):  # pylint: disable=too-few-public-methods
    """NSLS2API Ansible vars module"""

    def __init__(self):
        super().__init__()

        self._session = requests.Session()

    def _get_json(self, url):
        r = self._session.get(url)
        r.raise_for_status()
        j = r.json()
        return j

    def get_vars(self, loader, path, entities):
        """Parses the inventory file"""

        if not isinstance(entities, list):
            entities = [entities]

        super().get_vars(loader, path, entities)

        beamlines = self._get_json("https://api.nsls2.bnl.gov/v1/beamlines")

        data = {}

        data["satelite_location_name"] = {
            d["network_locations"][0]: d["nsls2_redhat_satellite_location_name"]
            for d in beamlines
            if len(d["network_locations"]) > 0
        }

        data["beamlines"] = [
            {
                "tla": d["name"].lower(),
                "operator_account": d["service_accounts"]["operator"],
            }
            for d in beamlines
        ]

        data["netwoks"] = [nn for d in beamlines for nn in d["network_locations"]]

        return data


if __name__ == "__main__":
    mod = VarsModule()
    v = mod.get_vars(None, None, None)
    print(json.dumps(v, sort_keys=True, indent=4))
