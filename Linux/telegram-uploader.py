import os
import time
import zipfile
import requests
import logging
import urllib3
import pandas as pd
import matplotlib
# Usar backend 'Agg' es CRÍTICO para scripts que corren solos (sin monitor)
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# --- CONFIGURACIÓN ---
BOT_TOKEN = "8427486269:AAGxnU4s4sEacrtBKqFEIa-npsfkxuOBWiw"
CHAT_ID = "7289719287"
LOG_DIR = "/home/log"

# DESACTIVAR ADVERTENCIAS DE SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuración de log
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "uploader.log")),
        logging.StreamHandler()
    ]
)

def log(msg):
    logging.info(msg)
    print(msg)

# =========================================================================
# NUEVA FUNCIÓN: GENERACIÓN DE GRÁFICO (Replicando MATLAB)
# =========================================================================
def generar_grafico_radiacion(ruta_carpeta, fecha_str):
    """
    Lee el CSV de radiación del día, genera un gráfico con estadísticas
    y lo guarda como imagen PNG en la misma carpeta.
    """
    archivo_csv = os.path.join(ruta_carpeta, f"{fecha_str}_radiation.csv")
    archivo_img = os.path.join(ruta_carpeta, f"{fecha_str}_grafico_radiacion.png")

    if not os.path.exists(archivo_csv):
        log(f"⚠️ No se encontró {archivo_csv} para graficar.")
        return False

    try:
        log(f"Generando gráfico para {fecha_str}...")
        
        # 1. Leer datos
        # Asumimos que no tiene headers o usamos los nombres generados por tu logger
        # Ajusta 'names' si tu CSV tiene headers distintos. 
        # Tu logger ponía: ['Time', 'Radiation(W/m^2)']
        df = pd.read_csv(archivo_csv)
        
        if df.empty:
            log("⚠️ El CSV de radiación está vacío.")
            return False

        # 2. Preprocesamiento (Igual que en MATLAB)
        # Convertir la columna Time a objetos datetime completos
        # El CSV tiene solo la hora (HH:MM:SS), le pegamos la fecha actual
        df['FullTime'] = pd.to_datetime(fecha_str + ' ' + df.iloc[:, 0]) # Columna 0 es Time
        radiation_vals = df.iloc[:, 1] # Columna 1 es Radiación

        # 3. Estadísticas
        max_rad = radiation_vals.max()
        mean_rad = radiation_vals.mean()

        # 4. Graficar
        plt.figure(figsize=(10, 6)) # Tamaño de imagen
        
        # Plot color naranja quemado (#D95319)
        plt.plot(df['FullTime'], radiation_vals, color='#D95319', linewidth=1.5)

        # Formato del gráfico
        plt.title(f"Perfil de Radiación Solar - {fecha_str.replace('_', '-')}")
        plt.xlabel("Hora del día")
        plt.ylabel("Radiación (W/m^2)")
        plt.grid(True, which='both', linestyle='--', alpha=0.7)

        # Formato Eje X (Mostrar solo horas:minutos)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.gcf().autofmt_xdate() # Rotar fechas si es necesario

        # 5. Caja de Texto (Estadísticas)
        stats_text = f"Máximo: {max_rad:.2f} W/m^2\nPromedio: {mean_rad:.2f} W/m^2"
        # Coordenadas relativas (0.05, 0.95) es arriba a la izquierda
        plt.text(0.05, 0.95, stats_text, transform=plt.gca().transAxes,
                 fontsize=10, verticalalignment='top', bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", alpha=0.8))

        # 6. Guardar imagen
        plt.savefig(archivo_img, dpi=100)
        plt.close() # Cerrar figura para liberar memoria
        
        log(f"✅ Gráfico guardado: {archivo_img}")
        return True

    except Exception as e:
        log(f"❌ Error generando gráfico: {e}")
        return False

# =========================================================================
# FUNCIONES EXISTENTES (TELEGRAM Y ZIP)
# =========================================================================

def enviar_telegram(archivo_path, mensaje):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    try:
        with open(archivo_path, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': CHAT_ID, 'caption': mensaje}
            resp = requests.post(url, files=files, data=data, verify=False, timeout=60)
            
        if resp.status_code == 200:
            log("✅ Archivo enviado correctamente a Telegram.")
            return True
        else:
            log(f"❌ Error API Telegram: {resp.text}")
            return False
    except Exception as e:
        log(f"❌ Error de conexión: {e}")
        return False

def comprimir_carpeta(ruta_carpeta, nombre_zip):
    zip_path = ruta_carpeta + ".zip"
    if os.path.exists(zip_path):
        os.remove(zip_path)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        archivos_agregados = False 
        for root, dirs, files in os.walk(ruta_carpeta):
            for file in files:
                file_path = os.path.join(root, file)
                if file == os.path.basename(zip_path):
                    continue
                arcname = os.path.relpath(file_path, os.path.dirname(ruta_carpeta))
                zipf.write(file_path, arcname)
                archivos_agregados = True
        
        if not archivos_agregados:
            return None
    return zip_path

def tarea_diaria():
    # 1. Calcular fecha de ayer
    ayer = datetime.now() - timedelta(days=1)
    nombre_carpeta = ayer.strftime('%Y_%m_%d')
    ruta_carpeta = os.path.join(LOG_DIR, nombre_carpeta)
    
    log(f"--- Iniciando reporte para: {nombre_carpeta} ---")
    
    if not os.path.exists(ruta_carpeta):
        log(f"⚠️ No existe carpeta {ruta_carpeta}.")
        return

    # >>> NUEVO: Generar gráfico ANTES de comprimir <<<
    generar_grafico_radiacion(ruta_carpeta, nombre_carpeta)

    try:
        # 2. Comprimir (Ahora incluirá el PNG generado)
        log("Comprimiendo archivos...")
        zip_generado = comprimir_carpeta(ruta_carpeta, nombre_carpeta)
        
        if zip_generado is None:
             log("⚠️ Carpeta vacía.")
             return

        # 3. Enviar
        peso_kb = os.path.getsize(zip_generado)/1024
        log(f"Subiendo {zip_generado} ({peso_kb:.1f} KB)...")
        mensaje = f"📊 Reporte Diario IoT\n📅 Fecha: {nombre_carpeta}\n📈 Incluye gráfico de radiación."
        
        enviado = enviar_telegram(zip_generado, mensaje)
        
        # 4. Limpieza
        if enviado:
            os.remove(zip_generado)
            log("Zip temporal eliminado.")
            
    except Exception as e:
        log(f"ERROR CRÍTICO: {e}")

def esperar_medianoche():
    ahora = datetime.now()
    mañana = (ahora + timedelta(days=1)).replace(hour=0, minute=5, second=0, microsecond=0)
    if mañana < ahora: mañana = mañana + timedelta(days=1)
    segundos = (mañana - ahora).total_seconds()
    log(f"💤 Durmiendo {segundos/3600:.2f} horas...")
    time.sleep(segundos)

# --- BUCLE PRINCIPAL ---
if __name__ == "__main__":
    log("🤖 Bot Uploader Graficador iniciado.")
    
    # Descomenta esto si quieres probarlo YA MISMO con la fecha de ayer:
    # tarea_diaria()
    
    while True:
        esperar_medianoche()
        tarea_diaria()