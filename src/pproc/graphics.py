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
import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
import cartopy.feature as cfeature

#turn off font warnings for logging
logging.getLogger('matplotlib.font_manager').disabled = True

### Functions ###

def make_poe_cmap():
	'''
	Create a colormap for POE
	'''
	colornames = ['palegoldenrod','chocolate','firebrick']

	#add transparancy
	poe_cm = colors.LinearSegmentedColormap.from_list('poe', colornames, N=256)
	poe_cmA = poe_cm(np.arange(poe_cm.N))
	alphas = list(np.linspace(0,1,5)) + [1] * 251
	poe_cmA[:,-1] = alphas	

	poe = colors.LinearSegmentedColormap.from_list('poe',poe_cmA)
	
	#save colormbar if ncessary - dumps strange log output
	#span = np.array([[0, 100]])
	#img = plt.imshow(span, cmap='YlOrBr')
	#plt.gca().set_visible(False)
	#cbar = plt.colorbar(orientation='horizontal', label='Probability of Exceedance (%)', ticks=np.arange(0, 101,10))
	#plt.savefig('colorbar_POE.png', dpi=100, bbox_inches = 'tight', pad_inches = 0.1)
	plt.close()

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
		bounds = [0, 39, 89, 139, 352, 527, 1000]
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
	alphas = list(np.linspace(0,1,5)) + [1] * 195
	cma[:,-1] = alphas

	#combine into a new colormap with transparancy
	aqi = colors.LinearSegmentedColormap.from_list('aqi',cma)
	norm = colors.BoundaryNorm(lvls, aqi.N)	

	#save colormap - for some reason prodcues a massive log dump
	cmplot = colors.LinearSegmentedColormap.from_list('aqi', colornames, N=len(bounds)-1)

	span = np.array([[0, bounds[-1]]])
	#img = plt.imshow(span,cmap=aqi)
	img = plt.imshow(span, cmap=cmplot)
	plt.gca().set_visible(False)
	cbar = plt.colorbar(orientation='horizontal', extend='max', label=clabel, ticks=np.arange(0, max(bounds),max(bounds)/(len(bounds)-1)))
	cbar.ax.set_xticklabels(bounds[:-1]) 
	plt.savefig('colorbar_{}.png'.format(pollutant),bbox_inches = 'tight', pad_inches = 0.1, dpi=200)
	plt.close()

	return aqi, norm

def make_ci_contours(nc_path, pollutant, cz, fmt, unit, leaflet):
	'''
	Create crude (qualitative) contours of column-integrated smoke, for user-defined layers cz
	'''
	logging.info('...creating column-integrated contours for: {}'.format(pollutant))

	#open netcdf file
	ds = nc.Dataset(nc_path)

	#get readable time dimension
	tdim = get_tdim(ds)

	#get the needed variable
	converted_fields = ds.variables[pollutant][:,:,:,:]

	#integrate over all layers to get total column mass
	#NOTE units are not appropriate for quantitative comparison
	ci_con = []
	#if there is a deposition layer, exclude
	if cz[0] == 0:
		mass_layers = cz[1:]
		deposition = 1
	else:
		mass_layers = cz.copy()
		deposition = 0
	#loop through remaining layers
	for iZ,z in enumerate(mass_layers):
		layer_tot = converted_fields[:,deposition+iZ,:,:] * z
		ci_con.append(layer_tot)
	cum_mass = np.sum(np.array(ci_con), axis = 0)		

	#loop through all frames, smoothing and saving
	for t,time in enumerate(tdim):
		
		if leaflet:
			ctr1 = plt.contourf(cum_mass[t,:,:],cmap='copper', origin='lower', levels=[5000,1e20], vmin=5000, vmax=1e100,alpha=0.05)
			ctr2 = plt.contourf(cum_mass[t,:,:],cmap='copper', origin='lower', levels=[1000,1e20], vmin=1000, vmax=1e100,alpha=0.05)
			ctr3 = plt.contourf(cum_mass[t,:,:],cmap='copper', origin='lower', levels=[10,1e20],  vmin=10, vmax=1e100,alpha=0.08)

			#hide all padding, margins and axes
			plt.axis('off')
			plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
			plt.margins(0,0)
			plt.gca().xaxis.set_major_locator(plt.NullLocator())
			plt.gca().yaxis.set_major_locator(plt.NullLocator())
			plt.savefig('./ci_{}.{}'.format(time,fmt), transparent=True, bbox_inches = 'tight', pad_inches = 0, dpi=200)
			plt.close()
		else:
			plt.figure()
			ax = plt.axes(projection=ccrs.PlateCarree())
			#TODO FINISH THIS	

	return

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


