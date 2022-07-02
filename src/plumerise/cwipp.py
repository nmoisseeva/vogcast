import numpy as np
from scipy.interpolate import interp1d
from scipy.optimize import fsolve
import logging

#---------default CWIPP parameters-------
# do not change these settings unless sure

g = 9.81		#gravity constant

#vertical level settings
dz = 20             	#height interpolation step for analysis (in meteres)
zmax = 10000        	#max height m AGL for analysis
BLfrac = 0.75       	#fraction of BL height to use as reference height z_s (default = 0.75)

#-----------end of parameters-----------

class Plume:
	"""
	Parent Plume class.

	Attributes
	----------
	name : str
		plume name
	zi : float
		boundary layer height [m]
	zs : float
		refernce height (zi * BLfrac) [m]
	sounding: ndarray
		vertical potential temperature sounding on interpolated analysis levels [K]
	THs : float
		ambient potential tempreature at reference height zs [K]
	I : float
		fireline intensity parameter [K m2 s-1]
	wf : float
		characteristic fire velocity scale [m s-1]
	Tau : float
		characteristic timescale [s]
	zCL : float
		parameterized plume injection height [m]
	THzCL : float
		ambient potential temperature at modelled zCL [K]

	"""

	def __init__(self, name):
		"""
		Constructs the plume object with some inital attributes

		Parameters
		-----------
		name: str
			plume name
		"""
	#---for ops version all parameters assigned later 
		self.name = name
		self.interpZ = np.arange(0,zmax+1,dz)

	def get_sounding(self, inputs):
		"""
		Calculates attributes relating to vertical potential temperature profile

		Parameters
		-----------
		T0: ndarray
			potential temperature profile on host model levels (not interpolated)

		Returns
		---------
		zi : float
			boundary layer height [m]
		zs : float
			refernce height (zi * BLfrac) [m]
		sounding: ndarray
			vertical potential temperature sounding on interpolated analysis levels [K]
		THs : float
			ambient potential tempreature at reference height zs [K]
		"""

		zi = inputs['PBLH']
		zs = zi * BLfrac

		#interpolate sounding to analysis levels
		interpT= interp1d(inputs['Z'],inputs['T'],fill_value='extrapolate')
		T0interp = interpT(self.interpZ)
		i_zs = np.argmin(abs(self.interpZ - zs))
		THs = T0interp[i_zs]

		self.zi = zi
		self.zs = zs
		self.sounding = T0interp
		self.THs = THs


	def get_wf(self):
		"""

		Finds characteristic time (Tau) and velocity (wf) scales.

		Returns
		---------
		wf : float
			characteristic fire velocity scale [m s-1]
		Tau : float
			characteristic timescale [s]
		"""
		Tau = 1/np.sqrt(g*(self.THzCL - self.THs)/(self.THs * (self.zCL-self.zs)))
		wf= ((g*self.I*(self.zCL-self.zs))/(self.THs*self.zi))**(1/3.)

		self.Tau = Tau
		self.wf = wf


	def classify(self):
		"""

		Classifies the plume as penetrative (True) or boundary layer (False)

		Returns
		--------
		penetrative : boolean
			classification (True if penetrative).
		"""

		if	self.zCL < (self.zi + (dz)/2):
			self.penetrative = False
		else:
			self.penetrative = True

	def iterate(self, biasFit=None, **kwargs):
		"""
		Applies iterative solution to parameterize plume injection height

		Parameters
		----------
		biasFit : array_like, optional
			bias fit parameters. If none provided defaults to m = 1, b = 0.
		argout: boolean, optional
			flag to output return arguments. If False(default) they are assigned as attributes

		Returns
		-------
		zCL : float
			parameterized plume injection height [m]
		THzCL : float
			ambient potential temperature at modelled zCL [K]
		"""
		if biasFit:
			m, b = biasFit[0], biasFit[1]
		else:
			m, b = 1, 0

		i_zs = np.nanargmin(abs(self.interpZ - self.zs))

		#deal with 0 intensity fires: set to BL top
		if self.I <= 0:
			logging.warning('WARNING: null/negative fireline intensity input. Setting to BL height.')
			zCL = self.zi
		else:
			#obtain iterative solution
			toSolve = lambda z : z	- b - m*(self.zs + \
							1/(np.sqrt(g*(self.sounding[int(z/dz)] - self.THs)/(self.THs * (z-self.zs))))	* \
							(g*self.I*(z-self.zs)/(self.THs * self.zi))**(1/3.))

			#set inital guess for day vs night time
			if self.zi < 400:
				z0 = 1000
			else:
				z0 = self.zi
			try:
				diagnostics = fsolve(toSolve, z0, factor=0.1, full_output=True)
				zCL = diagnostics[0][0]
			except:
				logging.warning('FAILED TO CONVERGE: setting to BL top')
				zCL = self.zi
			

		#get related vars
		i_zCL = np.nanargmin(abs(self.interpZ - zCL))
		THzCL = self.sounding[i_zCL]

		if 'argout' in kwargs.keys():
			if kwargs['argout']:
				return float(zCL), THzCL
			else:
				self.THzCL = THzCL
				self.zCL = float(zCL)
		else:
			self.THzCL = THzCL
			self.zCL = float(zCL)

	def explicit_solution(self, Gamma, ze, biasFit=None):
		"""
		Applies explicit solution to parameterize plume injection height

		Parameters
		----------
		biasFit : array_like, optional
			bias fit parameters. Default is m = 1, b = 0

		Returns
		-------
		zCL : float
			parameterized plume injection height [m]
		THzCL : float
			ambient potential temperature at modelled zCL [K]
		"""
		if biasFit:
			m, b = biasFit[0], biasFit[1]
		else:
			m, b = 1, 0

		zCL = m*(((self.THs/g)**(1/4.)) * ((self.I/self.zi)**(0.5)) * ((1/Gamma)**(3/4.)) + ze) + b

		self.zCL = zCL

	def get_uBL(self, inputs):
		"""
		Get BL wind magnitude
		"""
		#get index of BL top
		i_zi = np.nanargmin(abs(self.interpZ - self.zi))

		uBL = np.mean(inputs['U'][:i_zi])

		self.uBL = uBL


	def get_profile(self):
		"""
		Parameterization of the full normalized vertical smoke profile

		Parameters
		----------

		Returns
		-------
		profile : ndarray
			1D vector corresponding to quasi-stationary downwind PM profile
		layer_heights: ndarray
		layer_fraction: ndarray
		"""

		#set up empty profile vector
		profile = np.empty((len(self.interpZ))) * np.nan
		i_zCL = np.nanargmin(abs(self.interpZ - self.zCL))

		'''
		if not self.penetrative:
			#for BL plumes: uniform distribution
			profile[:i_zCL] = 1./i_zCL
			profile[i_zCL:] = 0

			#TODO make this dynamic like BSP
			#allocate to 5 source layers
			self.layer_fractions = [0.2, 0.2, 0.2, 0.2, 0.2]
			self.layer_heights = [self.zCL*0.1, self.zCL*0.3, self.zCL*0.5, self.zCL*0.7, self.zCL*0.9]
		
		elif self.penetrative:
		'''
		if self.penetrative or not self.penetrative:
			#get fire velocity scale
			self.get_wf()

			#get Deadorff's velocity for spread
			wD = (g * self.zi * 0.13 / self.THs)**(1/3.) #!!!! HARDCODED SURFACE HEAT FLUX: use wrf?

			#get smoke spread above zCL
			sigma_top = (self.zCL - self.zs)/3.

			#get smoke spread below zCL
			if self.wf/wD < 1.5:
				Rw = self.uBL/self.wf
			else:
				Rw = self.uBL/(self.wf - wD)

			if Rw > 1:
				sigma_bottom = Rw * sigma_top
			else:
				sigma_bottom = sigma_top


			#prescribe gaussian profile
			profile[i_zCL:] = np.exp(-0.5*((self.interpZ[i_zCL:] - self.zCL)/sigma_top)**2)
			profile[:i_zCL+1] = np.exp(-0.5*((self.interpZ[:i_zCL+1] - self.zCL)/sigma_bottom)**2)
			#profile[:i_zCL+1] = np.exp(-0.5*((self.interpZ[:i_zCL+1] - self.zCL)/sigma_top)**2)			

			#convert to normalized distribution (sum area = 1)
			intC = sum(profile[:])
			profile = profile/intC

			#allocate to 5 source layers
			#TODO make this dynamic like BSP (user-selected layers)
			#get layer thickness below and above injection height, assuming three layers below and 1 obove zCL
			h1 = int(i_zCL/4)
			h2 = 2*h1
			h3 = 3*h1	
			h4 = 4*h1  #this is i_zCL
			h5 = np.nanargmin(abs(self.interpZ - (self.zCL+sigma_top)))
			#get half-layer indeces
			l1 = int(h1*1.5)
			l2 = int(h1*2.5)
			l3 = int(h1*3.5)
			l4 = int((h4+h5)/2)

			self.layer_heights = [self.zCL/4, self.zCL/2, self.zCL*3/4, self.zCL, self.zCL+sigma_top]
			self.layer_fractions = [sum(profile[:l1]), sum(profile[l1:l2]), sum(profile[l2:l3]), sum(profile[l3:l4]),sum(profile[l4:])]			
			#logging.debug('Sanity check: sum of layer fractions is %s' %sum(self.layer_fractions))
			#self.layer_heights = [self.zCL-2*sigma_bottom, self.zCL-sigma_bottom, self.zCL, self.zCL+sigma_top, self.zCL+2*sigma_top]
			#self.layer_fractions = [0.092, 0.238, 0.34, 0.238, 0.092]


		self.profile = profile.squeeze().tolist()
