#!/usr/bin/python3.7
 
#Script extacts profile data from wrf meteorology and parameterizes vertical distribution of emissions

__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="July 2021"

import os
import logging
#import wrf
from set_vog_env import *
import glob
import plumerise.preproc_src as prepcwipp
import plumerise.cwipp as cwipp

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
	'''
	### inputs (conversion of emisisons ###
	to_mg_per_hr = (1./24) * 1e9 	#converstion factor from tonnes/day to mg/hr

	### main ###
	lat, lon, height, area = str(source['lat']), str(source['lon']), str(source['height']),  str(source['area'])
	so2 = str(to_mg_per_hr * emissions['so2'])

	lines = lat + ' ' + lon + ' ' + height + ' ' + so2 + ' ' + area

	#append main run json with area source data
	json_data = read_run_json()
	json_data['plumerise'] = {'sources': lines, 'src_cnt' : 1}
	update_run_json(json_data)

	return

def run_cwipp():
	'''
	Run dynamic plume rise model
	'''

	#-------this is a bias fit default from Moisseeva 2021----
	biasFit =  [0.9195, 137.9193]
	#---------------------------------------------------------

	#load input data
	cwippinputs = read_json('cwipp_inputs.json')

	#set up output dictionary
	output = {}

	#loop through available timestamps
	for tag in cwippinputs.keys():
		logging.debug('.....processing source: {}'.format(tag))
		output[tag] = {}

		#loop through all hours
		for dtime in cwippinputs[tag].keys():
			src = cwippinputs[tag][dtime]
		
			#run cwipp model
			plume = cwipp.Plume(tag)
			plume.get_sounding(src)
			plume.I = src['I']
			plume.iterate(biasFit)
			plume.classify()
			plume.get_uBL(src)
			plume.get_profile()

			output[tag][dtime] = plume.profile
	#write output? 	

	return


def main():
	'''
	Run plume rise/source model
	'''
	#load main run json
	json_data = read_run_json()	

	#get number of sources
	num_src = len(json_data['user_defined']['source'])

	logging.info('Running source model: {} emissions sources'.format(num_src))

	#run source model for each emissions location
	for iSrc in range(num_src):
		tag = 'src'+str(iSrc+1)
		source = json_data['user_defined']['source'][tag]
		emissions = json_data['emissions'][tag]

		#call the selected plume rise approach
		logging.info('... {} plumerise model: {}'.format(tag,source['pr_model']))
		
		if source['pr_model']=='ops':
			#this is legacy option up to 2021 (NOTE: note included in config)
			static_line(source, emissions)
		elif source['pr_model']=='static_area':
			#standard hysplit area source option
			static_area(source, emissions)
		elif source['pr_model']=='cwipp':
			#dynamic plume rise model adapted from widlfire
			prepcwipp.main()
			run_cwipp()
		else:
			logging.critical('ERROR: Plume-rise model not recognized. Available options are: "ops", "static_area", "bl_mixing" and "cwipp". Aborting!')

	return

 ### Main ###

if __name__ == '__main__':
	main()		
