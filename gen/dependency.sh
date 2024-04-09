#!/bin/bash

sudo apt install -y npm nodejs python3-pip 

root_dir=$(pwd)
cd GL
npm install express ejs

cd -
pip3 install -r requirements.txt
echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
source ~/.bashrc
echo '~/.local/bin ADDED TO YOUR EXECUTABLE PATH'
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 5500 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 7860 -j ACCEPT
sudo ufw allow 7860/tcp
sudo ufw allow 5500/tcp
sudo ufw allow 5000/tcp
