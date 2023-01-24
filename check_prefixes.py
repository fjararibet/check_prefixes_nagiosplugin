#!python
"""Nagios plugin to check the number of prefixes received"""

import subprocess

import nagiosplugin

class Prefixes(nagiosplugin.Resource):
    """Prefixes Received.

    Determines the number of prefixes received from a specific peer, 
    using the vtysh command "show ip bgp summary".

    """

    def __init__(self, peer):
        self.peer = peer

    def prefixes():
        prefixes = 
    