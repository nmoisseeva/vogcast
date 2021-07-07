# Setup environment for the vog model run
#
__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="July 2021"

### Inputs ###
config_path = '../vog.config' 		#json config file

#import supporint modules
from set_vog_env import *
import sys
import subprocess
import datetime
import os


### Main ###
if __name__ == "__main__":
	
	print("============BEGIN VOG PIPELINE RUN=============")
	print(datetime.datetime.utcnow())
	
	#read date input and determine run typ
	args = parse_inputs()				
	if args.date:
		rundate = args.date
		print("Performing historic run for: %s%s" %(rundate, args.cycle))	
	else:
		rundate = datetime.datetime.now().strftime('%Y%m%d')	
		print("Performing real-time run for: %s%s" %(rundate,args.cycle))	
	forecast = '%s%s' %(rundate,args.cycle)

	#load configuration settings
	settings = read_config(config_path)

	#set shared environmental variables
	set_env_var(settings, "vog_root")
	set_env_var(settings, "runhrs")

	#set variables for met modules
	# includes: get_nam, run_wps,
	set_env_var(settings['met'], "max_dom")
	set_env_var(settings['met'], "ibc_path")
	set_env_var(settings['met'], "wps_path")
	set_env_var(settings['met'], "wrf_path")

	#create storage folders
	create_run_dir(forecast)
	


	#download initial conditions
	#os.system('bash ./get_nam -d %s %s' %(rundate,args.cycle))
	#subprocess.Popen(['./get_nam','-d %s' %rundate, '%s' %args.cycle], shell=True, executable="/bin/bash")
	
	#run wps

	
