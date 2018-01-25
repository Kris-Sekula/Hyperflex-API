#!/usr/bin/env python2
	
from flask import Flask
from flask import Response
import requests
import json
import hx_creds
import time
from gevent.wsgi import WSGIServer

'''
the hx_creds.py looks like this:

hosts=[{'host':'10.1.1.1', 'username':'local/root', 'password':'*******'},{'host':'10.1.1.2', 'username':'local/root', 'password':'****'}]

'''

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
		# get auth token (either cached or new one)
		authdata = get_auth(host['host'], host['username'], host['password'])
	        
		url = "https://"+host['host']
		# url to get bandwidth data, we only look at the last 5 min (this will bring 5 records)
		uri_MBps = '/render?target=stats.counters.scvmclient.allhosts.nfsBytesRead.cluster.rate&target=stats.counters.scvmclient.allhosts.nfsBytesWritten.cluster.rate&format=json&from=-5min'
		# url to get the IOPS data 
		uri_IOPS = '/render?target=stats.counters.scvmclient.allhosts.nfsReads.cluster.rate&target=stats.counters.scvmclient.allhosts.nfsWrites.cluster.rate&format=json&from=-5min'
		# url to get Latency data
		uri_Lat ='/render?target=divideSeries(stats.timers.scvmclient.allhosts.nfsReadLatency.cluster.total%2Cstats.counters.scvmclient.allhosts.nfsReads.cluster.count)&target=divideSeries(stats.timers.scvmclient.allhosts.nfsWriteLatency.cluster.total%2Cstats.counters.scvmclient.allhosts.nfsWrites.cluster.count)&format=json&from=-5min'
		# get data
		MBps_data = get_stats(authdata,url+uri_MBps)
		IOPS_data = get_stats(authdata,url+uri_IOPS)
		Lat_data  = get_stats(authdata,url+uri_Lat)
		# extract data [-2] as we are taking one before last record, sometime last in "None" so I skip it	
		MBps_Read=round(MBps_data[0]['datapoints'][-2][0],3)
        	MBps_Write=round(MBps_data[1]['datapoints'][-2][0],3)
	
		IOPS_Read=round(IOPS_data[0]['datapoints'][-2][0],3)
        	IOPS_Write=round(IOPS_data[1]['datapoints'][-2][0],3)
		
		Lat_Read=round(Lat_data[0]['datapoints'][-2][0],3)
		Lat_Write=round(Lat_data[1]['datapoints'][-2][0],3)
		
		# build the results
		results += 'MBps_Read{host="%s"} %s\n'%(host['host'],str(MBps_Read))
		results += 'MBps_Write{host="%s"} %s\n'%(host['host'],str(MBps_Write))
		
		results += 'IOPS_Read{host="%s"} %s\n'%(host['host'],str(IOPS_Read))
		results += 'IOPS_Write{host="%s"} %s\n'%(host['host'],str(IOPS_Write))
		
		results += 'Lat_Read{host="%s"} %s\n'%(host['host'],str(Lat_Read))
                results += 'Lat_Write{host="%s"} %s\n'%(host['host'],str(Lat_Write))
	# return the results to the caller
	return Response(results, mimetype='text/plain')


def get_auth(host, username, password):
	print "call get_auth"	
	global tokens

	headers={'content-type':'application/json'}
	payload = {
		"username": username,
		"password": password,
		"client_id": "HxGuiClient",
		"client_secret": "Sunnyvale",
		"redirect_uri": "http://"+host
	}

	url = 'https://%s/aaa/v1/auth?grant_type=password'%host

	if tokens.get(host):
                # looks like we have token cached already
		# let's check if it's valid
		
		payload = {
			"access_token": tokens.get(host)['access_token'],
			"scope": "READ",
			"token_type": tokens.get(host)['token_type']
		}
		try:
			#validating token
                	url = 'https://%s/aaa/v1/validate'%host
			response = requests.post(url,headers=headers,data=json.dumps(payload),verify=False,timeout=4)
			if response.status_code == 200:
				print "Re-using token"
                                return tokens.get(host)
                	print "failed to validate"        	
		except Exception as e:
			print "failed to post validate",e	
	# this happens if no cached taken found
	
	payload = {
                "username": username,
                "password": password,
                "client_id": "HxGuiClient",
                "client_secret": "Sunnyvale",
                "redirect_uri": "http://"+host
        }

	try:
		response = requests.post(url,headers=headers,data=json.dumps(payload),verify=False,timeout=4)
		if response.status_code == 201:
			if  response.json().get('access_token'):
				tokens[host]=response.json()
				return response.json()
		print response.content
	except:
		print "failed to post get new token"
		return None

def get_stats(authdata, url):
	print "call get_stats"
	try:
		headers = {'Authorization': authdata['token_type'] + ' ' + authdata['access_token'],'Connection':'close'}
                response = requests.get(url,headers=headers,verify=False,timeout=4)
		if response.status_code == 200:
			return response.json()
        	print response.content
	except:
                return None

def date_txt(epoch):
	return  time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(epoch))
	
if __name__ == '__main__':
	#app.run(host='0.0.0.0', port=8082, threaded=True)
	http_server = WSGIServer(('10.100.253.13', 8082), app)
	http_server.serve_forever()
