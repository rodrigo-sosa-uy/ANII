import os
import time
import logging
from ftplib import FTP
from datetime import datetime, timedelta

#########################################################
################ Configuracion de datos #################
#########################################################
CARPETA_CSV = "/home/log"
FTP_HOST = "ftp.utecnologica.com"
FTP_USER = "u874918252.imec"
FTP_PASS = 
FTP_DIR = "/destino/remoto"      # <- CAMBIAR

#########################################################
################## Creacion del logger ##################
#########################################################
LOG_FILE = os.path.join(CARPETA_CSV, "data-send.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

#########################################################
####################### Funciones #######################
#########################################################

def log(msg):
    logging.info(msg)

def esperar_hasta_medianoche():
    """Duerme hasta las 00:00 del dia siguiente."""
    ahora = datetime.now()
    mañana = (ahora + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    segundos = (mañana - ahora).total_seconds()
    log(f"Durmiendo hasta la medianoche ({segundos} segundos)...")
    time.sleep(segundos)

def enviar_archivos():
    """Envia todos los CSV por FTP al servidor remoto."""
    log("Iniciando envio de archivos CSV por FTP...")

    try:
        ftp = FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        log("Conexion FTP establecida.")

        # Cambiar directorio remoto
        ftp.cwd(FTP_DIR)

        # Enviar archivos CSV
        for archivo in os.listdir(CARPETA_CSV):
            if archivo.endswith(".csv"):
                ruta_local = os.path.join(CARPETA_CSV, archivo)
                log(f"Enviando {archivo} ...")

                with open(ruta_local, "rb") as f:
                    ftp.storbinary(f"STOR {archivo}", f)

                log(f"{archivo} enviado correctamente.")

        ftp.quit()
        log("Transferencia FTP completada.")

    except Exception as e:
        log(f"ERROR al enviar archivos por FTP: {e}")

#########################################################
#################### Loop principal #####################
#########################################################

if __name__ == "__main__":
    log("Servicio de envio diario de CSV iniciado.")
    while True:
        esperar_hasta_medianoche()
        enviar_archivos()