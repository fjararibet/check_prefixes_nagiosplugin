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

    def __init__(self, peer_ip):
        self.peer_ip = peer_ip

    def prefixes(self):

        # sudo vtysh -c "show ip bgp summary" | grep {$peer_ip}
        try:
            bgp_summary = sp.Popen(['sudo', 'vtysh', '-c', "show ip bgp summary"], stdout=sp.PIPE)
            peer_line = sp.Popen(["grep", "-w", self.peer_ip], stdin=bgp_summary.stdout, stdout=sp.PIPE)
            bgp_summary.stdout.close()
            peer_data = peer_line.stdout.read().split()
            prefixes = int(peer_data[9])
        except IndexError:
            raise nagiosplugin.CheckError(
                "Cannot determine the number of Prefixes Received, try indicating a peer with -p")   
        except Exception:   
            raise nagiosplugin.CheckError(
                '''Cannot determine the number of Prefixes Received using 'vtysh -c "show ip bgp summary"'.''')

        
        try:
            bgp_neighbors = sp.Popen(['sudo', 'vtysh', '-c', "show ip bgp neighbors", self.peer_ip], stdout=sp.PIPE)
            grep_peer = sp.Popen(['grep', 'Local host:'], stdin=bgp_neighbors.stdout, stdout=sp.PIPE)
            bgp_neighbors.stdout.close()
            awk = sp.Popen(['awk', '-F', '[," "]', '{print $3}'] , stdin=grep_peer.stdout, stdout=sp.PIPE)
            grep_peer.stdout.close()
            host_ip = awk.stdout.read().strip()
        except OSError:
            raise nagiosplugin.CheckError(
                f'''Cannot determine the number of Prefixes Received using 'vtysh -c "show ip bgp neighbors {self.peer_ip}" "''')
        except AttributeError:
            raise nagiosplugin.CheckError(
                f'''Cannot determine the number of Prefixes Received using 'vtysh -c "show ip bgp neighbors {self.peer_ip},
                 peer might be out of service." "''')
        
        db = DB_bgp()
        max_prefixes = db.max_PfxRcd(host_ip, self.peer_ip)

        ratio = prefixes * 100 / max_prefixes
        
        return round(ratio, 1)
    
    # Returns a Metric nagiosplugin object with the prefixes information
    def probe(self):
        metric = nagiosplugin.Metric("prefixes proportion", self.prefixes(), uom="%")
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
        nagiosplugin.ScalarContext("prefixes proportion", args.warning, args.critical))
    check.main()

if __name__ == '__main__':
    main()
