import time
import re
import requests
import os
import urllib3

# --- CONFIGURACIÓN ---
BOT_TOKEN = "8427486269:AAGxnU4s4sEacrtBKqFEIa-npsfkxuOBWiw"
CHAT_ID = "7289719287"
LOG_FILE = "/var/log/scada-tunnel.log"

# Desactivar advertencias SSL (por la red de la UTEC)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def log(msg):
    print(f"[Notificador] {msg}")

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {'chat_id': CHAT_ID, 'text': mensaje, 'parse_mode': 'Markdown'}
    
    try:
        # verify=False es clave para tu red
        requests.post(url, data=data, verify=False, timeout=10)
        log("Mensaje enviado a Telegram.")
        return True
    except Exception as e:
        log(f"Error enviando mensaje: {e}")
        return False

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
            # Encontramos una URL, pero verifiquemos si es "fresca"
            # (O simplemente la enviamos, Telegram no cobra por mensajes repetidos)
            break
        
        log(f"URL no encontrada aún. Intento {intentos+1}/12. Esperando...")
        time.sleep(10)
        intentos += 1
        
    if url_encontrada:
        mensaje = (
            f"🟢 **SISTEMA INICIADO**\n"
            f"La MiniPC se ha recuperado de un reinicio.\n\n"
            f"🌍 **Nueva URL SCADA:**\n"
            f"`{url_encontrada}`"
        )
        enviar_telegram(mensaje)
    else:
        log("No se encontró la URL después de varios intentos.")
        enviar_telegram("⚠️ **ALERTA:** Sistema reiniciado, pero no se detectó la URL del Túnel. Revisa la conexión.")

if __name__ == "__main__":
    # Esperar un poco al inicio para asegurar que haya red
    time.sleep(15)
    main()