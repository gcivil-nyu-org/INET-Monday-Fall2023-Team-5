#!/bin/bash
# Save environment variables to a file
/opt/elasticbeanstalk/bin/get-config environment > /opt/elasticbeanstalk/deployment/envvars.json
