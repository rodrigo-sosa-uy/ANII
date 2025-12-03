import os
import time
import logging
import socket
from ftplib import FTP

#########################################################
################ Configuracion de datos #################
#########################################################
CARPETA_BASE = "/home/log/dev"

# --- CREDENCIALES FTP ---
#FTP_HOST = "ftp.utecnologica.org" 
FTP_HOST = "31.220.106.205"

FTP_USER = "u874918252.imec"
FTP_PASS = "" 
FTP_DIR = "/iot/dev" # Asegúrate que la ruta inicie bien

#########################################################
################## Creacion del logger ##################
#########################################################
if not os.path.exists(CARPETA_BASE):
    os.makedirs(CARPETA_BASE, exist_ok=True)

LOG_FILE = os.path.join("/home/log", "data-send.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

def log(msg):
    print(msg) 
    logging.info(msg)

def verificar_conexion_internet():
    """Intenta resolver Google para ver si tenemos DNS/Internet activo"""
    try:
        # Intentamos conectar al DNS de Google (8.8.8.8) puerto 53
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def enviar_archivos():  
    ruta_carpeta = CARPETA_BASE
    
    log(f"--- Iniciando Script de Envío FTP ---")

    # 1. Chequeo de Salud de Red
    if not verificar_conexion_internet():
        log("❌ ERROR CRÍTICO: No hay conexión a internet. El Portal Cautivo podría estar bloqueando.")
        log("   -> Asegúrate de que el servicio 'wifi-keeper' esté corriendo.")
        return

    # 2. Verificamos carpeta local
    if not os.path.exists(ruta_carpeta):
        log(f"⚠️ ADVERTENCIA: No existe la carpeta {ruta_carpeta}.")
        return

    archivos_encontrados = 0

    try:
        # 3. Conexión FTP
        log(f"Intentando conectar a {FTP_HOST}...")
        ftp = FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        log("✅ Conexion FTP establecida.")

        # Cambiar directorio remoto
        try:
            ftp.cwd(FTP_DIR)
        except Exception as e:
            log(f"⚠️ No se pudo entrar a {FTP_DIR}. Intentando crearlo o usando raiz. Error: {e}")

        # Opcional: Crear subcarpeta 'dev' en el servidor si no existe
        try:
            ftp.mkd("dev")
        except:
            pass 
        
        ftp.cwd("dev") # Entramos a la carpeta 'dev' remota

        # 4. Enviar archivos
        archivos_en_carpeta = os.listdir(ruta_carpeta)
        
        for archivo in archivos_en_carpeta:
            if archivo.endswith(".csv"):
                ruta_completa_archivo = os.path.join(ruta_carpeta, archivo)
                
                # Tamaño del archivo
                size_kb = os.path.getsize(ruta_completa_archivo) / 1024
                log(f"Enviando {archivo} ({size_kb:.1f} KB)...")

                with open(ruta_completa_archivo, "rb") as f:
                    ftp.storbinary(f"STOR {archivo}", f)

                log(f"--> {archivo} enviado exitosamente.")
                archivos_encontrados += 1

        ftp.quit()
        
        if archivos_encontrados == 0:
            log(f"La carpeta {ruta_carpeta} existe pero no tenía CSVs.")
        else:
            log(f"🏁 Proceso finalizado. Total archivos enviados: {archivos_encontrados}")

    except socket.gaierror:
        log("❌ ERROR DNS: No se pudo encontrar el servidor FTP. Revisa tu conexión o usa la IP.")
    except Exception as e:
        log(f"❌ ERROR FTP: {e}")

if __name__ == "__main__":
    enviar_archivos()