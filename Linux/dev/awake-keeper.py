import os
import subprocess
import sys

# =========================================================
# CONFIGURACIÓN
# =========================================================
SCRIPT_PATH = "/usr/local/bin/screen_keeper.sh"
SERVICE_PATH = "/etc/systemd/system/screen-keeper.service"

# Detectar el usuario real (no root) que usará la pantalla
# Asumimos que es el usuario que invocó sudo o el usuario 1000
try:
    REAL_USER = os.environ['SUDO_USER']
except KeyError:
    print("❌ Error: Debes ejecutar este script con 'sudo'.")
    sys.exit(1)

def log(msg):
    print(f"[Screen Keeper] {msg}")

def run_cmd(cmd):
    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        log(f"Error ejecutando: {cmd}")
        sys.exit(1)

# =========================================================
# 1. CONTENIDO DEL SCRIPT "VIGILANTE" (BASH)
# =========================================================
BASH_SCRIPT_CONTENT = f"""#!/bin/bash
# Esperar a que el servidor X (Gráfico) esté listo
export DISPLAY=:0
export XAUTHORITY=/home/{REAL_USER}/.Xauthority

# Bucle de espera hasta que X responda
until xset q > /dev/null 2>&1; do
    echo "Esperando al servidor X..."
    sleep 5
done

echo "Servidor X detectado. Aplicando configuración No-Sleep."

# 1. Forzar desactivación de ahorro de energía
xset -dpms
xset s off
xset s noblank

# 2. Bucle infinito de actividad
while true; do
    # Simular pulsación de tecla Shift izquierda (inocuo)
    # Esto engaña al sistema para que crea que hay un humano
    xdotool key Shift_L
    
    # Re-aplicar configuración por si el sistema la resetea
    xset -dpms
    xset s off
    
    sleep 60
done
"""

# =========================================================
# 2. CONTENIDO DEL SERVICIO SYSTEMD
# =========================================================
SERVICE_CONTENT = f"""[Unit]
Description=Servicio Anti-Congelamiento de Pantalla (RustDesk Fix)
After=graphical.target systemd-user-sessions.service

[Service]
# Ejecutar como el usuario real para tener acceso al Display :0
User={REAL_USER}
Group={REAL_USER}
Environment=DISPLAY=:0
ExecStart={SCRIPT_PATH}
Restart=always
RestartSec=10

[Install]
WantedBy=graphical.target
"""

# =========================================================
# INSTALACIÓN
# =========================================================
def main():
    if os.geteuid() != 0:
        log("Por favor ejecuta con sudo.")
        sys.exit(1)

    log(f"Instalando para el usuario: {REAL_USER}")

    # 1. Instalar dependencias
    log("Instalando xdotool (necesario para simular actividad)...")
    run_cmd("apt-get update && apt-get install -y xdotool x11-xserver-utils")

    # 2. Crear el script bash
    log(f"Creando script en {SCRIPT_PATH}...")
    with open(SCRIPT_PATH, "w") as f:
        f.write(BASH_SCRIPT_CONTENT)
    
    # Hacerlo ejecutable
    run_cmd(f"chmod +x {SCRIPT_PATH}")

    # 3. Crear el servicio
    log(f"Creando servicio en {SERVICE_PATH}...")
    with open(SERVICE_PATH, "w") as f:
        f.write(SERVICE_CONTENT)

    # 4. Activar
    log("Activando servicio...")
    run_cmd("systemctl daemon-reload")
    run_cmd("systemctl enable screen-keeper.service")
    run_cmd("systemctl restart screen-keeper.service")

    log("✅ Instalación completada.")
    log("El servicio 'screen-keeper' mantendrá la pantalla activa automáticamente.")

if __name__ == "__main__":
    main()