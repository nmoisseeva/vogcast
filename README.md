# vogcast
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.10035712.svg)](https://doi.org/10.5281/zenodo.10035712)

VogCast is an open-source volcanic air pollution modelling framework developed by the Vog Measurement and Prediction Program (VMAP) at the University of Hawaii at Manoa. It combines multiple existing models and data streams to create a flexible unified workflow designed for deployment on an HPC system. 

Scientific background and details of model development can be found in: [link to be released post-submission]

Full documentation is here: https://nmoisseeva.github.io/vogcast/

# Software Requirements

* HYSPLIT Model | https://www.ready.noaa.gov/HYSPLIT_linux.php
* slurm 22.05+ | https://slurm.schedmd.com/documentation.html
* (optional) Weather Research and Forecasting Model 4+ | https://github.com/wrf-model/WRF
* (optional) WRF Preprocessing System 4+ | https://github.com/wrf-model/WPS


# Python Dependencies

* Python 3.7+
* numpy 1.17.0+
* scipy 1.3.0+
* matplotlib 3.1.1+
* wrf-python 1.3.4+
* netCDF4 1.6.2+
* hjson 3.1.0+
* bs4 0.0.1+
* DateTime 4.7+
* pandas 1.5.0+
* Cartopy 0.21.0+
* sklearn 0.0+

-----------------



# License

[MIT License](https://github.com/nmoisseeva/vogcast/LICENSE)

# Contact
Nadya Moisseeva nadya.moisseeva@hawaii.edu
