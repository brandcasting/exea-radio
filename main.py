from src.player import Player
import threading
import time

if __name__ == "__main__":
    player = Player()
    player_thread = threading.Thread(target=player.player_loop, daemon=True)
    player_thread.start()

    try:
        while True:
            time.sleep(1)  # Mantiene el script vivo
    except KeyboardInterrupt:
        print("Apagando radio...")
        player.scheduler.shutdown(wait=False)  # Apaga correctamente
