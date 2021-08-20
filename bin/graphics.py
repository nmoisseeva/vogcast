#!/usr/bin/python3.7
 
# Script for generating colormaps, plots and other graphics

__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="August 2021"

from set_vog_env import *
import logging
import netCDF4 as nc
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors
from scipy.ndimage import gaussian_filter
import datetime as dt

### Functions ###


def make_aqi_cmap(pollutant):
	'''
	Create a custom colormap corresponding to so2 aqi levels
	'''
 	
	#create a list of AQI levels to normlize colormap
	if pollutant.lower() =='so2':
		#so2 aqi is in ppm - ensure corerct conversion in config
		bounds = [0, 0.1, 0.2, 1, 3, 5, 100]
	elif pollutant.lower() =='so4':
		#so3 standards are in ug/m3 - ensure correct conversion in config
		bounds = [0, 12, 35, 55, 150, 250, 100]
	else:
		logging.error('ERROR: pollutant not recognized - {}. Available options: "so2", "so4"'.format(pollutant))	

	lvls = []
	for n, lvl in enumerate(bounds):
		try:
			lvls.extend(list(np.linspace(lvl,bounds[n+1],20, endpoint = False)))
		except:
			pass
      
	#make a custom colormap correspomding to AQI
	colornames = ['limegreen','yellow','orange','orangered','rebeccapurple','mediumorchid']
	cm = colors.LinearSegmentedColormap.from_list('aqi', colornames, N=200)
	norm = colors.BoundaryNorm(lvls, cm.N)	

	#add alpha for near-zero values
	cma = cm(np.arange(cm.N))
	alphas = list(np.linspace(0,1,10)) + [1] * 190
	cma[:,-1] = alphas

	#combine into a new colormap with transparancy
	aqi = colors.LinearSegmentedColormap.from_list('aqi',cma)
	norm = colors.BoundaryNorm(lvls, aqi.N)	
	
	logging.debug('...created colormap')
	return aqi, norm


def get_tdim(ds):
	'''
	Reformat serial datetime stamps from hysplit into readable format
	'''

	#extract dates and convert to datetime from serial format
	def serial_date_to_string(srl_datetime):
		dtstamp = dt.datetime(1970,1,1,0) + dt.timedelta(srl_datetime)
		return dtstamp.strftime("%Y%m%d%H")

	tdim = []
	for item in ds.variables['time']:
		tdim.append(serial_date_to_string(float(item.data)))
	
	return tdim


def make_con_plots(nc_path, pollutant, fmt, conv):
	'''
	Create surface concentration plots for all available timesteps
	'''
	logging.info('...creating surface concentration plots for: {}'.format(pollutant))

	#open netcdf file
	ds = nc.Dataset(nc_path)

	#get readable time dimension
	tdim = get_tdim(ds)

	#get colormap
	aqi, norm = make_aqi_cmap(pollutant)

	#convert dataset fields to correct units
	converted_fields = ds.variables[pollutant][:,0,:,:] * conv 

	#loop through all frames, smoothing and saving
	for t,time in enumerate(tdim):
		logging.debug('plot number: {}'.format(t))
		smooth_con = gaussian_filter(converted_fields[t,:,:], sigma=2)
		img = plt.imshow(smooth_con,cmap=aqi, origin='lower', norm = norm)
		#hide all padding, margins and axes
		plt.axis('off')
		plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
		plt.margins(0,0)
		plt.gca().xaxis.set_major_locator(plt.NullLocator())
		plt.gca().yaxis.set_major_locator(plt.NullLocator())
		plt.savefig('./{}_{}.{}'.format(pollutant,time,fmt), transparent=True, bbox_inches = 'tight', pad_inches = 0, dpi=200)
		#plt.savefig('./{}.{}'.format(time,fmt), dpi=200, bbox_inches = 'tight', pad_inches = 0)
		plt.close()
	logging.debug('...created plots')
	return

