#!/bin/bash
LOG_FILE="/var/log/eb-hooks.log"

echo "$(date): Executing write_env.sh" >> "$LOG_FILE"

# Attempt to save environment variables to a file
/opt/elasticbeanstalk/bin/get-config environment > /opt/elasticbeanstalk/deployment/envvars.json

# Check the exit status of the previous command
if [ $? -eq 0 ]; then
    echo "$(date): Successfully wrote environment variables to /opt/elasticbeanstalk/deployment/envvars.json" >> "$LOG_FILE"
else
    echo "$(date): Failed to write environment variables" >> "$LOG_FILE"
fi
