import csv
import time
import os
import requests
import logging
from datetime import datetime

#########################################################
################ Configuracion OpenWeather ##############
#########################################################

# 1. TU API KEY (Registrate en openweathermap.org)
API_KEY = "8ffb8c6d3d547f878fdbcb8a0cee64bd"

# 2. TU UBICACION (Ejemplo: Fray Bentos, UY)
LAT = "-33.11780904626111"
LON = "-58.33070862584043"

# 3. Intervalo de muestreo (Segundos)
SAMPLE_TIME = 900  # 15 minutos (Ajustado para coincidir con la logica general)

#########################################################
################ Configuracion de Logging ###############
#########################################################

LOG_DIR_BASE = '/home/log'

# 1. Obtenemos el mes actual: "2025_12"
current_month_str = datetime.now().strftime('%Y_%m')

# 2. Definimos la carpeta del mes para LOGS DE SISTEMA
LOG_MONTH_DIR = os.path.join(LOG_DIR_BASE, current_month_str)

# 3. Definimos el archivo final: "/home/log/2025_12/weather-logger.log"
LOG_FILE = os.path.join(LOG_MONTH_DIR, 'weather-logger.log')

# 4. Crear estructura de carpetas si no existe
if not os.path.exists(LOG_MONTH_DIR):
    try:
        os.makedirs(LOG_MONTH_DIR)
        print(f"Carpeta de logs mensuales creada: {LOG_MONTH_DIR}")
    except OSError as e:
        print(f"CRITICAL ERROR: No se pudo crear directorio de logs {LOG_MONTH_DIR}: {e}")

# Configuracion del Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# Cabecera del CSV de DATOS
HEADER_WEATHER = ['Time', 'Condition', 'Description', 'Temp(°„C)', 'Humidity(%)', 'Clouds(%)', 'Pressure(hPa)']

#########################################################
################## Funciones Principales ################
#########################################################

def obtener_datos_clima():
    """
    Consulta la API y retorna una lista con los datos formateados.
    Retorna None si falla la conexi√≥n.
    """
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric&lang=es"
    
    try:
        logging.info("Solicitando datos a OpenWeatherMap...")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extraer datos relevantes del JSON
            condition = data['weather'][0]['main']
            description = data['weather'][0]['description']
            temp = data['main']['temp']
            hum = data['main']['humidity']
            clouds = data['clouds']['all'] 
            pressure = data['main']['pressure']
            
            logging.info(f"Datos recibidos: {condition}, {temp}°„C, {hum}% Hum")
            return [condition, description, temp, hum, clouds, pressure]
        else:
            logging.error(f"Error API: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        logging.error(f"Error de conexion al obtener clima: {e}")
        return None

def escribir_log_datos(datos_clima):
    """
    Escribe los DATOS en /home/log/YYYY_MM_DD/YYYY_MM_DD_weather.csv
    (Carpetas Diarias para los datos)
    """
    now = datetime.now()
    date_str = now.strftime('%Y_%m_%d')
    time_log = now.strftime('%H:%M:%S')

    # Ruta de la carpeta del dia (DATOS)
    daily_dir = os.path.join(LOG_DIR_BASE, date_str)

    # Crear carpeta diaria si no existe
    if not os.path.exists(daily_dir):
        try:
            os.makedirs(daily_dir)
            logging.info(f"Carpeta de datos diaria creada: {daily_dir}")
        except OSError as e:
            logging.error(f"Error creando directorio de datos: {e}")
            return

    # Nombre del archivo: 2025_11_25_weather.csv
    filename = os.path.join(daily_dir, f"{date_str}_weather.csv")
    archivo_existe = os.path.isfile(filename)

    try:
        with open(filename, 'a', newline='') as f:
            writer = csv.writer(f)
            
            # Escribir Header si es archivo nuevo
            if not archivo_existe:
                writer.writerow(HEADER_WEATHER)
            
            # Preparar fila
            row = [time_log] + datos_clima
            writer.writerow(row)
            
            logging.info(f"Clima registrado en CSV: {row}")

    except Exception as e:
        logging.error(f"Error escribiendo archivo CSV {filename}: {e}")

#########################################################
################### Bucle Principal #####################
#########################################################

if __name__ == "__main__":
    logging.info("--- Logger de Clima (OpenWeatherMap) INICIADO ---")
    logging.info(f"    Muestreo cada {SAMPLE_TIME} segundos.")
    logging.info(f"    Base de datos: {LOG_DIR_BASE}")
    logging.info(f"    Log de sistema: {LOG_FILE}")

    while True:
        try:
            # 1. Obtener datos
            datos = obtener_datos_clima()
            
            # 2. Guardar si hubo exito
            if datos:
                escribir_log_datos(datos)
            
            # 3. Esperar al siguiente ciclo
            time.sleep(SAMPLE_TIME)
            
        except KeyboardInterrupt:
            logging.info("Deteniendo servicio por usuario.")
            break
        except Exception as e:
            logging.critical(f"Error fatal en bucle principal: {e}")
            time.sleep(60) # Esperar un minuto antes de reintentar si exploto algo