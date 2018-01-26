# Hyperflex-API

This is an example of how to use Cisco Hyperflex API with python. I've been tasked with deploying multiple Hyperflex Cluster at Cisco Live 2018 in Barcelona. As part of that deployment I wanted to have a way to monitor performace of the system. The Hyperflex system has a built performace "screen" that can be accessed via the http://<ip>/perf link but I wanted to have both of my systems data presented on one scree. 

I decided to use the "Prometheus" https://prometheus.io/ as backend, Grafana as frontend and a python script to bring the data from the HX system to Prometheus. This script crates a local web server on address http://localhost:8082/metrics that will serve the following data: 

MBps_Read{host="10.127.253.81"} 1728.0 
MBps_Write{host="10.127.253.81"} 1490454.7 
IOPS_Read{host="10.127.253.81"} 0.9 
IOPS_Write{host="10.127.253.81"} 42.9 
Lat_Read{host="10.127.253.81"} 2.333 
Lat_Write{host="10.127.253.81"} 6.261

Every 1 min Prometheus calls the url and processes the data.

Keywords: Cisco Hyperflex, API, python.
