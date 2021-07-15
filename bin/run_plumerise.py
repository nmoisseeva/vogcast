#!/usr/bin/python3.7
 
#Script extacts profile data from wrf meteorology and parameterizes vertical distribution of emissions

__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="July 2021"

import os
import logging
#import wrf
from set_vog_env import *
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
	sounding = 0

	return sounding

def static_plumerise(settings):
	'''
	Performs current ops routine for definig an emission source line
	'''
	### inputs (historic ops settings) ###
	bias = 0.2314 * 1.458e7 	#obscure historic bias correction factors
	distribution = [0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.02, 0.9] 	#fixed vertical distribution
	levels = [50, 150, 300, 350, 400, 450, 550, 600, 650, 700] 		#no idea why
	area = 500

	### main ###
	#load main run json 
	with open(os.environ['json_path'], 'r') as f:
		json_data = json.load(f)
	
	#distribute the emissions vertically
	lines = ''
	lat, lon = str(settings['plumerise']['source_lat']), str(settings['plumerise']['source_lon'])
	for i in range(len(levels)):
		so2 = distribution[i] * bias * json_data['emissions']['so2']
		lines = lines + lat  + ' ' + lon + ' ' + str(levels[i]) + ' ' + str(so2) + ' ' + str (area) + '\n'
	logging.debug('Distributing emissions vertically...\n%s' %lines)
	
	#append main run json with vertical line source data
	json_data['plumerise'] = {'sources': lines}

	with open(os.environ['json_path'], 'w') as f:
		f.write(json.dumps(json_data, indent=4))

	logging.debug('Run json updated with source data')
	return


def main():
	'''
	Run plume rise 
	'''
	logging.info('Running plumerise module')	
	
	#get configuration settings
	settings = read_config(os.environ['config_path'])
		

	
	#steps for current static operational ("ops") model
	if settings['plumerise']['pr_model']=='ops':
		#do static stuff
		logging.debug('Running static %s plumerise model' %settings['plumerise']['pr_model'])
		static_plumerise(settings)
	else:
		#TODO: NOT TESTED FROM HERE ON
		#get source location in met domain
		nc_file,x,y = locate_source()

		#retrieve sounding
		#TODO: for now only retrieving BL height
		sounding = get_sounding(nc_file, x, y)

	return

 ### Main ###

if __name__ == '__main__':
	main()		
