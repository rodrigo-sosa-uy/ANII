import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import os
import csv
import logging
from datetime import datetime

# =========================================================
# CONFIGURACIÓN DE LOGGING (MENSUAL)
# =========================================================
LOG_DIR_BASE = '/home/log'
current_month_str = datetime.now().strftime('%Y_%m')
LOG_MONTH_DIR = os.path.join(LOG_DIR_BASE, current_month_str)
LOG_FILE = os.path.join(LOG_MONTH_DIR, 'scada.log')

# Crear carpeta si no existe
if not os.path.exists(LOG_MONTH_DIR):
    try:
        os.makedirs(LOG_MONTH_DIR)
    except:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def log(msg):
    logging.info(msg)

# =========================================================
# CONFIGURACIÓN APP
# =========================================================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secreto_monitor_v3'
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='eventlet')

BROKER = "localhost"
PORT = 1883

# Lista de Tópicos
TOPICS = [
    "measure/environment", 
    "measure/radiation",   
    "measure/temperature", 
    "measure/level_in",    
    "measure/level_out",
    "measure/chamber_level",
    "control/in_valve",
    "control/out_valve",
    "control/process"
]

# Estado actual (Cache)
last_data = {
    # Proceso (ml y °C)
    "lvl_in": "--",      # Volumen Entrada (ml)
    "chamber_level": "--", # Volumen Cámara (ml)
    "int_temp": "--",      # Temp Cámara
    "lvl_out": "--",     # Volumen Salida (ml)
    
    # Ambiente
    "radiation": "--",
    "env_temp": "--",
    "env_hum": "--",
    "env_pres": "--",
    
    # Estados de Control
    "in_valve": "0", 
    "out_valve": "0", 
    "process": "0"
}

# =========================================================
# HISTORIAL (Lectura de CSVs)
# =========================================================
def get_today_history(variable_web):
    data_points = []
    try:
        now = datetime.now()
        date_str = now.strftime('%Y_%m_%d')
        daily_dir = os.path.join(LOG_DIR_BASE, date_str)
        
        # Mapeo: Variable Web -> (Archivo CSV, Índice Columna)
        # CSV Structure:
        # environment: [Time(0), Temp(1), Hum(2), Pres(3)]
        # level_in/out: [Time(0), Weight(1), Dist(2), Vol(3)]
        # chamber: [Time(0), Vol(1)]
        
        map_config = {
            'env_temp':      ('environment', 1),
            'env_hum':       ('environment', 2),
            'env_pres':      ('environment', 3),
            'radiation':     ('radiation', 1),
            'int_temp':      ('temperature', 1),
            'chamber_level': ('chamber_level', 1),
            'lvl_in':        ('level_in', 3),  # Columna 3 es Volumen
            'lvl_out':       ('level_out', 3)  # Columna 3 es Volumen
        }
        
        if variable_web not in map_config: return []

        file_suffix, col_idx = map_config[variable_web]
        filename = f"{date_str}_{file_suffix}.csv"
        file_path = os.path.join(daily_dir, filename)
        
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                next(reader, None) 
                for row in reader:
                    if len(row) > col_idx:
                        try:
                            val = float(row[col_idx])
                            data_points.append({'time': row[0], 'value': val})
                        except ValueError: pass
    except Exception as e:
        logging.error(f"Error leyendo historial {variable_web}: {e}")
        
    return data_points

# =========================================================
# LÓGICA MQTT
# =========================================================
def update_and_emit(key, value):
    last_data[key] = value
    socketio.emit('nuevo_dato', {'sensor': key, 'valor': value})

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        log("✅ SCADA Conectado al Broker MQTT.")
        for t in TOPICS:
            client.subscribe(t)
    else:
        logging.error(f"❌ Falló conexión MQTT. Código: {rc}")

def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = msg.payload.decode()
        
        # --- PARSEO DE DATOS ---
        
        if topic == "measure/environment":
            # Payload: "25.5,60.0,1013.2"
            parts = payload.split(',')
            if len(parts) >= 3:
                update_and_emit('env_temp', parts[0])
                update_and_emit('env_hum', parts[1])
                update_and_emit('env_pres', parts[2])
                
        elif topic == "measure/level_in":
            # Payload: "Peso,Dist,Volumen"
            parts = payload.split(',')
            if len(parts) >= 3:
                update_and_emit('lvl_in', parts[2]) # Usamos Volumen (idx 2)

        elif topic == "measure/level_out":
            # Payload: "Peso,Dist,Volumen"
            parts = payload.split(',')
            if len(parts) >= 3:
                update_and_emit('lvl_out', parts[2]) # Usamos Volumen

        elif topic == "measure/chamber_level":
            update_and_emit('chamber_level', payload)

        elif topic == "measure/radiation":
            update_and_emit('radiation', payload)

        elif topic == "measure/temperature":
            update_and_emit('int_temp', payload)
            
        # --- FEEDBACK CONTROL ---
        elif topic == "control/in_valve":
            update_and_emit('in_valve', payload)
        elif topic == "control/out_valve":
            update_and_emit('out_valve', payload)
        elif topic == "control/process":
            update_and_emit('process', payload)
            
    except Exception as e:
        logging.error(f"Error procesando mensaje MQTT: {e}")

# Iniciar Cliente MQTT
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(BROKER, PORT, 60)
    client.loop_start()
except Exception as e:
    logging.critical(f"❌ Error fatal MQTT: {e}")

# =========================================================
# SOCKETIO - COMANDOS
# =========================================================
@socketio.on('control_cmd')
def handle_control_command(json_data):
    try:
        topic = json_data.get('topic')
        payload = json_data.get('payload')
        if topic and payload is not None:
            client.publish(topic, str(payload))
            log(f"🎮 Comando Web: [{topic}] = {payload}")
    except Exception as e:
        logging.error(f"Error comando web: {e}")

# =========================================================
# RUTAS WEB
# =========================================================
@app.route('/')
def index():
    return render_template('index.html', datos=last_data)

@app.route('/api/history')
def history():
    return jsonify({
        'env_temp': get_today_history('env_temp'),
        'env_hum': get_today_history('env_hum'),
        'env_pres': get_today_history('env_pres'),
        'radiation': get_today_history('radiation'),
        'int_temp': get_today_history('int_temp'),
        'lvl_in': get_today_history('lvl_in'),
        'chamber_level': get_today_history('chamber_level'),
        'lvl_out': get_today_history('lvl_out')
    })

if __name__ == '__main__':
    log("🚀 Servidor Web SCADA V2.0 Iniciado")
    socketio.run(app, host='0.0.0.0', port=5000)