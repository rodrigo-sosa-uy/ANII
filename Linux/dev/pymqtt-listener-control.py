import csv
from datetime import datetime
import time
import paho.mqtt.client as mqtt
import threading
import keyboard

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

#########################################################
################ Definicion de archivos #################
#########################################################

# Para el funcionamiento

temperature_file = '/home/log/temperature.csv'
radiation_file = '/home/log/radiation.csv'
humidity_file = '/home/log/humidity.csv'
in_valve_file = '/home/log/in_valve.csv'
out_valve_file = '/home/log/out_valve.csv'

#########################################################
############ Creacion de los archivos de log ############
#########################################################

with open(temperature_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Date', 'Time', 'Temperature(°C)'])
    
with open(radiation_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Date', 'Time', 'Radiation(W/m^2)'])

with open(humidity_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Date', 'Time', 'Humidity(%)'])

with open(in_valve_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Date', 'Time', 'Signal(IN)'])

with open(out_valve_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Date', 'Time', 'Signal(OUT)'])

#########################################################
############### Modo de operacion inicial ###############
#########################################################

modo = "auto"  # estado inicial

#########################################################
################### Hilos y funciones ###################
#########################################################

def publicar_valvula(topic, valor):
    client.publish(topic, valor)
    
    if topic == TOPIC_IN_VALVE:
        with open(in_valve_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([date, time, valor])
            
    elif topic == TOPIC_OUT_VALVE:
        with open(out_valve_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([date, time, valor])
            
    print(f"Publicado → {topic}: {valor}")

def mqtt_thread():
    global mediciones
    def on_connect(client, userdata, flags, rc):
        print("Conectado con código:", rc)
        for top in MEASURE_TOPICS:
            client.subscribe(top)
            print("Suscrito a", top)

    def on_message(client, userdata, msg):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        timestamp = timestamp.split(' ')
        date = timestamp[0]
        time = timestamp[1]
        
        print(f"Mensaje recibido → {msg.topic}: {msg.payload}")
        
        if msg.topic == "measure/temperature":
            temperature = msg.payload.decode()
            
            with open(temperature_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([date, time, temperature])
                
        elif msg.topic == "measure/radiation":
            radiation = msg.payload.decode()
            
            with open(radiation_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([date, time, radiation])
            
        elif msg.topic == "measure/humidity":
            humidity = msg.payload.decode()
            
            with open(humidity_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([date, time, humidity])
    
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, 1883, 60)
    client.loop_forever()

def teclado_thread():
    global modo
    while True:
        if keyboard.is_pressed("f1"):  # tecla para modo manual
            modo = "manual"
            print("Cambiado a MODO MANUAL")

        elif keyboard.is_pressed("f2"):  # tecla para modo automático
            modo = "auto"
            print("Cambiado a MODO AUTOMÁTICO")
        
        # Controles manuales
        if modo == "manual":
            if keyboard.is_pressed("f3"):
                publicar_valvula(TOPIC_IN_VALVE, 1)
                time.sleep(0.25)
            elif keyboard.is_pressed("f4"):
                publicar_valvula(TOPIC_IN_VALVE, 0)
                time.sleep(0.25)
            elif keyboard.is_pressed("f5"):
                publicar_valvula(TOPIC_OUT_VALVE, 1)
                time.sleep(0.25)
            elif keyboard.is_pressed("f6"):
                publicar_valvula(TOPIC_OUT_VALVE, 0)
                time.sleep(0.25)
                
        time.sleep(0.25)
        
threading.Thread(target=mqtt_thread, daemon=True).start()
threading.Thread(target=teclado_thread, daemon=True).start()

# Bucle principal
while True:
    time.sleep(1)