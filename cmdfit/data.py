# The CMDdata class needs to be able to hold however many filters are available to do statistics with...or however many filters are desired to do statistics with.
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
from cmdfit.processing import columnread as cread
from cmdfit.processing import userinteract as user
from cmdfit.processing import interp

class cmdset(object):
    
    def __init__(self, kind = 'data', data_file = None, usecol = None):

        def loadData(readmode='data', data_file = None, usecol = None):

            # If not file path was given, have the user select one:
            if readmode == 'data':
                if data_file == None:

                    specific_data_dir = select_pathtofile(readmode)
                    data_file = user.select_a_dir(specific_data_dir, 2)

                extras_flag = False

            elif readmode == 'model' or readmode == 'modeltest':
                if data_file == None:

                    selected_run_path = select_pathtofile(readmode)
                    data_file = user.select_a_dir(selected_run_path,type_flag = 2)
                
                # For model cmdsets, turn model extras on initially. This will allow for information detailing intitial
                # masses of model stars and their ages as well:
                extras_flag = True
            
            else:
                print('Usage:\ncmdset(kind = ...), where \'...\' is either \'data\' if reading from a data file or \'model\' if reading from a model file.')
                return

            # Arrays that will hold loaded data, uncertainties (if readmode = 'data'), 
            # header names, and uncertainty header names (if readmode = 'data'):
            dataMatrix = []
            uncertMatrix = []
            dataNames = []
            uncertNames = []

            # Initialize to true to execute while loop just below:
            keepgoing = True
            # Initialize number of bands read in for the cmdset to be 0:
            self.numbands = 0

            # For model cmdsets, we may want to load a bunch of files, so this array will
            # keep track of the columns used so that the user does not have to re-enter them.
            if readmode == 'model':
                if isinstance(usecol, type(None)):
                    self.usedcolumns = []
                    # Report magnitude correction and header info on first model:
                    silent_flag = False
                else:
                    self.usedcolumns = np.array(usecol)
                    usecol_index = 0
                    usecol = self.usedcolumns[usecol_index]
                    # If loading in subsequent models via all_modelcmdsets(), suppress notifications:
                    silent_flag = True
      
            # Data and modeltest cmdsets should report headers and notifications since they
            # are created singularly:
            else:
                silent_flag = False

            # This while loop runs a number of times to allow the user to select which columns to read in from the data file:
            while keepgoing:
                
                if extras_flag:
                    dataCol, usedcol, dataName, ages, masses, metadata = cread.assign_data(data_file, mode=readmode, 
                                                                                             given_column=usecol, returncols=True, 
                                                                                               returnNames=True, model_extras=extras_flag, 
                                                                                                 corrections='ABtoVega', silent=silent_flag)
                else:
                    if readmode == 'data':
                        dataCol, usedcol, dataName = cread.assign_data(data_file, mode=readmode, 
                                                                         given_column=usecol, returncols=True, 
                                                                           returnNames=True, corrections=None, silent=silent_flag)
                    else:
                        dataCol, usedcol, dataName = cread.assign_data(data_file, mode=readmode,
                                                                         given_column=usecol, returncols=True, 
                                                                           returnNames=True, corrections='ABtoVega', silent=silent_flag)
                
                # Ask about supplying uncertainty values from the data table:
                if readmode == 'data' or 'modeltest':

                    # For data files, ask about loading in uncertainties from the data table:
                    response = 'n'
                    # Reading uncertainties is disabled at the moment.
                    #if readmode == 'data':
              
                    #    print('\nSELECT UNCERTAINTIES FOR {:s}.'.format(dataName))
                        # Ask if uncertainties should be loaded from the data file, or generated in some other way.
                    #    response = user.ask_for_specific_input('LOAD FROM {:s}? (If \'n\', a nominal +/-0.1 dex will be used.)'.format(data_file.split('/')[-1]), 'y', 'n')
                    
                    if response == 'y':
                            uncertCol, uncertName = cread.assign_data(data_file, mode=readmode, returnNames=True)

                    # If the answer is no for loading uncertainties, just suppy some nominal values. modeltest cmdsets will always have this value as their uncertainty.
                    else:
                        # In the future maybe give some options for users to select how they want to 
                        # generate uncertainties if the data doesn't supply them.
                        # This nominal value is based on my reading of Jorgensen & Lindegren 2005.
                        uncertCol = [0.1] * len(dataCol)
                        uncertName = dataName + 'err'
                    
                    # Store uncertainties in their own matrix:
                    uncertMatrix.append(uncertCol)
                    uncertNames.append(uncertName)
                
                # Store log10 age and initial mass in the data matrix if extras are desired:
                if extras_flag:
                    dataMatrix.append(ages)
                    dataNames.append('log10 age')
                    dataMatrix.append(masses)
                    dataNames.append('Initial Mass')
                    # In MIST model files, FeH is the 3rd entry in the metadata line.
                    self.FeH = eval(metadata[2])
                
                # Store magnitudes in the data matrix, for models these columns will follow age and mass columns:
                dataMatrix.append(dataCol)
                dataNames.append(dataName)
               
                # Update the number of bands included so far in the cmdset:
                self.numbands += 1
                
                # If columns have not been given:
                if usecol == None:
                   
                    # Track the columns used so far:
                    if readmode == 'model':
                        self.usedcolumns.append(usedcol)                     

                    # Ask about reading in another column of magnitudes:
                    response = user.ask_for_specific_input('\n================================\nWould you like to enter another filter as data? ', 'y', 'n')
                    if response == 'y':
                        extras_flag = False
                        silent_flag = True
                        continue
                    else:
                        keepgoing = False

                # If columns have been given (as an array of which ones to use), keep going until all columns have been used:
                else:
                    usecol_index +=1
                    if usecol_index >= len(self.usedcolumns):
                        break
                    usecol = self.usedcolumns[usecol_index]
                    extras_flag = False

            # Now we have a matrix containing all selected magnitudes; each magnitude set is stored columnwise in dataMatrix and the respective column names are stored columnwise in dataNames.
            # Place the data into a Pandas data frame for easy reference:
            dataMatrix = np.array(dataMatrix)
            dataNames = np.array(dataNames)

            loadedData = pd.DataFrame(dataMatrix.T, columns = dataNames)
            
            # For data cmdsets, create a Pandas data frame for the loaded uncertainties as well:
            # modeltest cmdsets will have age and mass as well in their loaded data.
            if readmode == 'data' or readmode == 'modeltest':
                uncertMatrix = np.array(uncertMatrix)
                uncerNames = np.array(uncertNames)
                loadedUncert = pd.DataFrame(uncertMatrix.T, columns = uncertNames)

                return loadedData, loadedUncert

            # For models return age, mass, and magnitudes:
            return loadedData

        # === Attributes ===: 
        if kind == 'data':
            self.magnitudes, self.uncertainties = loadData(readmode = 'data', data_file=data_file, usecol=usecol)
        
        elif kind == 'model':
            self.fullframe = loadData(readmode = 'model', data_file=data_file, usecol=usecol)
            self.ages = self.fullframe.ix[:, 'log10 age']
            self.initmasses = self.fullframe.ix[:, 'Initial Mass']
            self.magnitudes = self.fullframe.ix[:, 2:]
            # Also load info on other params...

        elif kind == 'modeltest':
            self.fullframe, self.uncertainties = loadData(readmode = 'modeltest', data_file=data_file, usecol=usecol)
            self.ages = self.fullframe.ix[:, 'log10 age']
            self.initmasses = self.fullframe.ix[:, 'Initial Mass']
            self.magnitudes = self.fullframe.ix[:, 2:]

        self.kind = kind
     
    # Utility functions:
    def makeBand(self, bandindex):
          
        # This function will only operate if the cmdset object has a kind equal to 'data'.
        if self.kind == 'model':
            print('\nERROR: This is a model cmdset and makeBands() will only operate on data sets.\n')
            return
        
        banddata = [self.magnitudes.ix[:, bandindex].values, self.uncertainties.ix[:, bandindex].values]

        return banddata
       
    def getmag(self, age, initmass, band):
        
        # This function will only operate if the cmdset object has a kind equal to 'model'.
        if self.kind == 'data':
            print('\nERROR: This is a data cmdset and makeBands() will only operate on model sets.\n')
            return

        # So I need to check if interpolation between metallicities needs to take place first, since these are separate files....
        # This means that I need to take in all cmdsets, find the one with the given metallicity, and then figure out if interpolation
        # between cmdsets needs to be done.

        # Available ages in the cmdset:
        age_array = self.ages.values
        age_max = np.amax(age_array)
        age_min = np.amin(age_array)

        # Check if the proposed age is within the valid range:
        if age_min < age < age_max:

            # If the age does not exist, but it is within range of valid values:
            if age not in age_array:
                # Determine the closest ages via interpolation:
                younger_Age, older_Age = interp.find_closestAges(age, age_array)            

                # Pick out their isochrones:
                younger_iso = isochrone(self, younger_Age)
                older_iso = isochrone(self, older_Age)
               
                # Determine magnitudes and interpolate if necessary & possible:
                young_mag = younger_iso.isogetmag(initmass, band)
                older_mag = older_iso.isogetmag(initmass, band)

                # If we were able to interpolate masses in both isochrones, interpolate between isochrone ages:
                if np.isfinite(young_mag) and np.isfinite(older_mag):
                    mag = interp.linear_interp(age, (younger_Age, young_mag), (older_Age, older_mag))

                # Or else if magnitude retrieval failed (invalid mass) in at least one isochrone:
                else: 
                    # Use either the younger or older magnitude, if possible:
                    if np.isfinite(young_mag):
                        mag = young_mag
                    elif np.isfinite(older_mag):
                        mag = older_mag

                    # If interpolation failed in both cases, return infinity:
                    else:
                        # This signals 0 probability.
                        mag = np.inf   

                # Return the result:
                return mag

            # Now we have an interpolated magnitude in the event that the given age is not found. 
            # If the age was found, just return the corresponding magnitude (will be inf for 
            # invalid masses):
            else:
                iso = isochrone(self, age)
                return iso.isogetmag(self, initmass, band)

        # Or else if the proposed age is invalid, return an infinite magnitude to
        # trigger 0 probability for this proposition:
        else:
            return np.inf
                 
