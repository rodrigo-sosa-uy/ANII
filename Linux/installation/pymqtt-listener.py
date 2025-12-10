import csv
from datetime import datetime
import time
import paho.mqtt.client as mqtt
import threading
import keyboard
import os

time.sleep(2)

#########################################################
################# Definicion de topicos #################
#########################################################

BROKER = "localhost"
MEASURE_TOPICS = [
    "measure/temperature",
    "measure/radiation",
    "measure/humidity",
]

TOPIC_IN_VALVE = "control/in_valve"
TOPIC_OUT_VALVE = "control/out_valve"
TOPIC_CTRL = "control/sampletime"

#########################################################
################ Definicion de archivos #################
#########################################################

# Directorio base
LOG_DIR = '/home/log' 

# Diccionario para mapear el nombre del sensor con su cabecera CSV
HEADERS = {
    'temperature': ['Time', 'Temperature1(°C)', 'Temperature2(°C)'],
    'radiation':   ['Time', 'Radiation(W/m^2)'],
    'humidity':    ['Time', 'Humidity(%)'],
    'in_valve':    ['Time', 'Signal(IN)'],
    'out_valve':   ['Time', 'Signal(OUT)']
}

#########################################################
############ Logica de escritura dinamica ###############
#########################################################

def escribir_log(tipo_dato, valor):
    """
    1. Genera el nombre de la CARPETA basado en la fecha actual.
    2. Si la carpeta no existe, la crea.
    3. Genera el nombre del archivo y escribe los datos.
    """
    now = datetime.now()
    
    # 1. Definir nombre de la carpeta y archivo: "YYYY_mm_dd"
    date_str = now.strftime('%Y_%m_%d')
    time_log = now.strftime('%H:%M:%S')

    # Ruta de la carpeta del día: /home/log/2025_11_25
    daily_dir = os.path.join(LOG_DIR, date_str)

    # 2. CREAR CARPETA SI NO EXISTE
    # Esto se ejecutará la primera vez que llegue un dato en un nuevo día
    if not os.path.exists(daily_dir):
        try:
            os.makedirs(daily_dir)
            print(f"Carpeta creada: {daily_dir}")
        except OSError as e:
            print(f"Error creando directorio {daily_dir}: {e}")
            return # Salimos si no se puede crear la carpeta

    # Construimos la ruta completa: /home/log/2025_11_25/2025_11_25_variable.csv
    filename = os.path.join(daily_dir, f"{date_str}_{tipo_dato}.csv")
    
    # Verificamos si el archivo existe para saber si poner cabecera
    archivo_existe = os.path.isfile(filename)

    try:
        with open(filename, 'a', newline='') as f:
            writer = csv.writer(f)
            # Si es nuevo (acaba de cambiar el día), ponemos header
            if not archivo_existe:
                writer.writerow(HEADERS[tipo_dato])
            
            # Escribimos el dato
            writer.writerow([time_log, valor])
    except Exception as e:
        print(f"Error escribiendo archivo {filename}: {e}")

#########################################################
############### Modo de operacion inicial ###############
#########################################################

modo = "auto"  # estado inicial
client = mqtt.Client() 

#########################################################
################### Hilos y funciones ###################
#########################################################

def publicar_valvula(topic, valor):
    global client
    try:
        client.publish(topic, valor)
        
        # Identificamos el tipo para el log
        tipo = 'in_valve' if topic == TOPIC_IN_VALVE else 'out_valve'
        
        # Llamamos a la funcion dinamica
        escribir_log(tipo, valor)
            
        print(f"Publicado → {topic}: {valor}")
    except Exception as e:
        print(f"Error publicando: {e}")

def mqtt_thread():
    global client
    
    def on_connect(client, userdata, flags, rc):
        print("Conectado con código:", rc)
        for top in MEASURE_TOPICS:
            client.subscribe(top)
            print("Suscrito a", top)

    def on_message(client, userdata, msg):
        payload = msg.payload.decode()
        print(f"Mensaje recibido → {msg.topic}: {payload}")
        
        # Llamamos a la funcion dinamica segun el topico
        if msg.topic == "measure/temperature":
            escribir_log('temperature', payload)
                
        elif msg.topic == "measure/radiation":
            escribir_log('radiation', payload)
                
        elif msg.topic == "measure/humidity":
            escribir_log('humidity', payload)
    
    # Configuracion de callbacks
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(BROKER, 1883, 60)
        client.loop_forever()
    except Exception as e:
        print(f"Error conexión MQTT: {e}")

def teclado_thread():
    global modo
    while True:
        try:
            if keyboard.is_pressed("f1"):  # tecla para modo manual
                modo = "manual"
                print("Cambiado a MODO MANUAL")
                time.sleep(0.3)

            elif keyboard.is_pressed("f2"):  # tecla para modo automático
                modo = "auto"
                print("Cambiado a MODO AUTOMÁTICO")
                time.sleep(0.3)
            
            # Controles manuales
            if modo == "manual":
                if keyboard.is_pressed("f3"):
                    publicar_valvula(TOPIC_IN_VALVE, 1)
                    time.sleep(0.3)
                elif keyboard.is_pressed("f4"):
                    publicar_valvula(TOPIC_IN_VALVE, 0)
                    time.sleep(0.3)
                elif keyboard.is_pressed("f5"):
                    publicar_valvula(TOPIC_OUT_VALVE, 1)
                    time.sleep(0.3)
                elif keyboard.is_pressed("f6"):
                    publicar_valvula(TOPIC_OUT_VALVE, 0)
                    time.sleep(0.3)
            elif modo == "auto":
                if keyboard.is_pressed("f7"):
                    publicar_valvula(TOPIC_CTRL, 1)
                    time.sleep(0.3)
                elif keyboard.is_pressed("f8"):
                    publicar_valvula(TOPIC_CTRL, 0)
                    time.sleep(0.3)
                    
            time.sleep(0.1)
        except Exception as e:
            print(f"Error teclado: {e}")

# Iniciar hilos
threading.Thread(target=mqtt_thread, daemon=True).start()
threading.Thread(target=teclado_thread, daemon=True).start()

# Bucle principal
while True:
    time.sleep(1)