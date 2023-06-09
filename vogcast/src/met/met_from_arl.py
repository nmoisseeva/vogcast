#!/usr/bin/python3.7
 
#Script to extract met data from arl files

__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="March 2022"

import os
import sys
from pathlib import Path
import logging
import glob
from set_vog_env import *
import post_process as pproc
import pandas as pd
import datetime as dt
import linecache
import numpy as np

 ### Fucntions ###

#THIS IS WRONG for upper atmosphere
def derive_height(stepdata):
	'''
	Convert pressure coordinates to height
	'''
	
	#constants
	Rd = 287 	#J K-1 kg-1
	g = 9.81	#gravity

	numZ = len(stepdata['PRES'])
	#convert specific humidity to mixing ratio r: r = q / (1 - q)
	q = np.array(stepdata['SPHU']) / 1000 	#convert to kg/kg
	r = q / (1 - q)

	#calculate average vertical tempareture for each layer: Tv = Tp(1 + 0.61r)
	Tv = np.array(stepdata['TPOT']) * (1 + 0.61 * r)

	#use hypsometric equation to get layer height: h = z2 - z1 = (Rd * Tv /g)  * ln (p1 / p2)
	Z = np.zeros(numZ)
	for iZ in range(numZ-1):
		Tv_mean = np.mean([Tv[iZ], Tv[iZ + 1]])
		h = (Rd * Tv_mean / g) * np.log( stepdata['PRES'][iZ] / stepdata['PRES'][iZ + 1] )
		Z[iZ+1] = int(Z[iZ] + h)

	return list(Z)

def decode_hystxt(metdata,variables):
	'''
	Decode hysplit profile.txt output and write to storage dictionary
	NOTE: this assumes single timestep files, and is pretty hardcoded to current HYSPLIT format
	'''

	#get timestamp
	rawfile = open("profile.txt", "r")
	lines = rawfile.readlines()
	for iL, line in enumerate(lines):
		if 'Profile Time:' in line:
			year,month,day,hour,minute = [int(s) for s in line.split() if s.isdigit()]
			#NOTE: Hardcoded assumption that we are in the 21st century!
			dtstamp = dt.datetime(2000+year,month,day,hour,minute)
	#create storage dictionary
	step = dtstamp.strftime('%Y%m%d%H')
	metdata[step] = {}

	#get 2D vars	
	for iL, line in enumerate(lines):
		if '2D Fields' in line:
			names2d = lines[iL+1].split()
			vals2d = lines[iL+3].split()
			#check that the values don't end up merged, because hysplit just assumes 6 character lengths
			if any(len(s) > 6 for s in vals2d):
				vals2d = [[float(s[:-6]),float(s[-6:])] if len(s) > 5 else [float(s)] for s in vals2d]
				#flatten the list
				vals2d = [val for sublist in vals2d for val in sublist] 
			#if all is good simply convert to float
			else:
				vals2d = [float(val) for val in vals2d]

	for var2d in variables['2d']:
		nVar = names2d.index(var2d)
		#+1 accounts for the extra unlabeled pressure coordinate in profile files
		#deal with HYSPLIT failing to calculate WDIR and WSPD
		try:
			metdata[step][var2d] = 	vals2d[nVar+1]
		except: 
			metdata[step][var2d] = 0

	#get 3D variables

	for iL, line in enumerate(lines):
		if '3D Fields' in line:
			names3d = lines[iL+1].split()
			vert_data = pd.read_csv('profile.txt', skiprows=iL+3, delim_whitespace=True, names=['JUNK']+names3d)
	#drop the unnamed pressue coordinate
	vert_data = vert_data.drop('JUNK', 1)
	for var3d in variables['3d']:
		#etract vertical profile
		metdata[step][var3d] = vert_data[var3d].tolist()

	rawfile.close()

	#add height coordinate
	metdata[step]['Z'] = derive_height(metdata[step])
	
	return metdata

def main(locations):
	'''
	Extract met data for point locations, for given locations dictionary
	
	'''
	logging.info('Extracting met data from arl files')	

		
	#navigate to dispersion folder containing arl file (or symlink) and link hysplit exec
	os.chdir(os.environ['hys_rundir'])
	pproc.link_exec('profile')

	#create storage dataframe
	metdata = {}

	#loop through locations
	for lcn in locations['stns']:
		stn = locations['stns'][lcn]
		metdata[lcn] = {}
		#loop through timesteps
		for tidx in range(int(os.environ['runhrs'])):
			#run the hyslpit profile utility
			profile_cmd = './profile -d./ -f{} -y{} -x{}  -o{} -w1'.format(locations['arlfile'],stn['lat'],stn['lon'],tidx)
			os.system(profile_cmd)
			
			#convert data into dataframe and export to json
			metdata[lcn] = decode_hystxt(metdata[lcn],locations['vars'])	

	write_json('stn_met_arl.json',metdata)

	return

 ### Main ###

if __name__ == '__main__':
	main(locations)		
