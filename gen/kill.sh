#!/bin/bash

# Function to kill process listening on a given port
kill_process_on_port() {
  local port=$1
  echo "Attempting to kill process listening on port $port..."
  # Find the process using the port
  local pid=$(sudo lsof -t -i:$port)

  # If a process was found, kill it
  if [ -n "$pid" ]; then
    echo "Killing process with PID $pid on port $port..."
    sudo kill -9 $pid
    echo "Process killed."
  else
    echo "No process found listening on port $port."
  fi
}

# Ports to kill processes on
ports=(7860 5000 5500)

# Iterate over the ports and kill the processes
for port in "${ports[@]}"; do
  kill_process_on_port $port
done

echo "All specified ports have been processed."
