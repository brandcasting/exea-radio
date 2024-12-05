import socket
from src.utils.message import Message

class LCD:
  def __init__(self):
    self.message = Message()

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
      message = ip
    else:
      message = 'Error detectando'
    self.message.showMessage(message)

  def showNotInternet(self):
    self.message.showMessage('Sin internet')
  
  def showMessageCustom(self, message):
    self.message.showMessage(message)