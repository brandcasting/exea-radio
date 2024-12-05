# Verificar el estado del servicio
if [ "$(sudo systemctl is-active player.service)" == 'failed' ]; then
    # El servicio está pausado, iniciarlo
    sudo systemctl start player.service
else
    # El servicio no está pausado
    echo "El servicio player.service ya está en ejecución."
fi