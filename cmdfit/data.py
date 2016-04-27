# The CMDdata class needs to be able to hold however many filters are available to do statistics with...or however many filters are desired to do statistics with.
import numpy as np
import pandas as pd
import os
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
                    data_file = specific_data_dir + user.select_a_dir(specific_data_dir, 2)

                extras_flag = False

            elif readmode == 'model' or readmode == 'modeltest':
                if data_file == None:

                    selected_run_path = select_pathtofile(readmode)
                    data_file = selected_run_path + user.select_a_dir(selected_run_path,type_flag = 2)
                
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
                if usecol == None:
                    self.usedcolumns = []
                else:
                    self.usedcolumns = np.array(usecol)
                    usecol_index = 0
                    usecol = self.usedcolumns[usecol_index]
           
            # Flag to suppress reporting of header names:
            silent_flag = False

            # This while loop runs a number of times to allow the user to select which columns to read in from the data file:
            while keepgoing:
                
                if extras_flag:
                    dataCol, usedcol, dataName, ages, masses, metadata = cread.assign_data(data_file, mode=readmode, 
                                                                                             given_column=usecol, returncols=True, 
                                                                                               returnNames=True, model_extras=extras_flag, 
                                                                                                 corrections='ABtoVega', silent=silent_flag)
                else:
                    dataCol, usedcol, dataName = cread.assign_data(data_file, mode=readmode, given_column=usecol, returncols=True, returnNames=True, corrections='ABtoVega', silent=silent_flag)
                
                # Ask about supplying uncertainty values from the data table:
                if readmode == 'data' or 'modeltest':

                    # For data files, ask about loading in uncertainties from the data table:
                    response = 'n'
                    if readmode == 'data':

                        print('\nSELECT UNCERTAINTIES FOR {:s}.'.format(dataName))
                        # Ask if uncertainties should be loaded from the data file, or generated in some other way.
                        response = user.ask_for_specific_input('LOAD FROM {:s}? (If \'n\', a nominal +/-0.1 dex will be used.)'.format(data_file.split('/')[-1]), 'y', 'n')
                    
                    if response == 'y':
                            uncertCol, uncertName = cread.assign_data(data_file, mode=readmode, returnNames=True)

                    # If the answer is no for loading uncertainties, just suppy some nominal values. modeltest cmdsets will always have this value as their uncertainty.
                    else:
                        # In the future maybe give some options for users to select how they want to generate uncertainties if the data doesn't supply them.
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

        # Search for the given age, then the given mass, then get the magnitude and return it. Not always so easy; if necessary, interpolate.
        # So check if the given age exists already and get the indices of these entries if it does:
        age_array = self.ages.values
        mass_array = self.initmasses.values        
        mag_array = self.magnitudes.values[:, band]
        
        isochrone_indexlist = np.where(age_array == age)[0]
       
        # If the age does not exist, but it is within range of valid values:
        if not isochrone_indexlist:
            # Determine the closest ages via interpolation:
            younger_Age, older_Age = interp.find_closestAges(age, age_array)            
            
            # Get indices of all stars corresponding to the found ages (this is an isochrone block):
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
            
            # If the isochrone doesn't have the mass available, return infinity. This lets the code know that 
            else:
                # Making older_mass_index not empty will signal that no older mass was found.
                older_mass_index = [0]
                older_mag_val = np.inf
            
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
            else:
                younger_mass_index = [0]
                younger_mag_val = np.inf

            # Need a plan to deal with if the mass is NOT within these ranges...maybe return a weird number to let rest of code know to kill this value.
            
            # Right now, Ill just linearly interpolate...
            # Given then masses found and the magnitudes found, and the given initial mass, linearly interpolate the magnitude for the younger and older isochrones:
            # This  is if the given mass was not found:
            older_interp = False
            younger_interp = False
 
            # If we need to interpolate masses in the younger isochrone:
            if not younger_mass_index:
                younger_interpmag = interp.linear_interp(initmass, (younger_lilMass, younger_lilmag_val), (younger_bigMass, younger_bigmag_val))
                younger_interp = True
                # Set younger_mag_value to this interpolated value. This may then be used in case the mass was
                # already existent in the older isochrone:
                younger_mag_val = younger_interpmag
 
            # If we need to interpolate masses in the older isochrone:
            if not older_mass_index:
                older_interpmag = interp.linear_interp(initmass, (older_lilMass, older_lilmag_val), (older_bigMass, older_bigmag_val))
                older_interp = True
                older_mag_val = older_interpmag

            # If we were able to interpolate masses in both isochrones, interpolate between isochrone ages:
            if older_interp and younger_interp:
                # Now use the newly interpolated magnitudes for each isochrone and interpolate between isochrones to get the interpolated magnitude at the desired age:
                interpmag = interp.linear_interp(age, (younger_Age, younger_interpmag), (older_Age, older_interpmag))

            # Or else if either interpolation did not take place in both isochrones...
            else: 
                # ...but masses were in range in both isochrones, then it just means the masses already existed, so just interpolate between isochrones:
                if np.isfinite(younger_mag_val) and np.isfinite(older_mag_val):
                    interpmag = interp.linear_interp(age, (younger_Age, younger_mag_val), (older_Age, older_mag_val))

                # If either mass was out of range for an isochrone, then return a weird value to let the code know:
                else:
                    interpmag = [np.inf]   
         
            if isinstance(interpmag, float) or isinstance(interpmag, int):
                return interpmag
            else:
                return interpmag[0]

        # Now we have an interpolated magnitude in the event that the given age is not found. 
        # If the age was found, just return the corresponding magnitude as long as the given mass is within range
        # for the relevant isochrone.
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

            # Or else if the mass was not in range for the isochrone, return infinity to let the code know. These values will have zero probability.
            else:
                return [np.inf]
                 
