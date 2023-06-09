#!/usr/bin/python3.7
 
# Script creates and copies all necessary files for web display via Leaflet

__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="July 2021"

from set_vog_env import *
from pproc.graphics import*
import logging
import json
import os
import netCDF4 as nc
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors
from scipy.ndimage import gaussian_filter
import datetime as dt

### Functions ###

def make_fcst_json(json_name):
	'''
	Create control json for web display
	'''

	fcstjson = {}
	fcstjson['forecast'] = os.environ['forecast']
	
	#create some vars for easy info display
	fcstdate = dt.datetime.strptime(fcstjson['forecast'],'%Y%m%d%H')
	fcstjson['date'] = dt.datetime.strftime(fcstdate, '%Y-%m-%d')
	fcstjson['cycle'] = fcstjson['forecast'][-2:] + 'Z'

	#copy emissions info for display
	json_data = read_run_json()
	src1 = list(json_data['emissions'].keys())[0]
	fcstjson['emissions'] = str(json_data['emissions'][src1]['so2']) + ' tonnes/day'
	#fcstjson['emissions'] = str(json_data['emissions']['src1']['so2']) + ' tonnes/day'

	#create a tag for the first animation slide
	spinup = int(os.environ['spinup'])
	t0 = fcstdate + dt.timedelta(hours = spinup+1)
	fcstjson['firstoutput'] = dt.datetime.strftime(t0, '%Y%m%d%H') 

	#create time interval for the timedimension slider
	hys_hrs = int(os.environ['runhrs']) - spinup
	start_str = dt.datetime.strftime(t0, '%Y-%m-%dT%H:00:00Z/')
	end = t0 + dt.timedelta(hours = hys_hrs - 1)
	end_str = dt.datetime.strftime(end, '%Y-%m-%dT%H:00:00Z')
	fcstjson['timeInterval'] = start_str + end_str


	#WARNING: this is hardcoded to match the hysplit CONTROL file
	fcstjson['bounds'] = {}
	fcstjson['bounds']['minlat'] = 18.25
	fcstjson['bounds']['maxlat'] = 22.75
	fcstjson['bounds']['minlon'] = -160.5
	fcstjson['bounds']['maxlon'] = -154.5 

	#TODO: add POE thresholds (currently hardcoded on web-server) Low Prioirty

	fcstjson['completion'] = dt.datetime.strftime(dt.datetime.utcnow(), '%Y-%m-%d %H:%M:%S UTC')

	#write out json
	with open(json_name, 'w') as f:
		f.write(json.dumps(fcstjson, indent=4))

	logging.debug('...created {} for web server'.format(json_name))

	return


def main(web_path):
	'''
	Create config files and copy images to webserver
	NOTE: this is heavily hard-coded for MKWC webserver
	'''

	logging.info('Generating and copying web display data')

	#ensure one is in hysplit subdir
	os.chdir(os.environ['hys_rundir'])
	
	#create a config json for Leaflet display
	#TODO currently writes to local "src" folder
	json_name = 'vogfcst.json'
	make_fcst_json(json_name)

	#TODO copy station files to webserver
	stn_file = 'hysplit.haw*.txt' 
	stn_cmd = 'scp {} {}/../../hysplit/text/.'.format(stn_file, web_path)
	logging.debug('...copying station data: {}'.format(stn_cmd))
	os.system(stn_cmd)

	#copy json and pngs to webserver
	json_cmd = 'scp {} {}/json/.'.format(json_name, web_path)
	logging.debug('...copying json: {}'.format(json_cmd))
	os.system(json_cmd)

	con_png_cmd = 'scp SO2_2*.png SO4_2*.png {}/png/con/.'.format(web_path)
	logging.debug('...copying concentration pngs: {}'.format(con_png_cmd))
	os.system(con_png_cmd)

	poe_png_cmd = 'scp *lvl*.png {}/png/poe/.'.format(web_path)
	logging.debug('...copying poe pngs: {}'.format(poe_png_cmd))
	os.system(poe_png_cmd)

	ci_png_cmd = 'scp *ci*.png {}/png/ci/.'.format(web_path)
	logging.debug('...copying ci pngs: {}'.format(ci_png_cmd))
	os.system(ci_png_cmd)

	logging.info('Copy to webserver complete')


 ### Main ###
if __name__ == '__main__':
	main(web_path)		
