from configparser import ConfigParser

class Config:
  def getConfig(self):

    try:
      config = ConfigParser()
      config.read('./config/config.ini')
    except:
        print('Unable to read config file ../../config/config.ini')
    data = {
       'api': config.get('PLAYER', 'API_PLAYER'),
       'user': config.get('PLAYER', 'USER_PLAYER'),
       'pos': config.get('PLAYER', 'POS_PLAYER'),
       'cms': config.get('PLAYER', 'API_CMS'),
    }
    return data