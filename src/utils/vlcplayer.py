import vlc
from src.services.conectionService import ConectionService
from src.utils.config import Config
from src.utils.lcd import LCD
import threading
import requests
import time

class VLCPlayer:
  def __init__(self):
    self.config = Config().getConfig()
    self.conection = ConectionService()
    self.current_player = vlc.MediaPlayer()
    self.next_player = vlc.MediaPlayer()
    self.data = False
    self.loading_next = False
    self.next_song_url = None  # Guarda la URL de la siguiente canción
    self.lock = threading.RLock()
    self.special_lock = threading.Lock()
    self.special_active = False
    self.lcd = LCD()

  def check_internet(self):
    try:
      requests.get("https://www.google.com", timeout=5)
      return True
    except requests.RequestException:
      return False
    
  def wait_until_playing(self, player, timeout=10):
    """ Espera hasta que el reproductor entre en estado Playing o se agote el tiempo. """
    import time
    start = time.time()
    while time.time() - start < timeout:
        state = player.get_state()
        if state == vlc.State.Playing:
            return True
        elif state in (vlc.State.Error, vlc.State.Ended):
            return False
        time.sleep(0.2)
    return False

  def wait_until_finished(self, player, max_buffer=35):
    """Return ended/error/interrupted; never spin at full CPU."""
    stalled_since = time.monotonic()
    last_position = -1
    while True:
      with self.lock:
        if self.current_player is not player:
          return 'interrupted'
        state = player.get_state()
        position = player.get_time()
      if state == vlc.State.Ended:
        return 'ended'
      if state == vlc.State.Error:
        return 'error'
      if position >= 0 and position > last_position:
        last_position = position
        stalled_since = time.monotonic()
      if time.monotonic() - stalled_since > max_buffer:
        return 'stalled'
      time.sleep(0.2)

  def play(self, file):
    """Botonera: interrumpe música, luego devuelve control al ciclo normal."""
    with self.special_lock:
      with self.lock:
        self.special_active = True
        self.current_player.stop()
        player = vlc.MediaPlayer()
        self.current_player = player
        player.set_media(vlc.Media(file))
        player.play()
      try:
        if not self.wait_until_playing(player):
          return False
        return self.wait_until_finished(player) == 'ended'
      finally:
        with self.lock:
          player.stop()
          self.special_active = False


  def preload_next(self, song, data):
    """ Precarga la siguiente canción en otro reproductor. """
    with self.lock:
      self.data = data
      media = vlc.Media(song)
      self.next_player.set_media(media)
      self.loading_next = True

  def switch_to_next(self):
    with self.lock:
      if not self.loading_next or self.special_active:
        return False
      self.current_player.stop()
      candidate = self.next_player
      self.current_player = candidate
      song_data = self.data
      self.next_player = vlc.MediaPlayer()
      self.loading_next = False
      candidate.play()
    if not self.wait_until_playing(candidate, timeout=10):
      with self.lock:
        candidate.stop()
      return False
    with self.lock:
      if self.current_player is not candidate or self.special_active:
        return False
    try:
      self.lcd.showIp()
      message = 'Song:' + song_data['song']['title'] if song_data else 'Song: Backup'
      self.lcd.showMessageCustom(message)
      if song_data:
        self.conection.logSong(song_data, self.config)
    except Exception as exc:
      print('Aviso registrando canción:', exc, flush=True)
    return True


  def songByTime(self, rule, id):
    with self.special_lock:
      try:
        response = self.conection.songByRule(rule['id'], self.config)
        song = response['response']['song']
        with self.lock:
          self.special_active = True
          self.current_player.stop()
          player = vlc.MediaPlayer()
          self.current_player = player
          player.set_media(vlc.Media(song['url']))
          player.play()
        if not self.wait_until_playing(player):
          print('Error iniciando cuña programada', flush=True)
          return
        response['response'].update(ruleId=id, name=rule['name'], type='rules_default')
        try:
          self.conection.logSong(response['response'], self.config)
          self.lcd.showMessageCustom('Song exact time:' + song['title'])
        except Exception as exc:
          print('Aviso registrando cuña:', exc, flush=True)
        self.wait_until_finished(player)
      except Exception as exc:
        print('Error en cuña programada:', exc, flush=True)
      finally:
        with self.lock:
          if self.special_active:
            self.current_player.stop()
          self.special_active = False
