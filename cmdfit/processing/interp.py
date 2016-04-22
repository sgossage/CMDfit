import numpy as np

def linear_interp(given_x, lp, up):
            
            xu, yu = up
            xl, yl = lp
            
            resulting_y = yl + (yu - yl)*(given_x - xl) / (xu - xl)
            
            return resulting_y

def find_closestAges(age, age_array):

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

    closestMass = min(mass_array, key = lambda x: abs(x - initmass))

    # Found the closest mass that is less massive than the given mass.
    if closestMass < initmass:
        closestMass_index = np.where(mass_array == closestMass)[0]
        bigMass = mass_array[closestMass_index + 1]
        lilMass = closestMass
        bigMass_index = closestMass_index + 1
        lilMass_index = closestMass_index

    else:
        closestMass_index = np.where(mass_array == closestMass)[0]
        lilMass = mass_array[closestMass_index - 1]
        bigMass = closestMass
        bigMass_index = closestMass_index
        lilMass_index = closestMass_index - 1 

    if returnIndices:
        return bigMass, lilMass, bigMass_index, lilMass_index
    else:
        return bigMass, lilMass
