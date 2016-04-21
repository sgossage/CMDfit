# The CMDdata class needs to be able to hold however many filters are available to do statistics with...or however many filters are desired to do statistics with.
import numpy as np
import pandas as pd
import os
from processing import columnread as cread
from processing import userinteract as user

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
                    dataCol, dataName, ages, masses = cread.assign_data(data_file, mode=readmode, returnNames=True, model_extras=extras_flag)
                else:
                    dataCol, dataName = cread.assign_data(data_file, mode=readmode, returnNames=True)
                
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
            closestAge = min(age_array, key = lambda x: abs(x - age))
        
            if closestAge < age:
                # The index of the last element in the closest age isochrone.
                closestAge_index = np.where(age_array == closestAge)[0][-1]
                # Taking this index and adding one to enter the next closest isochrone and grab its age:
                older_closestAge = age_array[closestAge_index + 1]
                younger_closestAge = closestAge
         
            else:
                closestAge_index = np.where(age_array == closestAge)))[0][0]
                younger_Age = age_array[closestAge_index - 1]
                older_Age = closestAge

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
                   older_closestMass = min(older_mass_array, key = lambda x: abs(x - initmass))

                    # Found the closest mass that is less massive than the given mass.
                    # Need to get the more massive
                    if older_closest_mass < initmass:
                        closestMass_index = np.where(older_mass_array == older_closest_mass)[0]
                        older_bigMass = older_mass_array[closestMass_index + 1]
                        older_lilMass = older_closestMass

                        # Grab corresp. magnitudes
                        older_bigmag_val = older_mag_array[closestMass_index + 1]
                        older_lilmag_val = older_mag_array[closestMass_index]
                    else:
                        closestMass_index = np.where(older_mass_array == older_closest_mass)[0]
                        older_lilMass = older_mass_array[closestMass_index - 1]
                        older_bigMass = older_closestMass

                        # Grab corresp. magnitudes
                        older_bigmag_val = older_mag_array[closestMass_index - 1]
                        older_lilmag_val = older_mag_array[closestMass_index]
                 else:
                     older_mass_val = older_mass_array[older_mass_index]
                     older_mag_val = older_mag_array[older_mass_index]
            
            # See if we can grab masses from the younger isochrone too:
            if initmass < np.amax(np.array(younger_mass_array)) and initmass > np.amin(np.array(younger_mass_array)):
                
                younger_mass_index = np.where(younger_mass_array == initmass)[0]     
                
                if not younger_mass_index:
                    younger_closestMass = min(younger_mass_array, key = lambda x: abs(x - initmass))

                    # Found the closest mass that is less massive than the given mass.
                    # Need to get the more massive
                    if younger_closest_mass < initmass:
                        closestMass_index = np.where(younger_mass_array == younger_closest_mass)[0]
                        younger_bigMass = younger_mass_array[closestMass_index + 1]
                        younger_lilMass = younger_closestMass
                        
                        # Grab corresp. magnitudes
                        younger_bigmag_val = younger_mag_array[closestMass_index + 1]
                        younger_lilmag_val = younger_mag_array[closestMass_index]
                    else:
                        closestMass_index = np.where(younger_mass_array == younger_closest_mass)[0]
                        younger_lilMass = younger_mass_array[closestMass_index - 1]
                        younger_bigMass = younger_closestMass

                        # Grab corresp. magnitudes
                        younger_lilmag_val = younger_mag_array[closestMass_index - 1]
                        younger_bigmag_val = younger_mag_array[closestMass_index]
                else:
                    younger_mass_val = younger_mass_array[younger_mass_index]
                    younger_mag_val = younger_mag_array[younger_mass_index]

            # Now we have the bounding masses for the given mass value (or else the masses themselves) from each isochrone.
            # We also have either the bounding magnitudes or the magnitudes themselves.
            # In the case that we have bounding values, need to interpolate.

            # So, first may need to interpolate between masses and an interpolated magnitude for each isochrone.
            # Then will need to interpolate the magnitude between isohcrones (ages).
            # OK...
            
            
            
            
