#!/usr/bin/env python3

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
        '''Prefixes Received.

        Returns the prefixes received from the peer.
        '''

        # Tries to run this command to obtain
        # the prefixes received from the peer:
        # sudo vtysh -c "show ip bgp summary" | grep {peer_ip}
        try:
            bgp_summary = sp.Popen(
                ['sudo', 'vtysh', '-c', "show ip bgp summary"], stdout=sp.PIPE)
            peer_line = sp.Popen(["grep", "-w", self.peer_ip],
                                 stdin=bgp_summary.stdout, stdout=sp.PIPE)
            bgp_summary.stdout.close()
            peer_data = peer_line.stdout.read().split()
            prefixes = int(peer_data[9])
        except IndexError:
            raise nagiosplugin.CheckError(
                'Cannot determine the number of Prefixes Received,'
                ' try indicating a peer with -p')
        except Exception:
            raise nagiosplugin.CheckError(
                'Cannot determine the number of Prefixes Received'
                ''' using 'vtysh -c "show ip bgp summary".' '''
                ' Use -h for help.')

        return prefixes

    def probe(self):
        '''Nagios plugin probe function.

        Returns a Metric nagiosplugin object with the prefixes information,
        this is the function used by the nagios plugin library.
        '''
        metric = nagiosplugin.Metric(
            "prefixes", self.prefixes())
        return metric


@nagiosplugin.guarded
def main():
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument('-w', '--warning', metavar='RANGE', default='',
                      help='return warning if prefixes is outside RANGE')
    argp.add_argument('-c', '--critical', metavar='RANGE', default='',
                      help='return critical if prefixes is outside RANGE')
    argp.add_argument('-p', '--peer', help='IP of the BGP peer')

    args = argp.parse_args()
    check = nagiosplugin.Check(
        Prefixes(
            args.peer), nagiosplugin.ScalarContext(
            "prefixes", args.warning, args.critical))
    check.main()


if __name__ == '__main__':
    main()
