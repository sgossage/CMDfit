# The CMDdata class needs to be able to hold however many filters are available to do statistics with...or however many filters are desired to do statistics with.
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
from cmdfit.processing import columnread as cread
from cmdfit.processing import userinteract as user
from cmdfit.processing import interp as interp
from . import isochrone as iso

class cmdset(object):
    
    def __init__(self, kind = 'data', agecut = 0, data_file = None, usecol = None):

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
            
            # If readmode is none of the above, try it out as a filename, if it works, then use auto-mode:
            else:
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
            if readmode == 'model' or 'data':
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
                if readmode == 'data' or readmode == 'modeltest':

                    # For data files, ask about loading in uncertainties from the data table:
                    response = 'n'
                    # Reading uncertainties:
                    if readmode == 'data' and usecol == None:
              
                        print('\nSELECT UNCERTAINTIES FOR {:s}.'.format(dataName))
                        # Ask if uncertainties should be loaded from the data file, or generated in some other way.
                        response = user.ask_for_specific_input('LOAD FROM {:s}? (If \'n\', a nominal +/-0.05 dex will be used.)'.format(data_file.split('/')[-1]), 'y', 'n')
                    
                    if response == 'y':
                            uncertCol, uncertName = cread.assign_data(data_file, mode=readmode, returnNames=True, silent=True)

                    # If the answer is no for loading uncertainties, just sluppy some nominal values.
                    # modeltest cmdsets will always have this value as their uncertainty.
                    elif usecol == None or readmode == 'modeltest':
                        # In the future maybe give some options for users to select how they want to 
                        # generate uncertainties if the data doesn't supply them.
                        uncertCol = [0.05] * len(dataCol)
                        uncertName = dataName + 'err'
                    # If we were given columns they must supply indices to uncertainties as well:
                    elif usecol != None:
                        usecol_index +=1
                        if usecol_index >= len(self.usedcolumns):
                            break
                        usecol = self.usedcolumns[usecol_index]

                        uncertCol, uncertName = cread.assign_data(data_file, mode=readmode, given_column = usecol, returnNames=True, silent=True)                        

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
                print(usecol)
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

            # Now we have a matrix containing all selected magnitudes; 
            # each magnitude set is stored columnwise in dataMatrix and the 
            # respective column names are stored columnwise in dataNames.
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

                return loadedData, loadedUncert, data_file

            # For models return age, mass, and magnitudes:
            return loadedData

        # === Attributes ===: 
        if kind == 'data':
            self.magnitudes, self.uncertainties, filename = loadData(readmode = 'data', data_file=data_file, usecol=usecol)
            self.filename = filename.split('/')[-1]
        
        elif kind == 'model':
            if 5.0 <= agecut <= 10.0:
                self.fullframe = loadData(readmode = 'model', data_file=data_file, usecol=usecol)
                indices = np.where(self.fullframe['log10 age'].values >= agecut)[0]
                self.cutframe = self.fullframe.ix[indices,:].reset_index(drop=True)
                self.ages = self.cutframe.ix[:, 'log10 age']
                self.initmasses = self.cutframe.ix[:, 'Initial Mass']
                self.magnitudes = self.cutframe.ix[:, 2:]
            else:
                self.fullframe = loadData(readmode = 'model', data_file=data_file, usecol=usecol)
                self.ages = self.fullframe.ix[:, 'log10 age']
                self.initmasses = self.fullframe.ix[:, 'Initial Mass']
                self.magnitudes = self.fullframe.ix[:, 2:]
                # Also load info on other params...

        elif kind == 'modeltest':
            if 5.0 <= agecut <= 10.0:
                self.fullframe, self.uncertainties, filename = loadData(readmode = 'modeltest', data_file=data_file, usecol=usecol)
                indices = np.where(self.fullframe['log10 age'].values >= agecut)[0]
                self.cutframe = self.fullframe.ix[indices,:].reset_index(drop=True)
                self.ages = self.cutframe.ix[:, 'log10 age']
                self.initmasses = self.cutframe.ix[:, 'Initial Mass']
                self.magnitudes = self.cutframe.ix[:, 2:]
                self.uncertainties = self.uncertainties.ix[indices,:]
            else:
                self.fullframe, self.uncertainties, filename = loadData(readmode = 'modeltest', data_file=data_file, usecol=usecol)
                self.ages = self.fullframe.ix[:, 'log10 age']
                self.initmasses = self.fullframe.ix[:, 'Initial Mass']
                self.magnitudes = self.fullframe.ix[:, 2:]

            self.filename = filename.split('/')[-1]

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

                mag = iso.isointerpmag(self, initmass, age, age_array, band)                

                # Return the result:
                return mag

            # Now we have an interpolated magnitude in the event that the given age is not found. 
            # If the age was found, just return the corresponding magnitude (will be inf for 
            # invalid masses):
            else:
                isoch = iso.isochrone(self, age)
                return isoch.isogetmag(self, initmass, band)

        # Or else if the proposed age is invalid, return an infinite magnitude to
        # trigger 0 probability for this proposition:
        else:
            return np.inf

    # Confines a datasets magnitudes to a certain range:
    def datacutmags(self, lowerlim, upperlim):


        for i in range(self.numbands):
            #l_indices_tocut = np.where(self.magnitudes.ix[:,i].values < lowerlim)[0]
            u_indices_tocut = np.where(self.magnitudes.ix[:,i].values > upperlim)[0]
            
            if u_indices_tocut.size == 0:
                pass
            else:
                self.magnitudes = self.magnitudes.drop(self.magnitudes.index[u_indices_tocut])
                self.uncertainties = self.uncertainties.drop(self.uncertainties.index[u_indices_tocut])
                self.magnitudes = self.magnitudes.reset_index(drop=True)
                self.uncertainties = self.uncertainties.reset_index(drop=True)

            l_indices_tocut = np.where(self.magnitudes.ix[:,i].values < lowerlim)[0]
            
            if l_indices_tocut.size == 0:
                pass
            else:
                self.magnitudes = self.magnitudes.drop(self.magnitudes.index[l_indices_tocut])
                self.uncertainties = self.uncertainties.drop(self.uncertainties.index[l_indices_tocut])
                self.magnitudes = self.magnitudes.reset_index(drop=True)
                self.uncertainties = self.uncertainties.reset_index(drop=True)

        self.magnitudes = self.magnitudes.reset_index(drop=True)
        self.uncertainties = self.uncertainties.reset_index(drop=True)

        return

    def cutuncert(self, lowerlim, upperlim):


        for i in range(self.numbands):
            #l_indices_tocut = np.where(self.uncertainties.ix[:,i].values < lowerlim)[0]
            u_indices_tocut = np.where(self.uncertainties.ix[:,i].values > upperlim)[0]
            
            if u_indices_tocut.size == 0:
                pass
            else:
                self.uncertainties = self.uncertainties.drop(self.uncertainties.index[u_indices_tocut])
                self.magnitudes = self.magnitudes.drop(self.magnitudes.index[u_indices_tocut])
                self.magnitudes = self.magnitudes.reset_index(drop=True)
                self.uncertainties = self.uncertainties.reset_index(drop=True)

            l_indices_tocut = np.where(self.magnitudes.ix[:,i].values < lowerlim)[0]
            
            if l_indices_tocut.size == 0:
                pass
            else:
                self.uncertainties = self.uncertainties.drop(self.uncertainties.index[l_indices_tocut])
                self.magnitudes = self.magnitudes.drop(self.magnitudes.index[l_indices_tocut])
                self.magnitudes = self.magnitudes.reset_index(drop=True)
                self.uncertainties = self.uncertainties.reset_index(drop=True)

        self.magnitudes = self.magnitudes.reset_index(drop=True)
        self.uncertainties = self.uncertainties.reset_index(drop=True)

        return

    # Make a list of isochrones from a model cmdset:
    def makeisoset(self, low_age = None, high_age = None):

        if low_age == None:
            low_age = min(self.cmdset.ages.values)
        if high_age == None:
            high_age = max(self.cmdset.ages.values)

        lowindex = np.where(self.ages.values >= low_age)[0][0]
        highindex = np.where(self.ages.values <= high_age)[0][-1] + 1

        isoset = [iso.isochrone(self, age) for age in np.unique(self.ages.values[lowindex:highindex])]
        
        return isoset

    # Random sampling of dataset:
    def randsamp(self, samplenum):
    
        if self.kind == 'data':
            self.magnitudes = self.magnitudes.sample(samplenum)
            indices = self.magnitudes.index
            self.uncertainties = self.uncertainties.ix[indices].reset_index(drop=True)
            self.magnitudes = self.magnitudes.reset_index(drop=True)
        
        return
                


