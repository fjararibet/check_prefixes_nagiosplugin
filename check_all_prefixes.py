#!./venv/bin/python

import argparse
import subprocess as sp

import nagiosplugin

from DB_bgp import DB_bgp

class Prefixes(nagiosplugin.Resource):
    """Prefixes Received.

    Determines the number of prefixes received from a specific peer, 
    using the vtysh command "show ip bgp summary".

    """

    def __init__(self):
        self.__bgp_summary = sp.check_output('sudo vtysh -c "show ip bgp summary"', shell=True, text=True)

    def prefixes(self, peer_ip):

        # sudo vtysh -c "show ip bgp summary" | grep {$peer_ip}
        try:
            bgp_summary = sp.Popen(['echo', self.__bgp_summary], stdout=sp.PIPE)
            peer_line = sp.Popen(["grep", "-w", peer_ip], stdin=bgp_summary.stdout, stdout=sp.PIPE)
            bgp_summary.stdout.close()
            peer_data = peer_line.stdout.read().split()
            prefixes = int(peer_data[9])
        except IndexError:
            raise nagiosplugin.CheckError(
                "Cannot determine the number of Prefixes Received, no peers found.")   
        except Exception:   
            raise nagiosplugin.CheckError(
                '''Cannot determine the number of Prefixes Received using 'vtysh -c "show ip bgp summary"'.''')

        
        try:
            bgp_neighbors = sp.Popen(['sudo', 'vtysh', '-c', "show ip bgp neighbors", peer_ip], stdout=sp.PIPE)
            grep_peer = sp.Popen(['grep', 'Local host:'], stdin=bgp_neighbors.stdout, stdout=sp.PIPE)
            bgp_neighbors.stdout.close()
            awk = sp.Popen(['awk', '-F', '[," "]', '{print $3}'] , stdin=grep_peer.stdout, stdout=sp.PIPE)
            grep_peer.stdout.close()
            host_ip = awk.stdout.read().strip()
        except OSError:
            raise nagiosplugin.CheckError(
                f'''Cannot determine the number of Prefixes Received using 'vtysh -c "show ip bgp neighbors {peer_ip}" "''')
        except AttributeError:
            raise nagiosplugin.CheckError(
                f'''Cannot determine the number of Prefixes Received using 'vtysh -c "show ip bgp neighbors {peer_ip},
                 peer might be out of service." "''')
        
        db = DB_bgp()
        max_prefixes = db.max_PfxRcd(host_ip, peer_ip)

        ratio = prefixes / max_prefixes
        
        return ratio * 100
    
    # Returns a Metric nagiosplugin object with the prefixes information
    def probe(self):
        bgp_summary = sp.Popen(['echo', self.__bgp_summary], stdout=sp.PIPE)
        grep_total_neighbors = sp.Popen(['grep', "Total number of neighbors"], stdin=bgp_summary.stdout, stdout=sp.PIPE )
        bgp_summary.stdout.close()
        tail = sp.Popen(['tail', '-c', '+27'], stdin=grep_total_neighbors.stdout, stdout=sp.PIPE)
        grep_total_neighbors.stdout.close()
        total_neighbors = int(tail.stdout.read())

        peers = sp.check_output(
            f'''sudo vtysh -c "show ip bgp summary" | grep -A {total_neighbors} -w Neighbor | tail -n +2 ''',
            shell=True, text=True)
        peers = peers.split('\n', total_neighbors - 1)

        metric = []
        for line in peers:
            peer_data = line.split()
            peer_ip = peer_data[0]
            metric += [nagiosplugin.Metric("prefixes proportion", self.prefixes(peer_ip), uom="%")]

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
        Prefixes(),
        nagiosplugin.ScalarContext("prefixes proportion", args.warning, args.critical))
    check.main()

if __name__ == '__main__':
    main()
