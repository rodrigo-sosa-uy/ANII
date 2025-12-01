import os
import zipfile
import requests
import logging
import urllib3

# --- CONFIGURACIÓN ---
BOT_TOKEN = "8427486269:AAGxnU4s4sEacrtBKqFEIa-npsfkxuOBWiw"
CHAT_ID = "7289719287"
LOG_DIR = "/home/log"

# Fechas específicas a procesar manualmente
FECHAS_A_ENVIAR = [
    '2025_11_28', 
    '2025_11_29', 
    '2025_11_30'
]

# DESACTIVAR ADVERTENCIAS DE SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuración de log (Solo consola para este script manual)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def log(msg):
    logging.info(msg)

def enviar_telegram(archivo_path, mensaje):
    """Sube un documento a Telegram ignorando SSL"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    
    try:
        with open(archivo_path, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': CHAT_ID, 'caption': mensaje}
            
            # verify=False para evitar errores de certificados en la red
            resp = requests.post(url, files=files, data=data, verify=False, timeout=60)
            
        if resp.status_code == 200:
            log("✅ Archivo enviado correctamente a Telegram.")
            return True
        else:
            log(f"❌ Error API Telegram ({resp.status_code}): {resp.text}")
            return False
            
    except Exception as e:
        log(f"❌ Error de conexión: {e}")
        return False

def comprimir_carpeta(ruta_carpeta, nombre_zip):
    """Comprime una carpeta entera en un archivo .zip"""
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

def procesar_fecha(fecha_str):
    """Procesa una fecha específica"""
    log(f"--- Procesando fecha: {fecha_str} ---")
    
    ruta_carpeta = os.path.join(LOG_DIR, fecha_str)
    
    if not os.path.exists(ruta_carpeta):
        log(f"⚠️ La carpeta {ruta_carpeta} no existe. Saltando...")
        return

    try:
        # 1. Comprimir
        log(f"Comprimiendo carpeta {fecha_str}...")
        zip_generado = comprimir_carpeta(ruta_carpeta, fecha_str)
        
        if zip_generado is None:
             log("⚠️ La carpeta existía pero estaba vacía.")
             return

        # 2. Enviar
        peso_kb = os.path.getsize(zip_generado)/1024
        log(f"Subiendo {zip_generado} ({peso_kb:.1f} KB)...")
        
        mensaje = f"📊 Respaldo Manual IoT\n📅 Fecha: {fecha_str}\n💾 Peso: {peso_kb:.1f} KB"
        enviado = enviar_telegram(zip_generado, mensaje)
        
        # 3. Limpieza 
        if enviado:
            os.remove(zip_generado)
            log("Zip temporal eliminado.")
        else:
            log("⚠️ No se pudo enviar. El zip se mantiene.")
            
    except Exception as e:
        log(f"ERROR CRÍTICO AL PROCESAR {fecha_str}: {e}")

# --- EJECUCIÓN MANUAL ---
if __name__ == "__main__":
    log("🚀 Iniciando carga manual de archivos...")
    
    for fecha in FECHAS_A_ENVIAR:
        procesar_fecha(fecha)
        
    log("🏁 Proceso manual finalizado.")