import eventlet
eventlet.monkey_patch() # Parche necesario para websockets fluidos

from flask import Flask, render_template
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import json

# --- CONFIGURACIÓN ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secreto_monitor'
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='eventlet')

# Configuración MQTT (Local)
BROKER = "localhost"
PORT = 1883
TOPICS = [
    "measure/temperature",
    "measure/radiation",
    "measure/humidity"
]

# Memoria temporal para guardar el último dato recibido
last_data = {
    "temperature": "--",
    "radiation": "--",
    "humidity": "--"
}

# --- LÓGICA MQTT ---

def on_connect(client, userdata, flags, rc):
    print(f"✅ Conectado al Broker MQTT (Código: {rc})")
    for t in TOPICS:
        client.subscribe(t)
        print(f"   Suscrito a: {t}")

def on_message(client, userdata, msg):
    # Recibimos el mensaje del sensor
    topic = msg.topic
    payload = msg.payload.decode()
    
    # Limpiamos el nombre del tópico para usarlo de clave
    # Ej: "measure/temperature" -> "temperature"
    variable = topic.split("/")[-1]
    
    # Guardamos en memoria
    last_data[variable] = payload
    
    # ¡MAGIA! Enviamos el dato a la web en tiempo real
    socketio.emit('nuevo_dato', {'sensor': variable, 'valor': payload})
    # print(f"Dato recibido: {variable} = {payload}")

# Iniciar cliente MQTT en segundo plano
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(BROKER, PORT, 60)
    client.loop_start()
except Exception as e:
    print(f"❌ Error conectando a MQTT: {e}")

# --- RUTA WEB ---
@app.route('/')
def index():
    # Al entrar a la web, mostramos la plantilla con los últimos datos guardados
    return render_template('index.html', datos=last_data)

# --- ARRANQUE ---
if __name__ == '__main__':
    print("🚀 Servidor Web Iniciado en puerto 5000")
    # host='0.0.0.0' permite que otras PCs en tu red vean la página
    socketio.run(app, host='0.0.0.0', port=5000)