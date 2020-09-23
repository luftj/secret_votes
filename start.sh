#!/bin/bash

app="votes"
docker build -t ${app} .
docker stop ${app}
docker rm ${app}
docker run -d -p 8080:80 \
  -e SMTP_HOST='192.168.178.20' \
  -e SMTP_PORT='1026' \
  -e SMTP_FROM='vote@test.com' \
  -e URL_DATAPOLICY='https://masovia.de/datenschutzerklaerung/' \
  -e URL_IMPRINT='https://masovia.de/impressum/' \
  --name=${app} ${app}
docker logs -f ${app}