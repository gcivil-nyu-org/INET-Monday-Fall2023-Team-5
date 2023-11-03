#!/bin/bash
# load_and_run.sh

# Load the environment variables
source /opt/elasticbeanstalk/deployment/envvars.json

# Run the Django management command
cd /var/app/current && /var/app/venv/*/bin/python manage.py reset_likes
