# The CMDdata class needs to be able to hold however many filters are available to do statistics with...or however many filters are desired to do statistics with.
import numpy as np
import pandas as pd
import os
from processing import columnread as cread
from processing import userinteract as user
from processing import interp

class cmdset(object):
    
    def __init__(self, kind = 'data'):



        def loadData(readmode='data'):

             # root_dir should be /cmdfit
            root_dir = os.path.dirname(os.path.abspath(__file__))

            if readmode == 'data':
                data_dir = root_dir + '/data'
                print('SELECT DESIRED DATA PATH:\n(Reading from {:s}.)'.format(data_dir))
                specific_data_dir = data_dir + user.select_a_dir(data_dir,type_flag = 1)
                data_file = specific_data_dir + user.select_a_dir(specific_data_dir, 2)
                extras_flag = False

            elif readmode == 'model':
                cmd_model_path = root_dir + '/model'
                print('SELECT DESIRED MODEL PATH:\n(Reading from {:s}.)'.format(cmd_model_path))
                specific_model_path = cmd_model_path + user.select_a_dir(cmd_model_path,type_flag = 1)
                selected_run_path = specific_model_path + user.select_a_dir(specific_model_path,type_flag = 1)
                data_file = selected_run_path + user.select_a_dir(selected_run_path,type_flag = 2)
                extras_flag = True
            
            else:
                print('Usage:\ncmdset(kind = ...), where \'...\' is either \'data\' if reading from a data file or \'model\' if reading from a model file.')

            # Ask which column is relevant.
            # Store the column header name
            # Store the data in the column.
            # Do this until told to stop
            # Put data in a data frame with column names as the keys
            # Also put something in to let user see the keys on request.

            dataMatrix = []
            uncertMatrix = []
            dataNames = []
            uncertNames = []
            keepgoing = True

            while keepgoing:
                
                if extras_flag:
                    dataCol, dataName, ages, masses = cread.assign_data(data_file, mode=readmode, returnNames=True, model_extras=extras_flag, corrections='ABtoVega')
                else:
                    dataCol, dataName = cread.assign_data(data_file, mode=readmode, returnNames=True,corrections='ABtoVega')
                
                # Ask about supplying uncertainty values from the data table:
                if readmode == 'data':
                    print('\nSELECT UNCERTAINTIES CORRESPONDING TO COLUMN {:s}.'.format(dataName))
                    # Ask if uncertainties should be loaded from the data file, or generated in some other way.
                    response = user.ask_for_specific_input('LOAD FROM {:s}? (If \'n\', a nominal +/-0.1 dex will be used.)'.format(data_file.split('/')[-1]), 'y', 'n')
                    if response == 'y':
                        uncertCol, uncertName = cread.assign_data(data_file, mode=readmode, returnNames=True)
                    else:
                        # In the future maybe give some options for users to select how they want to generate uncertainties if the data doesn't supply them.
                        # This nominal value is based on my reading of Jorgensen & Lindegren 2005.
                        uncertCol = [0.1] * len(dataCol)
                        uncertName = dataName + 'err'

                    uncertMatrix.append(uncertCol)
                    uncertNames.append(uncertName)
                
                if extras_flag:
                    dataMatrix.append(ages)
                    dataNames.append('log10 age')
                    dataMatrix.append(masses)
                    dataNames.append('Initial Mass')
                
                dataMatrix.append(dataCol)
                dataNames.append(dataName)

                response = user.ask_for_specific_input('\n================================\nWould you like to enter another filter as data? ', 'y', 'n')
                if response == 'y':
                    extras_flag = False
                    continue
                else:
                    keepgoing = False

            # Now we have a matrix containing all selected magnitudes; each magnitude set is stored columnwise in dataMatrix and the respective column names are stored columnwise in dataNames.
            # Place the data into a Pandas data frame for easy reference:

            dataMatrix = np.array(dataMatrix)
            dataNames = np.array(dataNames)

            loadedData = pd.DataFrame(dataMatrix.T, columns = dataNames)

            if readmode == 'data':
                uncertMatrix = np.array(uncertMatrix)
                uncerNames = np.array(uncertNames)
                loadedUncert = pd.DataFrame(uncertMatrix.T, columns = uncertNames)

                return loadedData, loadedUncert

            return loadedData

        # === Attributes ===: 
        if kind == 'data':
            self.magnitudes, self.uncertainties = loadData(readmode = 'data')
        
        elif kind == 'model':
            self.fullframe = loadData(readmode = 'model')
            self.ages = self.fullframe.ix[:, 'log10 age']
            self.initmasses = self.fullframe.ix[:, 'Initial Mass']
            self.magnitudes = self.fullframe.ix[:, 2:]
            # Also load info on other params...

        self.kind = kind
     
    # Utility functions:
    def makeBands(self):
          
        # This function will only operate if the cmdset object has a kind equal to 'data'.
        if self.kind == 'model':
            print('\nERROR: This cmdset is a model and makeBands() will only operate on data sets.\n')
            return
        
        # Iterates through columns of the magnitude data frame:
        bandmags = [] 
        for band in self.magnitudes:
            bandmags.append(self.magnitudes[band].values)
       
        # Same, but for uncertainties:
        banduncert = []
        for banderr in self.uncertainties:
            banduncert.append(self.uncertainties[banderr].values)
        
        # Conglomerate into a larger list with column 1 holding the list of magnitude arrays and column 2 holding the list of uncertainty arrays:
        banddata = [bandmags, banduncert]

        return banddata
       
    def getmag(self, age, initmass, band):
        
        # Search for the given age, then the given mass, then get the magnitude and return it. Not always so easy; if necessary, interpolate.
        # So check if the given age exists already and get the indices of these entries if it does:
        age_array = self.ages.values
        mass_array = self.initmasses.values        
        mag_array = self.magnitudes.values[:, band]
        
        isochrone_indexlist = np.where(age_array == age)[0]
       
        # If the age does not exist:
        if not isochrone_indexlist:
            # Determine the closest ages:
            younger_Age, older_Age = interp.find_closestAges(age, age_array)            

            older_Iso_indexlist = np.where(age_array == older_Age)
            younger_Iso_indexlist = np.where(age_array == younger_Age)

            # Now we have either the closest ages. Need to do the same for masses.
            # Acquire the available masses for the isochrones found above:
            older_mass_array = mass_array[older_Iso_indexlist]
            younger_mass_array = mass_array[younger_Iso_indexlist]

            # Acquire the magnitudes as well, we will need these:
            older_mag_array = mag_array[older_Iso_indexlist]
            younger_mag_array = mag_array[younger_Iso_indexlist]

            # Check if the given mass is within bounds of the predicted masses for the isochrones found:
            # (If within bounds, get the masses from the isochrone.)
            if initmass < np.amax(np.array(older_mass_array)) and initmass > np.amin(np.array(older_mass_array)):

                older_mass_index = np.where(older_mass_array == initmass)[0]
           
                # If the mass does not exist, need to find adjacent masses and prepare for interpolation.
                if not older_mass_index:
                    # Find the closest masses in this isochrone:
                    older_bigMass, older_lilMass, bigMass_index, lilMass_index = interp.find_closestMasses(initmass, older_mass_array)
                    
                    # Get corresponding magnitudes:
                    older_bigmag_val = older_mag_array[bigMass_index]
                    older_lilmag_val = older_mag_array[lilMass_index]

                # Or else the mass was found:
                else:
                    older_mass_val = older_mass_array[older_mass_index]
                    older_mag_val = older_mag_array[older_mass_index]
            
            # See if we can grab masses from the younger isochrone too:
            if initmass < np.amax(np.array(younger_mass_array)) and initmass > np.amin(np.array(younger_mass_array)):
                
                younger_mass_index = np.where(younger_mass_array == initmass)[0]     
                
                if not younger_mass_index:

                    younger_bigMass, younger_lilMass, bigMass_index, lilMass_index = interp.find_closestMasses(initmass, younger_mass_array)

                    younger_lilmag_val = younger_mag_array[lilMass_index]
                    younger_bigmag_val = younger_mag_array[bigMass_index]

                else:
                    younger_mass_val = younger_mass_array[younger_mass_index]
                    younger_mag_val = younger_mag_array[younger_mass_index]

            # Need a plan to deal with if the mass is NOT within these ranges...
            
            # Right now, Ill just linearly interpolate...
            # Given then masses found and the magnitudes found, and the given initial mass, linearly interpolate the magnitude for the younger and older isochrones:
            # This  is if the given mass was not found:
            older_interp = False
            younger_interp = False
            if not younger_mass_index:
                younger_interpmag = interp.linear_interp(initmass, (younger_lilMass, younger_lilmag_val), (younger_bigMass, younger_bigmag_val))
                younger_interp = True
            if not older_mass_index:
                older_interpmag = interp.linear_interp(initmass, (older_lilMass, older_lilmag_val), (older_bigMass, older_bigmag_val))
                older_interp = True
            if older_interp and younger_interp:
                # Now use the newly interpolated magnitudes for each isochrone and interpolate between isochrones to get the interpolated magnitude at the desired age:
                interpmag = interp.linear_interp(age, (younger_Age, younger_interpmag), (older_Age, older_interpmag))

            else:
                interpmag = interp.linear_interp(age, (younger_Age, younger_mag_val), (older_Age, older_mag_val))
            
            return interpmag[0]

        # Now we have an interpolated magnitude in the event that the given age is not found. If the age was found, just return the corresponding magnitude.
        else:
            # Use isochrone_indexlist...
            # Get the relevant masses:
            mass_array = mass_array[isochrone_indexlist]
            
            # Check if the mass we need exists, and if the mass is within bounds:
            if initmass < np.amax(np.array(mass_array)) and initmass > np.amin(np.array(mass_array)):

                mass_index = np.where(mass_array == initmass)[0]
           
                # If the mass does not exist, need to find adjacent masses and prepare for interpolation.
                if not mass_index:
                    bigMass, lilMass, bigMass_index, lilMass_index = interp.find_closestMasses(initmass, mass_array)
                    
                    bigmag_val = mag_array[bigMass_index]
                    lilmag_val = mag_array[lilMass_index]
                    
                    # Interpolate between masses within this isochrone:
                    interp_mag = interp.linear_interp(initmass, (older_lilMass, older_lilmag_val), (older_bigMass, olderbigmag_val))

                    return interp_mag[0]

                # Or else the mass was found,
                else:
                    mass_val = mass_array[mass_index]
                    mag_val = mag_array[mass_index]

                    return mag_val[0]
                 
            
            
