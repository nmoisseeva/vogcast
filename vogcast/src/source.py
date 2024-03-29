#!/usr/bin/python3.7
 
#Script extacts profile data from wrf meteorology and parameterizes vertical distribution of emissions

__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="July 2021"

import os
import sys
import logging
#import wrf
from set_vog_env import *
import glob
import plumerise.preproc_src as prepcwipp
import plumerise.cwipp as cwipp
import matplotlib.pyplot as plt #NOTE this is for testing only
import datetime as dt


#turn off font warnings in logging
logging.getLogger('matplotlib.font_manager').disabled = True

### Inputs ####
# Some of these are specific to selected options (may or not be used in a given workflow)
emit_levels = 5 		#number of layers to approximate veritical emissions distribution with (CWIPP)


 ### Fucntions ###
def locate_source():
	'''
	Get source location met grid
	'''
	#locate the most high-resolution domain
	wrf_rundir = os.path.join(os.environ['run_path'],'wrf')
	nc_file = glob.glob(wrf_rundir + '/wrfout_d0' + str(os.environ['max_dom']) + '*')	
	logging.debug('Plumerise met: %s ' %nc_file)

	#get location
	#TODO add functionality for multiple sources
	lat, lon = os.environ['lat'], os.environ['lon']
	x, y = wrf.ll_to_xy(nc_file, lat, lon, timeidx=wrf.ALL_TIMES)

	return nc_file, x, y
"""
#THIS IS LEGACY CODE FOR REFERENCE ONLY (will not work edit CONTROL lines properly)
	
def static_line(source, emissions):
	#Performs static legacy ops routine for defining an emission source line:
	#	-assumes fixed BL day and night of 700m
	#	-fairly strange vertical level selections
	#	-uses undocumented fudge factors
	#	-must be ran with the following CONTROL settings: 1500m mixing depth, isobaric vertical motion
	### inputs (historic ops settings) ###
	bias = 0.2314 * 1.458e7 	#obscure historic bias correction factors
	distribution = [0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.02, 0.9] 	#fixed vertical distribution
	levels = [50, 150, 300, 350, 400, 450, 550, 600, 650, 700] 		#no idea why

	### main ###
	#distribute the emissions vertically
	lines = ''
	lat, lon, area = str(source['lat']), str(source['lon']), str(source['area'])
	for i in range(len(levels)):
		so2 = int(distribution[i] * bias * emissions['so2'])
		lines = lines + lat  + ' ' + lon + ' ' + str(levels[i]) + ' ' + str(so2) + ' ' + area + '\\n'
	logging.debug('Distributing emissions vertically...\n%s' %lines)

	#remove newline character from the last line
	lines = lines[:-2]
	
	#append main run json with vertical line source data
	json_data = read_run_json()
	json_data['plumerise'] = {'sources': lines, 'src_cnt' : len(levels)}
	update_run_json(json_data)

	return
"""

def static_area(source, emissions,iSrc):
	'''
	"Low buoyancy" approach for a single level area source
	'''
	### inputs (conversion of emisisons ###
	to_mg_per_hr = (1./24) * 1e9 	#converstion factor from tonnes/day to mg/hr

	### main ###
	lat, lon, height, area = str(source['lat']), str(source['lon']), str(source['height']),  str(source['area'])
	so2 = str(to_mg_per_hr * emissions['so2'])

	lines = lat + ' ' + lon + ' ' + height + ' ' + so2 + ' ' + area

	#append main run json with area source data
	#json_data = read_run_json()
	#if iSrc == 0:
	#	json_data['plumerise'] = {'sources': lines, 'src_cnt' : 1}
	#else:
	#	json_data['plumerise']['sources'] = json_data['plumerise']['sources'] + '\\n' + lines
	#	json_data['plumerise']['src_cnt'] = iSrc + 1
	#update_run_json(json_data)

	#get source count and lines for CONTROL file
	if iSrc == 0:
		#json_data['plumerise'] = {'sources': lines, 'src_cnt' : 1}
		src_lines = lines
	else:
		src_lines = '\\n' + lines
		#json_data['plumerise']['sources'] = json_data['plumerise']['sources'] + '\\n' + lines
		#json_data['plumerise']['src_cnt'] = iSrc + 1
	

	return src_lines

