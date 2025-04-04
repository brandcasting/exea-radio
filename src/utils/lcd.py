import platform
import time
import threading
import queue

class Message:
    def __init__(self):
        self.linux = True
        self.channel = self.getChannel()
        self.message_queue = queue.Queue()
        self.display_thread = threading.Thread(target=self._process_messages, daemon=True)
        self.display_thread.start()
        
        if not self.linux:
            self.max_chars = 16  # ancho de la pantalla
            self.max_rows = 2
            self.current_row = 0

    def getChannel(self):
        if platform.machine() == 'x86_64' or platform.machine() == 'arm64':
            from rich.console import Console
            return Console()
        else:
            from src.utils.GPIOlibrary import GPIOlibrary
            self.linux = False
            return GPIOlibrary()

    def showMessage(self, message):
        # Agrega el mensaje a la cola para ser mostrado
        self.message_queue.put(message)

    def _process_messages(self):
        while True:
            message = self.message_queue.get()  # Espera a que haya un mensaje
            if self.linux:
                self.channel.print(message, style="bold green")
            else:
                self.channel.begin(1, 2)
                self.channel.setCursor(0, self.current_row)

                if len(message) <= self.max_chars:
                    self.channel.message(message.ljust(self.max_chars) + "\n")
                    time.sleep(2)  # Espera un poco antes de mostrar el siguiente
                else:
                    full_message = message + " " * 4
                    for i in range(len(full_message) - self.max_chars + 1):
                        self.channel.setCursor(0, self.current_row)
                        self.channel.message(full_message[i:i + self.max_chars] + "\n")
                        time.sleep(0.3)  # Velocidad del scroll

                self.current_row += 1
                if self.current_row >= self.max_rows:
                    self.current_row = 0
                    self.channel.clear()

            self.message_queue.task_done()
