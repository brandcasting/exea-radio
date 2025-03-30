from src.player import Player
import threading

if __name__ == "__main__":
    player = Player()
    player_thread = threading.Thread(target=player.player_loop)
    player_thread.start()