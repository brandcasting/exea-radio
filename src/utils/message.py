import platform

class Message:
    def __init__(self):
        self.linux = True
        self.channel = self.getChannel()
        if not self.linux:
            self.max_rows = 2  # Suponiendo que tu LCD tiene 2 filas
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
        """Muestra un mensaje en la primera fila de la pantalla."""
        if self.linux:
            self.channel.print(message, style="bold green")
        else:
            self.displayMessage(message, 0)

    def showMessageSecondRow(self, message):
        """Muestra un mensaje en la segunda fila de la pantalla."""
        if self.linux:
            self.channel.print(message, style="bold green")
        else:
            self.displayMessage(message, 1)

    def displayMessage(self, message, row):
        """Método interno para manejar la lógica de impresión en una fila específica."""
        truncated_message = self.truncateMessage(message, 16)
        self.channel.setCursor(0, row)
        self.channel.message(truncated_message + "\n")

    def truncateMessage(self, message, max_length):
        """Trunca el mensaje si supera la longitud máxima permitida."""
        return message[:max_length - 3] + '...' if len(message) > max_length else message
