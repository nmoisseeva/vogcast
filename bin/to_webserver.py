#!/usr/bin/python3.7
 
# Script creates and copies all necessary files for web display via Leaflet

__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="July 2021"

from set_vog_env import *
from graphics import*
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
	

	#create a tag for the first animation slide
	spinup = int(os.environ['spinup'])
	t0 = dt.datetime.strptime(fcstjson['forecast'],'%Y%M%d%H') + dt.timedelta(hours = spinup)
	fcstjson['firstouput'] = dt.datetime.strftime(t0, '%Y%M%d%H') 

	#create time interval for the timedimension slider
	runhrs = int(os.environ['runhrs'])
	start_str = dt.datetime.strftime(t0, '%Y-%M-%dT%H/')
	end = t0 + dt.timedelta(hours = runhrs)
	end_str = dt.datetime.strftime(end, '%Y-%M-%dT%H')
	fcstjson['timeInterval'] = start_str + end_str


	#WARNING: this is hardcoded to match the hysplit CONTROL file
	fcstjson['bounds'] = {}
	fcstjson['bounds']['minlat'] = 18
	fcstjson['bounds']['maxlat'] = 23
	fcstjson['bounds']['minlon'] = -160.5
	fcstjson['bounds']['maxlon'] = -154.5 

	#TODO: add POE thresholds

	#write out json
	with open(json_name, 'w') as f:
		f.write(json.dumps(fcstjson, indent=4))

	return


def main(web_path):
	'''
	Create config files and copy images to webserver
	NOTE: this is heavily hard-coded for MKWC webserver
	'''

	logging.info('Generating and copying web display data')

	#create a config json for Leaflet display
	json_name = 'vogfcst.json'
	make_forecast_json(json_name)

	#copy json and pngs to webserver
	json_cmd = 'scp {} {}/json/.'.format(json_name, web_path)
	os.system(json_cmd)
	logging.debug('...copying json: {}'.format(json_cmd))

	png_cmd = 'scp *.png {}/png/.'.format(web_path)
	os.system(png_cmd)
	logging.debug('...copying pngs: {}'.format(png_cmd))


	logging.info('Copy to webserver complete')


 ### Main ###
if __name__ == '__main__':
	main(web_path)		
