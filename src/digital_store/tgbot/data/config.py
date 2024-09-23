from configparser import ConfigParser

reader = ConfigParser()
reader.read('tgbot/data/settings.ini')

settings = reader['settings']
token = settings['token']
admin_ids = [int(i) for i in settings['admins_ids'].split(',') if i.strip()]
p2p_token = settings['p2p_token']
receiver = settings['receiver']
database_path = 'sqlite:///tgbot/data/database.db'
