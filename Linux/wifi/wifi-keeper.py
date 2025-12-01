import requests
import time
import logging
import urllib3

# --- CONFIGURACIÓN DEL PORTAL CAUTIVO ---

# URL de respaldo (la que obtuviste con cURL).
# Se usará si no podemos detectar la URL dinámica automáticamente.
URL_LOGIN_FIJA = "http://192.168.101.1:1000/fgtauth?040f04de47f1a669"

# Headers exactos del cURL para "engañar" al portal Fortinet
HEADERS_LOGIN = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en;q=0.6',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Referer': 'http://www.msftconnecttest.com/',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
}

# --- CONFIGURACIÓN GENERAL ---
CHECK_INTERVAL = 60  # Revisar cada 60 segundos
LOG_FILE = "/var/log/wifi-keeper.log"

# Desactivar advertencias de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuración de logs
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def log(msg):
    print(msg)
    logging.info(msg)

def hay_internet():
    """Intenta contactar a Google para ver si tenemos salida real"""
    try:
        # Usamos timeout corto. Si responde 204, hay internet.
        # Si responde 200 con contenido HTML, es el portal cautivo (no hay internet real).
        r = requests.get("http://clients3.google.com/generate_204", timeout=5)
        if r.status_code == 204:
            return True
        return False
    except:
        return False

def obtener_url_magica():
    """
    Intenta obtener la URL de login dinámica (con el token nuevo).
    Hace una petición HTTP simple y ve a dónde nos redirige el portal.
    """
    try:
        log("🕵️ Buscando URL dinámica del portal...")
        # Hacemos petición a un sitio HTTP (no HTTPS) para provocar el redirect del portal
        r = requests.get("http://www.msftconnecttest.com/connecttest.txt", allow_redirects=True, timeout=5)
        
        # Si nos redirigió a una URL que contiene 'fgtauth', esa es la buena
        if 'fgtauth' in r.url:
            log(f"🎯 URL dinámica encontrada: {r.url}")
            return r.url
        elif 'fgtauth' in r.text:
            # A veces devuelve un HTML con un script de redirección window.location...
            # En ese caso es más complejo, retornamos None para usar la fija.
            return None
    except Exception as e:
        log(f"⚠️ No se pudo obtener URL dinámica: {e}")
    
    return None

def realizar_login():
    """Simula el proceso de login"""
    log("🔓 Detectada falta de internet. Ejecutando Login en Portal Fortinet...")

    # 1. Intentar obtener la URL fresca (el token suele cambiar)
    target_url = obtener_url_magica()
    
    # 2. Si falló la detección automática, usar la fija que nos diste
    if not target_url:
        log("⚠️ Usando URL fija de respaldo (el token podría haber expirado).")
        target_url = URL_LOGIN_FIJA

    try:
        # Petición GET con los headers copiados del cURL
        response = requests.get(
            target_url, 
            headers=HEADERS_LOGIN, 
            verify=False, 
            timeout=10
        )
        
        if response.status_code < 400:
            log(f"✅ Petición de login enviada (Código {response.status_code}).")
            time.sleep(3) # Esperar a que el router aplique cambios
            
            if hay_internet():
                log("🎉 ¡Conexión restablecida correctamente!")
            else:
                log("⚠️ Login enviado pero seguimos sin internet. El token podría ser inválido.")
        else:
            log(f"❌ El portal rechazó la conexión: {response.status_code}")
            
    except Exception as e:
        log(f"❌ Error crítico en proceso de login: {e}")

# --- BUCLE PRINCIPAL ---
if __name__ == "__main__":
    log("🛡️ Servicio Wifi-Keeper (Modo Fortinet GET) iniciado.")
    
    while True:
        if not hay_internet():
            realizar_login()
        else:
            # log("Conexión estable.")
            pass
            
        time.sleep(CHECK_INTERVAL)