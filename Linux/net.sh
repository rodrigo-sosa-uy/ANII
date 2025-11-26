##############################################################
####                Para configurar la red                ####
##############################################################

#sudo apt-get update -y
sudo apt install network-manager

sudo nmcli con mod "Wired connection 1" ipv4.method manual ipv4.addresses 192.168.101.250/24 ipv4.dns 8.8.8.8
sudo nmcli connection down "Wired connection 1" && sudo nmcli connection up "Wired connection 1"

sudo nmcli