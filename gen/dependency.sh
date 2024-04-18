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
