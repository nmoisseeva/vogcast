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
	logging.debug('Creating plumerise working subdirectory: {}'.format(cwipp_path))

	os.chdir(cwipp_path)
	#os.system('find -type l -delete')

	#link meteorology - always use the finest domain (max_dom)
	metpath = os.path.join(os.environ['run_path'],'meteorology','wrfout_d0{}'.format(os.environ['max_dom']))+'*'
	logging.debug(f'Linking wrf data: {metpath}')
	os.system(f'ln -sf {metpath} ./wrfout.nc')


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

	#get time index (accounting for possible resart run)
	min_from_start = hr * 60
	it = np.argmin(abs(ds.variables['XTIME'][:] - ds.variables['XTIME'][0]- min_from_start))
	time = str(wrf.extract_times(ds,it))
	logging.debug(f'Getting data for time: {time}')

	#get destaggered height vector, convert to AGL
	zstag = (ds.variables['PHB'][it,:,ilat,ilon] + ds.variables['PH'][it,:,ilat,ilon])//9.81
	z0 = wrf.destagger(zstag,0)
	sfc_elev = ds.variables['HGT'][it,ilat,ilon]
	logging.debug(f'Source elevation: {sfc_elev}')
	agl_height = z0 - sfc_elev

	#get vertical temperature profile
	T0 = ds.variables['T'][it,:,ilat,ilon] + 300
	P = (ds.variables['P'][it,:,ilat,ilon] + ds.variables['PB'][it,:,ilat,ilon]) * 0.01

	#get wind magnitude profile 
	#M  = (ds.variables['U'][it,:,ilat,ilon].squeeze()**2 + ds.variables['V'][it,:,ilat,ilon].squeeze()**2)**(0.5)
	M10 = (ds.variables['U10'][it,ilat,ilon]**2 + ds.variables['V10'][it,ilat,ilon]**2)**(0.5)

	#get wind  direction from wrf functions
	WDIR = wrf.g_uvmet.get_uvmet_wdir(ds, timeidx=it, meta=False)[:,ilat,ilon]
	WSPD = wrf.g_uvmet.get_uvmet_wspd(ds, timeidx=it, meta=False)[:,ilat,ilon]
	
	#get zi
	pblh = ds.variables['PBLH'][it,ilat,ilon]
	
	#get surface heat flux in kinematic form
	hfx = (ds.variables['HFX'][it,ilat,ilon]) * 1.2/1005

	#compile output dict
	metdata = {}
	metdata['T'] = T0.squeeze().tolist()
	metdata['P'] = P.squeeze().tolist()
	metdata['ELEV'] = int(sfc_elev)
	metdata['PBLH'] = int(pblh)
	metdata['Z'] = agl_height.squeeze().tolist()
	#metdata['U'] = M.squeeze().tolist()
	metdata['HFX'] = int(hfx)
	metdata['U10'] = float(M10)
	metdata['WDIR'] = WDIR.squeeze().tolist()
	metdata['WSPD'] = WSPD.squeeze().tolist()
	logging.debug(f'Near-vent windspeed is: {M10} m/s') 

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
	Calculate equivalent cross-wind intensity using heat transfer estimates
	'''

	#calculate heat flux using relationship identified in Keszthelyi et al., 2003
	#estimate is based on 3D surface fit to 1-, 5- and 10- m/s wind speeds
	parameters = [8.52891637, 1.00889672, 0.50909336]

	#get mean heat flux
	src_T = source['temperature'][hr]
	logging.debug(f'Source temperature is: {src_T} deg C')
	src_U = metdata['U10']
	logging.debug(f'Near-vent windspeed is: {src_U} m/s')

	#surface fit
	H = parameters[0] * (src_T**parameters[1]) * (src_U**parameters[2])
	logging.debug(f'H is: {H} W/m2')

	#get intensity
	diameter = 2* ((source['area'][hr]/3.14)**0.5)	
	I = H * diameter / (1.2 * 1005)
	#logging.debug(f'Cross-wind intensity I for hour {hr}:  {int(I)} K m2/s')

	return I

"""
def get_intensity_hc(source, metdata, hr):
	'''
	Calculate equivalent cross-wind intensity using heat transfer estimate
	'''
	#get mean heat flux
	logging.debug('BL height is: {}'.format(metdata['PBLH']))
	delT = (source['temperature'][hr] + 273) - metdata['T'][0]
	H = delT * source['hc']
	logging.debug('H is: {} W/m2'.format(H))

	#convert to kinematic flux and integrate along the diameter
	diameter = 2* ((source['area'][hr]/3.14)**0.5)
	I = H * diameter / (1.2 * 1005)
	logging.info(f'Cross-wind intensity I for hour {hr}:  {int(I)} K m2/s')

	return I
"""

def get_intensity_mass(source, metdata, emissions, hr):
	'''
	Calculate equivalent cross-wind intensity using mass-flux method
	NOTE: this assumes default plume composition of 88% H20, 2% CO2, 10% SO2 in mols (ref. Tricia Nadeau)
	'''

	#prescribe gas densities
	rho_so2 = 2.28
	rho_co2 = 1.84
	rho_h2o = 0.8

	#if plume composition is profided use assigned gas fractions
	if 'gas_fractions' in source.keys():
		logging.info('User-assigned plume gas fractions found in config. Overwriting defaults.')
		frac = source['gas_fractions']
		frac_so2 = frac['SO2']
		mean_rho = frac['H2O'] * rho_h2o + frac['CO2'] * rho_co2 + frac_so2 * rho_so2
	else:
		#use default for Kilauea summit
		#mean_rho = 0.88 * 0.8 + 1.84 * 0.02 + 2.28 * 0.1 
		frac_so2 = 0.1
		mean_rho = 0.88 * rho_h2o + 0.02 * rho_co2 + frac_so2 * rho_so2

	#get kinemtaic mass flux
	so2_kg_per_sec = emissions['so2'] * 1000 / ( 24 * 60 * 60 )
	tot_mass = (mean_rho/rho_so2) * so2_kg_per_sec / frac_so2
	mass_flux = tot_mass / (mean_rho * source['area'][hr])
	mass_flux_cw = mass_flux * 2* ((source['area'][hr]/3.14)**0.5)
	I = mass_flux_cw * (source['temperature'][hr] + 273 - metdata['T'][0])
	
	logging.info(f'Cross-wind intensity I for hour {hr}: {int(I)} K m2/s')

	return I


def main():
	'''
	Preprocess src location for cwwipp run
	'''
	logging.info('Preprocessing source locations for CWIPP')	
	logging.info('All vents will be processed at the same time')


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
	tags = json_data['user_defined']['source'].keys()

	#create slot for data in run_json
	vent_data = {}

	#for iSrc in range(num_src):
		#tag = 'src'+str(iSrc+1)
	for iSrc, tag in enumerate(tags):
		source = json_data['user_defined']['source'][tag]
		
		if source['pr_model'] != 'cwipp':
			logging.critical('ERROR: if using CWIPP plume-rise in must be applied to all source locations. Aborting!')	
			sys.exit(1)

		emissions = json_data['emissions'][tag]

		#get source location
		lat, lon = float(source['lat']),float(source['lon'])
		src_loc = np.array([lat,lon]).reshape(1, -1)
		logging.info(f'Getting source conditions for {tag}: {lat},{lon}')


		#get loc index nearest to fire
		met_idx = get_met_loc_idx(met_tree, src_loc)

		cwippjson[tag] = {}

		#get vent parameters
		vent_data[tag] = {}
		if source['vent_params'] == 'flir':
			logging.info('...pulling latest thermal image of the vent from HVO')
			#update source dictionary
			source = get_hvo_flir.main(source)
		elif source['vent_params'] == 'prescribed':
			logging.info('...using prescribed vent temperature and area')
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

	logging.info('CWIPP preprocessing is complete')

	return vent_data

 ### Main ###

if __name__ == '__main__':
	main()		
