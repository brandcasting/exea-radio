import platform
import time  # Para delays en el scroll

class Message:
    def __init__(self):
        self.linux = True
        self.channel = self.getChannel()
        if not self.linux:
            self.max_rows = 2
            self.max_cols = 16  # Asumiendo un display de 16x2
            self.channel.begin(1, 2)

    def getChannel(self):
        if platform.machine() in ['x86_64', 'arm64']:
            from rich.console import Console
            return Console()
        else:
            from src.utils.GPIOlibrary import GPIOlibrary
            self.linux = False
            return GPIOlibrary()

    def showMessageFirstRow(self, message):
        if self.linux:
            self.channel.print(message, style="bold green")
        else:
            self.displayMessage(message, 0)

    def showMessageSecondRow(self, message):
        if self.linux:
            self.channel.print(message, style="bold green")
        else:
            self.displayMessage(message, 1)

    def displayMessage(self, message, row):
        if len(message) <= self.max_cols:
            self.channel.setCursor(0, row)
            self.channel.message(message.ljust(self.max_cols))
        else:
            self.scrollMessage(message, row)

    def scrollMessage(self, message, row, delay=0.3, padding=4):
        """Desplaza el mensaje horizontalmente si es más largo que la pantalla."""
        scroll_text = message + " " * padding  # Espacio para hacer loop visualmente
        for i in range(len(scroll_text) - self.max_cols + 1):
            self.channel.setCursor(0, row)
            part = scroll_text[i:i + self.max_cols]
            self.channel.message(part)
            time.sleep(delay)

    def truncateMessage(self, message, max_length):
        return message[:max_length - 3] + '...' if len(message) > max_length else message
