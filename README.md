# Hyperflex-API

This is an example of how to use Cisco Hyperflex API with python. I've been tasked with deploying multiple Hyperflex Clusters at Cisco Live 2018 in Barcelona. As part of that deployment I wanted to have a way to monitor performace of the system. The Hyperflex system has a built performace "screen" that can be accessed via the http://hx-controller/perf link but I wanted to have both of my systems data presented on one screen. 

I decided to use the "Prometheus" https://prometheus.io/ as backend, Grafana as frontend and a python script to bring the data from the HX systems to Prometheus. This script crates a local web server on address http://localhost:8082/metrics that will serve the data that looks like this: 
```
MBps_Read{host="10.127.253.81"} 1728.0 
MBps_Write{host="10.127.253.81"} 1490454.7 
IOPS_Read{host="10.127.253.81"} 0.9 
IOPS_Write{host="10.127.253.81"} 42.9 
Lat_Read{host="10.127.253.81"} 2.333 
Lat_Write{host="10.127.253.81"} 6.261
```
Every 1 min Prometheus calls the url and processes the data.

Here is an example of thos the graphs look like:

![alt text](https://github.com/Kris-Sekula/Hyperflex-API/blob/master/cl2018-stats-example.png "Graphana Dashboard")

## How to deploy.

1. Install ubuntu server 16.04 64bit (I used: ubuntu-16.04.5-server-amd64.iso):
   * Basic installation, only select OpenSSH from the package list, create a user.
2. Install Prometheus:
   * create required user:
```
   sudo useradd -M -s /bin/fals prometheus
```
   * create required folders:
```
   sudo mkdir /etc/prometheus
   sudo mkdir /var/lib/prometheus
   sudo chown prometheus:prometheus /etc/prometheus
   sudo chown prometheus:prometheus /var/lib/prometheus
```
   * download and extract:
```
   curl -LO https://github.com/prometheus/prometheus/releases/download/v2.6.1/prometheus-2.6.1.linux-amd64.tar.gz
   tar xvf prometheus-2.6.1.linux-amd64.tar.gz
```
   * copy files and change premissions:
```
   sudo cp prometheus-2.6.1.linux-amd64/prometheus /usr/local/bin/
   sudo cp prometheus-2.6.1.linux-amd64/promtool /usr/local/bin/
   sudo chown prometheus:prometheus /usr/local/bin/prometheus
   sudo chown prometheus:prometheus /usr/local/bin/promtool
   sudo cp -r prometheus-2.6.1.linux-amd64/consoles /etc/prometheus
   sudo cp -r prometheus-2.6.1.linux-amd64/console_libraries /etc/prometheus
   sudo chown -R prometheus:prometheus /etc/prometheus/consoles
   sudo chown -R prometheus:prometheus /etc/prometheus/console_libraries
```
   * configure prometheus:
```
   sudo vim /etc/prometheus/prometheus.yml
```
   **Note:** watch out for formatting this is YAML, no TABs allowed, use two spaces instead.

```yaml
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'prometheus'
    scrape_interval: 5s
    static_configs:
      - targets: ['localhost:9090']
  - job_name: 'hx_metrics'
    scrape_interval: 1m
    static_configs:
      - targets: ['localhost:8082']
        labels:
          service_name: hx_read_write_stats
```
   * try to start prometheus:
```
   sudo -u prometheus /usr/local/bin/prometheus --config.file /etc/prometheus/prometheus.yml --storage.tsdb.path /var/lib/prometheus --web.console.templates=/etc/prometheus/consoles --web.console.libraries=/etc/prometheus/console_libraries
```
   * verfiy if it works:
   
   http://localhost:9090/status

   * if all good stop it:
   
   CTRL+C
	
   * create prometheus service:
```
   sudo vim /etc/systemd/system/prometheus.service
```
   File should looks like this:
```
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \
	--config.file /etc/prometheus/prometheus.yml \
	--storage.tsdb.path /var/lib/prometheus \
	--web.console.templates=/etc/prometheus/consoles \
	--web.console.libraries=/etc/prometheus/console_libraries
[Install]
WantedBy=multi-user.target
```
   * reload services:
```
   sudo systemctl daemon-reload
```
   * start Prometheus using the following command:
```
   sudo systemctl start prometheus
```
   * check if Prometheus is running, check the service.s status.
```
   sudo systemctl status prometheus
```
   * enable service:
```
	sudo systemctl enable prometheus
```


Keywords: Cisco Hyperflex, API, python.
