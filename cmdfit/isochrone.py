import numpy as np
import matplotlib.pyplot as plt
from cmdfit.processing import interp


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
    def isoplotCMD(self, blue_index, red_index, dataset = None, magindex=None, inverty = True, show=True):

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

        if inverty:
            plt.gca().invert_yaxis()
        if show:
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

# Given a cmdset (set of isochrones), finds the ages nearest to the given age and interpolates a magnitude
# at the given mass:
def isointerpmag(cmdset, initmass, age, age_array, band):

    # if we actually don't need to interpolate, just return the magnitude at
    # the given mass:
    if age in age_array:
        print('log10 age = {:f} exists; no need to interpolate!'.format(age))
        return isochrone(cmdset, age).isogetmag(initmass, band)
    
    # Determine the closest ages via interpolation:
    younger_Age, older_Age = interp.find_closestAges(age, age_array)            

    # Pick out their isochrones:
    younger_iso = isochrone(cmdset, younger_Age)
    older_iso = isochrone(cmdset, older_Age)
               
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

# Plots an array of isochrones.
def multiisoCMD(isochrone_set):
  
    numisos = len(isochrone_set)

    for iso in isochrone_set:
        iso.isoplotCMD(0,1, show=False, inverty=False)

    plt.gca().invert_yaxis()
    plt.show()

    return
