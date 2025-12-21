import requests
import time
import logging
import urllib3
import re

# --- CONFIGURACIÓN ---
CHECK_INTERVAL = 30  # Revisar cada 30 segundos (más agresivo)
LOG_FILE = "/var/log/wifi-keeper.log"

# URL Fija de respaldo (la del cURL que me pasaste), por si falla la detección automática
URL_BACKUP = "http://192.168.101.1:1000/fgtauth?040f04de47f1a669"

# Headers para imitar un navegador Windows
HEADERS_LOGIN = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Referer': 'http://www.msftconnecttest.com/',
    'Connection': 'keep-alive'
}

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def log(msg):
    print(msg)
    logging.info(msg)

def buscar_enlace_magico(html_content):
    """
    Busca dentro del HTML del portal el enlace de autenticación.
    Patrón: http://192.168.101.1:1000/fgtauth?SECRETO
    """
    # Expresión regular para encontrar enlaces de Fortinet
    # Busca: http://(ip):1000/fgtauth?(cualquier_cosa_hasta_comillas_o_espacio)
    patron = r"(http://192\.168\.101\.1:1000/fgtauth\?[a-zA-Z0-9]+)"
    
    match = re.search(patron, html_content)
    if match:
        return match.group(1)
    return None

def hay_internet_real():
    """Verifica si realmente salimos a Google"""
    try:
        # generate_204 devuelve código 204 y cuerpo vacío si hay internet.
        # Si devuelve 200 y cuerpo HTML, es el portal cautivo.
        r = requests.get("http://clients3.google.com/generate_204", timeout=5)
        if r.status_code == 204:
            return True
        return False
    except:
        return False

def intentar_login():
    log("🔓 Detectado corte de internet. Iniciando protocolo de reconexión...")

    try:
        # 1. Provocar al Portal
        # Usamos neverssl.com porque nunca usa HTTPS, forzando al portal a mostrarse
        log("1. Solicitando página trampa (neverssl.com)...")
        r_portal = requests.get("http://neverssl.com", headers=HEADERS_LOGIN, timeout=10)
        
        url_login = None
        
        # 2. Análisis inteligente
        if 'fgtauth' in r_portal.url:
            # Caso A: Nos redirigió en la cabecera (Poco probable en tu caso, pero posible)
            url_login = r_portal.url
            log(f"2. Redirección detectada en cabecera: {url_login}")
            
        elif 'fgtauth' in r_portal.text:
            # Caso B: Nos dio el HTML del portal (Lo más probable). Buscamos el link.
            log("2. Página del portal descargada. Buscando enlace mágico...")
            url_login = buscar_enlace_magico(r_portal.text)
            
            if url_login:
                log(f"🎯 Enlace encontrado en el HTML: {url_login}")
            else:
                log("⚠️ Se detectó texto de Fortinet pero no se pudo extraer el enlace exacto.")
        else:
            log("⚠️ La respuesta no parece ser del portal Fortinet (no contiene 'fgtauth').")
            # Podríamos imprimir r_portal.text[:200] para debuggear

        # 3. Ejecución del Login
        if not url_login:
            log("⚠️ No se encontró URL dinámica. Usando URL de RESPALDO (puede fallar si el token venció).")
            url_login = URL_BACKUP

        log(f"3. Ejecutando autenticación en: {url_login}")
        r_auth = requests.get(url_login, headers=HEADERS_LOGIN, verify=False, timeout=10)
        
        if r_auth.status_code < 400:
            log(f"✅ Petición enviada (Código {r_auth.status_code}). Esperando confirmación...")
            time.sleep(5) # Fortinet tarda unos segundos en abrir el grifo
            
            if hay_internet_real():
                log("🎉 ¡INTERNET RESTAURADO EXITOSAMENTE!")
            else:
                log("❌ Falló: Se envió la petición pero Google sigue inalcanzable.")
        else:
            log(f"❌ Error HTTP al autenticar: {r_auth.status_code}")

    except Exception as e:
        log(f"❌ Error crítico en script: {e}")

# --- BUCLE PRINCIPAL ---
if __name__ == "__main__":
    log("🛡️ Wifi-Keeper V2 (Modo Scraping) iniciado.")
    
    # Verificación inicial rápida
    if not hay_internet_real():
        intentar_login()
    
    while True:
        try:
            if not hay_internet_real():
                intentar_login()
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            break
        except Exception as e:
            log(f"Error en bucle principal: {e}")
            time.sleep(CHECK_INTERVAL)