import time
import paho.mqtt.client as mqtt

# =========================================================
# CONFIGURACIÓN
# =========================================================
BROKER = "localhost"
PORT = 1883

# Lista de datos simulados para probar TODOS los tópicos V2.0
# Formato: (Tópico, Payload)
TEST_PAYLOADS = [
    # --- SENSORES ---
    # CSV: Temp=25.5°C, Hum=60%, Pres=1013hPa
    ("measure/environment", "25.50,60.00,1013.20"), 
    
    # Float: 850.5 W/m^2
    ("measure/radiation",   "850.50"),              
    
    # Float: 45.2 °C (Temp Interna)
    ("measure/temperature", "45.20"),               
    
    # CSV: Peso=15.5kg, Distancia=50.0cm
    ("measure/level_in",    "15.50,50.00"),         
    
    # CSV: Peso=5.2kg, Distancia=10.0cm
    ("measure/level_out",   "5.20,10.00"),          

    # --- CONTROL ---
    ("control/in_valve",    "1"), # Válvula Abierta
    ("control/out_valve",   "0"), # Válvula Cerrada
    ("control/process",     "1")  # Proceso Iniciado
]

def main():
    print("--- 🚀 INICIANDO PRUEBA MANUAL MQTT ---")
    print(f"Objetivo: {BROKER}:{PORT}")
    
    client = mqtt.Client("Test_Script_Manual")
    
    try:
        client.connect(BROKER, PORT, 60)
        print("✅ Conectado al Broker.")
    except Exception as e:
        print(f"❌ Error conectando al broker: {e}")
        print("   -> Asegúrate de que Mosquitto esté corriendo (sudo systemctl status mosquitto)")
        return

    print("\n--- 📤 ENVIANDO DATOS ---")
    
    for topic, payload in TEST_PAYLOADS:
        client.publish(topic, payload)
        print(f"   Publicado -> [{topic}]: {payload}")
        time.sleep(0.5) # Pequeña pausa para ver el log ordenado

    client.disconnect()
    
    print("\n--- 🏁 PRUEBA FINALIZADA ---")
    print("Por favor verifica que se hayan creado los archivos en:")
    print("📂 /home/log/AAAA_MM_DD/")
    print("   -> environment.csv")
    print("   -> radiation.csv")
    print("   -> temperature.csv")
    print("   -> level_in.csv")
    print("   -> level_out.csv")
    print("   -> control_in.csv...")

if __name__ == "__main__":
    main()