#!/usr/bin/python3.7
 
# Script for generating hysplit ensemble averages, station traces and POEs

__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="July 2021"

from set_vog_env import *
import logging
import json
import os

### Functions ###

def link_exec(hysexec):
	'''
	Function to link hysplit executables into a local directory
	'''

	#create path to file
	exec_path =  os.path.join(os.environ['hys_path'], 'exec', hysexec)
	local_path = './{}'.format(hysexec)

	#create symlink
	try:
		os.symlink(exec_path, local_path)
	except:
		os.remove(local_path)
		os.symlink(exec_path, local_path)
	return

def ensmean():
	'''
	Run ensemble averaging
	'''
	logging.debug('...creating ensemble average')

	#move into dispersion working directory, clean up
	os.chdir(os.environ['hys_rundir'])
	os.system('find -type l -delete')

	#TODO check that that dispersion completed

	#link executables
	link_exec('conprob')
	#conprob = os.path.join(os.environ['hys_path'],'exec','conprob')
	#os.symlink(conprob, './conprob')

	
	#run hysplit averaging utility
	os.system('./conprob -bcdump') 

	return

def stn_traces(tag,stn_file):
	'''
	Script extracts ensmean concentrations from user-defined stations
	'''
	logging.debug('...creating station traces')
	
	#define conversion factor from mg/m3 to ppm for SO2
	conv = 0.382

	#link executables
	link_exec('con2stn')
	#con2stn = os.path.join(os.environ['hys_path'],'exec','con2stn')
	#os.symlink(con2stn, './con2stn')

	#extract station data
	out_file = 'HYSPLIT_so2.{}.{}.txt'.format(os.environ['forecast'],tag)
	con2stn_cmd = './con2stn -p1 -d2 -z2 -c{} -icmean -o{} -s{} -xi'.format(conv,out_file,stn_file)
	os.system(con2stn_cmd)

	#copy to webserver (mkwc)
	mkwc_file = 'hysplit.haw.{}.so2.{}.txt'.format(tag,os.environ['forecast'])
	scp_cmd = 'scp {} vmap@mkwc2.ifa.hawaii.edu:www/hysplit/text/{}'.format(out_file, mkwc_file)
	os.system(scp_cmd)
	logging.debug('...copying station data to mwkc as: {}'.format(mkwc_file))


	return


def to_netcdf(hysfile):
	'''
	Converts hysplit binary to NetCDF
	'''

	logging.debug('...converting data to netcdf')	

	#link netcdf converter
	link_exec('con2cdf4')

	#convert ensemble mean to netcdf
	con2cdf4_cmd = './con2cdf4 {} {}.nc'.format(hysfile, hysfile)
	os.system(con2cdf4_cmd)




def main():
	'''
	Main script for dispersion post-processing. 
	
	Returns:
	- ensemble-avareged surface concentrations
	- probabilities of exceedance for user-defined thresholds
	- station traces
	'''

	logging.info('Running post-processing steps')

	json_data = read_run_json()

	#create ensemble average, convert it to netcdf
	ensmean()
	to_netcdf('cmean')

	#TODO create POE for user-defined thresholds, if requested 

	#create station traces for user-defined stations, if requested
	#TODO make this optional
	pproc_settings = json_data['user_defined']['post_process']['stns']
	stn_traces(pproc_settings['tag'],pproc_settings['stn_file'])


	#create graphics
	


	logging.info('Post-processing complete')


 ### Main ###
if __name__ == '__main__':
	main()		
