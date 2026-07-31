#!/data/data/com.termux/files/usr/bin/bash
# Script de inicio para Termux - Servidor SMS Android
# Corre el servidor con wake-lock y auto-reinicio

echo "=== Iniciando Servidor SMS ==="

# Mantener el telefono despierto
termux-wake-lock
echo "[OK] Wake lock adquirido"

# Loop infinito: si el servidor se cae (ej: cambio de red), se reinicia solo
while true; do
    echo "[$(date +%H:%M:%S)] Iniciando server_android.py..."
    python ~/server_android.py
    EXIT_CODE=$?
    echo "[$(date +%H:%M:%S)] server_android.py termino con codigo $EXIT_CODE"
    echo "[$(date +%H:%M:%S)] Esperando 3s antes de reiniciar..."
    sleep 3
done
