from src.player import Player
import threading
import time
from datetime import datetime
from src.utils.config import Config

def parse_time_str(time_str):
	"""Convierte una cadena 'HH:MM' en un objeto datetime.time."""
	hour, minute = map(int, time_str.split(":"))
	return hour, minute

def is_within_range(start_hour, start_minute, end_hour, end_minute, now):
	"""Devuelve True si `now` está dentro del rango de tiempo definido."""
	start = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
	end = now.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)

	# Si el rango cruza medianoche
	if start > end:
		return now >= start or now <= end
	else:
		return start <= now <= end

def schedule_pause_resume(player, pause_time_str, resume_time_str):
	pause_hour, pause_minute = parse_time_str(pause_time_str)
	resume_hour, resume_minute = parse_time_str(resume_time_str)

	paused = None  # Estado desconocido al inicio

	while True:
		now = datetime.now()
		in_pause_range = is_within_range(pause_hour, pause_minute, resume_hour, resume_minute, now)

		if in_pause_range and paused != True:
			player.pause(resume_time_str)
			paused = True

		elif not in_pause_range and paused != False:
			player.resume()
			paused = False

		time.sleep(30)  # Verifica cada 30 segundos

if __name__ == "__main__":
	config = Config().getConfig() 
	player = Player()
	player_thread = threading.Thread(target=player.player_loop, daemon=True)
	player_thread.start()

	hora_pausa = "20:10"
	hora_reanudar = "21:45"

	control_thread = threading.Thread(
		target=schedule_pause_resume,
		args=(player, config['pause_time'], config['resume_time']),
		daemon=True
	)
	control_thread.start()

	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		print("Apagando radio...")
		player.scheduler.shutdown(wait=False)
