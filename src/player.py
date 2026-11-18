

from src.utils.vlcplayer import VLCPlayer
import time
import threading
from src.services.conectionService import ConectionService
from src.utils.config import Config
from src.utils.lcd import LCD
import os
import socketio
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import functools
from urllib.parse import quote

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
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'songs')
    folder = os.path.abspath(folder)
    return sorted(os.path.join(folder, f) for f in os.listdir(folder)
      if f.lower().endswith((".mp3", ".wav")))
  
  def player_loop(self):
    vlc_player = VLCPlayer()
    local_songs = self.get_local_songs()
    local_index = 0
    while True:
      self.pause_event.wait()
      with vlc_player.lock:
        special = vlc_player.special_active
      if special:
        time.sleep(0.2)
        continue

      data = self.fetch_next_song(vlc_player)
      if data:
        try:
          if data.get('rules_hours'):
            self.rulesByHours(data['rules_hours'], vlc_player)
          uri_encoded = quote(data['song']['uri'], safe="~()*!.'-_")
          next_song = data['url_media'] + '/s3fs-public' + uri_encoded
          print(next_song)
          print(data['song'])
          print(data)
        except (KeyError, TypeError) as exc:
          print('Respuesta musical inválida:', exc, flush=True)
          data = False
        if data and self.sio.connected:
          try:
            self.sio.emit('statusPointofsale', {
              'pos': int(self.config['pos']), 'idClient': self.sio.sid,
              'status': True, 'label': self.config['label'],
              'client_pos': self.config['client_id'], 'type': 'radio'})
          except Exception as exc:
            print('Aviso enviando estado:', exc, flush=True)

      if data:
        vlc_player.preload_next(next_song, data)
        success = vlc_player.switch_to_next()
        if success:
          player = vlc_player.current_player
          started_at = time.monotonic()
          result = vlc_player.wait_until_finished(player)
          # URLs que se cortan a los pocos segundos también son fallas.
          if result == 'ended' and time.monotonic() - started_at >= 20:
            continue
          if result == 'interrupted':
            continue
          print('Fallo de canción online:', result, flush=True)
        else:
          print('Fallo al iniciar canción online; usando respaldo', flush=True)

      # Una canción local completa antes de volver a consultar la API.
      # Si falla un archivo local, probar otro (máximo 5 por ciclo).
      if not local_songs:
        print('ERROR: no hay canciones locales disponibles', flush=True)
        time.sleep(10)
        continue
      for attempt in range(min(5, len(local_songs))):
        self.pause_event.wait()
        with vlc_player.lock:
          if vlc_player.special_active:
            break
        backup = local_songs[local_index]
        local_index = (local_index + 1) % len(local_songs)
        vlc_player.preload_next(backup, False)
        if not vlc_player.switch_to_next():
          print('No inicia respaldo:', backup, flush=True)
          continue
        started_at = time.monotonic()
        result = vlc_player.wait_until_finished(vlc_player.current_player)
        if result == 'interrupted':
          break
        if result == 'ended' and time.monotonic() - started_at >= 20:
          break
        print('Respaldo falló:', result, backup, flush=True)
      else:
        time.sleep(5)

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
      print('Error consultando API:', e, flush=True)
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
        "name": "Botonera",
        'type': 'botonera'
      }
      self.conection.logSong(song, self.config)
      self.lcd.showMessageCustom("Botonera - Song:" + data['title'])
      state = vlc_player.play(data['url_song'])
      if state:
        self.sio.emit("notification_transmission_end", data)
