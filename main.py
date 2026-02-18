from src.player import Player
import threading
import time
from datetime import datetime
from src.utils.config import Config


def parse_time_str(time_str):
	"""
	Convierte una cadena con formato 'HH:MM' en dos enteros: hora y minuto.
	Ejemplo: "23:45" -> (23, 45)
	"""
	hour, minute = map(int, time_str.split(":"))
	return hour, minute


def is_within_range(start_hour, start_minute, end_hour, end_minute, now):
	"""
	Devuelve True si la fecha/hora actual (`now`) está dentro del rango definido
	por (start_hour:start_minute) y (end_hour:end_minute).

	Soporta rangos que cruzan medianoche.
	Ejemplo:
	  22:00 a 06:00 -> válido desde las 10pm hasta las 6am del día siguiente.
	"""
	start = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
	end = now.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)

	# Si el rango cruza medianoche (por ejemplo: 22:00 -> 06:00)
	if start > end:
		return now >= start or now <= end
	else:
		return start <= now <= end


def schedule_pause_resume(player, pause_time_str, resume_time_str):
	"""
	Hilo que revisa constantemente la hora y decide si debe:
	- Pausar el reproductor
	- Reanudar el reproductor

	Usa las horas configuradas en pause_time_str y resume_time_str.
	"""
	pause_hour, pause_minute = parse_time_str(pause_time_str)
	resume_hour, resume_minute = parse_time_str(resume_time_str)

	paused = None  # Estado inicial desconocido (ni pausado ni reproduciendo forzado)

	while True:
		now = datetime.now()
		
		# Verifica si estamos dentro del rango de pausa
		in_pause_range = is_within_range(
			pause_hour,
			pause_minute,
			resume_hour,
			resume_minute,
			now
		)

		# Si estamos en horario de pausa y aún no se ha pausado
		if in_pause_range and paused != True:
			player.pause(resume_time_str)  # Pausa el reproductor
			paused = True

		# Si no estamos en horario de pausa y aún no se ha reanudado
		elif not in_pause_range and paused != False:
			player.resume()  # Reanuda el reproductor
			paused = False

		# Espera 30 segundos antes de volver a revisar la hora
		time.sleep(30)


if __name__ == "__main__":
	# Carga la configuración desde archivo o entorno
	config = Config().getConfig() 
	
	# Crea el reproductor
	player = Player()

	# Hilo principal del reproductor (streaming, reproducción, etc.)
	player_thread = threading.Thread(
		target=player.player_loop,
		daemon=True  # Se cierra automáticamente al cerrar el programa
	)
	player_thread.start()

	# Hilo que controla pausas y reanudaciones por horario
	control_thread = threading.Thread(
		target=schedule_pause_resume,
		args=(player, config['pause_time'], config['resume_time']),
		daemon=True
	)
	control_thread.start()

	# Mantiene vivo el programa principal
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		print("Apagando radio...")
		# Apaga el scheduler interno del player sin esperar tareas pendientes
		player.scheduler.shutdown(wait=False)
