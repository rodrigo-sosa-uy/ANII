##############################################################
####                Para configurar la red                ####
##############################################################

#sudo apt-get update -y
sudo apt install network-manager -y

sudo nmcli con mod "UTEC-Invitados" ipv4.method manual ipv4.addresses 192.168.101.250/24 ipv4.gateway 192.168.101.1 ipv4.dns 8.8.8.8
sudo nmcli connection down "UTEC-Invitados" && sudo nmcli connection up "UTEC-Invitados"

sudo nmcli