def run_cwipp():
	'''
	Run dynamic plume rise model
	'''

	#-------this is a bias fit default from Moisseeva 2021----
	biasFit =  [0.9195, 137.9193]
	#---------------------------------------------------------

	#load input data
	cwippinputs = read_json('cwipp_inputs.json')

	#set up output dictionary
	output = {}

	#extra high-resolution output for research
	#TODO: remove
	hires_out = {}

	#loop through available timestamps
	for tag in cwippinputs.keys():
		logging.debug(f'Processing source: {tag}')
		output[tag] = {}
		
		hires_out[tag] = {}
		
		#loop through all hours
		for dtime in cwippinputs[tag].keys():
			src = cwippinputs[tag][dtime]
		
			#run cwipp model
			plume = cwipp.Plume(tag)
			plume.get_sounding(src)
			plume.I = src['I']
			plume.iterate(biasFit)
			plume.classify()
			plume.get_uBL(src)
			plume.get_profile()
			output[tag][dtime] = {}
			output[tag][dtime]['fractions'] = plume.layer_fractions
			output[tag][dtime]['heights'] = plume.layer_heights
			logging.debug('...{}: estimated mean injection height is {:.1f} m'.format(dtime,plume.zCL))
	
			hires_out[tag][dtime] = {}
			hires_out[tag][dtime]['profile'] = plume.profile
			hires_out[tag][dtime]['interpZ'] = plume.interpZ.tolist()

			plt.figure()
			ax1 = plt.gca()
			ax1.set(xlabel='potential temperature (K)', ylabel='height (m)')
			l_sound = plt.plot(plume.sounding, plume.interpZ, color='C0', label='WRF sounding')
			l_zi = plt.axhline(y = plume.zi, ls='--', color='C0', label='broundary layer height')
			l_zCL = plt.axhline(y = plume.zCL, color='C1',ls=':', label='modelled injection height')
			ax2 = plt.twiny(ax1)
			l_cwipp = plt.plot(plume.profile, plume.interpZ, color='C1',label='modelled profile')
			plt.gca().set(xlabel='normalized concentration', ylabel='height [m]')
			plt.xlim(xmin=0)
			plt.legend([l_sound[0],l_zi,l_zCL,l_cwipp[0]],['WRF sounding','boundary layer height','modelled injection height','modelled vog profile'],loc=2)
			save_dir = os.path.join(os.environ['run_dir'],os.environ['forecast'],'plumerise')
			plt.savefig(save_dir + '/{}.png'.format(dtime))
			plt.close()
	write_json('cwipp_output.json',output)
	write_json('hires_output.json',hires_out)

	return

def generate_emitimes(vent,emissions):
	'''
	Create hysplit source files for time-varying emissions
	'''

	logging.info('Generating EMITIMES file for HYSPLIT')

	#format of EMITIMES file
	info_lines = 'YYYY MM DD HH DURATION(hhhh) #RECORDS\nYYYY MM DD HH MM DURATION(hhmm) LAT LON HGT(m) RATE(/h) AREA(m2) HEAT(w)\n'

	#read plumerise data
	cwippdata = read_json('cwipp_output.json')
	
	#string storage for control lines
	control_lines = ''

	#open write file$
	#TODO wipe old file$
	with open('../hysplit/EMITIMES', 'w') as emitimes:
		emitimes.write(info_lines)

		#EMITIMES wants all sources under one time block, our data is all times under single source block
		#pull the first tag (shouldn't matter cuz all times are the same)
		tags = list(cwippdata.keys())
		datetimes = cwippdata[tags[0]].keys()
		

		##loop through available timestamps
		#for tag in cwippdata.keys():
		#	logging.debug('...processing source: {}'.format(tag))

		#loop through emission cyles
		#for t, dtime in enumerate(cwippdata[tag].keys()):
		for t, dtime in enumerate(datetimes):
			#convert to datetime for convenience
			emitdate = dt.datetime.strptime(dtime, '%Y%m%d%H')
			spnp = int(os.environ['spinup'])			

			rec_cnt = int(emit_levels * 2 * len(tags))

			#generate block header			
			header = emitdate.strftime('%Y %m %d %H ') + f'0001 {rec_cnt} \n'
			emitimes.write(header)

			loc_lines = ''

			for tag in cwippdata.keys():
				for layer in range(emit_levels):
					# conversion of emisisons
					to_mg_per_hr = (1./24) * 1e9    #converstion factor from tonnes/day to mg/hr
					so2 = str(int(to_mg_per_hr * emissions[tag]['so2'] * cwippdata[tag][dtime]['fractions'][layer])) 

					#get height and location data as strings
					hgt = str(int(cwippdata[tag][dtime]['heights'][layer]))
					lat, lon, area = str(vent[tag]['lat']), str(vent[tag]['lon']), str(vent[tag]['area'][t+spnp])					

					#generate source lines for SO2 and SO4
					#TODO THIS IS SO HARDCODED!! FIX!!
					so2_line = emitdate.strftime('%Y %m %d %H ') + '00 0100 ' + lat + ' ' + lon  + ' ' + hgt  + ' ' + so2 + ' ' + area + ' 0\n'
					emitimes.write(so2_line)	
					so4_line = emitdate.strftime('%Y %m %d %H ') + '00 0100 ' + lat + ' ' + lon  + ' ' + hgt  + ' 0 ' + area + ' 0\n'
					emitimes.write(so4_line)
	
					#generate lines for hysplit CONTROL file
					loc_lines = loc_lines + lat + ' ' + lon + ' ' + hgt + ' ' + so2 + ' ' + area + '\\n'
				

		#update control lines
		control_lines = control_lines + loc_lines

	#count total number of source lines for control file
	src_cnt = len(cwippdata.keys()) * emit_levels

	#remove newline character from the last line
	control_lines = control_lines[:-2]

	#append main run json with area source data
	#json_data = read_run_json()
	#json_data['plumerise'] = {'sources': control_lines, 'src_cnt' : src_cnt}
	#json_data['vent'] = vent
	#update_run_json(json_data)


	return src_cnt, control_lines

