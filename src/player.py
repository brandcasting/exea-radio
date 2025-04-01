

from src.utils.vlcplayer import VLCPlayer
import time
import threading
import requests
from src.services.conectionService import ConectionService
from src.utils.config import Config
from src.utils.lcd import LCD
import os
import socketio

class Player():
  def __init__(self):
    self.config = Config().getConfig()
    self.conection = ConectionService()
    self.lcd = LCD()
    self.sio = socketio.Client()

  def get_local_songs(self):
    """ Obtiene la lista de canciones locales en la carpeta ./songs """
    return [os.path.join('./songs', f) for f in os.listdir('./songs') if f.endswith((".mp3", ".wav"))]
  
  def player_loop(self):
    vlc_player = VLCPlayer()
    local_songs = self.get_local_songs()
    local_index = 0  # Para recorrer canciones locales
    while True:
      # Verifica si hay internet
      data = self.fetch_next_song()

      if data:
        next_song = data['song']['url']
        self.sio.emit("statusPointofsale", {
          'pos': int(self.config['pos']),
          'idClient': self.sio.sid,
          'status': True,
          'label': self.config['user'],
          'client_pos': self.config['client_id'],
        })
      else:
        next_song = local_songs[local_index] if local_songs else None
        local_index = (local_index + 1) % len(local_songs) if local_songs else 0
        data = False

      if next_song:
        preload_thread = threading.Thread(target=vlc_player.preload_next, args=(next_song, data))
        preload_thread.start()
      else:
        self.lcd.showMessageCustom('No hay canciones disponibles en modo offline.')
        return

      # Esperar a que termine la canción actual
      while vlc_player.current_player.is_playing():
        time.sleep(1)

      # Cambiar al reproductor precargado
      vlc_player.switch_to_next()

  def fetch_next_song(self):
    """ Llama a la API para obtener la siguiente canción. """
    try:
      response = self.conection.getNext(self.config)
      if(response['code'] == 200):
        if self.sio.connected == False:
          self.sio.connect(self.config['api'], wait_timeout=5)
        return response['response']
    except requests.RequestException as e:
      return False
    return False