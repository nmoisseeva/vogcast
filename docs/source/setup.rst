.. _setup:

Initial Setup
==============

Initial setup of the framework involves installation and configuration of the required software and Python dependencies. At the minimum, the local HPC system must have **slurm** and **HYSPLIT** installed (see :ref:`requirements`). If using Weather Research and Forecasting Model (WRF) for Meteorology (see :ref:`modules`), working versions of **WPS** and **WRF** are also required. 

Once installed, follow the instructions below to perform the initial framework setup. These steps only need to be competed once. Following initial domain setup, the workflow is controlled via a centralized configuration file (see :ref:`workflow`).

Config Files
-------------
When running the framework for the first time, various components of system need to be configured for the local HPC environment and modelling domain. The files to be edited are located in the ``./config`` subdirectory of the VogCast repository. 

1. In ``./config/slurm/`` subdirectory back up and modify the slurm headers of ``hysplit.slurm`` and ``wrf.slurm`` (if using **WRF** for Meteorology) scripts to match your local HPC system. Note, that both **HYSPLIT** and **WRF** within VogCast require MPI support.  Do not modify the main calls to HYSPLIT and WRF executables. 

2. In ``./config/hysplit/`` subdirectory back up and modify the ``CONTROL`` and ``SETUP.CFG`` files to desired dispersion simulation parameters. Definitions and details about each parameter can be found in `HYSPLIT User Manual <https://www.arl.noaa.gov/documents/reports/hysplit_user_guide.pdf>`_. 

 .. warning::
    DO NOT modify any named parameters in ``{...}``. These are configured automatically via a centralized framework configuration file ``vog.config``. 

3. If using **WRF** for Meteorology module, back up and configure ``namelist.wps`` and ``namelist.input`` files in the ``./config/wrf/`` subdirectory to you desired domain. Definitions and details about each parameter can be found in **WRF** and **WPS** respositories (see :ref:`requirements`).

 .. warning::
    DO NOT modify any named parameters in ``{...}``. These are configured automatically via a centralized framework configuration file ``vog.config``. 


Running a Test Case 
--------------------
Existing HYSPLIT and WRF configuration files can be used as-is to create a test forecast simulation for the State of Hawai'i. To run this test case, one only needs to adjust the slurm scripts located in ``./config/slurm/``. Once configured, proceed to main workflow settings as described in :ref:`workflow`.