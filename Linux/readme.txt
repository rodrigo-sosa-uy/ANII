##############################################################
####             Guía para la puesta en marcha            ####
####             del sistema de recolección de            ####
####             datos del Proy. Desalinizador            ####
##############################################################
####             Desarrollado por Rodrigo Sosa            ####
####                rodrigo.sosa@utec.edu.uy              ####
##############################################################
##############################################################
##############            IMPORTANTE            ##############
##############################################################
- Asegurese de tener conexión a internet.
- El script ha sido desarrollado y probado para Xubuntu 22.04.
- Se debe tener una instalación limpia del sis. operativo.
- Este script pone en marcha el sistema, sin necesidad de
  acciones suplementarias.
- Se asume que Python está instalado en el sistema operativo.
- Las comprobaciones están desactivadas, puede verificar
  manualmente el estado del servicio o la red.
##############################################################
####             Para instalar automáticamente            ####
##############################################################

Se debe tener una carpeta con los archivos:
- pymqtt-listener.py
- pymqtt-listener.service
- data-send.py
- data-send.service
- telegram-uploader.py
- telegram-uploader.service
- install.sh

Abrir una terminal en el escritorio y ejecutar:
sudo apt update
sudo apt upgrade -y
sudo apt install git -y
sudo apt install mousepad -y

Abrir terminal en esa carpeta y ejecutar:
sudo chmod 777 install.sh
sudo bash install.sh

Al finalizar, deben haberse movido los archivos:
- pymqtt-listener.py
- pymqtt-listener.service
- data-send.py
- data-send.service
- telegram-uploader.py
- telegram-uploader.service

##############################################################
######################### IMPORTANTE #########################
##############################################################
####    Asegurese de que el servicio de RustDesk está     ####
####  corriendo efectivamente, al abrir la interfaz de    ####
####  la aplicación deberá decir "Stop Service", en caso  ####
####       de decir "Start Service", haga click ahí       ####
##############################################################

- Abra RustDesk desde el menú de aplicaciones.
- Anote el ID (número largo).
- A la derecha verás tres puntos verticales (Menú) o un icono
  de lápiz/escudo junto a la contraseña.
- Haz clic para editar la contraseña.
- Marca la casilla "Enable permanent password" (Habilitar
  contraseña permanente) y pon una clave segura.
  
Para conectarse al escritorio remoto:
- Instala RustDesk en tu laptop.
- Pon el ID anotado anteriormente.
- Introduzca la contraseña.

##############################################################
######################### IMPORTANTE #########################
##############################################################
####    Ejecutar solamente después de haber realizado     ####
####  la instalación, sea manualmente o automáticamente   ####
##############################################################
####                 Para configurar la red               ####
##############################################################

- Asegurese de que el dispositivo está conectado a la red
- Realice los cambios que sean necesarios dentro del script,
  por ejemplo el nombre de la conexión o la IP asignada.

Abrir terminal en esa carpeta y ejecutar:
sudo chmod 777 net.sh
sudo bash net.sh

Este script debe asignar una IP estática al dispositivo.
La IP definida es: 192.168.101.250/24

Se recomienda reiniciar el dispositivo y corroborar que tiene
la IP correcta:

sudo nmcli

Finalmente puede comprobar si sigue teniendo acceso a internet
con esta nueva IP, desde un navegador.