import configparser
import os.path


def check_config():
    if os.path.isfile('src/config.ini'):
        return('Using existing config.')
    else:
        config = configparser.ConfigParser()
        config['Settings'] = {'Bot_token': 'token', 'Bot_prefix': '-', 'DB_host': 'localhost',
                              'DB_db': 'database', 'DB_user': 'username', 'DB_pass': 'password'}
        with open('src/config.ini', 'w') as config_file:
            config.write(config_file)
        return('Config file does not exist. Creating with default values.')


def read(setting):
    config = configparser.ConfigParser()
    config.read('src/config.ini')
    return(config['Settings'][setting])