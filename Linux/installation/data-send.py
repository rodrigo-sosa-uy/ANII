import os
import time
import logging
from ftplib import FTP
from datetime import datetime, timedelta

#########################################################
################ Configuracion de datos #################
#########################################################
CARPETA_BASE = "/home/log"
FTP_HOST = "ftp.utecnologica.org"
#FTP_HOST = "31.220.106.205"
FTP_USER = "u874918252.imec"
FTP_PASS = "TU_CONTRASEÑA_AQUI"  # <- IMPORTANTE: Contraseña real
FTP_DIR = "/d_so/log"       # <- IMPORTANTE: Cambiar Directorio según región

#########################################################
################ Configuración de Logging ###############
#########################################################

# 1. Obtenemos el mes actual: "2025_12"
current_month_str = datetime.now().strftime('%Y_%m')

# 2. Definimos la carpeta del mes para LOGS DE SISTEMA
LOG_MONTH_DIR = os.path.join(CARPETA_BASE, current_month_str)

# 3. Definimos el archivo final: "/home/log/2025_12/data-send.log"
LOG_FILE = os.path.join(LOG_MONTH_DIR, 'data-send.log')

# 4. Crear estructura de carpetas si no existe
if not os.path.exists(LOG_MONTH_DIR):
    try:
        os.makedirs(LOG_MONTH_DIR)
        print(f"📁 Carpeta de logs mensuales creada: {LOG_MONTH_DIR}")
    except OSError as e:
        print(f"CRITICAL ERROR: No se pudo crear directorio de logs {LOG_MONTH_DIR}: {e}")

# Configuración del Logger (Archivo + Consola)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

#########################################################
####################### Funciones #######################
#########################################################

def esperar_hasta_medianoche():
    """Duerme hasta las 00:10:00 del dia siguiente."""
    ahora = datetime.now()
    
    # Calculamos la medianoche de mañana
    mañana = (ahora + timedelta(days=1)).replace(hour=0, minute=10, second=0, microsecond=0)
    
    segundos = (mañana - ahora).total_seconds()
    logging.info(f"Esperando {segundos:.2f} segundos hasta la medianoche para enviar reporte...")
    time.sleep(segundos)

def enviar_archivos_ayer():
    """
    1. Calcula la fecha de ayer.
    2. Busca la CARPETA correspondiente (/home/log/YYYY_MM_DD).
    3. Entra en ella y envia todos los CSV encontrados.
    """
    # 1. Calcular la fecha de AYER
    fecha_ayer = datetime.now() - timedelta(days=1)
    nombre_carpeta_ayer = fecha_ayer.strftime('%Y_%m_%d')
    
    # Construimos la ruta completa: /home/log/2025_11_25
    ruta_carpeta_ayer = os.path.join(CARPETA_BASE, nombre_carpeta_ayer)
    
    logging.info(f"Iniciando proceso. Buscando carpeta de ayer: {ruta_carpeta_ayer}...")

    # Verificamos si la carpeta del día existe
    if not os.path.exists(ruta_carpeta_ayer):
        logging.warning(f"ADVERTENCIA: No existe la carpeta {ruta_carpeta_ayer}. No hay datos para enviar.")
        return

    archivos_encontrados = 0

    try:
        # 2. Conexión FTP
        ftp = FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        logging.info(f"Conexion FTP establecida con {FTP_HOST}.")

        # Cambiar directorio remoto base
        ftp.cwd(FTP_DIR)
        
        # Crear/Entrar carpeta del día en el servidor
        try:
            ftp.mkd(nombre_carpeta_ayer)
        except:
            pass # La carpeta ya existe
        ftp.cwd(nombre_carpeta_ayer)

        # 3. Listar archivos DENTRO de la carpeta de la fecha
        archivos_en_carpeta = os.listdir(ruta_carpeta_ayer)
        
        for archivo in archivos_en_carpeta:
            if archivo.endswith(".csv"):
                
                ruta_completa_archivo = os.path.join(ruta_carpeta_ayer, archivo)
                # Tamaño del archivo para log
                size_kb = os.path.getsize(ruta_completa_archivo) / 1024
                logging.info(f"Enviando {archivo} ({size_kb:.1f} KB)...")

                with open(ruta_completa_archivo, "rb") as f:
                    ftp.storbinary(f"STOR {archivo}", f)

                logging.info(f"--> {archivo} enviado exitosamente.")
                archivos_encontrados += 1

        ftp.quit()
        
        if archivos_encontrados == 0:
            logging.warning(f"La carpeta {ruta_carpeta_ayer} existe pero estaba vacía de CSVs.")
        else:
            logging.info(f"✅ Proceso finalizado. Total archivos enviados desde {nombre_carpeta_ayer}: {archivos_encontrados}")

    except Exception as e:
        logging.error(f"❌ ERROR CRÍTICO al enviar archivos por FTP: {e}")

#########################################################
#################### Loop principal #####################
#########################################################

if __name__ == "__main__":
    logging.info("--- 🚀 Servicio de envio diario de CSV (FTP) INICIADO ---")
    logging.info(f"    Directorio base: {CARPETA_BASE}")
    logging.info(f"    Log de sistema:  {LOG_FILE}")
    
    # Bucle infinito
    while True:
        esperar_hasta_medianoche()
        # Al despertar (00:10:00), enviamos lo del dia anterior
        try:
            enviar_archivos_ayer()
        except Exception as e:
            logging.error(f"Excepción no manejada en bucle principal: {e}")