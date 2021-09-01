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

def make_poe_cmap():
	'''
	Create a colormap for POE
	'''
	#add transparancy
	poe_cm = plt.cm.YlOrBr
	poe_cmA = poe_cm(np.arange(poe_cm.N))
	alphas = list(np.linspace(0,1,10)) + [1] * 246
	poe_cmA[:,-1] = alphas	

	poe = colors.LinearSegmentedColormap.from_list('poe',poe_cmA)
	
	#save colormbar if ncessary - dumps strange log output
	#span = np.array([[0, 100]])
	#img = plt.imshow(span, cmap='YlOrBr')
	#plt.gca().set_visible(False)
	#cbar = plt.colorbar(orientation='horizontal', label='Probability of Exceedance (%)', ticks=np.arange(0, 101,10))
	#plt.savefig('colorbar_POE.png', dpi=100, bbox_inches = 'tight', pad_inches = 0.1)

	return poe

def make_aqi_cmap(pollutant):
	'''
	Create a custom colormap corresponding to aqi levels
	'''
 	
	#create a list of AQI levels to normlize colormap
	if pollutant.lower() =='so2':
		#so2 aqi is in ppm - ensure corerct conversion in config
		bounds = [0, 0.1, 0.2, 1, 3, 5, 100]
		clabel = r'SO$_2$ (ppm)'
	elif pollutant.lower() =='so4':
		#so4 standards are in ug/m3 - ensure correct conversion in config
		bounds = [0, 12, 35, 55, 150, 250, 1000]
		clabel = r'SO$_4$ ($\mu$g/m$^3$)'
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

	#save colormap - for some reason prodcues a massive log dump
	#cmplot = colors.LinearSegmentedColormap.from_list('aqi', colornames, N=len(bounds)-1)
	#span = np.array([[0, bounds[-1]]])
	#img = plt.imshow(span, cmap=cmplot)
	#plt.gca().set_visible(False)
	#cbar = plt.colorbar(orientation='horizontal', extend='max', label=clabel, ticks=np.arange(0, max(bounds),max(bounds)/(len(bounds)-1)))
	#cbar.ax.set_xticklabels(bounds[:-1]) 
	#plt.savefig('colorbar_{}.png'.format(pollutant),bbox_inches = 'tight', pad_inches = 0.1, dpi=200)

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
	#converted_fields = ds.variables[pollutant][:,0,:,:] * conv 
	converted_fields = ds.variables[pollutant][:,0,:,:]
	
	#loop through all frames, smoothing and saving
	for t,time in enumerate(tdim):
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
	return


def make_poe_plots(nc_prefix, pollutant, fmt):
	'''
	Create surface POE plots
	'''
	
	logging.info('...creating surface POE plots for: {}'.format(pollutant))
	
	#manually create tags to match HYSPLIT's very particular namting
	hys_keys = ['CM01', 'CM10', 'CM00']

	#get colormap
	poe = make_poe_cmap()

	#loop through thresholds
	for i in range(3):
		tag = 'lvl{}'.format(str(i+1))
		poe_file = nc_prefix + tag + '_' + pollutant + '.nc'
		

		#open netcdf file
		ds = nc.Dataset(poe_file)
		tdim = get_tdim(ds)
		
		#deal with Hysplit's weird naming: -p1 has keys CM00 etc, -pX uses pollutnat as key
		try:
			poe_field = ds.variables[hys_keys[i]][:,0,:,:]
		except:
			poe_field = ds.variables[pollutant][:,0,:,:]

		#loop through all frams with smoothing
		for t,time in enumerate(tdim):
			smooth_poe = gaussian_filter(poe_field[t,:,:], sigma=2)
			img = plt.imshow(smooth_poe, cmap=poe, vmin=0, vmax=100, origin='lower')
			#hide all padding, margins and axes
			plt.axis('off')
			plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
			plt.margins(0,0)
			plt.gca().xaxis.set_major_locator(plt.NullLocator())
			plt.gca().yaxis.set_major_locator(plt.NullLocator())
			plt.savefig('./{}_{}_{}.{}'.format(pollutant,tag,time,fmt), transparent=True, bbox_inches = 'tight', pad_inches = 0, dpi=200)
			plt.close()
	
	return
