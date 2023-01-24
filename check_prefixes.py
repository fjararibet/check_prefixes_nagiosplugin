#!python
"""Nagios plugin to check the number of prefixes received"""

import argparse
import subprocess as sp

import nagiosplugin

class Prefixes(nagiosplugin.Resource):
    """Prefixes Received.

    Determines the number of prefixes received from a specific peer, 
    using the vtysh command "show ip bgp summary".

    """

    def __init__(self, peer_ip):
        self.peer_ip = peer_ip

    def prefixes(self):
        bgp_summary = sp.Popen(['sudo vtysh -c "show ip bgp summary"'], stdout=sp.PIPE)
        peer_line = sp.Popen(["grep", self.peer_ip], stdin=bgp_summary.stdout, stdout=sp.PIPE)
        bgp_summary.stdout.close()
        prefixes_column = sp.Popen(["awk", "'{print $10}'"], stdin=peer_line.stdout, stdout=sp.PIPE)
        peer_line.stdout.close()

        prefixes = prefixes_column.stdout.read()

        return int(prefixes)
    
    # Returns a Metric nagiosplugin object with the prefixes information
    def probe(self):
        metric = nagiosplugin.Metric("prefixes", self.prefixes())
        return metric
    

     

@nagiosplugin.guarded
def main():
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument('-w', '--warning', metavar='RANGE', default='',
                    help='return warning if load is outside RANGE')
    argp.add_argument('-c', '--critical', metavar='RANGE', default='',
                    help='return critical if load is outside RANGE')
    argp.add_argument('-p', '--peer', help='IP of the BGP peer')
    argp.add_argument('-v', '--verbose', action='count', default=0,
                    help='increase output verbosity (use up to 3 times)')

    args = argp.parse_args()
    check = nagiosplugin.Check(
        Prefixes(args.peer),
        nagiosplugin.ScalarContext('prefixes', args.warning, args.critical))
    check.main()

if __name__ == '__main__':
    main()