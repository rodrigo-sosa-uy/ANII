import os
import time
import zipfile
import requests
import logging
from datetime import datetime, timedelta

# --- CONFIGURACIÓN ---
BOT_TOKEN = "8427486269:AAGxnU4s4sEacrtBKqFEIa-npsfkxuOBWiw"
CHAT_ID = "7289719287"
LOG_DIR = "/home/log"             # Ruta base de los logs

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
    """Sube un documento a Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    
    try:
        with open(archivo_path, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': CHAT_ID, 'caption': mensaje}
            resp = requests.post(url, files=files, data=data)
            
        if resp.status_code == 200:
            log("✅ Archivo enviado correctamente a Telegram.")
            return True
        else:
            log(f"❌ Error API Telegram: {resp.text}")
            return False
    except Exception as e:
        log(f"❌ Error de conexión: {e}")
        return False

def comprimir_carpeta(ruta_carpeta, nombre_zip):
    """Comprime una carpeta entera en un archivo .zip"""
    zip_path = ruta_carpeta + ".zip" # /home/log/2025_11_25.zip
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(ruta_carpeta):
            for file in files:
                # Ruta completa
                file_path = os.path.join(root, file)
                # Nombre relativo dentro del zip
                arcname = os.path.relpath(file_path, os.path.dirname(ruta_carpeta))
                zipf.write(file_path, arcname)
                
    return zip_path

def tarea_diaria():
    # 1. Calcular fecha de ayer
    ayer = datetime.now() - timedelta(days=1)
    nombre_carpeta = ayer.strftime('%Y_%m_%d') # Ej: 2025_11_25
    ruta_carpeta = os.path.join(LOG_DIR, nombre_carpeta)
    
    log(f"Iniciando respaldo de: {nombre_carpeta}")
    
    if not os.path.exists(ruta_carpeta):
        log(f"⚠️ No existe la carpeta {ruta_carpeta}. Nada que subir.")
        # Opcional: Avisar al bot que no hubo datos
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                      data={'chat_id': CHAT_ID, 'text': f"⚠️ Reporte {nombre_carpeta}: No hay datos."})
        return

    try:
        # 2. Comprimir
        log("Comprimiendo archivos...")
        zip_generado = comprimir_carpeta(ruta_carpeta, nombre_carpeta)
        
        # 3. Enviar
        log(f"Subiendo {zip_generado} ({os.path.getsize(zip_generado)/1024:.1f} KB)...")
        mensaje = f"📊 Reporte Diario IoT\n📅 Fecha: {nombre_carpeta}"
        enviado = enviar_telegram(zip_generado, mensaje)
        
        # 4. Limpieza (Opcional: borrar el zip para ahorrar espacio)
        if enviado:
            os.remove(zip_generado)
            log("Zip temporal eliminado.")
            
    except Exception as e:
        log(f"ERROR CRÍTICO: {e}")

def esperar_medianoche():
    ahora = datetime.now()
    # Programar para mañana a las 00:05:00
    mañana = (ahora + timedelta(days=1)).replace(hour=0, minute=5, second=0, microsecond=0)
    segundos = (mañana - ahora).total_seconds()
    
    log(f"💤 Durmiendo {segundos/3600:.2f} horas hasta el próximo reporte...")
    time.sleep(segundos)

# --- BUCLE PRINCIPAL ---
if __name__ == "__main__":
    log("🤖 Bot Uploader iniciado.")
    
    # Si quieres probarlo INMEDIATAMENTE al ejecutar, descomenta la siguiente linea:
    # tarea_diaria() 
    
    while True:
        esperar_medianoche()
        tarea_diaria()