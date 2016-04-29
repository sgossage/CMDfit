from unittest import TestCase
import os
import numpy as np
import cmdfit.processing.columnread as cread
from cmdfit import data as data
import cmdfit.processing.magcorrections as magcorr

# Tests that headers are being read correctly:
class TestIO(TestCase):
    def test_io(self):
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = root_dir + '/data'
        specific_data_dir = data_dir + '/Hyades'
        data_file = specific_data_dir + '/goldman_less_Hyades.txt'
        
        test_data = cread.get_header(data_file)
        
        self.assertEqual(test_data[3], 'pmRA')

# Tests that magnitude corrections will be applied correctly (this tests the AB to Vega correction and applies a distance modulus of 3.33 corresponding
# to roughly what is believed for this cluster):
class TestABCorrections(TestCase):
    def test_corr(self):
        root_dir = data.select_pathtofile('test')
        ABtoVegafile = root_dir + '/data/convert_AB_to_Vega.txt'
        model_file = root_dir + '/model/MIST_v0.31/HBlim005/MIST_v0.31_feh_m0.15_afe_p0.0_vvcrit0.4_03to8M_HBlim005_full.iso.cmd'
        # Read in 2MASS J magnitudes from this model file:
        index2MASSJ = 12
        modelvalues = np.array(cread.get_values(model_file, index2MASSJ, mode='model'))

        correctedmags = np.array(magcorr.ABtoVega(modelvalues, index2MASSJ))
        corr2MASSJ = 0.8940495232
        HYADESdmod = 3.33

        self.assertEqual(all(correctedmags == modelvalues - corr2MASSJ + HYADESdmod), True)      
    
