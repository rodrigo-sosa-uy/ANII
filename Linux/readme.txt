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
####    Ejecutar solamente después de haber realizado     ####
####  la instalación, sea manualmente o automáticamente   ####
##############################################################
####                 Para configurar la red               ####
##############################################################

- Asegurese de que el dispositivo está conectado a la red

Abrir terminal en esa carpeta y ejecutar:
sudo chmod 777 net.sh
sudo bash net.sh

Este script debe asignar una IP estática al dispositivo.
La IP definida es: 192.168.101.250/24

Se recomienda reiniciar el dispositivo y corroborar que tiene
la IP correcta:

sudo nmcli