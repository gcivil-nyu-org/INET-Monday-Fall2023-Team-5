files:
  "/opt/elasticbeanstalk/hooks/appdeploy/post/write_env.sh":
    mode: "000755"
    owner: root
    group: root
    content: |
      #!/bin/bash
      # Save environment variables to a file
      /opt/elasticbeanstalk/bin/get-config environment --output YAML > /opt/elasticbeanstalk/deployment/envvars.yml
