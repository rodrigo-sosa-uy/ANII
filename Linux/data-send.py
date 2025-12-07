import os
import time
import logging
from ftplib import FTP
from datetime import datetime, timedelta

#########################################################
################ Configuracion de datos #################
#########################################################
CARPETA_BASE = "/home/log"
FTP_HOST = "ftp.utecnologica.com"
FTP_USER = "u874918252.imec"
FTP_PASS = "TU_CONTRASEÑA_AQUI"  # <- IMPORTANTE: Contraseña real
FTP_DIR = "/destino/remoto"      # <- IMPORTANTE: Cambiar Directorio

#########################################################
################## Creacion del logger ##################
#########################################################
# El log general se queda en la raiz para no perderse
LOG_FILE = os.path.join(CARPETA_BASE, "data-send.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

#########################################################
####################### Funciones #######################
#########################################################

def log(msg):
    print(msg) 
    logging.info(msg)

def esperar_hasta_medianoche():
    """Duerme hasta las 00:10:00 del dia siguiente."""
    ahora = datetime.now()
    
    # Calculamos la medianoche de mañana
    mañana = (ahora + timedelta(days=1)).replace(hour=0, minute=10, second=0, microsecond=0)
    
    segundos = (mañana - ahora).total_seconds()
    log(f"Esperando {segundos:.2f} segundos hasta la medianoche para enviar reporte...")
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
    
    log(f"Iniciando proceso. Buscando carpeta de ayer: {ruta_carpeta_ayer}...")

    # Verificamos si la carpeta del día existe
    if not os.path.exists(ruta_carpeta_ayer):
        log(f"ADVERTENCIA: No existe la carpeta {ruta_carpeta_ayer}. No hay datos para enviar.")
        return

    archivos_encontrados = 0

    try:
        # 2. Conexión FTP
        ftp = FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        log("Conexion FTP establecida.")

        # Cambiar directorio remoto
        ftp.cwd(FTP_DIR)
        
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
                log(f"Enviando {archivo} ...")

                with open(ruta_completa_archivo, "rb") as f:
                    ftp.storbinary(f"STOR {archivo}", f)

                log(f"--> {archivo} enviado exitosamente.")
                archivos_encontrados += 1

        ftp.quit()
        
        if archivos_encontrados == 0:
            log(f"La carpeta {ruta_carpeta_ayer} existe pero estaba vacía de CSVs.")
        else:
            log(f"Proceso finalizado. Total archivos enviados desde {nombre_carpeta_ayer}: {archivos_encontrados}")

    except Exception as e:
        log(f"ERROR CRÍTICO al enviar archivos por FTP: {e}")

#########################################################
#################### Loop principal #####################
#########################################################

if __name__ == "__main__":
    log("Servicio de envio diario de CSV (por carpetas) iniciado.")
    
    # Bucle infinito
    while True:
        esperar_hasta_medianoche()
        # Al despertar (00:10:00), enviamos lo del dia anterior
        enviar_archivos_ayer()