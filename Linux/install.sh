#!/bin/bash
##############################################################
####                Script automático para                ####
####                la instalación de MQTT                ####
##############################################################
####                Proyecto Desalinzador                 ####
##############################################################
#### Los archivos:                                        ####
#### - pymqtt-listener.py                                 ####
#### - pymqtt-listener.service                            ####
#### deben estar en la misma carpeta que este script.     ####
##############################################################

##############################################################
####                Para instalar mosquitto               ####
##############################################################

sudo apt-get update -y
sudo apt install -y mosquitto mosquitto-dev mosquitto-clients

#Para comprobar que está funcionando:
#sudo systemctl status mosquitto

#Para iniciarlo (si no está):
#sudo systemctl start mosquitto

##############################################################
####           Ubicación de pymqtt-listener.py            ####
##############################################################

#El archivo pymqtt-listener.py va en /usr/local/bin

if [ -f "pymqtt-listener.py" ]; then
    sudo mv pymqtt-listener.py /usr/local/bin/
    sudo chmod +x /usr/local/bin/pymqtt-listener.py
else
    echo "⚠️  No se encontró pymqtt-listener.py en el directorio actual"
fi

##############################################################
######################### IMPORTANTE #########################
##############################################################
#### - pymqtt-listener.service: para pymqtt-listener.py  #####
##############################################################

##############################################################
####        Ubicación de pymqtt-listener.service          ####
##############################################################

#El archivo pymqtt-listener.service va en /etc/systemd/system

if [ -f "pymqtt-listener.service" ]; then
    sudo mv pymqtt-listener.service /etc/systemd/system/
    sudo chmod 777 /etc/systemd/system/pymqtt-listener.service
    sudo systemctl daemon-reload
    sudo systemctl enable pymqtt-listener.service
    sudo systemctl start pymqtt-listener.service
	
	#sudo systemctl status pymqtt-listener.service
else
    echo "⚠️  No se encontró pymqtt-listener.service en el directorio actual"
fi

#Para que pueda escuchar en la red:
#En la carpeta /etc/mosquitto/conf.d, crear el archivo re.conf

cd /etc/mosquitto/conf.d || { echo "No se pudo acceder a /etc/mosquitto/conf.d"; exit 1; }

#El archivo debe contener:
#listener 1883
#allow_anonymous true

echo "listener 1883
allow_anonymous true" | sudo tee re.conf > /dev/null

#Ejecutar:
sudo systemctl restart mosquitto

#Se puede comprobar con:
#netstat -an | grep tcp

##############################################################
####                 Para instalar python                 ####
##############################################################

#Para instalar Python:
#sudo apt install --break-system-packages -y python3
sudo apt install --break-system-packages -y python3-pip

#Para instalar los módulos requeridos:
pip install --break-system-packages paho-mqtt datetime threaded keyboard

##############################################################
######################### IMPORTANTE #########################
##############################################################
#### - pymqtt-listener.py: escribe un timestamp en csv   #####
##############################################################

#Se crea el directorio para el csv:
sudo mkdir -p /home/log
sudo chmod 777 /home/log

##############################################################
####              Ubicación de archivo csv                ####
##############################################################

#El servicio escribe en el archivo:
#/home/log/temperature.csv

#Si se quiere cambiar archivo de registro:
#	Cambiar en pymqtt-listener.py

##############################################################
####              Ubicación de archivo csv                ####
##############################################################

echo "Instalación finalizada."

##############################################################