def check_model_compatibility(json_data,tag):
	'''
	Check that the plume-rise model is compatible with other options selected
	'''
	pr_model = json_data['user_defined']['source'][tag]['pr_model']
	met_model = json_data['user_defined']['meteorology']['model']

	if (pr_model == 'cwipp') and (met_model not in ['wrf','prerun']):
		logging.critical('ERROR: "cwipp" plume-rise model currently requires WRF meteorology. Aborting!')
		sys.exit(1)		

	return



def main():
	'''
	Run plume rise/source model
	'''
	logging.info('=============SOURCE MODULE===========')
	
	#load main run json
	json_data = read_run_json()	

	#get number of sources
	num_src = len(json_data['user_defined']['source'])
	src_tags = json_data['user_defined']['source'].keys()

	logging.info('Running source model: {} emissions sources'.format(num_src))

	#storage lists for source counts and lines (eventually added to hysplit CONTROL file)
	hys_src_cnt = 0
	hys_src_lines = ''

	cwipp_done = 0

	emissions = json_data['emissions']
	
	#run source model for each emissions location
	#for iSrc in range(num_src):
	for iSrc, tag in enumerate(src_tags):
		#tag = 'src'+str(iSrc+1)
		source = json_data['user_defined']['source'][tag]
		#emissions = json_data['emissions'][tag]

		#call the selected plume rise approach
		logging.info('{} plumerise model: {}'.format(tag,source['pr_model']))
		check_model_compatibility(json_data,tag)
		
		if source['pr_model']=='static_area':
			#standard hysplit area source option
			lines = static_area(source, emissions[tag], iSrc)
	
			#update vent info for control file
			hys_src_cnt = hys_src_cnt + 1
			hys_src_lines = hys_src_lines + lines

		elif source['pr_model']=='cwipp':
			#dynamic plume rise model adapted from widlfire
			#if any of the sources use cwipp, run the preprocessor (but only the first time)
			if cwipp_done==0:
				vent = prepcwipp.main()
				run_cwipp()
				src_cnt, lines = generate_emitimes(vent,emissions)
				cwipp_done = 1
				json_data['vent'] = vent

				#update vent info for control file
				hys_src_cnt = hys_src_cnt + src_cnt
				hys_src_lines = hys_src_lines + lines
			else:
				logging.info('...completed on previous step')
		else:
			logging.critical('ERROR: Plume-rise model not recognized. Available options are: "static_area" and "cwipp". Aborting!')
			sys.exit(1)

	#append main run json with vent data data
	json_data['plumerise'] = {'sources': hys_src_lines, 'src_cnt' : hys_src_cnt}
	update_run_json(json_data)


	return 

 ### Main ###

if __name__ == '__main__':
	main()		
