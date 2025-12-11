mkdir /home/scada
mkdir /home/scada/templates
mkdir /home/scada/static

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

##############################################################
####             Ubicación de scada.service               ####
##############################################################

#El archivo scada.service va en /etc/systemd/system

if [ -f "scada/scada.service" ]; then
    sudo mv scada/scada.service /etc/systemd/system/
    sudo chmod 777 /etc/systemd/system/scada.service
    sudo systemctl daemon-reload
    sudo systemctl enable scada.service
    sudo systemctl start scada.service
	
	#sudo systemctl status scada.service
else
    echo "⚠️  No se encontró scada.service en el directorio"
fi

sudo mv scada/utec.png /home/scada/static
sudo mv scada/anii.png /home/scada/static
sudo mv scada/meca.png /home/scada/static

sudo mkdir -p --mode=0755 /usr/share/keyrings
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null

echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared jammy main' | sudo tee /etc/apt/sources.list.d/cloudflared.list

sudo apt-get update
sudo apt-get install cloudflared -y

##############################################################
####          Ubicación de cloudflare.service             ####
##############################################################

#El archivo cloudflare.service va en /etc/systemd/system

if [ -f "scada/cloudflare.service" ]; then
    sudo mv scada/cloudflare.service /etc/systemd/system/
    sudo chmod 777 /etc/systemd/system/cloudflare.service
    sudo systemctl daemon-reload
    sudo systemctl enable cloudflare.service
    sudo systemctl start cloudflare.service
	
	#sudo systemctl status cloudflare.service
else
    echo "⚠️  No se encontró cloudflare.service en el directorio"
fi

grep "trycloudflare.com" /var/log/scada-tunnel.log | tail -n 1