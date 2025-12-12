import os
import time
import zipfile
import requests
import logging
import urllib3
from datetime import datetime, timedelta

# --- CONFIGURACIÓN ESPECÍFICA DEL DISPOSITIVO ---
DEVICE_REGION = "SO"
#DEVICE_REGION = "CS"
#DEVICE_REGION = "SE"

# --- CONFIGURACIÓN DE TELEGRAM ---
if DEVICE_REGION == "SO":
    BOT_TOKEN = "8570350769:AAGSjPs9-rCCdg6LFk1KJ88jVCN4TosBMSY"
elif DEVICE_REGION == "CS":
    BOT_TOKEN = "8353406476:AAGLcsu-O0Nh_6_f32ARE9TyGuqF3DCi0qo"
elif DEVICE_REGION == "SE":
    BOT_TOKEN = "8454182171:AAHwSK2J_O_SSTsXzhKR_MFJx06o-01V5iU"

# LISTA DE USUARIOS (Agrega aquí los ID de los nuevos usuarios separados por coma)
CHAT_IDS = [
    "7289719287"
    # "123456789",
    # "987654321"
]

LOG_DIR = "/home/log"

# DESACTIVAR ADVERTENCIAS DE SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuración de log
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

def enviar_telegram_multiusuario(archivo_path, mensaje_base):
    """
    Envía el archivo a TODOS los usuarios en la lista CHAT_IDS.
    Retorna True si se envió correctamente a al menos uno.
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    envios_exitosos = 0
    
    # Agregamos la identificación de la región al mensaje
    mensaje_completo = f"📍 **REGIÓN: {DEVICE_REGION}**\n{mensaje_base}"

    for usuario_id in CHAT_IDS:
        try:
            # Abrimos el archivo en cada iteración para reiniciar el puntero de lectura
            with open(archivo_path, 'rb') as f:
                files = {'document': f}
                data = {'chat_id': usuario_id, 'caption': mensaje_completo, 'parse_mode': 'Markdown'}
                
                log(f"Enviando a usuario {usuario_id}...")
                resp = requests.post(url, files=files, data=data, verify=False, timeout=60)
            
            if resp.status_code == 200:
                log(f"✅ Enviado OK a {usuario_id}")
                envios_exitosos += 1
            else:
                log(f"❌ Falló envío a {usuario_id}: {resp.text}")
                
        except Exception as e:
            log(f"❌ Error de conexión con {usuario_id}: {e}")
            
    # Si al menos uno lo recibió, consideramos la tarea cumplida para borrar el zip
    return envios_exitosos > 0

def enviar_alerta_texto(texto):
    """Envía un mensaje de texto simple a todos los usuarios"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    mensaje_completo = f"📍 **REGIÓN: {DEVICE_REGION}**\n{texto}"
    
    for usuario_id in CHAT_IDS:
        try:
            data = {'chat_id': usuario_id, 'text': mensaje_completo, 'parse_mode': 'Markdown'}
            requests.post(url, data=data, verify=False, timeout=10)
        except:
            pass

def comprimir_carpeta(ruta_carpeta, nombre_zip):
    zip_path = ruta_carpeta + ".zip"
    
    if os.path.exists(zip_path):
        os.remove(zip_path)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        archivos_agregados = False 
        for root, dirs, files in os.walk(ruta_carpeta):
            for file in files:
                file_path = os.path.join(root, file)
                if file == os.path.basename(zip_path):
                    continue
                arcname = os.path.relpath(file_path, os.path.dirname(ruta_carpeta))
                zipf.write(file_path, arcname)
                archivos_agregados = True
        
        if not archivos_agregados:
            return None
                
    return zip_path

def tarea_diaria():
    # 1. Calcular fecha de ayer
    ayer = datetime.now() - timedelta(days=1)
    nombre_carpeta = ayer.strftime('%Y_%m_%d')
    ruta_carpeta = os.path.join(LOG_DIR, nombre_carpeta)
    
    log(f"--- Iniciando respaldo {DEVICE_REGION}: {nombre_carpeta} ---")
    
    if not os.path.exists(ruta_carpeta):
        log(f"⚠️ No existe la carpeta {ruta_carpeta}.")
        enviar_alerta_texto(f"⚠️ **Alerta:** No se encontraron datos locales del día {nombre_carpeta}.")
        return

    try:
        # 2. Comprimir
        log("Comprimiendo archivos...")
        zip_generado = comprimir_carpeta(ruta_carpeta, nombre_carpeta)
        
        if zip_generado is None:
             log("⚠️ La carpeta existía pero estaba vacía.")
             return

        # 3. Enviar a Múltiples Usuarios
        peso_kb = os.path.getsize(zip_generado)/1024
        log(f"Subiendo {zip_generado} ({peso_kb:.1f} KB)...")
        
        mensaje = f"📊 **Reporte Diario IoT**\n📅 Fecha: `{nombre_carpeta}`\n💾 Peso: `{peso_kb:.1f} KB`"
        
        # Llamamos a la nueva función multiusuario
        enviado_alguno = enviar_telegram_multiusuario(zip_generado, mensaje)
        
        # 4. Limpieza (Solo si al menos uno lo recibió)
        if enviado_alguno:
            os.remove(zip_generado)
            log("Zip temporal eliminado.")
        else:
            log("⚠️ No se pudo enviar a ningún usuario. Se mantiene el zip.")
            
    except Exception as e:
        log(f"ERROR CRÍTICO EN TAREA: {e}")

def esperar_medianoche():
    ahora = datetime.now()
    mañana = (ahora + timedelta(days=1)).replace(hour=0, minute=5, second=0, microsecond=0)
    
    if mañana < ahora:
        mañana = mañana + timedelta(days=1)

    segundos = (mañana - ahora).total_seconds()
    log(f"💤 Dispositivo {DEVICE_REGION} durmiendo {segundos/3600:.2f} horas...")
    time.sleep(segundos)

# --- BUCLE PRINCIPAL ---
if __name__ == "__main__":
    log(f"🤖 Bot Uploader [{DEVICE_REGION}] iniciado para {len(CHAT_IDS)} usuarios.")
    
    # Verificación de conexión al inicio
    try:
        r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", verify=False, timeout=10)
        if r.status_code == 200:
            log(f"✅ Conexión con Bot exitosa.")
        else:
            log(f"⚠️ Error conectando con Telegram: {r.status_code}")
    except Exception as e:
        log(f"❌ Sin conexión a internet al inicio: {e}")

    while True:
        esperar_medianoche()
        tarea_diaria()