import serial
import csv
from datetime import datetime
import time

# Ajustá el puerto y velocidad a tu configuración
puerto = 'COM6'         # Ejemplo en Windows (en Linux podría ser '/dev/ttyUSB0')
baudrate = 115200
archivo_csv = 'datos_sensor.csv'

time.sleep(2) 

# Abrir conexión serial
ser = serial.Serial(puerto, baudrate, timeout=1)

# Abrir archivo CSV y escribir encabezado si está vacío
with open(archivo_csv, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Timestamp', 'Temperatura (°C)', 'Humedad (%)', 'Presión (hPa)'])

print("Grabando datos... presioná Ctrl+C para detener")

try:
    while True:
        linea = ser.readline().decode('utf-8').strip()
        if linea:
            try:
                temperatura, humedad, presion = linea.split(',')
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                with open(archivo_csv, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([timestamp, temperatura, humedad, presion])

                print(f"{timestamp} | Temp: {temperatura} °C | Hum: {humedad} % | Pres: {presion} hPa")

            except ValueError:
                # Si llega una línea corrupta o incompleta
                print("Línea inválida:", linea)

except KeyboardInterrupt:
    print("\nGrabación finalizada")

finally:
    ser.close()