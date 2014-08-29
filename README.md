nhm-dataportal-monitor
======================

Overview
--------

This repository contain the monitoring daemon used for monitoring the Natural History Museum dataportal servers. The daemon reports to a [Graphite](http://graphite.wikidot.com/) server. This repository also contains a [Docker](https://www.docker.com/) file used to build the Graphite server with a [Grafana](http://grafana.org/) frontend. 

The monitoring daemon will report to the Graphite server:

- 1 minute CPU load average;
- Memory available and used;
- Swap space available and used;
- Number of http requests;
- Number of cache hits;
- Number of bytes sent;
- Time spent for http requests; 
- Time spent for non-cached http generation.

Load, memory, swap and time are averaged over each second, while requests and cache hits are summed over each second - so there is no need to use carbon-aggregator (though you can if you want to do further aggregations).

The monitor expects that the server is runing an nginx proxy cache, with the following log format:

```
    log_format timed_combined '$remote_addr - $remote_user [$time_iso8601] '
                              '"$request" $status $body_bytes_sent '
                              '"$http_referer" "$http_user_agent" '
                              '$request_time $upstream_response_time';
```

The monitoring process will not catch up on missed log entries if is switched off. It will continue working, and recover, if the graphite server or the monitored log files are temporarilly unavailable.

The Grafana front end includes a default dashboard to monitor all servers. There is no backend to save additional dashboards, but those can be exported as JSON files.

Usage
-----

To run the monitor:
- Install via pip: ```pip install git+https://NaturalHistoryMuseum/dataportal_monitor.git#egg=dataportal_monitor```
- Create a config file in `/etc/dataportal_monitor/config.ini` (the default location) or elsewehre;
- Run `dataportal_monitor`. If the config file is not at the default location, pass it as first parameter.

To run the Graphite server:
- Install docker;
- Clone the repository, and go into the graphite subfolder;
- Run `build.sh` (once)
- Run `run.sh`.

The database data is stored in `/var/lib/dataportal_monitor`. To change this path edit `build.sh` and `run.sh`. If you want a terminal in the server, run the docker run command add add `/bin/bash` at the end. You can then start the services by running `/usr/bin/supervisord`.

Configuration
-------------

Configuration for the monitoring daemon. This is expected to be in /etc/dataportal_monitor/config.ini by default:

```
[main]
# Set this to true to run dataportal_monitor in daemon mode
daemon = true

# Metrics path prefix. All metrics sent to Graphite are prefixed with this string. Typically this would the server name.
path_prefix = server 

# Graphite server host name
graphite = 127.0.0.1

# Graphite server port for the plain text API
port = 2003

# Define how often (in seconds) to send updates to the Graphite server. Approximate.
update_period = 5

# Path to the NGINX log file
nginx_log = /var/log/nginx/access.log

# Log file path
log_file = /var/log/dataportal_monitor/dp.log

# Log level. debug, info or error.
log_level = info 
```
