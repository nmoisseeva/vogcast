# September 2021
#nmoisseeva@eoas.ubc.ca
# This code is an ops versio of the CWIPP code

import logging

import utils
#import config
import cwipp


#====================INPUT BEGINS HERE================


#default model bias fit parameters
biasFit = [0.9195, 137.9193]

#paths
input_data = '../../run/2021102912/plumerise/cwipp_inputs.json'

#====================end of input====================

#set up logging
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(message)s', datefmt='[%Y-%m-%d %H:%M:%S %Z]')

logging.info('==========CWIPP PLUME-RISE PARAMETERIZATION SCHEME========')
#load inputs
inputs = utils.read_json(input_data)
logging.debug('Loading data: %s' %input_data)

#set up output json
output = {}

#loop through all time stamps
for dtime in inputs.keys():
    logging.debug('Processing timestamp: {}'.format(dtime))

    output[dtime] = {}
    #loop through all fires
    for fID in inputs[dtime].keys():
        logging.debug('...Processing fire: %s' %fID)
        
        output[dtime][fID] = {}
        fire = inputs[dtime][fID]
        case = cwipp.Plume(fID)
        case.get_sounding(fire)
        case.I = fire['I']    #TODO change this to I in preprocessors
        case.iterate(biasFit)
        case.classify()
        case.get_uBL(fire)
        case.get_profile()

        #FUTURE ADDITION: incroporate vertical profile code here to reconstruct full profile here

        #write data to output file
        utils.compile_output(output[dtime][fID],case)

        # #temporary plot for sanity check for mesoWRF
        # import matplotlib.pyplot as plt

        # plt.figure()
        # plt.plot(case.sounding, case.interpZ, color='grey', label='WRF sounding')
        # ax1 = plt.gca()
        # ax1.set(xlabel='potential temperature (K)', ylabel='height [m]')
        # plt.axhline(y = case.zi, color='grey', label='zi')
        # plt.axhline(y = case.zCL, color='C1', label='modelled injection height')
        # ax2 = plt.twiny(ax1)
        # plt.plot(case.profile, case.interpZ, color='red',label='CWIPP profile')
        # plt.gca().set(xlabel='norm smoke concentration', ylabel='height [m]')
        # plt.legend()
        # plt.show()

utils.write_json('./output.json', output)

logging.info('COMPLETED')
