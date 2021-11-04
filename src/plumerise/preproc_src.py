#!/usr/bin/python3.7
 
#Script converst wrf output to hysplit arl format

__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="October 2021"

import os
import sys
from pathlib import Path
import logging
import glob
from set_vog_env import *
import netCDF4 as nc
from sklearn.neighbors import KDTree
from scipy.interpolate import interp1d
import wrf
import pandas as pd
import numpy as np
import datetime as dt

 ### Fucntions ###

def setup_cwipp_dir():
	'''
	Set up and navigate to plumerise subdirectory within main run folder, link data
	'''
	#create subdirectory for cwipp files, clean up
	cwipp_path = os.path.join(os.environ['run_path'],'plumerise')
	Path(cwipp_path).mkdir(exist_ok=True)
	logging.debug('...creating plumerise working subdirectory: {}'.format(cwipp_path))

	os.chdir(cwipp_path)
	os.system('find -type l -delete')

	#link meteorology - always use the finest domain (max_dom)
	metpath = os.path.join(os.environ['run_path'],'meteorology','wrfout_d0{}'.format(os.environ['max_dom']))+'*'
	logging.debug('...linking wrf data: {}'.format(metpath))
	os.system('ln -s {} ./wrfout.nc'.format(metpath))


	return

def build_met_tree(ds):
	'''
	Bbuild met kd-tree
	'''
	locs = pd.DataFrame({'XLAT': ds.variables['XLAT'][0].ravel(), 'XLONG': ds.variables['XLONG'][0].ravel()})
	tree = KDTree(locs)

	return tree


def get_met_loc_idx(tree, src_loc):
	'''
	Query kd-tree and do sanity check
	'''
	dist, ind = tree.query(src_loc, k=1)

	#make sure the points are not too far (NOTE: hardcoded cutoff)
	if dist > 0.1:
		logging.error('ERROR: Closest WRF location is too far: dist = {}'.format(dist[0][0]))
		sys.exit(1)
	else:
		return ind


def get_met_data(ds,hr,met_idx):
	'''
	Extract profiles
	'''
	
	#get indecies in two differet formats for convenience
	iz,ilat,ilon =  np.unravel_index(met_idx[0],shape = np.shape(ds.variables['XLAT']))
	inds = np.unravel_index(met_idx[0],shape = np.shape(ds.variables['XLAT']))

	#debug sanity-check prinout
	logging.debug('...closest grid location found: {},{}'.format(ds.variables['XLAT'][hr,ilat,ilon].squeeze(),ds.variables['XLONG'][hr,ilat,ilon].squeeze()))


	#get destaggered height vector, convert to AGL
	zstag = (ds.variables['PHB'][hr,:,ilat,ilon] + ds.variables['PH'][hr,:,ilat,ilon])//9.81
	z0 = wrf.destagger(zstag,0)
	sfc_elev = ds.variables['HGT'][inds]
	agl_height = z0 - sfc_elev

	#get vertical temperature profile
	T0 = ds.variables['T'][hr,:,ilat,ilon] + 300

	#get wind magnitude profile 
	M  = (ds.variables['U'][hr,:,ilat,ilon].squeeze()**2 + ds.variables['V'][hr,:,ilat,ilon].squeeze()**2)**(0.5)

	#get zi
	pblh = ds.variables['PBLH'][inds]


	logging.debug('SANITY CHECK: {}'.format(ds.variables['XLONG'][hr,ilat,ilon]))


	#compile output dict
	metdata = {}
	metdata['T'] = T0.squeeze().tolist()
	metdata['PBLH'] = int(pblh)
	metdata['Z'] = agl_height.squeeze().tolist()
	metdata['U'] = M.squeeze().tolist()

	return metdata

def parse_timestamp(json_data,hr):
	'''
	Create timestamp (str) using environment variables and hour index
	'''
	fcstdate = dt.datetime.strptime(os.environ['forecast'],'%Y%m%d%H')
	tstamp = fcstdate + dt.timedelta(hours = hr)
	tstamp_str = dt.datetime.strftime(tstamp, '%Y%m%d%H')

	return tstamp_str


def main():
	'''
	Preprocess src location for cwwipp run
	'''
	logging.info('...Preprocessing source locations for CWIPP')	


	#set up cwipp directory
	setup_cwipp_dir()

	#get runsjon and setup output dictionary
	json_data = read_run_json()
	cwippjson = {}

	#read linked wrfout file and build kd-tree
	ds = nc.Dataset('wrfout.nc')
	met_tree = build_met_tree(ds)
	
	#loop through sources
	num_src = len(json_data['user_defined']['source'])
	for iSrc in range(num_src):
		tag = 'src'+str(iSrc+1)
		source = json_data['user_defined']['source'][tag]

		#get source location
		lat, lon = float(source['lat']),float(source['lon'])
		src_loc = np.array([lat,lon]).reshape(1, -1)
		logging.info('...getting source conditions for {}: {},{}'.format(tag,lat,lon))


		#get loc index nearest to fire
		met_idx = get_met_loc_idx(met_tree, src_loc)

		#loop through hours of simulation
		for hr in range(int(os.environ['spinup']),int(os.environ['runhrs'])):
			
			#get met inputs for cwipp 
			metdata = get_met_data(ds,hr,met_idx)

			#parse timestamp
			timestamp = parse_timestamp(json_data, hr)
			
			#add data to out dictionary
			cwippjson[timestamp] = {}
			cwippjson[timestamp][tag] = metdata 

    			#add intensity record
			#NOTE future: is there a diurnal temperature cycle to consider?
			cwippjson[timestamp][tag]['I'] = source['intensity']

	#write out the cwipp json
	write_json('cwipp_inputs.json',cwippjson)

	logging.info('... cwipp preprocessing is complete')

	return

 ### Main ###

if __name__ == '__main__':
	main()		