#!/bin/bash

app="votes"
docker build -t ${app} .
docker stop ${app}
docker rm ${app}
docker run -d -p 8080:80 \
  --name=${app} ${app}
docker logs -f ${app}