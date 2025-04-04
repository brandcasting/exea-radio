import socket
from src.utils.message import Message
import os
from datetime import datetime

class LCD:
  def __init__(self):
    self.message = Message()
    self.log_file = os.path.join('logs', "app.log")

  @staticmethod
  def getIp():
    try:
      s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      s.connect(("8.8.8.8", 80))
      ip_address = s.getsockname()[0]
      s.close()
      return ip_address
    except Exception as e:
        return False

  def showIp(self):
    ip = self.getIp()
    if ip:
      message = f"{ip} Online"
    else:
      message = 'Sin internet'
    self.message.showMessageFirstRow(message)
    hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(self.log_file, "a") as file:  # "a" para añadir sin sobrescribir
      file.write(f"[{hora_actual}] {message}.\n")
  
  def showMessageCustom(self, message):
    self.message.showMessageSecondRow(message)
    hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(self.log_file, "a") as file:  # "a" para añadir sin sobrescribir
      file.write(f"[{hora_actual}] {message}.\n")