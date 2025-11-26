import os
import time
import logging
from ftplib import FTP
from datetime import datetime, timedelta

#########################################################
################ Configuracion de datos #################
#########################################################
CARPETA_BASE = "/home/log/dev"
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

def enviar_archivos():  
    # Construimos la ruta completa: /home/log/2025_11_25
    ruta_carpeta = CARPETA_BASE
    
    log(f"Iniciando proceso. Buscando carpeta de ayer: {ruta_carpeta}...")

    # Verificamos si la carpeta del día existe
    if not os.path.exists(ruta_carpeta):
        log(f"ADVERTENCIA: No existe la carpeta {ruta_carpeta}. No hay datos para enviar.")
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
            ftp.mkd("dev")
        except:
            pass # La carpeta ya existe
        ftp.cwd("dev")

        # 3. Listar archivos DENTRO de la carpeta de la fecha
        archivos_en_carpeta = os.listdir(ruta_carpeta)
        
        for archivo in archivos_en_carpeta:
            if archivo.endswith(".csv"):
                
                ruta_completa_archivo = os.path.join(ruta_carpeta, archivo)
                log(f"Enviando {archivo} ...")

                with open(ruta_completa_archivo, "rb") as f:
                    ftp.storbinary(f"STOR {archivo}", f)

                log(f"--> {archivo} enviado exitosamente.")
                archivos_encontrados += 1

        ftp.quit()
        
        if archivos_encontrados == 0:
            log(f"La carpeta {ruta_carpeta} existe pero estaba vacía de CSVs.")
        else:
            log(f"Proceso finalizado. Total archivos enviados desde dev: {archivos_encontrados}")

    except Exception as e:
        log(f"ERROR CRÍTICO al enviar archivos por FTP: {e}")

#########################################################
#################### Loop principal #####################
#########################################################

if __name__ == "__main__":
    log("Servicio de envio diario de CSV (por carpetas) iniciado.")
    enviar_archivos_ayer()