#!./venv/bin/python

import argparse
import subprocess as sp

import nagiosplugin
import mysql.connector
from mysql.connector import errorcode

import config

class DB_bgp():
    """Manages the connection to MySQL"""

    # gets credentials from a config file
    def __init__(self, credentials = config.credentials):
        self.__credentials = credentials
    
    def __open(self):
        try:
            conn = mysql.connector.connect(**self.__credentials)
            self.__conn = conn
            self.__cursor = conn.cursor()
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)

    # returns the maximun number prefixes received over the last 31 days, given a peer.
    def max_PfxRcd(self, equipo, peer):
        sql = '''
                SELECT MAX(Prefijos) 
                FROM PfxRcd 
                WHERE Fecha_Hora > DATE_SUB(CURDATE(),INTERVAL 31 DAY)
                AND equipo_IP = %s 
                AND peer_IP = %s
              '''

        self.__open()
        self.__cursor.execute(sql, (equipo, peer))
        result = self.__cursor.fetchall()[0][0]

        self.__cursor.close()
        self.__conn.close()
        
        return result

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
            raise nagiosplugin.CheckError("Cannot determine the number of Prefixes Received, try indicating a peer with -p")   
        except OSError:   
            raise nagiosplugin.CheckError('''Cannot determine the number of Prefixes Received using 'vtysh -c "show ip bgp summary"'.''')

        db = DB_bgp()
        max_prefixes = db.max_PfxRcd()

        ratio = prefixes / max_prefixes
        
        return ratio
    
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
