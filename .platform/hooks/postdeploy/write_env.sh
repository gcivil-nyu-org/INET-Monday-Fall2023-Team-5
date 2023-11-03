#!/bin/bash
# Save environment variables to a file
/opt/elasticbeanstalk/bin/get-config environment --output YAML > /opt/elasticbeanstalk/deployment/envvars.yml
