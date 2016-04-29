import os

# ======================================================================================================================================================

def select_a_dir(dir_to_search, type_flag = 1):
    """
    This takes in a directory (string) to search and diplay all of the subdirectories from.
    Then, the subdirs are displayed and the user is asked to select one subdirectory.
    The name of this subdirectory is returned as a string with / prepended to it.

    The param called type may be used as 0, 1, or 2 to select from the current dir (not too helpful),
    the sub directories, or the files contained in the search dir, respectively.
    """
    contents_list = next(os.walk(dir_to_search))[type_flag]     
    

    readin_types = ['directory', 'file']
    
    print('-----------------------------------------------')
    # Have user select the directory to enter for the desired iso files:
    print('Select the desired {:s} from those found below:'.format(readin_types[type_flag - 1]))
    print('===============================================')
    for i, name in enumerate(contents_list):
        print("{:d}) {:s}".format(i, name))

    # Ask for file selection (as an int) from the displayed results:
    print('===============================================')
    selection = ask_for_specific_input("Enter the index of the desired {:s}".format(readin_types[type_flag -1]), type_to_check = int)
    print('-----------------------------------------------')
    
    # return the path to the selected sub-directory or file:
    return os.path.join(dir_to_search, contents_list[selection])  

# ======================================================================================================================================================
# ======================================================================================================================================================

def ask_for_specific_input(question, positive_answer = None, negative_answer = None, type_to_check = None):
    
    """
    This function takes asks the user the given question (a string). It asks until an answer is given that matches one of the specified
    negative or positive answers. The answer is returned once it matches the specified.

    May also be put in 'type' mode to check if the input "type_to_check" (a type, e.g. str, int, ...) matches the type of the input to the question. 
    """
    
    if type_to_check == None:
        # case where possible inputs are strings:
        if isinstance(positive_answer, str):
        
            answer = None        
            while (answer != positive_answer) and (answer != negative_answer):

                # Keep asking the question until one of the specified answers is given:
                answer = input("{:s} (\'{:s}\' or \'{:s}\'): ".format(question, positive_answer, negative_answer))

    	# case where a list of possible inputs is given:
        if isinstance(positive_answer, list):
        
            answer = None
            while(answer not in positive_answer) and (answer not in negative_answer):
            
                # Keep asking the question until one of the specified answers is given:
                answer = input("{:s}: ".format(question))

    if type_to_check != None:
        # case where the function checks if the input matches a certain type
        answer = None
        while type(answer) != type_to_check:
            
            # Keep asking the question until one of the specified answers is given:
            answer = input("{:s} (requesting type: {:s}): ".format(question, type_to_check.__name__))
            
            # If an int was entered and the requested type is int, convert the string to an int:
            if is_int(answer) and type_to_check == int:
                answer = int(answer)

            # Or if the required type is float, convert the string to float:
            if is_float(answer) and type_to_check == float:
                answer = float(answer)

    return answer

# =========================================================================================================================================================
# =========================================================================================================================================================

# Functions that check if strings maybe should be ints or floats:

def is_int(string):
    """
    Checks if the input string is a number.
    """
    
    try:
        int(string)
        return True
    except ValueError:
        return False

def is_float(string):
    """
    Checks if the input is a float.
    """
    
    try:
        float(string)
        return True
    except ValueError:
        return False     

# ==========================================================================================================================================================
    
