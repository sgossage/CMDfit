import numpy as np
import re
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
    for string in lines:
        if '#' in string:
            comments.append(string)
        # Break if we've gone past top most comments:
        if '#' not in string:
            break

    # Assumes that the header is contained in the last set of comments:
    header_str = comments[-1]
    # Clean the header:
    hlist = (header_str.split('#')[1]).split()

    # Returns the list of header names.
    if mode == 'data':
        return hlist
    if mode == 'model':
        return hlist[6:]

# ==========================================================================================================================

def header_select_col(data_file, operation = None, axis= None, mode = 'data', returnNames = False):

    # Report the headers:
    hlist = get_header(data_file, mode)

    print('Select data columns from {:s}'.format(data_file.split('/')[-1]))
    print('========================================================')
    for i, name in enumerate(hlist):
        print('{:d}) {:s}'.format(i, name))
        
    print('========================================================')
    
    if axis != None:
        col1 = user.ask_for_specific_input('COL1 ({:s} axis): '.format(axis), type_to_check = int)
    # If just loading data...
    else:
        col1 = user.ask_for_specific_input('ENTER COLUMN INDEX OF DESIRED FILTER: ', type_to_check = int)

    # If having a color is requested for this axis, will need to select a second magnitude.
    if operation == '1m2':

        col2 = user.ask_for_specific_input('COL2 ({:s} axis): '.format(axis), type_to_check = int)
    
        # Case where the header names for the selected columns are returned as well:
        if returnNames:
            return col1, col2, hlist[col1], hlist[col2]
        else:
            return col1, col2

    else:
        
        if returnNames:
            return col1, hlist[col1]
        else:
            return col1

# ==========================================================================================================================

def get_values(data_file, column_index, mode='data', model_extras=False):
    print('\nLoading data from {:s}...\n'.format(data_file.split('/')[-1]))
    # Open the data file and read in all lines, then close the file buffer:
    f = open(data_file)
    lines = f.readlines()
    f.close()

    # Remove comment lines:
    data_lines = []
    for string in lines:
        if '#' not in string:
            data_lines.append(string)
    
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
        if mode == 'model':
            if not l:
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

    elif mode == 'model':
        if model_extras:
            return np.array(data_column), np.array(age_column), np.array(mass_column)
        else:
            return np.array(data_column)
    
# ==========================================================================================================================

def assign_data(cmd_datafile, operation = None, axis = None, mode = 'data', returncols = False, returnNames = False, model_extras=False, corrections=None):
    
    if axis != None:
        print('\nDATA FOR {:s}-AXIS:\n'.format(axis))
    else:
        print('\nASSIGNING DATA...\n')    

    # Get two data columns if we need to do col1 - col2 for e.g. a color like B-V, or else just get one column for e.g. a V maginitude:
    if operation == '1m2':
        # If we need the header names...
        if returnNames:
            col1, col2, col1_name, col2_name = header_select_col(cmd_datafile, operation, axis, mode, returnNames) 
        # Or if we do not need the names...
        else:
            col1, col2 = header_select_col(cmd_datafile, operation, axis, mode)
    # Same as block above, but not subtracting magnitudes:
    else:
        if returnNames:
            col1, col1_name = header_select_col(cmd_datafile, operation, axis, mode, returnNames)
        else:
            col1 = header_select_col(cmd_datafile, operation, axis, mode)

    # with mode = 'model' in the header_select_... function, the returned column numbers will be offset by 6, since it skips
    # the columns which are not bandpass magnitudes. Here, that offset is corrected.
    if mode == 'model':
        col1 += 6
        # column 2 only exists if the operation is col1 - col2.
        if operation == '1m2':
            col2 += 6

    # If returning extra values and not just magnitude:
    if model_extras:
        data1, agecol, masscol = get_values(cmd_datafile, col1, mode, model_extras)
        data_assignment = data1

        if corrections == 'ABtoVega':
            data_assignment = magcorr.ABtoVega(data_assignment, band_column=col1)

        ages = agecol
        masses = masscol
        if returncols:
            if returnNames:
                return data_assignment, col1, col1_name, ages, masses
            else:
                return data_assignment, col1, ages, masses
        else:
            if returnNames:
                return data_assignment, col1_name, ages, masses
            else:
                return data_assignment, ages, masses

    # Or else if just returning magnitude(s):
    else:
        data1 = get_values(cmd_datafile, col1, mode)
        if operation == '1m2':
            data2 = get_values(cmd_datafile, col2, mode)

        # Perform desired operation:
        if operation == '1m2':
            data_assignment = data1 - data2
        else:
            data_assignment = data1

        # If requested, return the selected columns along with the data:
        if returncols:
            if operation == '1m2':
                if returnNames:
                    return data_assignment, col1, col2, col1_name, col2_name
                else:
                    return data_assignment, col1, col2
            else:
                if returnNames:
                    return data_assignment, col1, col1_name
                else:
                    return data_assignment, col1

        else:
            if operation == '1m2':
                if returnNames:
                    return data_assignment, col1_name, col2_name
                else:
                    return data_assignment
            else:
                if returnNames:
                    return data_assignment, col1_name
                else:
                    return data_assignment


    
