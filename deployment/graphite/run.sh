#!/bin/bash

docker kill nhm-dp-graf
docker rm nhm-dp-graf

docker run -v /var/lib/dataportal_monitor/data:/var/lib/graphite/storage/whisper -v /var/lib/dataportal_monitor/grafana:/src/grafana -p 80:80 -p 81:81 -p 2003:2003 -p 2004:2004 -p 7002:7002 --name=nhm-dp-graf nhmd/dpgraf
