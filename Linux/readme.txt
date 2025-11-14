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
- install.sh

Abrir terminal en esa carpeta y ejecutar:
sudo chmod 777 install.sh
sudo bash install.sh

Al finalizar, deben haberse movido los archivos:
- pymqtt-listener.py
- pymqtt-listener.service

##############################################################
####               Para instalar manualmente              ####
##############################################################
##############################################################
####                Para instalar mosquitto               ####
##############################################################
#Para instalar mosquitto:

sudo apt-get update -y
sudo apt install -y mosquitto mosquitto-dev mosquitto-clients

#Para comprobar que está funcionando:
sudo systemctl status mosquitto

#Para iniciarlo (si no está):
sudo systemctl start mosquitto

Para que pueda escuchar en la red:
En la carpeta /etc/mosquitto/conf.d, crear el archivo re.conf

El archivo debe contener:
listener 1883
allow_anonymous true

Ejecutar:
sudo systemctl restart mosquitto

Se puede comprobar con:
netstat -an | grep tcp

##############################################################
######################### IMPORTANTE #########################
##############################################################
#### - pymqtt-listener.py: escribe un timestamp en csv   #####
##############################################################

##############################################################
####           Ubicación de pymqtt-listener.py            ####
##############################################################

El archivo pymqtt-listener.py va en /usr/local/bin

sudo mv pymqtt-listener.py /usr/local/bin/
sudo chmod +x /usr/local/bin/pymqtt-listener.py

##############################################################
######################### IMPORTANTE #########################
##############################################################
#### - pymqtt-listener.service: para pymqtt-listener.py  #####
##############################################################

##############################################################
####        Ubicación de pymqtt-listener.service          ####
##############################################################

El archivo pymqtt-listener.service va en /etc/systemd/system

sudo chmod 777 /etc/systemd/system/pymqtt-listener.service

sudo systemctl daemon-reload
sudo systemctl enable pymqtt-listener.service
sudo systemctl start pymqtt-listener.service

sudo systemctl status pymqtt-listener.service

##############################################################
####                 Para instalar python                 ####
##############################################################

Para instalar Python:
sudo apt install -y python3 python3-pip

Para instalar los módulos requeridos:
pip install paho-mqtt datetime threaded keyboard

##############################################################
####             Se crea directorio de log                ####
##############################################################

sudo mkdir -p /home/log
sudo chmod 777 /home/log

##############################################################
####              Ubicación de archivo csv                ####
##############################################################

El servicio escribe en el archivo:
/home/log/temperature.csv

##############################################################
####               Instalación finalizada                 ####
##############################################################