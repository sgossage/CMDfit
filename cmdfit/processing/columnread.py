import numpy as np
import re
import os
from . import userinteract as user
from . import magcorrections as magcorr

# ==========================================================================================================================

def get_header(data_file, mode = 'data'):

    """
        Extracts the header of a data file.
    """

    # Assumes that the files comments include '#' in them

    f = open(data_file)

    lines = f.readlines()
    f.close()

    comments = []
    #metadata_numlines = 1
    #metadata_linesread = 0

    for string in lines:
        if '#' in string:
            comments.append(string)
        # Break if we've gone past top most comments:
        if '#' not in string:
            # In MIST model files, metadata will exist on an uncommented line before the header, 
            # so don't exit just because we've reached that line:
            #if mode == 'model' or mode == 'modeltest' and metadata_linesread < metadata_numlines:
            #    metadata_linesread += 1
            #    continue
                
            break

    # Assumes that the header is contained in the last set of comments:
    header_str = comments[-1]
    # Clean the header:
    hlist = (header_str.split('#')[1]).split()

    # Returns the list of header names.
    if mode == 'data':
        return hlist
    if mode == 'model' or mode == 'modeltest':
        modelfile_skippedcols = 7
        return hlist[modelfile_skippedcols:]

# ==========================================================================================================================

def header_select_col(data_file, mode = 'data', returnNames = False, silent=False):

    """
      Asks user to select a column from which data will be read.
    """
    
    # Get the header names in a list:
    hlist = get_header(data_file, mode)
    
    if silent != True:

        # Report the headers:
        print('Select data columns from {:s}'.format(data_file.split('/')[-1]))
        print('========================================================')
        for i, name in enumerate(hlist):
            print('{:d}) {:s}'.format(i, name))
        print('========================================================')
    
    col1 = user.ask_for_specific_input('ENTER COLUMN INDEX OF DESIRED FILTER: ', type_to_check = int)
        
    if returnNames:
        return col1, hlist[col1]
    else:
        return col1

# ==========================================================================================================================

def get_values(data_file, column_index, mode='data', model_extras=False):

    """
      Handles the loading of data; loads a single column.
    """

    #print('\nLoading data from {:s}...'.format(data_file.split('/')[-1]))
    # Open the data file and read in all lines, then close the file buffer:
    f = open(data_file)
    lines = f.readlines()
    f.close()

    # Remove comment lines:
    data_lines = []
    for string in lines:
        if '#' not in string:
            data_lines.append(string)

    # If the mode is set to a model file, pick out the first uncommented line...in MIST .cmd files this line holds
    # metadata; this block grabs the meta data and separates it from the other data lines.
    if mode == 'model' or mode == 'modeltest':
        # metadata  exists on the sixth line in MIST model files.
        meta_data = re.compile('[+-]?\d+\.\d+|[+-]?\d+\.\d+\[eE][+-]?\d+').findall(lines[5])
        data_lines = data_lines[1:]
    
    # Look through lines and pick values from the desired column:
    data_column = []
    if model_extras:
        mass_column = []
        age_column = []

    for line in data_lines:
        if mode == 'data':
            l = re.compile('[+-]?\d+\.\d+|\w+|       ').findall(line)
            # delete the first blank, if it's there:
            if ' ' in l[0]:
                l = np.delete(l, 0).tolist()
        # if dealing with the iso .cmd file, the following format is req. for the data entries:
        else:
            l = re.compile('[+-]?\d+\.\d+[eE][-+]?\d+|[+-]?\d+\.\d+|[+-]?\d+').findall(line)
        
        # For model files, we need to skip the lines between isochrones which exist in blocks separated by several empty lines.
        # Also, incomplete lines should be skipped -- I have a quick fix to handle this, but it should be ammended later.
        # Right now the code just checks if the length is less than the selected clumn index to mark incomplete lines.
        if mode == 'model' or mode == 'modeltest':
            if not l or len(l) < column_index:
                continue

        # Now we can work with the line. Try to convert it to a float and append it to the list of data values:
        try:
            data_column.append(eval(l[column_index]))
            if model_extras:
                age_column.append(eval(l[1]))
                mass_column.append(eval(l[2]))
        # If that is a failure, report the error and do not append the data point since it doesn't exist:
        except ValueError:
            print('WARNING: Could not convert data element to float.')
    
    if mode == 'data':
        return np.array(data_column)

    elif mode == 'model' or mode == 'modeltest':
        # If returning ages, masses, and meta data (i.e., extras) w/ the magnitudes:
        if model_extras:
            return np.array(data_column), np.array(age_column), np.array(mass_column), np.array(meta_data)
        # Or else if just returning the magnitudes:
        else:
            return np.array(data_column)
    
