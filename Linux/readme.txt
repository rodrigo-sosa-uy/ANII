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
#### Se debe utilizar solamente una de las alternativas: #####
#### - mqtt-listener.sh: escribe directamente en log     #####
#### - pymqtt-listener.py: escribe un timestamp en csv   #####
##############################################################

##############################################################
####            Ubicación de mqtt-listener.sh             ####
##############################################################

El archivo mqtt-listener.sh va en /usr/local/bin

sudo mv mqtt-listener.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/mqtt-listener.sh

##############################################################
####           Ubicación de pymqtt-listener.py            ####
##############################################################

El archivo pymqtt-listener.py va en /usr/local/bin

sudo mv pymqtt-listener.py /usr/local/bin/
sudo chmod +x /usr/local/bin/pymqtt-listener.py

##############################################################
######################### IMPORTANTE #########################
##############################################################
#### Se debe utilizar solamente una de las alternativas: #####
#### - mqtt-listener.service: para mqtt-listener.sh      #####
#### - pymqtt-listener.service: para pymqtt-listener.py  #####
##############################################################

##############################################################
####         Ubicación de mqtt-listener.service           ####
##############################################################

El archivo mqtt-listener.service va en /etc/systemd/system

sudo chmod 777 /etc/systemd/system/mqtt-listener.service

sudo systemctl daemon-reload
sudo systemctl enable mqtt-listener.service
sudo systemctl start mqtt-listener.service

sudo systemctl status mqtt-listener.service

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
pip install paho-mqtt datetime

##############################################################
####             Se crea directorio de log                ####
##############################################################

sudo mkdir -p /home/log
sudo chmod 777 /home/log

##############################################################
####              Ubicación de archivo log                ####
##############################################################

El servicio escribe en el archivo:
/home/log/temperature.log

Si se quiere cambiar archivo de registro:
	Cambiar en mqtt-listener.sh

##############################################################
####              Ubicación de archivo csv                ####
##############################################################

El servicio escribe en el archivo:
/home/log/temperature.csv

Si se quiere cambiar archivo de registro:
	Cambiar en pymqtt-listener.py

##############################################################