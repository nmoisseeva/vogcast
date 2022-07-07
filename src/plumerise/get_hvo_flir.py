#!/usr/bin/python3.7

#This script pulls vent thermal image from HVO and determines source area and temperature
#This script contains adaptation of Matt Patrick's methods (USGS) for calculatting thermal image pixel area

__date__ = 'June 2022'
__author__ = 'Nadya Moisseeva (nadya.moisseeva@hawaii.edu)'

import requests
import datetime as dt
import logging
import json
from math import cos, sin, tan, atan, radians
import os
import glob
import time
from copy import deepcopy
import pandas as pd
import numpy as np
from set_vog_env import *
from bs4 import BeautifulSoup
import pymatreader as mat



### Inputs ###
url = 'https://hvovalve.wr.usgs.gov/cams/data/F1cam/images/mat/'
url_lava = 'https://hvo-api.wr.usgs.gov/api/v1/laserlavalevel/'
channels_lava = {'channel': 'HMM','rank':1, 'series': ['sealevel']} 	#this is set to summit vent only
Tactive = 300 		#threshold for "active lava" (deg C)


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
		#TODO add two-min wait
		return logging.crititcal('ERROR: Cannot reach HVO server. Continuing with whatever data is available locally.')


def download_images(listing, keypath, flir_path):
	'''
	Download all images and save to disk
	'''

	login = read_config(keypath)
	for item in listing:
		#allow a 2min wait to avoid issues during server update times (~58min after each hour)
		try:
			response = requests.get(item,auth=(login['hvo']['user'],login['hvo']['pwd']))
		except:
			logging.warning('...HVO server not available. Retrying in 2 minutes')
			time.sleep(2)
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



def get_lake_level(keypath):
	'''
	Get the lava lake level in m ASL from HVO-API
	'''
	#format date for api
	fc_date = dt.datetime.strptime(os.environ['forecast'], '%Y%m%d%H')
	#fc_hr = fc_date + dt.timedelta(hours = (hr))
	runhrs = int(os.environ['runhrs'])
	hr_range = pd.date_range(fc_date, fc_date + dt.timedelta(hours = runhrs), freq = '1H')
	start_hst= fc_date + dt.timedelta(hours = - 10)
	end_hst = fc_date + dt.timedelta(hours = (runhrs - 10))

	api_call = url_lava + dt.datetime.strftime(start_hst,'%Y%m%d%H%M%S') + '/' + dt.datetime.strftime(end_hst,'%Y%m%d%H%M%S')
	logging.debug(f'...pulling lake level data from: {api_call}')

	login = read_config(keypath)
	response = requests.post(api_call,auth=(login['hvo']['user'],login['hvo']['pwd']),data=json.dumps(channels_lava))
	
	#if theres no data, set to default
	response = response.json()
	if response['nr']==0:
		lake_level = [870] * runhrs
		logging.warning(f'WARNING: Did not find lava lake data for the given time. Defaulting to {lake_level} m ASL')
	else:
		lake_level = []
		#find closest time and get lake data
		dtstamps = [dt.datetime.strptime(i['date'],'%Y-%m-%dT%H:%M:%S%z') for i in response['results']]
		pdtime = pd.DatetimeIndex(dtstamps)

		for h in hr_range:
			record_idx = pdtime.get_loc(h, method='nearest')
			obs_level = int(response['results'][record_idx]['sealevel'])
			lake_level.append(obs_level)
			obs_date = response['results'][record_idx]['date']
			logging.info(f'...Lava lake level on {obs_date}: {obs_level}m ASL')


	return lake_level


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
	active_lava = deepcopy(flir_data)
	active_lava[active_lava < Tactive] = None

	#get nanmean
	mean_lava_temperature = int(np.nanmean(active_lava))
	
	logging.info(f'...mean lava temperature: {mean_lava_temperature} deg C')

	return mean_lava_temperature


def get_pixel_coordinates(lake_level, pY, pX):
	'''
	Get horizontal coordinates of pixel relative to camera location
	'''
	dZ = 1142		#camera heigth (m ASL)
	fovY, fovX = 33.75, 45	#camera FOV (vertical and horizontal)
	dipY = 23.7		#camera dip angle
	dimY, dimX = 640, 480	#image size in pixels

	mZ = dZ - lake_level 
	#get angle below horizon
	top = dipY - .5*fovY

	#get vertical and horizonal focal lengths in pixels
	ctrY, ctrX = (dimY / 2.), (dimX / 2.)
	Oy, Ox  = radians(0.5 * fovY), radians(0.5 * fovX)
	ly = ctrY / tan(Oy) 
	lx = ctrX / tan(Ox)

	#recall that images are flipped on the sensor
	#deal with vertical projection
	dy = abs(ctrY - pY)
	theta = atan(dy/ly)
	if pY <= ctrY:
		theta = -1 * theta
	gamma = radians(top) + Oy + theta
	mY = mZ / tan(gamma)
	L = mZ / sin(gamma)
	
	#deal with horizonal projection
	dx = abs(ctrX- pX)
	phi = atan(dx/lx)
	mX = L * sin(phi)
	if pX <= ctrX:
		mX = -1 * mX
	
	#logging.debug(f'...pY = {pY}, pX = {pX}') 
	#logging.debug(f'...mY = {mY} m; L = {L} m, mX = {mX} m  ')

	return mX, mY
	
