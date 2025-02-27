import pygame
import glob
import os
import requests
import random
from src.utils.config import Config
from src.services.conectionService import ConectionService;
import vlc
from src.utils.lcd import LCD
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import socketio


class Player():
  def __init__(self):
    self.config = Config().getConfig()
    self.lcd = LCD()
    self.sio = socketio.Client()
    pygame.init()
    pygame.mixer.init()
    pygame.mixer.music.set_endevent(pygame.USEREVENT)
    self.scheduler = BackgroundScheduler()
    self.player: vlc.MediaPlayer = vlc.MediaPlayer()

  #Inicialización de player 
  def initPlayer(self):
    #Valido si hay internet
    if self.checkConection():
      self.playerPointOfSale()
    else:
      #Suena el backup
      self.backupSong()
  
  #Función para validar internet
  def checkConection(self):
    try:
      response = requests.head("https://www.google.com", timeout=5)
      if response.status_code == 200:
        if self.sio.connected == False:
          self.sio.connect(self.config['api'], wait_timeout=5)
          self.sio.on("notification_transmission", self.on_notification_transmission)
        return True
    except requests.ConnectionError:
      return False
    return False
  
  def backupSong(self):
    folder = glob.glob(os.path.join('./songs', '*.mp3'))
    random.shuffle(folder)
    if (folder):
      for file in folder:
        media = vlc.Media(file)
        self.player.set_media(media)
        self.lcd.showNotInternet()
        try:
          self.player.play()
          self.lcd.showMessageCustom('Song: backup')
        except Exception:
          self.lcd.showMessageCustom('Error play song backup')

        while True:
          if self.player.get_state() == vlc.State.Ended:
            if self.checkConection():
              return self.playerPointOfSale()
            break
        if file == folder[-1]:
          self.backupSong()
    else:
      self.lcd.showMessageCustom('Carpeta Backup Vacia')
    
  #Consulta de reglas punto de venta
  def playerPointOfSale(self):
    self.lcd.showIp()
    try:
      conection = ConectionService()
      response = conection.getNext(self.config)
      if(response['code'] == 200):
        if (response['response']['rules_hours']):
          self.rulesByHours(response['response']['rules_hours'])
        self.player.stop()
        song = response['response']['song']
        media = vlc.Media(song['url'])
        self.player.set_media(media)
        self.player.play()
        conection.logSong(response['response'], self.config)
        self.sio.emit("statusPointofsale", {
          'pos': int(self.config['pos']),
          'idClient': self.sio.sid,
          'status': True,
          'label': self.config['user'],
          'client_pos': self.config['client_id'],
        })
        self.lcd.showMessageCustom("Song:" + song['title'])
        while True:
          state = self.player.get_state()
          if state == vlc.State.Ended:
            self.initPlayer()
      else:
        self.lcd.showMessageCustom('Backup - Rules Error')
        self.backupSong()
    except Exception as e:
        self.backupSong()

  def rulesByHours(self, rules):
    existing_jobs = {job.id for job in self.scheduler.get_jobs()}
    for rule in rules:
      if (rules[rule]):
        for index, hour in enumerate(rules[rule]['hours']):
          target_time = datetime.fromtimestamp(hour / 1000.0)
          job_id = f"job_{rule}_{index}"
          if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
          self.scheduler.add_job(self.songByTime, 'date', run_date=target_time, args=[rules[rule], rule], id=job_id)
    if (self.scheduler.running == False):
      self.scheduler.start()
    return True

  def songByTime(self, rule, id):
    conection = ConectionService()
    response = conection.songByRule(rule['id'], self.config)
    self.player.stop()
    song = response['response']['song']
    media = vlc.Media(song['url'])
    self.player.set_media(media)
    self.player.play()
    response['response']['ruleId'] = id
    response['response']['name'] = rule['name']
    conection.logSong(response['response'], self.config)
    
    self.lcd.showMessageCustom("Song:" + song['title'] )
    while True:
      state = self.player.get_state()
      if state == vlc.State.Ended:
        """ self.initPlayer() """
  
  def on_notification_transmission(self, data):
    if str(data['point_of_sale']) == self.config['pos']:
      self.lcd.showIp()
      conection = ConectionService()
      self.player.stop()
      media = vlc.Media(data['url_song'])
      self.player.set_media(media)
      self.player.play()
      song = {
        "song": {
          "title": data['title'],
          "artist": 'Botonera',
          "id": data['song_id']
        },
        "ruleId": 0,
        "name": "Botonera"
      }
      conection.logSong(song, self.config)
      self.lcd.showMessageCustom("Botonera - Song:" + data['title'])
      while True:
        state = self.player.get_state()
        if state == vlc.State.Ended:
          self.sio.emit("notification_transmission_end", data)
          return