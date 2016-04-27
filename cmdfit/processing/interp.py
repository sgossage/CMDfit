import numpy as np

def linear_interp(given_x, lp, up):

            xu, yu = up
            xl, yl = lp

            #print(given_x)
            #print(xl)
            #print(xu)
            #print(yl)
            #print(yu)
            
            
            resulting_y = yl + (yu - yl)*(given_x - xl) / (xu - xl)
            
            return resulting_y

# These finding functions require that their input array be in ascending order as is...

def find_closestAges(age, age_array):

    #age_array = np.array(age_array)

    # Determine the closest ages:
    closestAge = min(age_array, key = lambda x: abs(x - age))

    if closestAge < age:
        # The index of the last element in the closest age isochrone.
        closestAge_index = np.where(age_array == closestAge)[0][-1]
        # Taking this index and adding one to enter the next closest isochrone and grab its age:
        older_Age = age_array[closestAge_index + 1]
        younger_Age = closestAge

    else:
        closestAge_index = np.where(age_array == closestAge)[0][0]
        younger_Age = age_array[closestAge_index - 1]
        older_Age = closestAge
  
    return younger_Age, older_Age

def find_closestMasses(initmass, mass_array, returnIndices = True):

    #mass_array = np.array(mass_array)

    closestMass = min(mass_array, key = lambda x: abs(x - initmass))
        

    # Found the closest mass that is less massive than the given mass.
    if closestMass < initmass:
        closestMass_index = np.where(mass_array == closestMass)[0]

        # If an array of indices were found...
        if isinstance(closestMass_index, list) or isinstance(closestMass_index, np.ndarray):
            closestMass_index = closestMass_index[0]

        bigMass = mass_array[closestMass_index + 1]
        lilMass = closestMass
        bigMass_index = closestMass_index + 1
        lilMass_index = closestMass_index

    else:
        closestMass_index = np.where(mass_array == closestMass)[0]
        
        # If an array of indices were found...
        if isinstance(closestMass_index, list) or isinstance(closestMass_index, np.ndarray):
            closestMass_index = closestMass_index[0]
   
        lilMass = mass_array[closestMass_index - 1]
        bigMass = closestMass
        bigMass_index = closestMass_index
        lilMass_index = closestMass_index - 1 

    if returnIndices:
        return bigMass, lilMass, bigMass_index, lilMass_index
    else:
        return bigMass, lilMass

def find_closestFeHs(FeH, FeH_array, returnIndices = True):
    
    FeH_array = np.array(FeH_array)
    
    closestFeH = min(FeH_array, key = lambda x: abs(x - FeH))

    # Found the closest FeH that is poorer than the given FeH.
    if closestFeH < FeH:
        closestFeH_index = np.where(FeH_array == closestFeH)[0][0]
        richFeH = FeH_array[closestFeH_index + 1]
        poorFeH = closestFeH
        richFeH_index = closestFeH_index + 1
        poorFeH_index = closestFeH_index

    # '                           ' richer than the given FeH.
    else:
        closestFeH_index = np.where(FeH_array == closestFeH)[0][0]
        poorFeH = FeH_array[closestFeH_index - 1]
        richFeH = closestFeH
        richFeH_index = closestFeH_index
        poorFeH_index = closestFeH_index - 1 

    if returnIndices:
        return richFeH, poorFeH, richFeH_index, poorFeH_index
    else:
        return richFeH, poorFeH
