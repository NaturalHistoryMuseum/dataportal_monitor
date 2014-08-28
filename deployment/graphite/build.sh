#!/bin/bash
if [ ! -d /var/lib/dataportal_monitor/data ]; then
    mkdir -p /var/lib/dataportal_monitor/data
    chown -R www-data:www-data /var/lib/dataportal_monitor/data
fi
docker build -t nhmd/dpgraf .
