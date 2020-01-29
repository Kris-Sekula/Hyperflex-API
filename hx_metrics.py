#!/usr/bin/env python2
# ver 1.2 CL2020

from flask import Flask
from flask import Response
import requests
from requests.auth import HTTPBasicAuth
import json
import time
from gevent.wsgi import WSGIServer
#
import logging
import logging.handlers
#
import hx_creds

'''
the hx_creds.py looks like this:

hosts=[{'host':'10.1.1.1', 'username':'local/root', 'password':'*******'},{'host':'10.1.1.2', 'username':'local/root', 'password':'****'}]


'''
#
server_IP ='10.100.252.13'
server_port = '8082'

# Logging config
logFile="hx_stats_%s_%s.log"%(server_IP,server_port)
logCount=4
logBytes=1048576

# suppress the unverified request messages (when using self-signed certificates)
requests.packages.urllib3.disable_warnings()

# cache the credentials, if you keep requesting this you will hit th 256 open session/user limit
tokens = {}

app = Flask('HX Stats')

# gets called via the http://your_server_ip:port/metrics
@app.route('/metrics')
def get_stats():
	results =''
	for host in hx_creds.hosts:
		logger.info("----------- Processing Host: %s -----------"%host['host'])
		url = "https://"+host['host']
                # uri for throughput data with "last 5 min" filter
		uri_MBps = '/stats?target=stats.counters.scvmclient.allhosts.nfsBytesRead.cluster.rate&target=stats.counters.scvmclient.allhosts.nfsBytesWritten.cluster.rate&format=json&from=-5min'
		# Get throughput data
		MBps_data = get_stats(host['username'],host['password'],url+uri_MBps)
		if MBps_data:
			try:
				MBps_Read=round(MBps_data[0]['datapoints'][-2][0],3)
                		MBps_Write=round(MBps_data[1]['datapoints'][-2][0],3)
				logger.info("Got MBps info")

				# build the results
                		results += 'MBps_Read{host="%s"} %s\n'%(host['host'],str(MBps_Read))
                		results += 'MBps_Write{host="%s"} %s\n'%(host['host'],str(MBps_Write))

			except Exception as e:
				logger.error(e)
				logger.error("Couldn't parse returned throughput data")
				pass

		# url to get the IOPS data
                uri_IOPS = '/stats?target=stats.counters.scvmclient.allhosts.nfsReads.cluster.rate&target=stats.counters.scvmclient.allhosts.nfsWrites.cluster.rate&format=json&from=-5min'
		# get IOPS data
		IOPS_data = get_stats(host['username'],host['password'],url+uri_IOPS)
		if IOPS_data:
			try:
				IOPS_Read=round(IOPS_data[0]['datapoints'][-2][0],3)
                		IOPS_Write=round(IOPS_data[1]['datapoints'][-2][0],3)
				logger.info("Got IOPS info")

				# build the results
 				results += 'IOPS_Read{host="%s"} %s\n'%(host['host'],str(IOPS_Read))
                		results += 'IOPS_Write{host="%s"} %s\n'%(host['host'],str(IOPS_Write))
			
			except Exception as e:
				logger.error(e)
				logger.error("Couldn't parse returned IOPS data")
                                pass

		# url to get Latency data
		uri_Lat ='/stats?target=divideSeries(stats.timers.scvmclient.allhosts.nfsReadLatency.cluster.total%2Cstats.counters.scvmclient.allhosts.nfsReads.cluster.count)&target=divideSeries(stats.timers.scvmclient.allhosts.nfsWriteLatency.cluster.total%2Cstats.counters.scvmclient.allhosts.nfsWrites.cluster.count)&format=json&from=-5min'

		# get latency data
		Lat_data  = get_stats(host['username'],host['password'],url+uri_Lat)
		if Lat_data:
			try:
				Lat_Read=round(Lat_data[0]['datapoints'][-2][0],3)
                		Lat_Write=round(Lat_data[1]['datapoints'][-2][0],3)
				logger.info("Got Latency info")
	
				# build the results
				results += 'Lat_Read{host="%s"} %s\n'%(host['host'],str(Lat_Read))
                		results += 'Lat_Write{host="%s"} %s\n'%(host['host'],str(Lat_Write))

			except Exception as e:
				logger.error(e)
				logger.error("Couldn't parse returned latency data")
                                pass
		#
		#  When processing data I'm taking one before last record ([-2]), as sometimes the last record is None
		#
	# return the results to the caller
		logger.info("----------- Finished -----------")
	return Response(results, mimetype='text/plain')

#
# calls HX API
#
def get_stats(username, password, url):
	logger.info("call for get_stats")
	try:
		headers = {'Connection':'close'}
		
		#logger.info("username: %s"%username)
		#logger.info("pass: %s"%password)
		#logger.info("url: %s"%url)
		#logger.info("headers: %s"%headers)

		response = requests.get(url, auth=HTTPBasicAuth('admin',password), headers=headers, verify=False,timeout=4)
	
		#logger.info("status code:%s"%str(response.status_code))

		if response.status_code == 200:
			logger.info("Got data ok")
			return response.json()
		logger.error("Failed to get data "+response.content)
		return None

	except Exception as e:
                logger.error("Post for data failed \n"+str(e))
                return None

if __name__ == '__main__':
	print "Service Started"
	# Enable logging
	logger = logging.getLogger("HX-Stats")
    	logger.setLevel(logging.DEBUG)
    	handler = logging.handlers.RotatingFileHandler(logFile, maxBytes=logBytes, backupCount=logCount)
    	formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    	handler.setFormatter(formatter)
    	logger.addHandler(handler)
	logger.info("-"*25)
    	logger.info("HX Stats script started")

	http_server = WSGIServer((server_IP, int(server_port)), app, log = logger)
	http_server.serve_forever()
