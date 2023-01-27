import configparser
import os
import nagiosplugin


def config_check():
    config = configparser.ConfigParser()
    if not os.path.exists('./config.ini'):
        config['credentials'] = {'user': '',
                                 'password': '',
                                 'host': '',
                                 'database': '',
                                 'port': 3306
                                 }
        config.write(open('config.ini', 'w'))
        raise nagiosplugin.CheckError(
            'Could not find config.ini, a template file '
            'was created with the fields needed to connect to the database.')
