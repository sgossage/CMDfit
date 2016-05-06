from unittest import TestCase
import os
import numpy as np
import pandas as pd
import cmdfit.processing.columnread as cread
from cmdfit import data as data
import cmdfit.processing.magcorrections as magcorr
from cmdfit import isochrone as isochrone
from cmdfit import isointerpmag
import emcee
from cmdfit import fitsingle
from cmdfit import fitall

# Tests that headers are being read correctly:
class TestIO(TestCase):
    def test_io(self):
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(root_dir, 'data')
        specific_data_dir = os.path.join(data_dir, 'Hyades')
        data_file = os.path.join(specific_data_dir, 'goldman_Hyades2MASS.txt')
        
        test_data = cread.get_header(data_file)
        
        self.assertEqual(test_data[3], 'Vperp')

# Tests that magnitude corrections will be applied correctly (this tests the AB to Vega correction and applies a distance modulus of 3.33 corresponding
# to roughly what is believed for this cluster):
class TestABCorrections(TestCase):
    def test_corr(self):
        root_dir = data.select_pathtofile('test')
        ABtoVegafile = os.path.join(root_dir, 'data/convert_AB_to_Vega.txt')
        model_file = os.path.join(root_dir, 'model/MIST_v0.31/HBlim005/MIST_v0.31_feh_p0.15_afe_p0.0_vvcrit0.4_03to8M_HBlim005_full.iso.cmd')
        # Read in 2MASS J magnitudes from this model file:
        index2MASSJ = 12
        modelvalues = np.array(cread.get_values(model_file, index2MASSJ, mode='model'))

        correctedmags = np.array(magcorr.ABtoVega(modelvalues, index2MASSJ))
        corr2MASSJ = 0.8940495232
        HYADESdmod = 3.33

        # Changed this because new model files do not require AB correction, only distance modulus:
        self.assertEqual(all(correctedmags == modelvalues + HYADESdmod), True) 

# Tests cmdset in 'data' mode:
class Testcmdset(TestCase):
    def test_cmdset(self):
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(root_dir, 'data')
        specific_data_dir = os.path.join(data_dir, 'Hyades')
        data_file = os.path.join(specific_data_dir, 'goldman_Hyades2MASS.txt')

        # Indices of the J, Jerr, H, and Herr columns:
        indices = (5, 6, 7, 8)

        dataset = data.cmdset('data', data_file = data_file, usecol = indices)
        
        self.assertEqual(isinstance(dataset.magnitudes, pd.core.frame.DataFrame),True)
        self.assertEqual(isinstance(dataset.uncertainties, pd.core.frame.DataFrame),True)

        Jband = dataset.makeBand(0)
 
        self.assertEqual(Jband[0][0], dataset.magnitudes.values[0][0])
         
# '          ' in 'model' mode. Also tests isochrones:
class TestIso(TestCase):
    def test_iso(self):
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_dir = os.path.join(root_dir, 'model')
        modeltype_dir = os.path.join(model_dir, 'MIST_v0.31')
        modelrun_dir = os.path.join(modeltype_dir, 'HBlim005')
        model_file = os.path.join(modelrun_dir, 'MIST_v0.31_feh_p0.15_afe_p0.0_vvcrit0.4_03to8M_HBlim005_full.iso.cmd')

        #Indices of the J and H bands:
        indices = (12, 13)

        dataset = data.cmdset('model', data_file = model_file, usecol = indices)
        
        self.assertEqual(isinstance(dataset.magnitudes, pd.core.frame.DataFrame),True)
        
        isoch = isochrone(dataset, 8.8)

        self.assertEqual(isoch.age <= 8.8 ,True)

        isoset = dataset.makeisoset(8.0, 9.6)

        self.assertEqual(isoset[0].age < isoset[-1].age, True)

        self.assertEqual(isinstance(isoch.isogetmag(1.0, 0), float), True)
        
        self.assertEqual(isinstance(isointerpmag(dataset, initmass=1.0, age=8.8, age_array=[iso.age for iso in isoset], band=0), float), True)

# test cmdfit.py:
class TestCMDFIT(TestCase):
    def test_cmdfit(self):

        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(root_dir, 'data')
        specific_data_dir = os.path.join(data_dir, 'Hyades')
        data_file = os.path.join(specific_data_dir, 'goldman_Hyades2MASS.txt')

        # Indices of the J, Jerr, H, and Herr columns:
        dindices = (5, 6, 7, 8)
        mindices = (12, 13)

        sampler = fitsingle('data', ndim=5,nwalkers=12,nsteps=4,data_file=data_file, datausecol=dindices, modelusecol=mindices, default=True, test=True)

        samples = sampler.chain[:,:,:]

        self.assertEqual(np.isfinite(samples).all(), True)

        allsampler= fitall('data', nwalkers=4, nsteps=4, data_file=data_file, datausecol=dindices, modelusecol=mindices, default=True, test=True)

        samples = allsampler.chain[:,:,:]

        self.assertEqual(np.isfinite(samples).all(), True)

        
