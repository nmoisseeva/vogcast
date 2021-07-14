#!/usr/bin/python3.7
 
#Script extacts profile data from wrf meteorology and parameterizes vertical distribution of emissions

__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="July 2021"

import os
import logging
import wrf
from import set_vog_env import *
import glob

 ### Fucntions ###
def locate_source():
        '''
        Get source location met grid
        '''
	#locate the most high-resolution domain
	wrf_rundir = os.path.join(os.environ['run_path'],'wrf')
	nc_file = glob.glob(wrf_rundir + '/wrfout_d0' + str(os.environ['met']['max_dom']) + '*')	
	logging.debug('Plumerise met: %s ' %nc_file)

	#get location
	lat, lon = os.environ['source_lat'], os.environ['source_lon']
	x, y = wrf.ll_to_xy(nc_file, lat, lon, timeidx=wrf.ALL_TIMES)

	return nc_file, x, y
	
def get_sounding(nc_file, x, y):
        '''
        Get sounding from source location
        '''
	
	#pblh = wrf_extract


	return sounding


def main():
	'''
	Run plume rise 
	'''
	logging.info('Running plumerise module')	
	
	#get configuration settings
	settings = read_config(os.environ['config_path'])
	for key in settings['plumerise']:
		set_env_var(settings[key], key)

	#get source location in met domain
	nc_file,x,y = locate_source()

	#retrieve sounding
	#TODO: for now only retrieving BL height
	sounding = get_sounding(nc_file, x, y)

	return

 ### Main ###

if __name__ == '__main__':
	main()		
