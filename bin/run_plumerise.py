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
	nc_file = glob.glob(wrf_rundir + '/wrfout_d0' + str(os.environ['max_dom']) + '*')	
	logging.debug('Plumerise met: %s ' %nc_file)

	#get location
	#TODO add functionality for multiple sources
	lat, lon = os.environ['lat'], os.environ['lon']
	x, y = wrf.ll_to_xy(nc_file, lat, lon, timeidx=wrf.ALL_TIMES)

	return nc_file, x, y
	
def get_sounding(nc_file, x, y):
	'''
	Get sounding from source location
	'''
	
	#pblh = wrf_extract
	sounding = 0

	return sounding

def static_line(source, emissions):
	'''
	Performs static legacy ops routine for defining an emission source line:
		-assumes fixed BL day and night of 700m
		-fairly strange vertical level selections
		-uses undocumented fudge factors
		-must be ran with the following CONTROL settings: 1500m mixing depth, isobaric vertical motion
	'''
	### inputs (historic ops settings) ###
	bias = 0.2314 * 1.458e7 	#obscure historic bias correction factors
	distribution = [0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.02, 0.9] 	#fixed vertical distribution
	levels = [50, 150, 300, 350, 400, 450, 550, 600, 650, 700] 		#no idea why

	### main ###
	#distribute the emissions vertically
	lines = ''
	lat, lon, area = str(source['lat']), str(source['lon']), str(source['area'])
	for i in range(len(levels)):
		so2 = int(distribution[i] * bias * emissions['so2'])
		lines = lines + lat  + ' ' + lon + ' ' + str(levels[i]) + ' ' + str(so2) + ' ' + area + '\\n'
	logging.debug('Distributing emissions vertically...\n%s' %lines)

	#remove newline character from the last line
	lines = lines[:-2]
	
	#append main run json with vertical line source data
	json_data = read_run_json()
	json_data['plumerise'] = {'sources': lines, 'src_cnt' : len(levels)}
	update_run_json(json_data)

	return

def static_area(source, emissions):
	'''
	New "low buoyancy" approach for a single level area source
	-must be ran with the following CONTROL settings: 150m mixing depth, met-driven vertical motion
	'''
	### inputs (conversion of emisisons ###
	to_g_per_hr = 1./24 * 1e9 	#converstion factor from tonnes/day to mg/hr
	lvl = 100			#virtual source hegith in m AGL

	### main ###
	lat, lon, area = str(source['lat']), str(source['lon']), str(source['area'])
	so2 = str(to_g_per_hr * emissions['so2'])

	lines = lat + ' ' + lon + ' ' + str(lvl) + ' ' + so2 + ' ' + area

	#append main run json with area source data
	json_data = read_run_json()
	json_data['plumerise'] = {'sources': lines, 'src_cnt' : 1}
	update_run_json(json_data)

	return

def main():
	'''
	Run plume rise 
	'''
	#load main run json
	json_data = read_run_json()	
	source = json_data['user_defined']['source']
	emissions = json_data['emissions']

	#TODO: this must all be extended for multiple source locations

	#call the selected plume rise approach
	logging.info('Running plumerise model: %s' %source['pr_model'])
	if source['pr_model']=='ops':
		static_line(source, emissions)
	elif source['pr_model']=='static_area':
		static_area(source, emissions)
	else:
		logging.critical('ERROR: Plume-rise model not recognized. Available options are: "ops", "static_area", "bl_mixing" and "cwipp". Aborting!')
	'''
	elif source['pr_model']=='bl_mixing':
		bl_mixing(source, emissions)
	elif source['pr_model']=='cwipp':
		bl_mixing(source, emissions)
	else:
		#TODO: NOT TESTED FROM HERE ON
		#get source location in met domain
		nc_file,x,y = locate_source()

		#retrieve sounding
		#TODO: for now only retrieving BL height
		sounding = get_sounding(nc_file, x, y)
	'''
	return

 ### Main ###

if __name__ == '__main__':
	main()		
