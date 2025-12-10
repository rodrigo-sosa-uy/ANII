import os
import subprocess
import sys

# --- CONFIGURACIÓN ---
# Elige la resolución que quieras ver cuando te conectes remotamente
# Opciones comunes: "1920x1080", "1366x768", "1280x720"
RESOLUCION = "1366x768" 

def log(msg):
    print(f"[Headless Setup] {msg}")

def run_command(command):
    try:
        subprocess.check_call(command, shell=True)
        return True
    except subprocess.CalledProcessError:
        return False

def crear_configuracion_dummy():
    log("Generando archivo de configuración Xorg...")
    
    # Contenido del archivo xorg.conf para el driver dummy
    # Define un monitor virtual con la resolución deseada
    config_content = f"""
    Section "Device"
        Identifier  "Configured Video Device"
        Driver      "dummy"
        VideoRam    256000
    EndSection

    Section "Monitor"
        Identifier  "Configured Monitor"
        HorizSync 31.5-48.5
        VertRefresh 50-70
    EndSection

    Section "Screen"
        Identifier  "Default Screen"
        Monitor     "Configured Monitor"
        Device      "Configured Video Device"
        DefaultDepth 24
        SubSection "Display"
            Depth 24
            Modes "{RESOLUCION}"
        EndSubSection
    EndSection
    """
    
    # Ruta donde Xubuntu busca la configuración de pantalla
    config_path = "/usr/share/X11/xorg.conf.d/xorg.conf"
    
    try:
        with open(config_path, "w") as f:
            f.write(config_content)
        log(f"✅ Archivo creado exitosamente en: {config_path}")
        return True
    except PermissionError:
        log("❌ Error de permisos. Debes ejecutar este script con SUDO.")
        return False
    except Exception as e:
        log(f"❌ Error creando archivo: {e}")
        return False

def main():
    # Verificar permisos de root
    if os.geteuid() != 0:
        log("Este script requiere permisos de administrador.")
        log("Por favor ejecuta: sudo python3 setup_headless.py")
        sys.exit(1)

    log("--- Iniciando configuración de Monitor Virtual (Headless) ---")

    # 1. Instalar el driver dummy
    log("Instalando xserver-xorg-video-dummy...")
    if run_command("apt-get update && apt-get install -y xserver-xorg-video-dummy"):
        log("✅ Driver instalado.")
    else:
        log("❌ Error instalando el driver. Verifica tu conexión a internet.")
        sys.exit(1)

    # 2. Crear configuración
    if crear_configuracion_dummy():
        log("--- CONFIGURACIÓN FINALIZADA ---")
        log("⚠️  IMPORTANTE: Para que los cambios surtan efecto, debes reiniciar.")
        log("   ¿Quieres reiniciar ahora? (s/n)")
        
        # Preguntar para reiniciar
        response = input().lower()
        if response == 's':
            os.system("reboot")
        else:
            log("Recuerda reiniciar manualmente con 'sudo reboot' antes de desconectar el monitor.")

if __name__ == "__main__":
    main()