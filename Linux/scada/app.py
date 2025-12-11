import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import os
import csv
from datetime import datetime

# --- CONFIGURACIÓN ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secreto_monitor'
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='eventlet')

BROKER = "localhost"
PORT = 1883
TOPICS = ["measure/temperature", "measure/radiation", "measure/humidity"]
LOG_DIR = '/home/log'

# Memoria temporal (último valor)
last_data = {
    "temperature": "--",
    "radiation": "--",
    "humidity": "--"
}

# --- FUNCIONES AUXILIARES ---

def get_today_history(sensor_name):
    """
    Lee el CSV del día actual para un sensor específico y devuelve una lista de puntos.
    Estructura: [{'time': '10:00:00', 'value': 25.5}, ...]
    """
    data_points = []
    try:
        now = datetime.now()
        date_str = now.strftime('%Y_%m_%d') # Nombre carpeta: 2025_12_11
        
        # Ruta: /home/log/2025_12_11/2025_12_11_temperature.csv
        file_path = os.path.join(LOG_DIR, date_str, f"{date_str}_{sensor_name}.csv")
        
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                next(reader, None) # Saltar encabezado
                for row in reader:
                    if len(row) >= 2:
                        # Asumimos Col 0: Hora, Col 1: Valor
                        try:
                            val = float(row[1])
                            data_points.append({'time': row[0], 'value': val})
                        except ValueError:
                            pass # Ignorar datos corruptos
    except Exception as e:
        print(f"Error leyendo historial {sensor_name}: {e}")
        
    return data_points

# --- LÓGICA MQTT ---

def on_connect(client, userdata, flags, rc):
    print(f"✅ Conectado al Broker MQTT (Código: {rc})")
    for t in TOPICS:
        client.subscribe(t)

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    variable = topic.split("/")[-1]
    
    # Guardamos en memoria
    last_data[variable] = payload
    
    # Enviamos a la web (SocketIO)
    socketio.emit('nuevo_dato', {'sensor': variable, 'valor': payload})

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(BROKER, PORT, 60)
    client.loop_start()
except Exception as e:
    print(f"❌ Error conectando a MQTT: {e}")

# --- RUTAS WEB ---

@app.route('/')
def index():
    return render_template('index.html', datos=last_data)

@app.route('/api/history')
def history():
    """Endpoint para que la web descargue los datos del día al iniciar"""
    return jsonify({
        'temperature': get_today_history('temperature'),
        'radiation': get_today_history('radiation'),
        'humidity': get_today_history('humidity')
    })

if __name__ == '__main__':
    print("🚀 Servidor Web con Gráficos Iniciado")
    socketio.run(app, host='0.0.0.0', port=5000)