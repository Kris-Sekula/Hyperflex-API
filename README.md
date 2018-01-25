# Hyperflex-API

This is an example of how to use Cisco Hyperflex API. As I was looking after multiple Hyperflex Cluster at Cisco Live 2018 event I wanted to have a single screen where I can track perfromance. I decided to use the "Prometheus" https://prometheus.io/ as backend, Grafana as frontend and a python script that will collect the performance data from the Hyperflex systems. This script crates a local web server on address http://localhost:8082/metrics that will serve the following data: 

MBps_Read{host="10.127.253.81"} 1728.0
MBps_Write{host="10.127.253.81"} 1490454.7
IOPS_Read{host="10.127.253.81"} 0.9
IOPS_Write{host="10.127.253.81"} 42.9
Lat_Read{host="10.127.253.81"} 2.333
Lat_Write{host="10.127.253.81"} 6.261
MBps_Read{host="10.127.254.81"} 2112.0
MBps_Write{host="10.127.254.81"} 520650.4
IOPS_Read{host="10.127.254.81"} 0.9
IOPS_Write{host="10.127.254.81"} 36.6
Lat_Read{host="10.127.254.81"} 1.556
Lat_Write{host="10.127.254.81"} 1.478

Every 1 min Prometheus will call the url and process the data, you can than create custom graphs.
