"""Ansible filter to find networks from subnet in nsls2network"""

from __future__ import absolute_import, division, print_function

from ipaddress import IPv4Address

from nsls2network import nsls2network  # type: ignore[attr-defined]

DOCUMENTATION = r"""
    name: nsls2network
    author: Stuart B. Wilkins (@stuwilkins) <swilkins@bnl.gov>
    version_added: "0.1"
    short_description: Filters to return network and subnet from nsls2network.
    description:
        - These filters return the beamline (network) and segment (subnet) based on
        - comparing an IP address with the nsls2network IP scheme.
"""


def find(searchnet):
    """Find network in nsls2network"""
    for net in nsls2network:
        for subnet in nsls2network[net]:
            if IPv4Address(searchnet) in nsls2network[net][subnet]["subnet"]:
                return {"net": net, "subnet": subnet}
    return None


class FilterModule:
    """Ansible filter module for nsls2network"""

    def filters(self):
        """Return filters for this module"""
        return {
            "nsls2network_find": self.find,
        }

    def find(self, searchnet, mode=None):
        """Find subnet in nsls2network"""
        res = find(searchnet)
        if res is not None:
            if mode == "net":
                return res["net"]
            if mode == "subnet":
                return res["subnet"]

            return res

        return None