def make_con_plots(nc_path, pollutant, fmt, unit, plot_settings):
	'''
	Create surface concentration plots for all available timesteps
	'''
	logging.info('...creating surface concentration plots for: {}'.format(pollutant))

	leaflet = plot_settings['leaflet']
	smooth = plot_settings['smooth']

	#open netcdf file
	ds = nc.Dataset(nc_path)

	#get readable time dimension
	tdim = get_tdim(ds)

	#get bounds
	lons, lats = ds.variables['longitude'][:], ds.variables['latitude'][:]
	bounds = [np.min(lons), np.max(lons),np.min(lats), np.max(lats)]

	#get colormap
	aqi, norm = make_aqi_cmap(pollutant)

	#get fields
	logging.debug('...REMINDER: first vertical layer is assumed to be deposition only, extracting second layer')
	converted_fields = ds.variables[pollutant][:,1,:,:]
	
	#loop through all frames, smoothing and saving
	for t,time in enumerate(tdim):
		if smooth:
			con_frame = gaussian_filter(converted_fields[t,:,:], sigma=1)
		else:
			con_frame = converted_fields[t,:,:]

		if leaflet:
			img = plt.imshow(con_frame,cmap=aqi, origin='lower', norm = norm)
			#hide all padding, margins and axes
			plt.axis('off')
			plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
			plt.margins(0,0)
			plt.gca().xaxis.set_major_locator(plt.NullLocator())
			plt.gca().yaxis.set_major_locator(plt.NullLocator())
			plt.savefig('./{}_{}.{}'.format(pollutant,time,fmt), transparent=True, bbox_inches = 'tight', pad_inches = 0, dpi=200)
			plt.close()
		else:
			stamen_terrain = cimgt.Stamen(desired_tile_form='L', style='terrain-background')
			fig = plt.figure()
			ax = plt.axes(projection=ccrs.PlateCarree())
			ax.add_image(stamen_terrain, 7, cmap='gray',alpha=0.4,zorder=2)
			ax.add_feature(cfeature.OCEAN,color='white',zorder=3)
			im = ax.imshow(con_frame, origin='lower',cmap=aqi,norm=norm, extent=bounds, transform=ccrs.PlateCarree())
			ax.set_extent(bounds, crs=ccrs.Geodetic())
			gl = ax.gridlines(crs=ccrs.PlateCarree(),draw_labels=True,linewidth=0.5, color='gray', alpha=0.5, linestyle='--',zorder=10)
			gl.top_labels = False
			gl.right_labels = False
			ax.coastlines(zorder=4)
			plt.title(f'ENSEMBLE MEAN {pollutant} CONCENTRATION | {time}', fontsize=10)
			plt.colorbar(im, label = f'{pollutant} concentration ({unit[1]})', fraction=0.05, pad = 0.07, orientation = 'horizontal', extend='max')
			plt.tight_layout()
			plt.savefig('./{}_{}.{}'.format(pollutant,time,fmt),dpi=200)
			plt.close()

	return


def make_poe_plots(nc_prefix, pollutant, fmt, plot_settings):
	'''
	Create surface POE plots
	'''
	
	logging.info('...creating surface POE plots for: {}'.format(pollutant))
	
	leaflet = plot_settings['leaflet']
	smooth = plot_settings['smooth']	

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

		#get bounds
		lons, lats = ds.variables['longitude'][:], ds.variables['latitude'][:]
		bounds = [np.min(lons), np.max(lons),np.min(lats), np.max(lats)]
		
		#deal with Hysplit's weird naming: -p1 has keys CM00 etc, -pX uses pollutnat as key
		logging.debug('...REMINDER: first vertical layer is assumed to be deposition only, extracting second layer')
		try:
			poe_field = ds.variables[hys_keys[i]][:,1,:,:]
		except:
			poe_field = ds.variables[pollutant][:,1,:,:]

		#loop through all frams with smoothing
		for t,time in enumerate(tdim):
			if smooth:
				poe_frame = gaussian_filter(poe_field[t,:,:], sigma=2)
			else:
				poe_frame = poe_field[t,:,:]

			if leaflet:
				img = plt.imshow(poe_frame, cmap=poe, vmin=0, vmax=100, origin='lower')
				#hide all padding, margins and axes
				plt.axis('off')
				plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
				plt.margins(0,0)
				plt.gca().xaxis.set_major_locator(plt.NullLocator())
				plt.gca().yaxis.set_major_locator(plt.NullLocator())
				plt.savefig('./{}_{}_{}.{}'.format(pollutant,tag,time,fmt), transparent=True, bbox_inches = 'tight', pad_inches = 0, dpi=200)
				plt.close()
			else:
				stamen_terrain = cimgt.Stamen(desired_tile_form='L', style='terrain-background')
				fig = plt.figure()
				ax = plt.axes(projection=ccrs.PlateCarree())
				ax.add_image(stamen_terrain, 7, cmap='gray',alpha=0.4,zorder=2)
				ax.add_feature(cfeature.OCEAN,color='white',zorder=3)
				im = ax.imshow(poe_frame, origin='lower',cmap=poe, extent=bounds,vmin=0, vmax=100, transform=ccrs.PlateCarree())
				ax.set_extent(bounds, crs=ccrs.Geodetic())
				gl = ax.gridlines(crs=ccrs.PlateCarree(),draw_labels=True,linewidth=0.5, color='gray', alpha=0.5, linestyle='--',zorder=10)
				gl.top_labels = False
				gl.right_labels = False
				ax.coastlines(zorder=4)
				plt.title(f'POE {pollutant} {tag} | {time}', fontsize=10)
				plt.colorbar(im, label = f'probability of exceedance (%)', fraction=0.05, pad = 0.07, orientation = 'horizontal')
				plt.tight_layout()
				plt.savefig('./{}_{}_{}.{}'.format(pollutant,tag,time,fmt),  dpi=200)
				plt.close()
