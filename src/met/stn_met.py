#!/usr/bin/python3.7
 
# Script extracts point station data from meteorology of all kinds

__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="April 2022"

from set_vog_env import *
import logging
import json
import os
import met.met_from_arl as met_from_arl
import pandas as pd

### Functions ###
def get_stn_locations(lcn_file):

	#read locations file
	locs = pd.read_csv(lcn_file, delim_whitespace=True, names = ['id','lat','lon'])

	#convert into a dictionary
	stations = {}
	for iStn, stn in locs.iterrows():
		stations[stn.id] = { 'lat' : stn.lat, 'lon' : stn.lon }

	return stations

def compile_input(stn_met):
	#create the locations dictionary from station file

	#create control file for arl extraction
	locations = {}	
	if 'arl' in stn_met['met_src']:
		locations['arl'] = {}
		locations['arl']['arlfile'] = 'd01.arl'
		locations['arl']['vars'] = { '2d' : ['SHGT','PRSS','PBLH','T02M','U10M','V10M', 'WDIR','WSPD'], '3d': ['PRES','UWND','VWND','WWND','SPHU','TPOT','WDIR','WSPD']}
		locations['arl']['stns'] = get_stn_locations(stn_met['loc_file'])
		#locations['arl']['stns'] = { 'src1' : {'lat':19.4055 , 'lon':-155.2811 }}
	
	if 'wrf' in stn_met['met_src']:
	#create control file for wrf extraction
		locations['wrf'] = {}
		locations['wrf']['wrffile'] = 'wrfout_d01'


	return locations

def main(stn_met):
	'''
	Extracts data from wrf and arl files for point locations
	'''
	#TODO compile input from stn file
	locations = compile_input(stn_met)

	if 'arl' in stn_met['met_src']:
		met_from_arl.main(locations['arl'])

	logging.info('Extracting meteorology at point locations')



 ### Main ###
if __name__ == '__main__':
	main(stn_met)		