def all_modelcmdsets():

    # Go to a desired directory and get all of the .cmd files there:
    selected_run_path = select_pathtofile('model')

    # Load all files in the selected directory:
    data_files = cread.getall_files(selected_run_path)
    print("In " + selected_run_path + "...")
    for filename in data_files:
        print("Found " + filename.split('/')[-1] + "...")

    model_cmdsets = []
    usedcolumns = None
    print()
    
    # Loop through model files and create a cmdset from each:
    for i in range( len(data_files) ):
        
        print('\n======================================================================')
        print('Creating model cmdset #{:d} for '.format(i) + data_files[i].split('/')[-1] + '...')

        model_cmdsets.append(cmdset('model', data_files[i], usedcolumns))

        # On subsequent loops, use the user selected columns of the first model cmdset:
        usedcolumns = model_cmdsets[i].usedcolumns
        
        if i > 1:
            # Returns True if any of the columns do not match; issue a warning if this is the case:
            usedcol_donot_match = any(model_cmdsets[i].usedcolumns - model_cmdsets[i-1].usedcolumns)
            if usedcol_donot_match:
                print('WARNING: The usedcolumns do not match between cmdsets {:d} and {:d}. This will likely lead to errors.'.format(i, i-1))
        

    return model_cmdsets

def select_pathtofile(mode):
            
    # returns string in the form of '/path/to/file'

    # root_dir path should lead to /cmdfit.
    root_dir = os.path.dirname(os.path.abspath(__file__))

    # For running tests, this function just returns the root directory.
    if mode == 'test':
        return root_dir

    elif mode == 'model' or mode == 'modeltest':
        cmd_model_path = os.path.join(root_dir, 'model')
        print('SELECT DESIRED MODEL PATH:\n(Reading from {:s}.)'.format(cmd_model_path))
        model_version_path = user.select_a_dir(cmd_model_path,type_flag = 1)
        selected_run_path = user.select_a_dir(model_version_path,type_flag = 1)
        return selected_run_path

    elif mode == 'data':
        data_dir = os.path.join(root_dir, 'data')
        print('SELECT DESIRED DATA PATH:\n(Reading from {:s}.)'.format(data_dir))
        specific_data_dir = user.select_a_dir(data_dir,type_flag = 1)
        return specific_data_dir

    else:                                             
        return "ERROR: Improper mode input for select_pathtofile(mode). Input should be either: mode = \'data\' or mode = \'model\'."
        
