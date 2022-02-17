#!/usr/bin/python3.7
 
# Script for generating hysplit ensemble averages, station traces, POEs, archiving and web display

__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="July 2021"

from set_vog_env import *
import pproc.to_webserver as web
import pproc.archive as archive
import pproc.hazard_map as hazard
import logging
import json
import os

'''
INSTRUCTIONS FOR ADDING USER-SPECIFIC SUBMODULES

1) Create a new python module (recommended location: 'pproc' subfolder)

2) Add a corresponding json key in vog.config under 'extras' section

3) Import the module and add a call to execute it in main() below 

'''

def main():
	'''
	Main script for additional user-specific modules. 
	
	Current extras:
	- graphics copy to web server
	- data cleanup and archiving to thredds
	- create hazard maps	
	'''

	logging.info('===========EXTRAS: USER-SPECIFIC SUBMODULES=========')

	json_data = read_run_json()
	
	#extras: archive and move to webserver if requested
	extras = json_data['user_defined']['extras']
	if 'web' in extras.keys():
		web.main(extras['web'])
	if 'archive' in extras.keys():
		archive.main(extras['archive'])
	if 'hazard_map' in extras.keys():
		hazard.main(extras['hazard_map'])
		
	#FOR ADDITIONAL SUBMODULES ADD AN EXTRA CALL HERE
	else:
		logging.info('No other modules requested')


 ### Main ###
if __name__ == '__main__':
	main()		
