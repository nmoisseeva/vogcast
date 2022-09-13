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
import plumerise.get_hvo_flir as get_hvo_flir
import netCDF4 as nc
from sklearn.neighbors import KDTree
from scipy.interpolate import interp1d
import wrf
import pandas as pd
import numpy as np
import datetime as dt

#turn off excessive logging
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger('matplotlib').setLevel(logging.WARNING)

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
	#os.system('find -type l -delete')

	#link meteorology - always use the finest domain (max_dom)
	metpath = os.path.join(os.environ['run_path'],'meteorology','wrfout_d0{}'.format(os.environ['max_dom']))+'*'
	logging.debug('...linking wrf data: {}'.format(metpath))
	os.system('ln -sf {} ./wrfout.nc'.format(metpath))


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

	#get destaggered height vector, convert to AGL
	zstag = (ds.variables['PHB'][hr,:,ilat,ilon] + ds.variables['PH'][hr,:,ilat,ilon])//9.81
	z0 = wrf.destagger(zstag,0)
	sfc_elev = ds.variables['HGT'][hr,ilat,ilon]
	agl_height = z0 - sfc_elev

	#get vertical temperature profile
	T0 = ds.variables['T'][hr,:,ilat,ilon] + 300
	P = (ds.variables['P'][hr,:,ilat,ilon] + ds.variables['PB'][hr,:,ilat,ilon]) * 0.01

	#get wind magnitude profile 
	M  = (ds.variables['U'][hr,:,ilat,ilon].squeeze()**2 + ds.variables['V'][hr,:,ilat,ilon].squeeze()**2)**(0.5)

	#get zi
	pblh = ds.variables['PBLH'][hr,ilat,ilon]
	
	#get surface heat flux in kinematic form
	hfx = (ds.variables['HFX'][hr,ilat,ilon]) * 1.2/1005

	#compile output dict
	metdata = {}
	metdata['T'] = T0.squeeze().tolist()
	metdata['P'] = P.squeeze().tolist()
	metdata['PBLH'] = int(pblh)
	metdata['Z'] = agl_height.squeeze().tolist()
	metdata['U'] = M.squeeze().tolist()
	metdata['HFX'] = int(hfx)

	return metdata

def parse_timestamp(json_data,hr):
	'''
	Create timestamp (str) using environment variables and hour index
	'''
	fcstdate = dt.datetime.strptime(os.environ['forecast'],'%Y%m%d%H')
	tstamp = fcstdate + dt.timedelta(hours = hr)
	tstamp_str = dt.datetime.strftime(tstamp, '%Y%m%d%H')

	return tstamp_str

def get_intensity_hc(source, metdata, hr):
	'''
	Calculate equivalent cross-wind intensity using heat transfer estimate
	'''
	#get mean heat flux
	logging.debug('... BL height is: {}'.format(metdata['PBLH']))
	delT = (source['temperature'][hr] + 273) - metdata['T'][0]
	logging.debug('... delT is: {} K'.format(delT))
	H = delT * source['hc']
	logging.debug('... H is: {} W/m2'.format(H))

	#convert to kinematic flux and integrate along the diameter
	diameter = 2* ((source['area'][hr]/3.14)**0.5)
	I = H * diameter / (1.2 * 1005)
	logging.info(f'... Cross-wind intensity I for hour {hr}:  {int(I)} K m2/s')

	return I

def get_intensity_mass(source, metdata, emissions, hr):
	'''
	Calculate equivalent cross-wind intensity using mass-flux method
	NOTE: this assumes constnant plume composition of 88% H20, 2% CO2, 10% SO2 (ref. Tricia Nadeau)
	'''

	#prescribe gas densities
	rho_so2 = 2.28
	rho_co2 = 1.84
	rho_h2o = 0.8
	mean_rho = 0.88 * 0.8 + 1.84 * 0.02 + 2.28 * 0.1

	#get kinemtaic mass flux
	so2_kg_per_sec = emissions['so2'] * 1000 / ( 24 * 60 * 60 )
	tot_mass = (mean_rho/rho_so2) * so2_kg_per_sec / 0.1
	mass_flux = tot_mass / (mean_rho * source['area'][hr])
	mass_flux_cw = mass_flux * 2* ((source['area'][hr]/3.14)**0.5)
	I = mass_flux_cw * (source['temperature'][hr] + 273)
	
	logging.info(f'...Cross-wind intensity I for hour {hr}: {int(I)} K m2/s')

	return I


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

	#create slot for data in run_json
	#json_data['vent'] = {}
	vent_data = {}

	for iSrc in range(num_src):
		tag = 'src'+str(iSrc+1)
		source = json_data['user_defined']['source'][tag]
		emissions = json_data['emissions'][tag]

		#get source location
		lat, lon = float(source['lat']),float(source['lon'])
		src_loc = np.array([lat,lon]).reshape(1, -1)
		logging.info('...getting source conditions for {}: {},{}'.format(tag,lat,lon))


		#get loc index nearest to fire
		met_idx = get_met_loc_idx(met_tree, src_loc)

		cwippjson[tag] = {}

		#get vent parameters
		#json_data['vent'][tag] = {}
		vent_data[tag] = {}
		if source['vent_params'] == 'flir':
			logging.info('...pulling latest thermal image of the vent from HVO')
			#update source dictionary
			source = get_hvo_flir.main(source)
		elif source['vent_params'] == 'prescribed':
			logging.info('....using prescribed vent temperature and area')
			#assume static vent conditions for all run hours
			source['temperature'] = [source['temperature']] * int(os.environ['runhrs'])
			source['area'] = [source['area']] * int(os.environ['runhrs'])
		else:
			logging.critical('ERROR: unrecognized vent parameter input. Available options: "prescribed"/"flir"')

		#loop through hours of simulation
		for hr in range(int(os.environ['spinup']),int(os.environ['runhrs'])):
			
			#get met inputs for cwipp 
			metdata = get_met_data(ds,hr,met_idx)

			#parse timestamp
			timestamp = parse_timestamp(json_data, hr)
			
			#add data to out dictionary
			cwippjson[tag][timestamp] = metdata 

			#calculate intensity based on user-defined method
			if source['method'] == 'hc':
				I = get_intensity_hc(source, metdata, hr)
			elif source['method'] == 'mass':
				I = get_intensity_mass(source, metdata, emissions, hr)
	
			cwippjson[tag][timestamp]['I'] = I

		#save vent data for reference
		#json_data['vent'][tag] = source
		vent_data[tag] = source

	#write out the cwipp json
	write_json('cwipp_inputs.json',cwippjson)

	#update run json
	#update_run_json(json_data)

	logging.info('... cwipp preprocessing is complete')

	return vent_data

 ### Main ###

if __name__ == '__main__':
	main()		
