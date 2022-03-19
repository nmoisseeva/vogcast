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

 ### Fucntions ###


def compile_input():

	print('compiling input')
	return


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
		metdata[step][var2d] = 	vals2d[nVar+1]
	

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
	
	return metdata

def main(locations):
	'''
	Extract met data for point locations, for given 'getdata' dictionary
	
	'''
	logging.info('Extracting met data from arl files')	

		
	#navigate to dispersion folder containing arl file (or symlink) and link hysplit exec
	os.chdir(os.environ['hys_rundir'])
	pproc.link_exec('profile')

	#create storage dataframe
	metdata = {}

	#check what's provided as input: file path or dictionary
	if isinstance(locations, str):
		getdata = compile_input(locations)
	elif isinstance(locations, dict):	
		getdata = locations			
	else:
		logging.CRITICAL('Accepted input types for arl data extraction: str or dict')
		

	#loop through locations
	for lcn in getdata['stns']:
		stn = getdata['stns'][lcn]
		metdata[lcn] = {}
		#loop through timesteps
		#TODO remove the timestep hardcoding
		for tidx in range(18):
			#run the hyslpit profile utility
			profile_cmd = './profile -d./ -f{} -y{} -x{}  -o{} -w1'.format(getdata['arlfile'],stn['lat'],stn['lon'],tidx)
			os.system(profile_cmd)
			
			#convert data into dataframe and export to json
			metdata[lcn] = decode_hystxt(metdata[lcn],getdata['vars'])	

	write_json('arlmet_{}.json'.format(lcn),metdata)

	return

 ### Main ###

if __name__ == '__main__':
	main(locations)		
