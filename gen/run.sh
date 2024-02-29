#!/bin/bash

root_dir=$(pwd)
# Start the first script in the background
cd src/img_generation
python3 script.py &
PID_SCRIPT=$!


# Start the second script in the background
python3 server.py &
PID_SERVER=$!

# run express server 
cd $root_dir
cd GL
node server.js &
PID_SERVER_JS=$!

# Function to kill both processes
cleanup() {
    echo "Stopping both scripts..."
    kill $PID_SCRIPT
    kill $PID_SERVER
	kill $PID_SERVER_JS
    exit
}

# Wait for the user to press 'q' then clean up
echo "Press 'q' to stop both scripts."
while : ; do
    read -n 1 k <&1
    if [[ $k = q ]] ; then
        cleanup
    fi
done

# or it can be turned off by running the script kill.sh
# Path: kill.sh
