#!/usr/bin/python3.7

#This script pulls vent thermal image from HVO and determines source area and temperature

__date__ = 'June 2022'
__author__ = 'Nadya Moisseeva (nadya.moisseeva@hawaii.edu)'

import requests
import datetime as dt
import logging
import json
import os
import glob
import pandas as pd
import numpy as np
from set_vog_env import *
from bs4 import BeautifulSoup
import pymatreader as mat

#logging.getLogger("requests").setLevel(logging.ERROR)

### MAKE SURE TO RESENT TEMP AND AREA (set to None) BEFORE DOING ANYTHING ###



### Inputs ###
#url = 'https://hvo-api.wr.usgs.gov/api/so2emissions?channel=SUMDFW&starttime='
url = 'https://hvovalve.wr.usgs.gov/cams/data/F1cam/images/mat/'
#ext = 'mat'


### Functions ###
def get_dir_listing(url,keypath,ext=''):
	'''
	Get a listing of all files in hvo directory
	'''
	login = read_config(keypath)
	page = requests.get(url,auth=(login['hvo']['user'],login['hvo']['pwd']))
	if page.ok:
		soup = BeautifulSoup(page.text,'html.parser')
		listing = [url + '/' + node.get('href') for node in soup.find_all('a') if node.get('href').endswith(ext)]
		
		return listing
	else:
		return logging.crititcal('ERROR: Cannot reach HVO server. Continuing with whatever data is available locally.')


def download_images(listing, keypath, flir_path):
	'''
	Download all images and save to disk
	'''
	login = read_config(keypath)
	for item in listing:
		response = requests.get(item,auth=(login['hvo']['user'],login['hvo']['pwd']))
		#save file data to local disk
		filename = os.path.basename(item)
		logging.debug(f'...downloading thermal image {filename}')
		savepath = os.path.join(flir_path, filename)
		if os.path.exists(savepath):
			logging.debug('WARNING: file already exists, skipping...')
		else:
			with open(savepath, 'wb') as file:
				file.write(response.content)

	return

def get_nearest_image(source, hr):
	'''
	Get the nearest file for each forecast hour
	'''
	#get the timestamp of the current forecast step
	fc_date = dt.datetime.strptime(os.environ['forecast'] + '+0000', '%Y%m%d%H%z')
	fcst_hr = fc_date + dt.timedelta(hours=hr)
 
	#get a listing of availble files and convert to a list of datetimes
	image_dirlist = os.path.join(source['flir_path'], '*.mat')
	local_images = glob.glob(image_dirlist)
	
	img_dates = []
	for img in local_images:
		img_name = os.path.split(img)[-1]
		img_dt_str = img_name.split('_')[0]
		# convert to date, assuming filenames are in HST
		img_dt = dt.datetime.strptime(img_dt_str+'-1000','%Y%m%d%H%M%S%z')
		img_dates.append(img_dt)

	
	#get closest availble image
	nearest = min(img_dates, key=lambda x: abs(x - fc_date))
	nearest_img_name = dt.datetime.strftime(nearest,'%Y%m%d%H%M%S_F1.mat')
	if (fcst_hr - nearest) > dt.timedelta(days = 3):
		logging.warning(f'WARNING: time mismatch with thermal image {nearest_img_name} is more than 3 days')

	#get data from file as array
	img_path = os.path.join(source['flir_path'],nearest_img_name)
	flir_data = mat.read_mat(img_path)['img']

	return flir_data


def get_lava_temperature(flir_data):
	'''
	Get mean temperature of all active lava pixels
	'''
	#mask everything below active-lava threshold (set in inputs in the beginning of this module)
	active_lava = flir_data[:]
	active_lava[active_lava<300] = None

	#get nanmean
	mean_lava_temperature = np.nanmean(active_lava)

	return mean_lava_temperature

def get_lava_area(flir_data):
	'''
	Get total area of all active lava pixels
	'''
	#TODO
	#THIS IS JUST A PLACEHOLDER FOR NOW
	area = 50000	

	return area


### MAIN SCRIPT ###

def main(source):
	'''
	Main script for extracing data from thermal images
	'''

	#read user settings
	json_data = read_run_json()	
	keypath = json_data['user_defined']['keys']

	#downlaod mat files
	listing = get_dir_listing(url,keypath,'mat')
	download_images(listing, keypath, source['flir_path'])	

	#get data for each hour
	#for future/missing times, assume closts/most recent values
	temperature, area = [], []
	for hr in range(int(os.environ['runhrs'])):
		#locate most relevant file and read data
		flir_data = get_nearest_image(source, hr)
		#extract temperature
		temperature.append(get_lava_temperature(flir_data))
		#extract area
		area.append(get_lava_area(flir_data))
	
	source['temperature'] = temperature
	source['area'] = area

	return source

if __name__ == '__main__':
        main(source)









'''

		obs_datetimes_utc = [dt.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S%z') for date in obs_dates]

		#use pandas to locate nearest record to emission start datetime and get index
		pdtime = pd.DatetimeIndex(obs_datetimes_utc)
		em_date = dt.datetime.strptime(os.environ['forecast']+'UTC', '%Y%m%d%H%Z') + dt.timedelta(hours=int(os.environ['spinup']))
		logging.debug('...emissions start hour in UTC is {}'.format(em_date))
		record_idx = pdtime.get_loc(em_date, method='nearest')


def main():
	#read user settings
	json_data = read_run_json()

	#get number of emissions sources
	num_src = len(json_data['user_defined']['emissions'])
	json_data['emissions'] = {}

	#get emissions for each source
	for iSrc in range(num_src):
		tag = 'src' + str(iSrc + 1)
		emis_settings = json_data['user_defined']['emissions'][tag]

		logging.debug('...getting emissions for {}:'.format(tag))

		#get emissions based on user preferences
		if emis_settings['input'] == 'hvo':
			#pull from hvo-api
			so2, obs_date = get_hvo_data(emis_settings['keys'])
			logging.info('...HVO emissions value: {} tonnes/day'.format(so2))
		elif emis_settings['input'] == 'manual':
			#assign user defined value
			so2 = emis_settings['rate']
			obs_date = 'manual update'
			logging.info('...manual emissions assignment requested: rate = {} tonnes/day)'.format(so2))
		else:
			logging.critical('ERROR: Emissions input not recognized. Availble options are: "hvo","manual"')

		#write to main json file
		json_data['emissions'][tag] = {'so2' : so2, 'obs_date': obs_date }

	#update run json
	update_run_json(json_data)

'''
