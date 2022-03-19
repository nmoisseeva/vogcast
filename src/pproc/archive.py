#!/usr/bin/python3.7
 
# Script for generating hysplit ensemble averages, station traces, POEs, archiving and web display

__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="September 2021"

from set_vog_env import *
import logging
import os

### Functions ###
def clean_hysdir():
	#clean up dispersion folder

	logging.debug('Cleaning up HYSPLIT direcotry')
	#os.system('find -type l -delete')
	os.system('rm *.OK VMSDIST* PARDUMP* MESSAGE* WARNING* *.out *.err *.log > /dev/null 2>&1')

	return

def archive(archive_path):
	#archiving script: compresses the main run folder and pushes to remote archive
	logging.info('Compressing data and pushing to remote archive')
	logging.warning('...this step may take a LONG time')
	
	#move out of forecast direcotry
	os.chdir(os.environ['run_dir'])

	#run tar command - THIS WILL BE SLOW
	tar_cmd = 'tar -zcf {}TEST.tar.gz {}'.format(os.environ['forecast'], os.environ['forecast'])
	os.system(tar_cmd)

	#push archived data to remote set by user (requires ssh key)
	scp_cmd = 'scp {}TEST.tar.gz {}'.format(os.environ['forecast'],archive_path)
	logging.debug('...copying to remote: {}'.format(scp_cmd))
	os.system(scp_cmd)

	return

def main(settings):
	'''
	Main script for archiving to thredds
	'''
	
	clean_hysdir()
	archive(settings)

	return

 ### Main ###
if __name__ == '__main__':
	main()		
