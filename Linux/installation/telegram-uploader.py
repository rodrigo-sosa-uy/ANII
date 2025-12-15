import os
import time
import zipfile
import requests
import logging
import urllib3
from datetime import datetime, timedelta

# =========================================================
# CONFIGURACIÓN ESPECÍFICA DEL DISPOSITIVO
# =========================================================
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

LOG_DIR_BASE = "/home/log"

# DESACTIVAR ADVERTENCIAS DE SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =========================================================
# CONFIGURACIÓN DE LOGGING (MENSUAL)
# =========================================================
# 1. Obtenemos el mes actual para guardar el log de ESTE script
current_month_str = datetime.now().strftime('%Y_%m')
LOG_MONTH_DIR = os.path.join(LOG_DIR_BASE, current_month_str)
LOG_FILE = os.path.join(LOG_MONTH_DIR, 'uploader.log')

# Crear carpeta de logs si no existe
if not os.path.exists(LOG_MONTH_DIR):
    try:
        os.makedirs(LOG_MONTH_DIR)
    except:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def log(msg):
    # Wrapper para logging
    logging.info(msg)

# =========================================================
# FUNCIONES DE TELEGRAM
# =========================================================

def enviar_telegram_multiusuario(archivo_path, mensaje_base):
    """Envía archivo a todos los usuarios."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    envios_exitosos = 0
    
    mensaje_completo = f"📍 **REGIÓN: {DEVICE_REGION}**\n{mensaje_base}"

    for usuario_id in CHAT_IDS:
        try:
            with open(archivo_path, 'rb') as f:
                files = {'document': f}
                data = {'chat_id': usuario_id, 'caption': mensaje_completo, 'parse_mode': 'Markdown'}
                
                log(f"Enviando a usuario {usuario_id}...")
                resp = requests.post(url, files=files, data=data, verify=False, timeout=300) # Timeout alto para archivos grandes
            
            if resp.status_code == 200:
                log(f"✅ Enviado OK a {usuario_id}")
                envios_exitosos += 1
            else:
                log(f"❌ Falló envío a {usuario_id}: {resp.text}")
                
        except Exception as e:
            log(f"❌ Error de conexión con {usuario_id}: {e}")
            
    return envios_exitosos > 0

def enviar_alerta_texto(texto):
    """Envía alerta de texto a todos."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    mensaje_completo = f"📍 **REGIÓN: {DEVICE_REGION}**\n{texto}"
    
    for usuario_id in CHAT_IDS:
        try:
            data = {'chat_id': usuario_id, 'text': mensaje_completo, 'parse_mode': 'Markdown'}
            requests.post(url, data=data, verify=False, timeout=10)
        except:
            pass

# =========================================================
# FUNCIONES DE COMPRESIÓN
# =========================================================

def comprimir_carpeta(ruta_carpeta, nombre_zip):
    zip_path = ruta_carpeta + ".zip"
    
    if os.path.exists(zip_path):
        os.remove(zip_path)

    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zipf:
            archivos_agregados = False 
            for root, dirs, files in os.walk(ruta_carpeta):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Evitar comprimirse a sí mismo o archivos corruptos
                    if file == os.path.basename(zip_path) or file.endswith('.lock'):
                        continue
                    
                    arcname = os.path.relpath(file_path, os.path.dirname(ruta_carpeta))
                    zipf.write(file_path, arcname)
                    archivos_agregados = True
            
            if not archivos_agregados:
                return None
    except Exception as e:
        log(f"Error comprimiendo: {e}")
        return None
                
    return zip_path

# =========================================================
# TAREAS PROGRAMADAS
# =========================================================

