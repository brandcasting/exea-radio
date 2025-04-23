import vlc
from src.services.conectionService import ConectionService
from src.utils.config import Config
from src.utils.lcd import LCD
import requests

class VLCPlayer:
  def __init__(self):
    self.config = Config().getConfig()
    self.conection = ConectionService()
    self.current_player = vlc.MediaPlayer()
    self.next_player = vlc.MediaPlayer()
    self.data = False
    self.loading_next = False
    self.next_song_url = None  # Guarda la URL de la siguiente canción
    self.lcd = LCD()

  def check_internet(self):
    try:
      requests.get("https://www.google.com", timeout=5)
      return True
    except requests.RequestException:
      return False

  def play(self, file):
    """ Reproduce una canción en el reproductor actual. """
    media = vlc.Media(file)
    self.current_player.set_media(media)
    self.current_player.play()
    while True:
      state = self.current_player.get_state()
      if state == vlc.State.Ended:
        return True

  def preload_next(self, song, data):
    """ Precarga la siguiente canción en otro reproductor. """
    self.data = data
    media = vlc.Media(song)
    self.next_player.set_media(media)
    self.loading_next = True  # Indica que hay una canción pre-cargada

  def switch_to_next(self):
    """ Cambia al reproductor precargado y lo inicia. """
    if self.loading_next:
      self.current_player.stop()
      self.current_player = self.next_player  # Cambia de reproductor
      self.current_player.play()
      self.lcd.showIp()
      try:
        message = "Song:"+ self.data['song']['title']
        self.conection.logSong(self.data, self.config)
      except Exception as e:
        print(e)
        message = "Song: Backup"
      self.lcd.showMessageCustom(message)
      self.next_player = vlc.MediaPlayer()  # Crea un nuevo reproductor para la siguiente canción
      self.loading_next = False

  def songByTime(self, rule, id):
    response = self.conection.songByRule(rule['id'], self.config)
    self.current_player.stop()
    song = response['response']['song']
    media = vlc.Media(song['url'])
    self.current_player.set_media(media)
    self.current_player.play()
    response['response']['ruleId'] = id
    response['response']['name'] = rule['name']
    self.conection.logSong(response['response'], self.config)
    self.lcd.showMessageCustom("Song exact time:" + song['title'] )
    while True:
      state = self.current_player.get_state()
      if state == vlc.State.Ended:
        """ self.initPlayer() """