from configparser import ConfigParser

class Config:
  def getConfig(self):

    try:
      config = ConfigParser()
      config.read('./config/config.ini')
    except:
        print('Unable to read config file')

    def clean(value):
        return value.strip() if value and value.strip() else None

    data = {
       'api': config.get('PLAYER', 'API_PLAYER'),
       'user': config.get('PLAYER', 'USER_PLAYER'),
       'pos': config.get('PLAYER', 'POS_PLAYER'),
       'cms': config.get('PLAYER', 'API_CMS'),
       'label': config.get('PLAYER', 'LABEL'),
       'client_id': config.get('PLAYER', 'CLIENT_ID'),
       'pause_time': clean(config.get('PLAYER', 'PAUSE_TIME')),
       'resume_time': clean(config.get('PLAYER', 'RESUME_TIME')),
    }

    return data