def get_pixel_utm_coordinates(lake_level, pxY, pxX):
	'''
	Calculate area of the pixel by georeferencing the coordinates and lake height
	-adapted from Matt Patric
	-THIS MIGHT HAVE ERRORS, USE WITH CAUTION!!!
	-the angles are misnamed (around if statements)
	-for better names of other variables refer to the get_pixel_coordinates function above
	'''

	camX, camY, camH = 259336, 2147516, 1141        #F1 camera coordinates in meters
	camFOVx, camFOVy = 45, 33.75                    #F1 horizontal and vertical FOV angles, assuming 4:3 pixel ratio
	camDip = 23.7                                   #F1 camera dip angle
	dimX, dimY = 640, 480                           #F1 image dimensions in pixels
	alpha = 93                                      #F1 viewing azimuth (degrees)

	#get sensor height above lake (in meteres) and top angle (degrees)
	h = camH - lake_level
	topangle = camDip - 0.5 * camFOVy

	#get vertical and horizonal focal lengths in pixels
	ctrY, ctrX = (dimY / 2.), (dimX / 2.) 		#center pixel
	half_FOVy_r, half_FOVx_r = radians(0.5 * camFOVy), radians(0.5 * camFOVx)
	foc_Y_px = ctrY / tan(half_FOVy_r)
	foc_X_px = ctrX / tan(half_FOVx_r)

	#get vertical coordinate of pixel in meters
	offsetY = abs(ctrY - pxY) 	#distance from center in pixels
	thetaY = atan(offsetY/foc_Y_px)
	if pxY <= ctrY:
		theta_net = half_FOVy_r - thetaY
	elif pxY > ctrY:
		theta_net = thetaY + half_FOVy_r
	thetaYtilt = radians(topangle) + theta_net
	hY = h/tan(thetaYtilt)
	sY = h/sin(thetaYtilt)
	logging.debug(f'pY = {pxY}, pX = {pxX}')

	#get horizontal coordinate of pixel in meteres
	offsetX = abs(ctrX - pxX)
	phi_fov = atan(offsetX/foc_X_px)
	if pxX <= ctrX:
		phi = -1 * phi_fov
	elif pxX > ctrX:
		phi = phi_fov
	yy = hY
	xx = sY * tan(phi)

	#viewing azimuth of camera
	azimuth = radians(-alpha)
	es = xx * cos(azimuth) - yy * sin(azimuth)
	no = yy * cos(azimuth) + xx * sin(azimuth)

	#get final georeferenced easting and northing
	E = es + camX
	N = no + camY

	return E, N 


def get_lava_area(flir_data, lake_level):
	'''
	Get total area of all active lava pixels
	'''
	
	#mask everything below active-lava threshold, this time with 0 to use numpy nonzero
	active_lava = deepcopy(flir_data)
	active_lava[active_lava < Tactive] = 0
	

	#get list of index-pairs that are non-zero
	active_pixels = np.nonzero(active_lava)

	pixel_areas = []
	for pY, pX in zip(*active_pixels):
		x1, y1 = get_pixel_coordinates(lake_level, pY-.5, pX-.5)
		x2, y2 = get_pixel_coordinates(lake_level, pY-.5, pX+.5)
		x3, y3 = get_pixel_coordinates(lake_level, pY+.5, pX+.5)
		x4, y4 = get_pixel_coordinates(lake_level, pY+.5, pX-.5)
		X = [x1, x2, x3, x4]
		Y = [y1, y2, y3, y4]
		#get area using Shoeslace formula
		px_area = 0.5*np.abs(np.dot(X,np.roll(Y,1))-np.dot(Y,np.roll(X,1)))
		pixel_areas.append(px_area)
	area = int(sum(pixel_areas))
	logging.info(f'...total area of active lava lake: {area} m2')	

	return area


### MAIN SCRIPT ###

def main(source):
	'''
	Main script for extracing data from thermal images
	'''

	#read user settings
	json_data = read_run_json()	
	keypath = json_data['user_defined']['keys']

	#downlaod mat files if running as a forecast, otherwise will use images in flir directory
	if os.environ['runtype'] == 'realtime':
		listing = get_dir_listing(url,keypath,'mat')
		download_images(listing, keypath, source['flir_path'])	


	#get data for each hour
	#for future/missing times, assume closts/most recent values
	temperature, area = [], []
	lake_level = get_lake_level(keypath)
	for hr in range(int(os.environ['runhrs'])):
		#locate most relevant file and read data
		flir_data = get_nearest_image(source, hr)
		#TODO add logic to test image and make sure temperatures are reasonable
		#extract temperature
		temperature.append(get_lava_temperature(flir_data))
		#extract area
		area.append(get_lava_area(flir_data, lake_level[hr]))
	
	source['temperature'] = temperature
	source['area'] = area

	return source

if __name__ == '__main__':
        main(source)