def tarea_diaria():
    """Respalda la carpeta del día anterior (YYYY_MM_DD)"""
    ayer = datetime.now() - timedelta(days=1)
    nombre_carpeta = ayer.strftime('%Y_%m_%d')
    ruta_carpeta = os.path.join(LOG_DIR_BASE, nombre_carpeta)
    
    log(f"--- Iniciando respaldo DIARIO {DEVICE_REGION}: {nombre_carpeta} ---")
    
    if not os.path.exists(ruta_carpeta):
        log(f"⚠️ No existe carpeta diaria {ruta_carpeta}.")
        # No enviamos alerta para no spammear si no hubo datos ese día
        return

    try:
        log("Comprimiendo carpeta diaria...")
        zip_generado = comprimir_carpeta(ruta_carpeta, nombre_carpeta)
        
        if zip_generado:
            peso_kb = os.path.getsize(zip_generado)/1024
            log(f"Subiendo {zip_generado} ({peso_kb:.1f} KB)...")
            
            mensaje = f"📊 **Reporte Diario**\n📅 Fecha: `{nombre_carpeta}`\n💾 Peso: `{peso_kb:.1f} KB`"
            if enviar_telegram_multiusuario(zip_generado, mensaje):
                os.remove(zip_generado)
                log("Zip diario eliminado.")
            else:
                log("⚠️ Falló envío diario.")
    except Exception as e:
        log(f"ERROR TAREA DIARIA: {e}")

def tarea_mensual():
    """
    Verifica si hoy es día 1. Si es así, busca la carpeta del mes anterior (YYYY_MM),
    la comprime entera y la envía.
    """
    hoy = datetime.now()
    
    # Solo ejecutamos si es el primer día del mes
    if hoy.day != 1:
        return

    # Calculamos cuál fue el mes anterior
    # Restamos un día al 1ro del mes actual para caer en el mes anterior
    ultimo_dia_mes_anterior = hoy - timedelta(days=1)
    nombre_carpeta_mensual = ultimo_dia_mes_anterior.strftime('%Y_%m') # Ej: 2025_11
    
    ruta_carpeta_mensual = os.path.join(LOG_DIR_BASE, nombre_carpeta_mensual)
    
    log(f"--- 📅 EJECUTANDO CIERRE MENSUAL: {nombre_carpeta_mensual} ---")
    
    if not os.path.exists(ruta_carpeta_mensual):
        log(f"⚠️ No se encontró la carpeta mensual {ruta_carpeta_mensual}.")
        return

    try:
        log("📦 Comprimiendo CARPETA MENSUAL (Esto puede tardar)...")
        zip_mensual = comprimir_carpeta(ruta_carpeta_mensual, nombre_carpeta_mensual)
        
        if zip_mensual:
            peso_mb = os.path.getsize(zip_mensual) / (1024 * 1024)
            log(f"Subiendo respaldo mensual ({peso_mb:.2f} MB)...")
            
            # --- MENSAJE ACTUALIZADO ---
            mensaje = (
                f"🗂️ **REPORTE MENSUAL DE SISTEMA**\n"
                f"📅 Período: `{nombre_carpeta_mensual}`\n"
                f"💾 Tamaño: `{peso_mb:.2f} MB`\n"
                f"ℹ️ Incluye únicamente los logs de funcionamiento del sistema.\n"
                f"*(Los datos CSV ya fueron enviados diariamente)*"
            )
            
            if enviar_telegram_multiusuario(zip_mensual, mensaje):
                os.remove(zip_mensual)
                log("Zip mensual eliminado.")
            else:
                log("⚠️ Falló envío mensual (posiblemente archivo muy grande).")
        else:
            log("Carpeta mensual vacía.")
            
    except Exception as e:
        log(f"ERROR CRÍTICO TAREA MENSUAL: {e}")

def esperar_medianoche():
    ahora = datetime.now()
    # Programar para las 00:05:00
    mañana = (ahora + timedelta(days=1)).replace(hour=0, minute=5, second=0, microsecond=0)
    
    if mañana < ahora:
        mañana = mañana + timedelta(days=1)

    segundos = (mañana - ahora).total_seconds()
    log(f"💤 Dispositivo {DEVICE_REGION} durmiendo {segundos/3600:.2f} horas...")
    time.sleep(segundos)

# --- BUCLE PRINCIPAL ---
if __name__ == "__main__":
    log(f"🤖 Bot Uploader [{DEVICE_REGION}] iniciado.")
    log(f"    Log de sistema: {LOG_FILE}")
    
    # Check inicial de red
    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", verify=False, timeout=10)
        log("✅ Conexión Telegram OK.")
    except:
        log("❌ Sin conexión inicial.")

    while True:
        esperar_medianoche()
        
        # 1. Primero el reporte del día de ayer
        tarea_diaria()
        
        # 2. Después verificamos si hay que cerrar el mes
        tarea_mensual()