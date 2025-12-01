sudo mv wifi-keeper.service /etc/systemd/system/
sudo chmod 777 /etc/systemd/system/wifi-keeper.service
sudo mv wifi-keeper.py /usr/local/bin
sudo chmod 777 /usr/local/bin/wifi-keeper.py
sudo systemctl daemon-reload
sudo systemctl enable wifi-keeper.service
sudo systemctl start wifi-keeper.service