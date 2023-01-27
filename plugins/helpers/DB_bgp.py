import mysql.connector
from mysql.connector import errorcode
import nagiosplugin
import configparser

from .config_check import config_check


class DB_bgp():
    """Manages the connection to MySQL"""

    # gets credentials from a config file
    def __init__(self):
        config = configparser.ConfigParser()
        try:
            config_check()
            config.read('./config.ini')
            credentials = config['credentials']
            self.__credentials = {'user': credentials['user'],
                                  'password': credentials['password'],
                                  'host': credentials['host'],
                                  'database': credentials['database'],
                                  'port': credentials['port']
                                  }
        except KeyError:
            raise nagiosplugin.CheckError(
                """Cannot connect to database,
                 config file not found or incomplete.""")

    def __open(self):
        try:
            conn = mysql.connector.connect(**self.__credentials)
            self.__conn = conn
            self.__cursor = conn.cursor()
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                raise nagiosplugin.CheckError(
                    "Something is wrong with user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                raise nagiosplugin.CheckError("Database does not exist")
            else:
                raise nagiosplugin.CheckError(err)

    # returns the maximun number prefixes received over the last 31 days,
    # given a peer.
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