# ==========================================================================================================================

def assign_data(cmd_datafile, mode = 'data', given_column = None, returncols = False, returnNames = False, model_extras=False, corrections=None, silent=False):
    
    """
      returns columns in a useful way (e.g. mass, age, and a magnitude all together), or the columns with their names and indices.
    """
    modelfile_skippedcols = 7
    
    if given_column != None:
        col1 = given_column
        hlist = get_header(cmd_datafile, mode)
        # get_header() skips the first 6 columns (b/c they are not magnitudes), so need to offset
        # the given column index by seven.
        col1_name = hlist[col1 - modelfile_skippedcols]
        print('------------------------------------------------------------------------')
        print('\nASSIGNING {:s}...'.format(col1_name) + 'for ' + cmd_datafile.split('/')[-1])    

    else:
        # Get one column index and possibly header name for a desired magnitude:
        if returnNames:
            col1, col1_name = header_select_col(cmd_datafile, mode, returnNames, silent=silent)
        else:
            col1 = header_select_col(cmd_datafile, mode, silent=silent)

        print('------------------------------------------------------------------------')
        print('\nASSIGNING {:s}...'.format(col1_name) + 'for ' + cmd_datafile.split('/')[-1])    

    # with mode = 'model' in the header_select_... function, the returned column 
    # numbers will be offset by 6, since it skips the columns which are not bandpass
    # magnitudes. Here, that offset is corrected.

    # A given column will have already had this offset applied, so no need to do it again.
    if mode == 'model' or mode == 'modeltest'and given_column == None:
        col1 += modelfile_skippedcols

    # If returning extra values (masses and ages of all stars) and not just magnitudes:
    if model_extras:

        # Extract magnitude, age, and mass columns; get_values(...) knows where to
        # find age and mass based on the MIST file format.
        data_assignment, agecol, masscol, metadata = get_values(cmd_datafile, col1, mode, model_extras)

        # Convert magnitudes from AB system to Vega:
        if corrections == 'ABtoVega':
            data_assignment = magcorr.ABtoVega(data_assignment, band_column=col1)

        # Arrays holding mass and age:
        ages = agecol
        masses = masscol

        # Return age, magnitude, and masses (w/ or w/o magnitude column index or header names):
        if returncols:
            if returnNames:
                return data_assignment, col1, col1_name, ages, masses, metadata
            else:
                return data_assignment, col1, ages, masses, metadata
        else:
            if returnNames:
                return data_assignment, col1_name, ages, masses, metadata
            else:
                return data_assignment, ages, masses, metadata

    # Or else if just returning magnitudes:
    else:
        data_assignment = get_values(cmd_datafile, col1, mode)

        if corrections == 'ABtoVega':
            data_assignment = magcorr.ABtoVega(data_assignment, band_column=col1)

        # If requested, return the selected columns and header name along with the 
        # selected magnitude:
        if returncols:
            if returnNames:
                return data_assignment, col1, col1_name
            else:
                return data_assignment, col1

        else:
            if returnNames:
                return data_assignment, col1_name
            else:
                return data_assignment

# ======================================================================================================================================================

def getall_files(file_dir):

    """
      Reads and returns a list containing the paths to all files in the input directory.
    """

    # Returns an array of all files in a selected directory.
    
    # file list is an array of strings; each string is the name of a file in the given directory
    file_list = next(os.walk(file_dir))[2]

    for i in range(len(file_list)):

        # Add on the directory's path to turn each list element into the full path to the file:
        file_list[i] = file_dir + "/" + file_list[i]

    # Return file_list as a list of fulls paths to each file:
    return file_list

# ======================================================================================================================================================

    
