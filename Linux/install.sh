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
#### - data-send.py                                       ####
#### - data-send.service                                  ####
#### - telegram-uploader.py                               ####
#### - telegram-uploader.service                          ####
#### - weather-logger.py                                  ####
#### - weather-logger.service                             ####
#### deben estar en la misma carpeta que este script.     ####
##############################################################

##############################################################
####                Para instalar RustDesk                ####
##############################################################

# Descargar el paquete (versión estable)
wget https://github.com/rustdesk/rustdesk/releases/download/1.4.4/rustdesk-1.4.4-x86_64.deb

# Instalarlo y sus dependencias
sudo apt install ./rustdesk-1.4.4-x86_64.deb -y

sudo rm rustdesk-1.4.4-x86_64.deb -y

##############################################################
####                Para instalar mosquitto               ####
##############################################################

#sudo apt update
sudo apt install -y mosquitto mosquitto-dev mosquitto-clients

#Para comprobar que está funcionando:
#sudo systemctl status mosquitto

#Para iniciarlo (si no está):
#sudo systemctl start mosquitto

##############################################################
####           Ubicación de pymqtt-listener.py            ####
##############################################################

#El archivo pymqtt-listener.py va en /usr/local/bin

if [ -f "installation/pymqtt-listener.py" ]; then
    sudo mv installation/pymqtt-listener.py /usr/local/bin/
    sudo chmod +x /usr/local/bin/pymqtt-listener.py
else
    echo "⚠️  No se encontró pymqtt-listener.py en el directorio"
fi

##############################################################
####              Ubicación de data-send.py               ####
##############################################################

#El archivo data-send.py va en /usr/local/bin

if [ -f "installation/data-send.py" ]; then
    sudo mv installation/data-send.py /usr/local/bin/
    sudo chmod +x /usr/local/bin/data-send.py
else
    echo "⚠️  No se encontró data-send.py en el directorio"
fi

##############################################################
####          Ubicación de telegram-uploader.py           ####
##############################################################

#El archivo telegram-uploader.py va en /usr/local/bin

if [ -f "installation/telegram-uploader.py" ]; then
    sudo mv installation/telegram-uploader.py /usr/local/bin/
    sudo chmod +x /usr/local/bin/telegram-uploader.py
else
    echo "⚠️  No se encontró telegram-uploader.py en el directorio"
fi

##############################################################
####            Ubicación de weather-logger.py            ####
##############################################################

#El archivo weather-logger.py va en /usr/local/bin

if [ -f "installation/weather-logger.py" ]; then
    sudo mv installation/weather-logger.py /usr/local/bin/
    sudo chmod +x /usr/local/bin/weather-logger.py
else
    echo "⚠️  No se encontró weather-logger.py en el directorio"
fi

##############################################################
######################### IMPORTANTE #########################
##############################################################
#### - pymqtt-listener.service: para pymqtt-listener.py  #####
#### - data-send.service: para data-send.py              #####
##############################################################

##############################################################
####        Ubicación de pymqtt-listener.service          ####
##############################################################

#El archivo pymqtt-listener.service va en /etc/systemd/system

if [ -f "installation/pymqtt-listener.service" ]; then
    sudo mv installation/pymqtt-listener.service /etc/systemd/system/
    sudo chmod 777 /etc/systemd/system/pymqtt-listener.service
    sudo systemctl daemon-reload
    sudo systemctl enable pymqtt-listener.service
    sudo systemctl start pymqtt-listener.service
	
	#sudo systemctl status pymqtt-listener.service
else
    echo "⚠️  No se encontró pymqtt-listener.service en el directorio"
fi

##############################################################
####           Ubicación de data-send.service             ####
##############################################################

#El archivo data-send.service va en /etc/systemd/system

if [ -f "installation/data-send.service" ]; then
    sudo mv installation/data-send.service /etc/systemd/system/
    sudo chmod 777 /etc/systemd/system/data-send.service
    sudo systemctl daemon-reload
    sudo systemctl enable data-send.service
    sudo systemctl start data-send.service
	
	#sudo systemctl status data-send.service
else
    echo "⚠️  No se encontró data-send.service en el directorio"
fi

##############################################################
####       Ubicación de telegram-uploader.service         ####
##############################################################

#El archivo telegram-uploader.service va en /etc/systemd/system

if [ -f "installation/telegram-uploader.service" ]; then
    sudo mv installation/telegram-uploader.service /etc/systemd/system/
    sudo chmod 777 /etc/systemd/system/telegram-uploader.service
    sudo systemctl daemon-reload
    sudo systemctl enable telegram-uploader.service
    sudo systemctl start telegram-uploader.service
	
	#sudo systemctl status telegram-uploader.service
else
    echo "⚠️  No se encontró telegram-uploader.service en el directorio"
fi

##############################################################
####         Ubicación de weather-logger.service          ####
##############################################################

#El archivo weather-logger.service va en /etc/systemd/system

if [ -f "installation/weather-logger.service" ]; then
    sudo mv installation/weather-logger.service /etc/systemd/system/
    sudo chmod 777 /etc/systemd/system/weather-logger.service
    sudo systemctl daemon-reload
    sudo systemctl enable weather-logger.service
    sudo systemctl start weather-logger.service
	
	#sudo systemctl status weather-logger.service
else
    echo "⚠️  No se encontró weather-logger.service en el directorio"
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
#sudo apt install -y python3
sudo apt install -y python3-pip

#Para instalar los módulos requeridos:
sudo apt install python3-paho-mqtt -y
sudo apt install python3-requests -y
sudo apt install python3-pandas -y
sudo apt install python3-matplotlib -y
sudo pip3 install keyboard

##############################################################
######################### IMPORTANTE #########################
##############################################################
#### - pymqtt-listener.py: escribe un timestamp en csv   #####
##############################################################

#Se crea el directorio para el csv:
sudo mkdir -p /home/log
sudo chmod 777 /home/log

##############################################################
####                Finaliza la ejecucíon                 ####
##############################################################

echo "##############################################################"
echo "################### Instalación finalizada ###################"
echo "##############################################################"
echo "#### En caso de no haber errores, puede proseguir con la  ####"
echo "#### ejecucion de net.sh y wifi.sh (solo si lo requiere)  ####"
echo "##############################################################"

cd ~/Desktop/ANII/Linux

sudo chmod 777 net.sh
sudo chmod 777 scada.sh

##############################################################