import csv
import time
import os
import requests
from datetime import datetime

#########################################################
################ Configuracion OpenWeather ##############
#########################################################

# 1. TU API KEY (Regístrate en openweathermap.org)
API_KEY = "8ffb8c6d3d547f878fdbcb8a0cee64bd"

# 2. TU UBICACIÓN (Ejemplo: Fray Bentos, UY)
LAT = "-33.11780904626111"
LON = "-58.33070862584043"

# 3. Intervalo de muestreo (Segundos)
# La cuenta gratuita permite 60 llamadas por minuto, 
# pero el clima no cambia tanto. Cada 5 o 10 min está bien.
SAMPLE_TIME = 900  # 10 minutos

#########################################################
################ Definicion de archivos #################
#########################################################

# Directorio base (Mismo que el sistema MQTT)
LOG_DIR = '/home/log' 

# Cabecera del CSV
HEADER_WEATHER = ['Time', 'Condition', 'Description', 'Temp(°C)', 'Humidity(%)', 'Clouds(%)', 'Pressure(hPa)']

#########################################################
################## Funciones Principales ################
#########################################################

def obtener_datos_clima():
    """
    Consulta la API y retorna una lista con los datos formateados.
    Retorna None si falla la conexión.
    """
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric&lang=es"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extraer datos relevantes del JSON
            # 'main' es la condición principal (Rain, Clouds, Clear)
            condition = data['weather'][0]['main']
            # 'description' es detallado (cielo claro, nubes dispersas)
            description = data['weather'][0]['description']
            temp = data['main']['temp']
            hum = data['main']['humidity']
            clouds = data['clouds']['all'] # % de nubosidad (Crucial para piranómetro)
            pressure = data['main']['pressure']
            
            return [condition, description, temp, hum, clouds, pressure]
        else:
            print(f"Error API: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"Error de conexión al obtener clima: {e}")
        return None

def escribir_log(datos_clima):
    """
    Escribe los datos en /home/log/YYYY_MM_DD/YYYY_MM_DD_weather.csv
    """
    now = datetime.now()
    date_str = now.strftime('%Y_%m_%d')
    time_log = now.strftime('%H:%M:%S')

    # Ruta de la carpeta del día
    daily_dir = os.path.join(LOG_DIR, date_str)

    # Crear carpeta si no existe (Sincronizado con tu otro script)
    if not os.path.exists(daily_dir):
        try:
            os.makedirs(daily_dir)
            print(f"Carpeta creada: {daily_dir}")
        except OSError as e:
            print(f"Error creando directorio: {e}")
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
            
            # Preparar fila: [Hora, Condicion, Desc, Temp, Hum, Nubes, Presion]
            row = [time_log] + datos_clima
            writer.writerow(row)
            
            print(f"✅ Clima registrado: {row}")

    except Exception as e:
        print(f"Error escribiendo archivo {filename}: {e}")

#########################################################
################### Bucle Principal #####################
#########################################################

if __name__ == "__main__":
    print("🌤️ Logger de Clima (OpenWeatherMap) iniciado.")
    print(f"   Muestreo cada {SAMPLE_TIME} segundos.")
    print(f"   Guardando en: {LOG_DIR}")

    while True:
        # 1. Obtener datos
        datos = obtener_datos_clima()
        
        # 2. Guardar si hubo éxito
        if datos:
            escribir_log(datos)
        
        # 3. Esperar al siguiente ciclo
        time.sleep(SAMPLE_TIME)