import numpy as np
import os
from . import userinteract as user

def ABtoVega(magnitude_array, band_column):

    print('\nConverting from AB magnitude system to Vega system...\nApplying distance modulus correction...')

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = root_dir + '/data'
    mag_correction_file = data_dir + '/convert_AB_to_Vega.txt'

    # The corrections that we want are in the last column of this file:
    ABtoVega_corrections = np.loadtxt(mag_correction_file, usecols=(-1,))
    
    # Apply corrections (AB --> Vega, and distance modulus):
    
    # (for Hyades, van Leeuwen et al., 2009):
    # if 'Hyades' in data_file:
    distance_modulus = 3.33
    print('Applying HYADES distance modulus: {:f}'.format(distance_modulus))     

    modelfile_skippedcols = 7

    magnitude_array = magnitude_array - ABtoVega_corrections[band_column - modelfile_skippedcols] + distance_modulus 

    return magnitude_array

#def get_distanceModulus():

 #   dmod_name = ''

   # while dmod_name not in available_dmods:
   #     dmod_name = input('Enter the name of the cluster')
    # Distance modulus corrections. These are not exact, but are based on values cited in the following papers: 
    # (for Pleiades, Stello & Nissen, 2001):
   # if 'Pleiades' in data_file:
   #     dmod = 5.61
   #     print('Applying PLEIADES dist. modulus:{:f}'.format(dmod))
    # (for Hyades, van Leeuwen et al., 2009):
    #if 'Hyades' in data_file:
    #    dmod = 3.33
    #    print('Applying HYADES dist. modulus:{:f}'.format(dmod))

    #return dmod
