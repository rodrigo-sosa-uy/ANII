#!/usr/bin/python3
import csv
from datetime import datetime
import time
import paho.mqtt.client as mqtt

BROKER = "localhost"
TOPIC = "measure/temperature"

archivo_csv = '/home/log/temperature.csv'

time.sleep(2)

def on_connect(client, userdata, flags, rc):
    print("Conectado con código:", rc)
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    timestamp = timestamp.split(' ')
    date = timestamp[0]
    time = timestamp[1]
    if msg.topic == TOPIC:
        temperature = msg.payload.decode()
    
    with open(archivo_csv, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([date, time, temperature])

with open(archivo_csv, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Date', 'Time', 'Temperature(°C)'])
    
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, 1883, 60)
client.loop_forever()