#!/bin/bash
# Path to log file
log_file="/var/log/temperature.log"

# Add header to the log file if it doesn't exist
if [ ! -f "$log_file" ]; then
    echo "Date, CPU Temp" > "$log_file"
fi

# Log the temperature every 10 seconds
while true; do
    temperature=$(sensors | grep 'Core 0' | awk '{print $3}')  # Adjust this if>
    echo "$(date '+%Y-%m-%d %H:%M:%S'), $temperature" >> "$log_file"
    sleep 10  # Log every 10 seconds
done
