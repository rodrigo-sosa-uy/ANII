import os
import sys
import time

# Rutas de configuración
CONFIG_PATH = "/usr/share/X11/xorg.conf.d/xorg.conf"
BACKUP_PATH = "/usr/share/X11/xorg.conf.d/xorg.conf.disabled"

def log(msg):
    print(f"[Monitor Switch] {msg}")

def check_root():
    if os.geteuid() != 0:
        log("❌ Debes ejecutar este script como ROOT (sudo).")
        sys.exit(1)

def main():
    check_root()
    
    print("========================================")
    print("   INTERRUPTOR DE MODO DE PANTALLA")
    print("========================================")

    # CASO 1: El archivo existe -> Estamos en MODO HEADLESS (Dummy)
    # Acción: Desactivarlo para usar monitor físico.
    if os.path.exists(CONFIG_PATH):
        print("Estado actual: 👻 MODO HEADLESS (Monitor Virtual Activo)")
        print("Acción: Se desactivará el monitor virtual para usar HDMI físico.")
        
        try:
            os.rename(CONFIG_PATH, BACKUP_PATH)
            log("✅ Configuración desactivada (movida a .disabled).")
            print("\n>> AL REINICIAR: El puerto HDMI funcionará, pero RustDesk podría mostrar pantalla negra si no hay monitor.")
        except Exception as e:
            log(f"❌ Error al cambiar modo: {e}")
            return

    # CASO 2: El archivo no existe (o está en backup) -> Estamos en MODO FÍSICO
    # Acción: Activarlo para usar sin monitor.
    elif os.path.exists(BACKUP_PATH):
        print("Estado actual: 📺 MODO FÍSICO (HDMI Activo)")
        print("Acción: Se activará el monitor virtual (Dummy) para acceso remoto sin pantalla.")
        
        try:
            os.rename(BACKUP_PATH, CONFIG_PATH)
            log("✅ Configuración activada (Dummy Driver habilitado).")
            print("\n>> AL REINICIAR: El puerto HDMI dejará de dar imagen.")
        except Exception as e:
            log(f"❌ Error al cambiar modo: {e}")
            return
            
    # CASO 3: No existe ni el config ni el backup (Nunca se instaló el dummy)
    else:
        log("⚠️ No se encontró configuración del Dummy Driver.")
        log("Primero debes ejecutar el script de instalación 'setup_headless.py'.")
        return

    # PREGUNTA DE REINICIO
    print("\n⚠️  ES NECESARIO REINICIAR PARA APLICAR CAMBIOS.")
    choice = input("¿Reiniciar ahora? (s/n): ").lower()
    
    if choice == 's':
        log("Reiniciando sistema...")
        time.sleep(1)
        os.system("reboot")
    else:
        log("Cambios guardados. Reinicia manualmente cuando estés listo.")

if __name__ == "__main__":
    main()