# For getting magnitudes across cmdsets:
def getcmdsetsmag(allmodel_cmdsets, age, initmass, FeH, FeH_list, data_bandindex, secondarymass = None):

    # Here I should check on interpolating between metallicities; 
    # if necessary, getmag from two nearest cmdsets and interpolate 
    # a new magnitude at the given metallicity if the given metallicity 
    # does not exist. Check an input list of available metallicities:
    FeH_max = np.amax(FeH_list)
    FeH_min = np.amin(FeH_list)

    # If the given metallicity was not found, but it is within valid range:
    if (FeH not in FeH_list) and (FeH_min <= FeH <= FeH_max):
        # Find cmdsets with closest FeH:
        FeHrich, FeHpoor, FeHrich_index, FeHpoor_index = interp.find_closestFeHs(FeH, FeH_list)

        # Calculate model magnitudes from each:
        FeHrich_mag = allmodel_cmdsets[FeHrich_index].getmag(age, initmass, data_bandindex)
        FeHpoor_mag = allmodel_cmdsets[FeHpoor_index].getmag(age, initmass, data_bandindex)

        if secondarymass != None:
            FeHrich_mag2 = allmodel_cmdsets[FeHrich_index].getmag(age, secondarymass, data_bandindex)
            FeHpoor_mag2 = allmodel_cmdsets[FeHpoor_index].getmag(age, secondarymass, data_bandindex)

        # If both interpolated magnitudes were produced from values within valid ranges of mass and age:
            if np.isfinite(FeHpoor_mag) and np.isfinite(FeHrich_mag) and np.isfinite(FeHpoor_mag2) and np.isfinite(FeHrich_mag2):
                # Finally interpolate using the closest FeHs and their magnitudes to get the magnitude at the given FeH:
                model_mag = interp.linear_interp(FeH, (FeHpoor, FeHpoor_mag), (FeHrich, FeHrich_mag))
                model_mag2 = interp.linear_interp(FeH, (FeHpoor, FeHpoor_mag2), (FeHrich, FeHrich_mag2))
                # Combine magnitudes:
                model_mag = -2.5 * np.log10(10**(-model_mag/2.5) + 10**(-model_mag2/2.5))
            
            else:
                model_mag = np.inf

        # If not using a secondary initial mass:
        elif np.isfinite(FeHpoor_mag) and np.isfinite(FeHrich_mag):
            model_mag = interp.linear_interp(FeH, (FeHpoor, FeHpoor_mag), (FeHrich, FeHrich_mag))
        
        # Or else if FeH interpolation could not be done, either because of invalid mass or age,
        # can't interpolate between inf, so make the probability 0:
        else:
            model_mag = np.inf

        return model_mag

    # Or else if the metallicity already exists:
    elif FeH_min <= FeH <= FeH_max:

        # Get the right index:
        FeH_index = np.where(FeH_list == FeH)[0]
        # Get the magnitude:
        model_mag = allmodel_cmdsets[FeH_index].getmag(age, initmass, data_bandindex)
        
        # If necessary, get the secondary mass' magnitude too:
        if secondarymass != None: 
            model_mag2 = allmodel_cmdsets[FeH_index].getmag(age, secondarymass, data_bandindex)
            # Combine magnitudes:
            model_mag = -2.5 * np.log10(10**(-model_mag/2.5) + 10**(-model_mag2/2.5))

        return model_mag

    # Or else if FeH is not in the valid range, make probability zero:
    else:
        return np.inf

                 
