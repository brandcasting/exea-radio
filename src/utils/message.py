import platform
import time

class Message:
  def __init__(self):
    self.linux = True
    self.channel = self.getChannel()
    if not self.linux:
      self.current_row = 0
      self.max_rows = 2  # Suponiendo que tu LCD tiene 2 filas
      self.max_chars = 16  # Número máximo de caracteres visibles en la pantalla

  def getChannel(self):
    if platform.machine() == 'x86_64' or platform.machine() == 'arm64':
      from rich.console import Console
      return Console()
    else:
      from src.utils.GPIOlibrary import GPIOlibrary
      self.linux = False
      return GPIOlibrary()

  def showMessage(self, message, scroll_speed=0.3):
    if self.linux:
      self.channel.print(message, style="bold green")
    else:
      self.channel.begin(1, 2)
      self.channel.setCursor(0, self.current_row)
      
      if len(message) <= self.max_chars:
        # Si el mensaje cabe en la pantalla, se muestra directamente
        self.channel.message(message.ljust(self.max_chars) + "\n")
      else:
        # Si el mensaje es más largo, se desplaza de derecha a izquierda
        full_message = message + " " * 4  # Espaciado para un mejor bucle
        for i in range(len(full_message) - self.max_chars + 1):
          self.channel.setCursor(0, self.current_row)
          self.channel.message(full_message[i:i + self.max_chars] + "\n")
          time.sleep(scroll_speed)  # Controla la velocidad del desplazamiento

      self.current_row += 1
      if self.current_row >= self.max_rows:
        self.current_row = 0
        self.channel.clear()
