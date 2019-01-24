# Hyperflex-API

This is an example of how to use the Cisco Hyperflex API with python. I've been tasked with deploying multiple Hyperflex Clusters at Cisco Live 2018 in Barcelona. As part of that deployment, I wanted to have a way to monitor the performance of the system. The Hyperflex system has a built performance "screen" that can be accessed via the http://hx-controller_ip/perf link but I wanted to have both of my system's data presented on one screen. 

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

Here is an example of those the graphs look like:

![alt text](https://github.com/Kris-Sekula/Hyperflex-API/blob/master/cl2018-stats-example.png "Graphana Dashboard")

## How to deploy (as of January 2019).

1. Install ubuntu server 16.04 64bit (I used: ubuntu-16.04.5-server-amd64.iso)
    * Basic installation, only select OpenSSH from the package list, create a user.
2. Install Prometheus:
   * create the required user:
   ```
   sudo useradd -M -s /bin/fals prometheus
   ```
   * create the required folders:
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
   * copy files and change permissions:
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
   **Note:** watch out for formatting this is YAML, no TABs allowed, use two spaces instead. The second 'localhost' below      tells prometheus to make a call to http://localhost:8082/hx_metrics and fetch the data every one minute, the url is served by the python script running on the prometheus server.

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
   * verify if it works:
   
   http://localhost:9090/status

   * if all good stop it:
   
   CTRL+C
	
   * create prometheus service:
   ```
   sudo vim /etc/systemd/system/prometheus.service
   ```
   The file should look like this:
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
   * check if Prometheus is running, check the service status.
   ```
   sudo systemctl status prometheus
   ```
   * enable service:
   ```
	sudo systemctl enable prometheus
   ```
3. Install Grafana
   * Add grafana sources to apt
   ```
   sudo vim /etc/apt/sources.list.d/grafana.list
   ```
   ```
   deb https://packages.grafana.com/oss/deb stable main
   ```
   * Add apt key:
   ```
   curl https://packages.grafana.com/gpg.key | sudo apt-key add -
   ```
   * update apt:
   ```
   sudo apt-get update
   ```
   * Verify what is the install candidate:
   ```
   apt-cache policy grafana
   ```
   * Install grafana:
   ```
   sudo apt-get install grafana
   ```
   * Configure grafana to start automatically using systemd
   ```
   sudo /bin/systemctl daemon-reload
   sudo /bin/systemctl enable grafana-server
   ```
   * Start grafana-server by executing
   ```
   sudo /bin/systemctl start grafana-server
   ```
   * Verify if it's running:
   ```
   sudo systemctl status grafana-server
   ```
   * Login to gui via:
   
   `http://<ip>:3000/login` (use your `<ip>`, default port is 3000, username: admin password: admin)

   * Add prometheus as a source:
   
   Got to source and select, prometheus, http://localhost:9090, hit save and test
   
   * import dashboard from file :
   
   use the provided HX-monitor-Grafana_normal.json file that has a preconfigured dashboard
   you will need to open this file first and replace the ip addresses that I've been using
   with our addresses. Once done save and use it to import new dashboard into Grafana.

4. Install the script:
   * Clone the repositry locally.
   ```
   git clone https://github.com/Kris-Sekula/Hyperflex-API.git'
   ```
   * Create credentials file:
   ```
   vi hx_creds.py
   ```
   This is how the file should look like:
   ```
   hosts=[{'host':'ip_HX_Cluster_1', 'username':'local/root', 'password':'password_HX1'},{'host':'ip_HX_Cluster2', 'username':'local/root', 'password':'password_HX2'}]
   ```
   * run the script:
   ```
   python hx_metrics.py
   ```
   * Logs are created in the same directory, you can watch them to see if prometheus is calling the script every 1 minute.
   
   * If you don't see the graphs updating, verify you changed the ip addresses, passwords etc to match, also fetch the data manually and see if it gets served by opening the url in your browser, replace the "localhost" with ip address of the server that is hosting your script/grafana/prometheus:
   ```
   http://localhost:8082/hx_metrics
   ```
   
   **NOTE** This instruction is for testing purposes only, no attempt to make it "secure" has been made, use at your own risk.


Keywords: Cisco Hyperflex, API, python.
