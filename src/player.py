

from src.utils.vlcplayer import VLCPlayer
import time
import threading
import requests
from src.services.conectionService import ConectionService
from src.utils.config import Config
from src.utils.lcd import LCD
import os
import socketio
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import functools

class Player():
  def __init__(self):
    self.config = Config().getConfig()
    self.conection = ConectionService()
    self.lcd = LCD()
    self.sio = socketio.Client()
    self.scheduler = BackgroundScheduler(daemon=True)
    self.pause_event = threading.Event()  # Evento para controlar la pausa
    self.pause_event.set()
    if not self.scheduler.running:
      self.scheduler.start(paused=False)

  def pause(self, resume_time_str):
    self.lcd.showIp()
    self.lcd.showMessageCustom(f"Pausado hasta {resume_time_str}")
    self.pause_event.clear()  # Bloquea el player_loop

  def resume(self):
    self.pause_event.set()

  def get_local_songs(self):
    return [os.path.join('./songs', f) for f in os.listdir('./songs') if f.endswith((".mp3", ".wav"))]
  
  def player_loop(self):
    vlc_player = VLCPlayer()
    local_songs = self.get_local_songs()
    local_index = 0  # Para recorrer canciones locales
    while True:
      # Verifica si hay internet
      data = self.fetch_next_song(vlc_player)

      if data:
        if (data['rules_hours']):
          self.rulesByHours(data['rules_hours'], vlc_player)
        next_song = data['song']['url']
        self.sio.emit("statusPointofsale", {
          'pos': int(self.config['pos']),
          'idClient': self.sio.sid,
          'status': True,
          'label': self.config['label'],
          'client_pos': self.config['client_id'],
          'type': 'radio'
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
        self.pause_event.wait()

      # Cambiar al reproductor precargado
      vlc_player.switch_to_next()

  def fetch_next_song(self, vlc_player):
    """ Llama a la API para obtener la siguiente canción. """
    try:
      response = self.conection.getNext(self.config)
      if(response['code'] == 200):
        if self.sio.connected == False:
          self.sio.connect(self.config['api'], wait_timeout=5)
          self.sio.on("notification_transmission", functools.partial(self.on_notification_transmission, vlc_player))
        return response['response']
    except Exception as e:
      return False
    return False
  
  def rulesByHours(self, rules, vlc_player):
    existing_jobs = {job.id for job in self.scheduler.get_jobs()}
    for rule in rules:
      if rules[rule]:  # Validar que la regla existe
        for index, hour in enumerate(rules[rule]['hours']):
            target_time = datetime.fromtimestamp(hour / 1000.0)  # Convertir a datetime
            if target_time <= datetime.now():
                continue
            job_id = f"job_{rule}_{index}"
            if job_id in existing_jobs:
                self.scheduler.remove_job(job_id)
            self.scheduler.add_job(
                vlc_player.songByTime, 
                'date', 
                run_date=target_time, 
                args=[rules[rule], rule], 
                id=job_id,
                misfire_grace_time=3600  # Permite ejecutar con hasta 1 hora de retraso
            )
    return True
  
  def on_notification_transmission(self, vlc_player, data ):
    if str(data['point_of_sale']) == self.config['pos']:
      self.lcd.showIp()
      song = {
        "song": {
          "title": data['title'],
          "artist": 'Botonera',
          "id": data['song_id']
        },
        "ruleId": 0,
        "name": "Botonera"
      }
      self.conection.logSong(song, self.config)
      self.lcd.showMessageCustom("Botonera - Song:" + data['title'])
      state = vlc_player.play(data['url_song'])
      if state:
        self.sio.emit("notification_transmission_end", data)