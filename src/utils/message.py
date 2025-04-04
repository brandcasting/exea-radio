import platform
import time
import threading

class Message:
    def __init__(self):
        self.linux = True
        self.channel = self.getChannel()
        self.max_cols = 16
        self.max_rows = 2
        self.scroll_threads = [None, None]  # Uno por fila
        self.scroll_flags = [False, False]  # Control de ejecución del scroll

        if not self.linux:
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
        self.showMessage(message, 0)

    def showMessageSecondRow(self, message):
        self.showMessage(message, 1)

    def showMessage(self, message, row):
        if self.linux:
            self.channel.print(f"Fila {row + 1}: {message}", style="bold green")
        else:
            if len(message) <= self.max_cols:
                self._stopScroll(row)  # Asegúrate de detener scroll anterior si hay
                self.channel.setCursor(0, row)
                self.channel.message(message.ljust(self.max_cols))
            else:
                self._startScrollThread(message, row)

    def _startScrollThread(self, message, row, delay=0.3, padding=4):
        self._stopScroll(row)  # Detenemos scroll anterior si existe

        def scroll():
            scroll_text = message + " " * padding
            self.scroll_flags[row] = True
            while self.scroll_flags[row]:
                for i in range(len(scroll_text) - self.max_cols + 1):
                    if not self.scroll_flags[row]:
                        break
                    part = scroll_text[i:i + self.max_cols]
                    self.channel.setCursor(0, row)
                    self.channel.message(part)
                    time.sleep(delay)

        thread = threading.Thread(target=scroll, daemon=True)
        self.scroll_threads[row] = thread
        thread.start()

    def _stopScroll(self, row):
        """Detiene el scroll en una fila específica."""
        self.scroll_flags[row] = False
        thread = self.scroll_threads[row]
        if thread and thread.is_alive():
            thread.join(timeout=0.1)
        self.scroll_threads[row] = None