def all_modelcmdsets():

    # Go to a desired directory and get all of the .cmd files there:

    # root_dir should be /cmdfit
    #root_dir = os.path.dirname(os.path.abspath(__file__))
    #cmd_model_path = root_dir + '/model'
    #print('SELECT DESIRED MODEL PATH:\n(Reading from {:s}.)'.format(cmd_model_path))
    #specific_model_path = cmd_model_path + user.select_a_dir(cmd_model_path,type_flag = 1)
    selected_run_path = select_pathtofile('model')#specific_model_path + user.select_a_dir(specific_model_path,type_flag = 1)

    # Load all files in the selected directory:
    data_files = cread.getall_files(selected_run_path)
    print("In " + selected_run_path + "...")
    for filename in data_files:
        print("Found " + filename.split('/')[-1] + "...")

    model_cmdsets = []
    usedcolumns = None
    print()

    for i in range( len(data_files) ):
        
        print('======================================================================')
        print('Creating model cmdset for ' + data_files[i].split('/')[-1] + '...')

        model_cmdsets.append(cmdset('model', data_files[i], usedcolumns))

        # On subsequent loops, use the user selected columns of the first model cmdset:
        usedcolumns = model_cmdsets[0].usedcolumns

    return model_cmdsets

def select_pathtofile(mode):
            
    # returns string in the form of '/path/to/file'

    # root_dir path should lead to /cmdfit.
    root_dir = os.path.dirname(os.path.abspath(__file__))

    # For running tests, this function just returns the root directory.
    if mode == 'test':
        return root_dir

    elif mode == 'model' or mode == 'modeltest':
        cmd_model_path = root_dir + '/model'
        print('SELECT DESIRED MODEL PATH:\n(Reading from {:s}.)'.format(cmd_model_path))
        model_version_path = cmd_model_path + user.select_a_dir(cmd_model_path,type_flag = 1)
        selected_run_path = model_version_path + user.select_a_dir(model_version_path,type_flag = 1)
        return selected_run_path

    elif mode == 'data':
        data_dir = root_dir + '/data'
        print('SELECT DESIRED DATA PATH:\n(Reading from {:s}.)'.format(data_dir))
        specific_data_dir = data_dir + user.select_a_dir(data_dir,type_flag = 1)
        return specific_data_dir

    else:                                             
        return "ERROR: Improper mode input for select_pathtofile(mode). Input should be either: mode = \'data\' or mode = \'model\'."
            
