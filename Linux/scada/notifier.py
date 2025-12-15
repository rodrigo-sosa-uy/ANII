import time
import re
import requests
import os
import urllib3

# --- CONFIGURACIÓN ESPECÍFICA DEL DISPOSITIVO ---
DEVICE_REGION = "SO"
#DEVICE_REGION = "CS"
#DEVICE_REGION = "E"

# --- CONFIGURACIÓN DE TELEGRAM ---
if DEVICE_REGION == "SO":
    BOT_TOKEN = "8570350769:AAGSjPs9-rCCdg6LFk1KJ88jVCN4TosBMSY"
elif DEVICE_REGION == "CS":
    BOT_TOKEN = "8353406476:AAGLcsu-O0Nh_6_f32ARE9TyGuqF3DCi0qo"
elif DEVICE_REGION == "E":
    BOT_TOKEN = "8454182171:AAHwSK2J_O_SSTsXzhKR_MFJx06o-01V5iU"

# LISTA DE USUARIOS
CHAT_IDS = [
    "7289719287"
    # "987654321",
    # "123456789"
]

LOG_FILE = "/var/log/scada-tunnel.log"

# Desactivar advertencias SSL (por la red de la UTEC)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def log(msg):
    print(f"[Notificador {DEVICE_REGION}] {msg}")

def enviar_telegram_multiusuario(mensaje_base):
    """Envía el mensaje a todos los usuarios de la lista"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    # Agregamos la cabecera de región al mensaje
    mensaje_completo = f"📍 **REGIÓN: {DEVICE_REGION}**\n{mensaje_base}"
    
    envios_exitosos = 0
    
    for usuario_id in CHAT_IDS:
        data = {
            'chat_id': usuario_id, 
            'text': mensaje_completo, 
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        
        try:
            # verify=False es clave para tu red
            requests.post(url, data=data, verify=False, timeout=10)
            log(f"Mensaje enviado a {usuario_id}.")
            envios_exitosos += 1
        except Exception as e:
            log(f"Error enviando a {usuario_id}: {e}")
            
    return envios_exitosos > 0

def buscar_url_en_log():
    """Lee el log y busca la última URL de trycloudflare.com"""
    if not os.path.exists(LOG_FILE):
        return None
        
    try:
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()
            
        # Leemos de atrás hacia adelante para encontrar la más reciente
        for line in reversed(lines):
            # Regex para encontrar https://algo-random.trycloudflare.com
            match = re.search(r'(https://[a-zA-Z0-9-]+\.trycloudflare\.com)', line)
            if match:
                return match.group(1)
    except Exception as e:
        log(f"Error leyendo log: {e}")
    
    return None

def main():
    log("Iniciando búsqueda de URL del túnel...")
    
    # Intentos: Esperamos hasta 2 minutos (12 intentos de 10s)
    # Porque Cloudflare puede tardar en arrancar o Wifi-Keeper en dar internet
    intentos = 0
    url_encontrada = None
    
    while intentos < 12:
        url_encontrada = buscar_url_en_log()
        
        if url_encontrada:
            # Encontramos una URL
            break
        
        log(f"URL no encontrada aún. Intento {intentos+1}/12. Esperando...")
        time.sleep(10)
        intentos += 1
        
    if url_encontrada:
        mensaje = (
            f"🟢 **SISTEMA INICIADO**\n"
            f"El dispositivo se ha recuperado de un reinicio.\n\n"
            f"🌍 **Nueva URL SCADA:**\n"
            f"`{url_encontrada}`"
        )
        enviar_telegram_multiusuario(mensaje)
    else:
        log("No se encontró la URL después de varios intentos.")
        enviar_telegram_multiusuario("⚠️ **ALERTA:** Sistema reiniciado, pero no se detectó la URL del Túnel. Revisa la conexión.")

if __name__ == "__main__":
    # Esperar un poco al inicio para asegurar que haya red
    time.sleep(15)
    main()