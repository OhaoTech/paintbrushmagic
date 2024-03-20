#!/bin/bash

pkill -f ./src/img_generation/script.py
pkill -f ./src/img_generation/server.py
pkill -f ./GL/server.js
echo "All processes killed"
