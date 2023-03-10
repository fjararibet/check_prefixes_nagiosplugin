#!/usr/bin/env python3

import argparse
import subprocess as sp

import nagiosplugin

from helpers.DB_bgp import DB_bgp


class Prefixes(nagiosplugin.Resource):
    """Prefixes Received.

    Determines the number of prefixes received from all peers,
    using the vtysh command "show ip bgp summary".

    """

    def __init__(self, excluded_peers=[], excluded_ASNs=[]):
        self.__excluded_peers = excluded_peers
        self.__excluded_ASNs = excluded_ASNs
        self.__bgp_summary = sp.check_output(
            'sudo vtysh -c "show ip bgp summary"', shell=True, text=True)

    def prefixesProportion(self, peer_ip):
        '''Proportion of Prefixes Received.

        Returns the ratio between the prefixes received
        and the maximun received from the peer indicated.
        '''

        prefixes = self.prefixes(peer_ip)
        host_ip = self.retrieveHostIP(peer_ip)

        # Compares the prefixes received to the maximun given by the function
        db = DB_bgp()
        max_prefixes = db.max_PfxRcd(host_ip, peer_ip)

        ratio = prefixes * 100 / max_prefixes

        return round(ratio, 1)

    def prefixes(self, peer_ip):
        '''Retrieve number of prefixes.

        Tries to run this command to obtain
        the prefixes received from the peer:
        sudo vtysh -c "show ip bgp summary" | grep {peer_ip}
        '''
        try:
            bgp_summary = sp.Popen(
                ['echo', self.__bgp_summary], stdout=sp.PIPE)
            peer_line = sp.Popen(["grep", "-w", peer_ip],
                                 stdin=bgp_summary.stdout, stdout=sp.PIPE)
            bgp_summary.stdout.close()
            peer_data = peer_line.stdout.read().split()
            prefixes = int(peer_data[9])
        except IndexError:
            raise nagiosplugin.CheckError(
                "Cannot determine the number of Prefixes Received,"
                "no peers found.")
        except Exception:
            raise nagiosplugin.CheckError(
                "Cannot determine the number of Prefixes Received using"
                'vtysh -c "show ip bgp summary"')

        return prefixes

    def getPeers_IPs(self):
        '''Returns all BGP peer's IPs
        '''

        try:
            # Tries to obtain total number of peers
            bgp_summary = sp.Popen(
                ['echo', self.__bgp_summary], stdout=sp.PIPE)
            grep_total_neighbors = sp.Popen(
                ['grep', "Total number of neighbors"],
                stdin=bgp_summary.stdout, stdout=sp.PIPE)
            bgp_summary.stdout.close()
            tail = sp.Popen(['tail', '-c', '+27'],
                            stdin=grep_total_neighbors.stdout, stdout=sp.PIPE)
            grep_total_neighbors.stdout.close()
            total_neighbors = int(tail.stdout.read())

            # Tries to obtain peer data
            peers = sp.check_output(
                'sudo vtysh -c "show ip bgp summary"'
                f' | grep -A {total_neighbors} -w Neighbor | tail -n +2',
                shell=True, text=True)
            peers = peers.split('\n', total_neighbors - 1)
        except Exception:
            raise nagiosplugin.CheckError(
                'Could not obtain list of peers.')

        self.__peers_IPs = []
        for line in peers:
            peer_data = line.split()
            peer_ip = peer_data[0]
            asn = peer_data[2]
            if peer_ip in self.__excluded_peers or asn in self.__excluded_ASNs:
                continue
            self.__peers_IPs += [peer_ip]

        return self.__peers_IPs

    def retrieveHostIP(self, peer_ip):
        '''Returns the host's BGP address.

        Tries to run a command to obtain the IP that the host uses for BGP:
        sudo vtysh -c "show ip bgp neighbors |
        grep 'Local host:' | awk -F '[," "]' '{print $3}'
        '''
        try:
            bgp_neighbors = sp.Popen(
                ['sudo', 'vtysh', '-c', "show ip bgp neighbors", peer_ip],
                stdout=sp.PIPE)
            grep_peer = sp.Popen(['grep', 'Local host:'],
                                 stdin=bgp_neighbors.stdout, stdout=sp.PIPE)
            bgp_neighbors.stdout.close()
            awk = sp.Popen(['awk',
                            '-F',
                            '[," "]',
                            '{print $3}'],
                           stdin=grep_peer.stdout,
                           stdout=sp.PIPE)
            grep_peer.stdout.close()
            host_ip = awk.stdout.read().strip()
        except OSError:
            raise nagiosplugin.CheckError(
                'Cannot determine the number of Prefixes Received using'
                f'vtysh -c "show ip bgp neighbors {peer_ip}"')
        except AttributeError:
            raise nagiosplugin.CheckError(
                'Cannot determine the number of Prefixes Received using'
                f'vtysh -c "show ip bgp neighbors {peer_ip},'
                'peer might be out of service.')

        return host_ip

    def probe(self):
        '''Nagios plugin probe function.

        Returns a Metric nagiosplugin object per peer,
        with the prefixes information,
        this is the function used by the nagios plugin library.
        '''

        metric = []
        for peer_ip in self.getPeers_IPs():
            metric += [
                nagiosplugin.Metric(
                    f"{peer_ip} prefixes proportion",
                    self.prefixesProportion(peer_ip),
                    uom="%")]

        return metric


@nagiosplugin.guarded
def main():
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument('-w', '--warning', metavar='RANGE', default='',
                      help='return warning if prefixes'
                      'is outside RANGE (0-100)')
    argp.add_argument('-c', '--critical', metavar='RANGE', default='',
                      help='return critical if prefixes'
                      'is outside RANGE (0-100)')
    argp.add_argument('-exp', '--exclude-peer', metavar='IP', action='extend',
                      nargs='*', default=[], help='Excludes a single peer.'
                      'Can be used multiple times.')
    argp.add_argument('-exa', '--exclude-asn', metavar='ASN', action='extend',
                      nargs='*', default=[],
                      help='Excludes all peers that match the ASN.'
                      'Can be used multiple times.')

    args = argp.parse_args()

    pfx = Prefixes(args.exclude_peer, args.exclude_asn)
    check = nagiosplugin.Check(pfx)
    for peer in pfx.getPeers_IPs():
        check.add(
            nagiosplugin.ScalarContext(
                f"{peer} prefixes proportion",
                args.warning,
                args.critical))
    check.main()


if __name__ == '__main__':
    main()