# WIP
class isochrone(object):

    def __init__(self, cmdset, age):
        
        # Pick out the relevent age block from the given cmdset:
        age_array = cmdset.ages.values
        age_max = np.amax(age_array)
        age_min = np.amin(age_array)

        # Check if the proposed age is within the valid range:
        if (age_min <= age <= age_max) and (age not in age_array):
         
            isochrone_indexlist = np.where(age_array == age)[0]
         
            # If the age does not exist, but it is within range of valid values:
            if not isochrone_indexlist:
                # Determine the closest ages:
                younger_Age, older_Age = interp.find_closestAges(age, age_array)
                
                # For now just default to the younger age found. Maybe later make this selectable:
                print("log10 age = {:f} was found.".format(younger_Age))
                age = younger_Age

        elif not age_min <= age <= age_max:
            print("isochrone init ERROR: Desired age outside of max/min range of {:.2f} to {:.2f} log10 age.".format(age_min, age_max))
            return
         
        # Now we have an age to work with; so get all models within its block:
        isochrone_indexlist = np.where(age_array == age)[0]
        self.magnitudes = cmdset.magnitudes.ix[isochrone_indexlist,:]
        if cmdset.kind == 'modeltest':
            self.uncertainties = cmdset.uncertainties.ix[isochrone_indexlist,:]

        self.initmasses = cmdset.initmasses.ix[isochrone_indexlist]
        self.age = age
        self.kind = cmdset.kind

    # Plots a magnitude vs. a color for an isochrone, given a dataset and two magnitude indices:
    def isoplotCMD(self, blue_index, red_index, dataset = None, magindex=None):

        if magindex == None and dataset != None:
            dataset_bluemag = dataset.magnitudes.ix[:,blue_index].values
            dataset_redmag = dataset.magnitudes.ix[:,red_index].values
            data_color = dataset_bluemag - dataset_redmag
     
            datamag_blueerr = dataset.uncertainties.ix[:,blue_index].values
            datamag_rederr = dataset.uncertainties.ix[:,red_index].values
            data_colorerr = np.sqrt(datamag_blueerr**2 + datamag_rederr**2)

            plt.errorbar(data_color, dataset_redmag, xerr = data_colorerr, yerr = datamag_rederr, fmt='o')

        elif dataset != None:
            dataset_bluemag = dataset.magnitudes.ix[magindex,blue_index]
            dataset_redmag = dataset.magnitudes.ix[magindex,red_index]
            data_color = dataset_bluemag - dataset_redmag
     
            datamag_blueerr = dataset.uncertainties.ix[magindex,blue_index]
            datamag_rederr = dataset.uncertainties.ix[magindex,red_index]
            data_colorerr = np.sqrt(datamag_blueerr**2 + datamag_rederr**2)

            plt.errorbar(data_color, dataset_redmag, xerr = data_colorerr, yerr = datamag_rederr, fmt='o')

        isomag_blue = self.magnitudes.ix[:,blue_index].values
        isomag_red = self.magnitudes.ix[:,red_index].values 
        color = isomag_blue - isomag_red
        
        if self.kind == 'modeltest':
            isomag_blueerr = self.uncertainties.ix[:,blue_index].values
            isomag_rederr = self.uncertainties.ix[:,red_index].values
            colorerr = np.sqrt(isomag_blueerr**2 + isomag_rederr**2)
            
            plt.errorbar(color, isomag_red, xerr = colorerr, yerr = isomag_rederr,fmt='o')
        
        else:
            plt.plot(color, isomag_red)

        plt.xlabel('{:s} - {:s}'.format(self.magnitudes.ix[:,blue_index].name, self.magnitudes.ix[:,red_index].name))
        plt.ylabel('{:s}'.format(self.magnitudes.ix[:,red_index].name))

        plt.gca().invert_yaxis()

        plt.show()

        return

    # Given an isochrone and proposed initial mass, get the magnitude of the star with the proposed mass:
    def isogetmag(self, initmass, band):

        # Magnitudes and masses of models in the isochrone:
        mag_array = self.magnitudes.values[:, band]
        mass_array = self.initmasses.values
        max_mass = np.amax(mass_array)
        min_mass = np.amin(mass_array)

        # Check if the given mass is within bounds of the predicted masses for the isochrones found:
        # (If within bounds, get the masses from the isochrone.)
        if min_mass < initmass < max_mass:

            mass_index = np.where(mass_array == initmass)[0]

            # If the mass does not exist, need to find adjacent masses and prepare for interpolation.
            if not mass_index:
                # Find the closest masses in this isochrone:
                bigMass, lilMass, bigMass_index, lilMass_index = interp.find_closestMasses(initmass, mass_array)

                # Get corresponding magnitudes:
                bigmag_val = mag_array[bigMass_index]
                lilmag_val = mag_array[lilMass_index]
                massinterp = True

            # Or else the mass was found:
            else:
                mass_val = mass_array[older_mass_index]
                mag_val = mag_array[older_mass_index]
                result = (mag_val, mass_val)
                massinterp = False

        # If the given mass is outside of the bounds of the masses available in the isochrone, return infinity. 
        # This lets the code know that the mass was invalid for the isochrone and could not be interpolated:
        else:
            mag_val = np.inf
            massinterp = False

        # If we need to interpolate between masses to get a magnitude closer to what would come from
        # the proposed mass, then do so:
        if massinterp:

            interpmag = interp.linear_interp(initmass, (lilMass, lilmag_val), (bigMass, bigmag_val))
            mag_val = interpmag
  
        # This should be a number, and if it is infinite then it means a magnitude could not be found;
        # in this case, 0 probability should result, or else the magnitude should not be used.
        return mag_val

