mkdir /home/scada
mkdir /home/scada/templates

sudo pip3 install flask flask-socketio eventlet

##############################################################
####                 Ubicación de app.py                  ####
##############################################################

#El archivo app.py va en /home/scada

if [ -f "scada/app.py" ]; then
    sudo mv scada/app.py /home/scada
    sudo chmod +x /home/scada/app.py
else
    echo "⚠️  No se encontró app.py en el directorio"
fi

##############################################################
####               Ubicación de index.html                ####
##############################################################

#El archivo index.html va en /home/scada/templates

if [ -f "scada/index.html" ]; then
    sudo mv scada/index.html /home/scada/templates
    sudo chmod +x /home/scada/templates/index.html
else
    echo "⚠️  No se encontró index.html en el directorio"
fi