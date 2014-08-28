# DOCKER-VERSION 0.4.0

from	ubuntu:12.04
run	echo 'deb http://us.archive.ubuntu.com/ubuntu/ precise universe' >> /etc/apt/sources.list
run	apt-get -y update

# Install pre-requisites 
run	apt-get -y install python-ldap python-cairo python-django python-twisted python-django-tagging python-simplejson python-memcache python-pysqlite2 python-support python-pip gunicorn supervisor nginx-light wget

# Install whisper, carbon & graphisste-web
run	pip install whisper
run	pip install --install-option="--prefix=/var/lib/graphite" --install-option="--install-lib=/var/lib/graphite/lib" carbon
run	pip install --install-option="--prefix=/var/lib/graphite" --install-option="--install-lib=/var/lib/graphite/webapp" graphite-web

# Install Grafana
run     mkdir -p /src/grafana && cd /src/grafana &&\
        wget http://grafanarel.s3.amazonaws.com/grafana-1.6.1.tar.gz &&\
        tar xzvf grafana-1.6.1.tar.gz --strip-components=1 && rm grafana-1.6.1.tar.gz

# Configure whiser, carbon and graphite-web 
add	./initial_data.json /var/lib/graphite/webapp/graphite/initial_data.json
add	./local_settings.py /var/lib/graphite/webapp/graphite/local_settings.py
add	./carbon.conf /var/lib/graphite/conf/carbon.conf
add	./storage-schemas.conf /var/lib/graphite/conf/storage-schemas.conf
run	mkdir -p /var/lib/graphite/storage/whisper
run	touch /var/lib/graphite/storage/graphite.db /var/lib/graphite/storage/index
run	chown -R www-data /var/lib/graphite/storage
run	chmod 0775 /var/lib/graphite/storage /var/lib/graphite/storage/whisper
run	chmod 0664 /var/lib/graphite/storage/graphite.db
run	cd /var/lib/graphite/webapp/graphite && python manage.py syncdb --noinput

# Configure graphana
add	./grafana_config.js /src/grafana/config.js
add     ./dashboard.json /src/grafana/app/dashboards/default.json

# Configure nginx and supervisord 
add	./nginx.conf /etc/nginx/nginx.conf
add	./supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Nginx
expose	:80
# Carbon line receiver port
expose	:2003
# Carbon pickle receiver port
expose	:2004
# Carbon cache query port
expose	:7002

cmd	["/usr/bin/supervisord"]

# vim:ts=8:noet:
