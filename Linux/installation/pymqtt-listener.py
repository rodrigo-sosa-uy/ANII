import csv
import time
import os
import logging
import paho.mqtt.client as mqtt
from datetime import datetime

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
BROKER = "localhost"
PORT = 1883
LOG_DIR_BASE = '/home/log'

# --- CONFIGURACIÓN DE LOGGING MENSUAL ---
# 1. Obtenemos el mes actual: "2025_12"
current_month_str = datetime.now().strftime('%Y_%m')

# 2. Definimos la carpeta del mes para LOGS DE SISTEMA
LOG_MONTH_DIR = os.path.join(LOG_DIR_BASE, current_month_str)

# 3. Definimos el archivo final: "/home/log/2025_12/pymqtt-listener.log"
LOG_FILE = os.path.join(LOG_MONTH_DIR, 'pymqtt-listener.log')

# 4. Crear estructura de carpetas si no existe
if not os.path.exists(LOG_MONTH_DIR):
    try:
        os.makedirs(LOG_MONTH_DIR)
        print(f"📁 Carpeta de logs mensuales creada: {LOG_MONTH_DIR}")
    except OSError as e:
        print(f"CRITICAL ERROR: No se pudo crear directorio de logs {LOG_MONTH_DIR}: {e}")

# CONFIGURACIÓN DEL LOGGER
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE), # Guardar en carpeta del mes
        logging.StreamHandler()        # Mostrar en consola (systemd)
    ]
)

# Lista de tópicos a escuchar
TOPICS = {
    # Sensores
    "measure/environment":   "environment",
    "measure/radiation":     "radiation",
    "measure/temperature":   "temperature",
    "measure/level_in":      "level_in",
    "measure/level_out":     "level_out",
    "measure/chamber_level": "chamber_level", # Agregado para evitar warnings
    
    # Control (Eventos)
    "control/in_valve":      "control_in",
    "control/out_valve":     "control_out",
    "control/process":       "control_process"
}

# Definición de Encabezados CSV
HEADERS = {
    'environment':   ['Time', 'Amb_Temp(°C)', 'Humidity(%)', 'Pressure(hPa)'],
    'radiation':     ['Time', 'Radiation(W/m^2)'],
    'temperature':   ['Time', 'Internal_Temp(°C)'],
    'level_in':      ['Time', 'Weight(kg)', 'Distance(cm)', 'Volume(ml)'],
    'level_out':     ['Time', 'Weight(kg)', 'Distance(cm)', 'Volume(ml)'],
    'chamber_level': ['Time', 'Volume(ml)'],
    
    'control_in':      ['Time', 'State(1=OPEN/0=CLOSE)'],
    'control_out':     ['Time', 'State(1=OPEN/0=CLOSE)'],
    'control_process': ['Time', 'State(1=START/0=STOP)']
}

# =========================================================
# LÓGICA DE ALMACENAMIENTO (DATOS CSV)
# =========================================================
def escribir_log(nombre_variable, payload_str):
    """
    Gestiona la creación de carpetas DIARIAS y escritura en CSV.
    Nota: Los datos siguen en carpetas diarias para granularidad.
    """
    now = datetime.now()
    
    # Nombres basados en fecha
    date_str_folder = now.strftime('%Y_%m_%d') 
    time_log = now.strftime('%H:%M:%S')        

    # Verificar/Crear Directorio del DÍA (dentro de la base)
    # Ej: /home/log/2025_12_11/
    daily_dir = os.path.join(LOG_DIR_BASE, date_str_folder)
    
    if not os.path.exists(daily_dir):
        try:
            os.makedirs(daily_dir)
            logging.info(f"📂 Carpeta de datos diaria creada: {daily_dir}")
        except OSError as e:
            logging.error(f"❌ Error creando directorio diario: {e}")
            return

    # Ruta del Archivo CSV
    filename = os.path.join(daily_dir, f"{date_str_folder}_{nombre_variable}.csv")
    archivo_existe = os.path.isfile(filename)

    # Procesar los datos
    datos_recibidos = payload_str.split(',')
    fila_a_escribir = [time_log] + datos_recibidos

    # Escribir en CSV
    try:
        with open(filename, 'a', newline='') as f:
            writer = csv.writer(f)
            
            # Escribir cabecera solo si el archivo es nuevo
            if not archivo_existe:
                header = HEADERS.get(nombre_variable, ['Time', 'Value'])
                writer.writerow(header)
            
            # Escribir datos
            writer.writerow(fila_a_escribir)
            logging.info(f"💾 Guardado en {nombre_variable}: {fila_a_escribir}")
            
    except Exception as e:
        logging.error(f"❌ Error escribiendo archivo {filename}: {e}")

# =========================================================
# LÓGICA MQTT
# =========================================================

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info(f"✅ Conectado al Broker MQTT local (Código: {rc})")
        # Suscribirse a todos los tópicos
        for topic in TOPICS.keys():
            client.subscribe(topic)
            logging.info(f"   Suscrito a: {topic}")
    else:
        logging.error(f"❌ Falló conexión al Broker. Código: {rc}")

def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = msg.payload.decode()
        
        if topic in TOPICS:
            nombre_variable = TOPICS[topic]
            escribir_log(nombre_variable, payload)
        else:
            logging.warning(f"⚠️ Tópico desconocido recibido: {topic}")
            
    except Exception as e:
        logging.error(f"❌ Error procesando mensaje MQTT: {e}")

# =========================================================
# BUCLE PRINCIPAL
# =========================================================

if __name__ == "__main__":
    logging.info("--- 📝 INICIANDO LOGGER MQTT V2.0 ---")
    logging.info(f"    Directorio base: {LOG_DIR_BASE}")
    logging.info(f"    Log de sistema:  {LOG_FILE}")

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        logging.info(f"Intentando conectar a {BROKER}:{PORT}...")
        client.connect(BROKER, PORT, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        logging.info("Deteniendo Logger por solicitud del usuario.")
    except Exception as e:
        logging.critical(f"❌ Error fatal de conexión: {e}")