#!/bin/bash

sudo apt install npm nodejs python3-pip 

root_dir=$(pwd)
cd GL
npm install express

cd -
pip3 install -r requirements.txt

sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 5500 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 7860 -j ACCEPT
sudo ufw allow 7860/tcp
sudo ufw allow 5500/tcp
sudo ufw allow 5000/tcp