def all_modelcmdsets(agecut = 0, usecol = None, default = False):

    # Go to a desired directory and get all of the .cmd files there:
    if default:
        selected_run_path = select_pathtofile('defaultmodel')
    else:
        selected_run_path = select_pathtofile('model')

    # Load all files in the selected directory:
    data_files = cread.getall_files(selected_run_path)
    print("In " + selected_run_path + "...")
    for filename in data_files:
        print("Found " + filename.split('/')[-1] + "...")

    model_cmdsets = []
    usedcolumns = usecol
    print()
    
    # Loop through model files and create a cmdset from each:
    for i in range( len(data_files) ):
        
        print('\n======================================================================')
        print('Creating model cmdset #{:d} for '.format(i) + data_files[i].split('/')[-1] + '...')

        model_cmdsets.append(cmdset('model', agecut, data_files[i], usedcolumns))

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

    elif mode == 'defaultmodel':
        model_dir = os.path.join(root_dir, 'model')
        modeltype_dir = os.path.join(model_dir, 'MIST_v0.31')
        modelrun_dir = os.path.join(modeltype_dir, 'HBlim005')
        return modelrun_dir

    elif mode == 'defaultdata':
        data_dir = os.path.join(root_dir, 'data')
        specific_data_dir = os.path.join(data_dir, 'Hyades')
        return specific_data_dir

    else:                                             
        return "ERROR: Improper mode input for select_pathtofile(mode). Input should be either: mode = \'data\' or mode = \'model\'."


        
        
