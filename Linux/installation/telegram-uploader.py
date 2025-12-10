import os
import time
import zipfile
import requests
import logging
import urllib3  # Necesario para silenciar la advertencia de seguridad
from datetime import datetime, timedelta

# --- CONFIGURACIÓN ---
BOT_TOKEN = "8427486269:AAGxnU4s4sEacrtBKqFEIa-npsfkxuOBWiw"
CHAT_ID = "7289719287"
LOG_DIR = "/home/log"             # Ruta base de los logs

# DESACTIVAR ADVERTENCIAS DE SSL (Para que no llene el log de basura)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuración de log local
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "uploader.log")),
        logging.StreamHandler()
    ]
)

def log(msg):
    logging.info(msg)
    print(msg)

def enviar_telegram(archivo_path, mensaje):
    """Sube un documento a Telegram ignorando SSL"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    
    try:
        with open(archivo_path, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': CHAT_ID, 'caption': mensaje}
            
            # --- CAMBIO CRÍTICO AQUÍ ---
            # verify=False hace que Python no chequee si el certificado es válido.
            # Esto soluciona el error SSLCertVerificationError.
            resp = requests.post(url, files=files, data=data, verify=False, timeout=60)
            
        if resp.status_code == 200:
            log("✅ Archivo enviado correctamente a Telegram.")
            return True
        elif resp.status_code == 403 or resp.status_code == 401:
             log(f"❌ Error de Permisos (Token incorrecto): {resp.text}")
             return False
        else:
            log(f"❌ Error API Telegram ({resp.status_code}): {resp.text}")
            return False
            
    except requests.exceptions.SSLError as ssl_err:
        log(f"❌ Error SSL persistente (incluso sin verify?): {ssl_err}")
        return False
    except Exception as e:
        log(f"❌ Error de conexión general: {e}")
        return False

def comprimir_carpeta(ruta_carpeta, nombre_zip):
    """Comprime una carpeta entera en un archivo .zip"""
    zip_path = ruta_carpeta + ".zip" # /home/log/2025_11_25.zip
    
    # Aseguramos que el zip anterior no exista corrupto
    if os.path.exists(zip_path):
        os.remove(zip_path)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Variable para saber si encontramos archivos
        archivos_agregados = False 
        for root, dirs, files in os.walk(ruta_carpeta):
            for file in files:
                file_path = os.path.join(root, file)
                # Evitar comprimir el propio zip si se guardó dentro (por error)
                if file == os.path.basename(zip_path):
                    continue
                
                arcname = os.path.relpath(file_path, os.path.dirname(ruta_carpeta))
                zipf.write(file_path, arcname)
                archivos_agregados = True
        
        if not archivos_agregados:
            return None # Retorna None si la carpeta estaba vacía
                
    return zip_path

def tarea_diaria():
    # 1. Calcular fecha de ayer
    ayer = datetime.now() - timedelta(days=1)
    nombre_carpeta = ayer.strftime('%Y_%m_%d') # Ej: 2025_11_25
    ruta_carpeta = os.path.join(LOG_DIR, nombre_carpeta)
    
    log(f"Iniciando respaldo de: {nombre_carpeta}")
    
    if not os.path.exists(ruta_carpeta):
        log(f"⚠️ No existe la carpeta {ruta_carpeta}. Nada que subir.")
        # Intento enviar alerta (sin verify)
        try:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                          data={'chat_id': CHAT_ID, 'text': f"⚠️ Reporte {nombre_carpeta}: No hay datos localmente."},
                          verify=False)
        except:
            pass
        return

    try:
        # 2. Comprimir
        log("Comprimiendo archivos...")
        zip_generado = comprimir_carpeta(ruta_carpeta, nombre_carpeta)
        
        if zip_generado is None:
             log("⚠️ La carpeta existía pero estaba vacía.")
             return

        # 3. Enviar
        peso_kb = os.path.getsize(zip_generado)/1024
        log(f"Subiendo {zip_generado} ({peso_kb:.1f} KB)...")
        
        mensaje = f"📊 Reporte Diario IoT\n📅 Fecha: {nombre_carpeta}\n💾 Peso: {peso_kb:.1f} KB"
        enviado = enviar_telegram(zip_generado, mensaje)
        
        # 4. Limpieza 
        if enviado:
            os.remove(zip_generado)
            log("Zip temporal eliminado.")
        else:
            log("⚠️ No se pudo enviar. El zip se mantiene para reintento manual.")
            
    except Exception as e:
        log(f"ERROR CRÍTICO EN TAREA: {e}")

def esperar_medianoche():
    ahora = datetime.now()
    # Programar para mañana a las 00:05:00
    mañana = (ahora + timedelta(days=1)).replace(hour=0, minute=5, second=0, microsecond=0)
    
    # Seguridad: Si por alguna razón 'mañana' quedó en el pasado (ej. cambio de hora), sumar un día
    if mañana < ahora:
        mañana = mañana + timedelta(days=1)

    segundos = (mañana - ahora).total_seconds()
    
    log(f"💤 Durmiendo {segundos/3600:.2f} horas hasta el próximo reporte ({mañana})...")
    time.sleep(segundos)

# --- BUCLE PRINCIPAL ---
if __name__ == "__main__":
    log("🤖 Bot Uploader iniciado (Modo Inseguro SSL activado).")
    
    # Comprobar conexión al inicio (opcional)
    try:
        r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", verify=False, timeout=10)
        if r.status_code == 200:
            log(f"✅ Conexión con Bot exitosa: {r.json().get('result', {}).get('username')}")
        else:
            log(f"⚠️ Alerta: El bot responde con error {r.status_code}")
    except Exception as e:
        log(f"❌ Alerta: No hay conexión a internet al inicio: {e}")

    while True:
        esperar_medianoche()
        tarea_diaria()