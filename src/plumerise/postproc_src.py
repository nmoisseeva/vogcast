#post processing functions for cwipp run 


__author__="Nadya Moisseeva (nadya.moisseeva@hawaii.edu)"
__date__="October 2021"

import os
import sys
from pathlib import Path
import logging
import glob
from set_vog_env import *
from sklearn.neighbors import KDTree
from scipy.interpolate import interp1d
import pandas as pd
import numpy as np


 ### Fucntions ###
def compile_output(outdict, plume):
        '''
        Fill useful variables for output
        '''
        outdict['zCL'] = plume.zCL
        outdict['zi'] = plume.zi
        outdict['I'] = plume.I
        outdict['penetrative'] = plume.penetrative
        outdict['Z'] = plume.interpZ.tolist()
        outdict['Cnorm'] = plume.profile

        return outdict


def fit_layers(cwippout, z, source):
	'''
	Approximates the cwipp-generated profile with user-defined number of points
	'''

	output = {}

	#loop through sources
	for tag in cwippout.keys():
		lvls = source[tag]['levels']
		logging.debug('...number of vog levels requested by user for {}: {}'.format(tag, lvls))
		output[tag] = {}
		
		#loop through hours
		for dtime in cwippout[tag].keys():

			#get the current profile
			profile = cwippout[tag][dtime]	

			#find the "top" of the plume: last level with at least 1% 
			ztop_idx = next(i for i,val in enumerate(reversed(profile)) if i >= 0.01) 
			logging.debug('index {}; value: {}'.format(ztop_idx, profile[ztop_idx]))
	



