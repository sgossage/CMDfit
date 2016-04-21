import numpy as np

def likelihood(data_mag, phot_uncert, model_cmdset, data_mag_max, data_mag_min, calc_log = False):

    """
    The form used here is based on the likelihood function used by van Dyk et al. 2009.

    INPUT:
    =====================================================================================================
    
        data_mag (float):
        +++++++++++++++++++++
          A number taken from a data table. Meant to be the value of a measured magnitude
        for an observed star in a stellar cluster (our definition of a data point).

        phot_uncert (float):
        ++++++++++++++++++++++
          The photometric uncertainties recorded along with the supplied data. This is photon shot noise
        essentially and represents the variance of the distribution from which our data has been drawn.
        
        model_mag (float):
        ++++++++++++++++++++++
          A number taken from a file holding tabulated magnitudes from a stellar evolution model 
        simulation.

        data_mag_max (float):
        +++++++++++++++++++++
          Maximum magnitude from array of data points under consideration. For use in determining a field
        star magnitude distribution.
    
        data_mag_min (float):
        +++++++++++++++++++++
          Minimum magnitude from array of data points under consideration. For use in determining a field
        star magnitude distribution.
    
    OUTPUT:
    ======================================================================================================

        return (float):
        +++++++++++++++++++
          Result of the likelihood calculation. This is the probability of the model being a good 
        representation of the data.

    OPTIONS:
    ======================================================================================================

        calc_log (bool):
        +++++++++++++++++++
          Default: False

          If set to True, this option will set the returned value to be the log (base e) of the calculated
        likelihood function.
    """
    
    # CHANGES TO MAKE:
    # Have this function take in theta (a list of parameters such as initmass, age, FeH), instead of model_mag. Implement code to
    # have this function search the model cmdset for the point corresponding to the supplied parameters...if it DNE, interpolate it.
    # Search for the metallicity file corresp. to selected FeH. Should search the age and get that block.
    # Then search the block (isochrone) for the corresponding init mass. If it DNE, interpolate the two adjacent rows.
    # Will need to interpolate the corresp. magnitudes. Look up the corresp. mag and use that for the model value.
    age, initmass = theta
    model_mag = model_cmdset.getmag(age, initmass)  
    
    # MAKE THIS INPUT SETH <><@! (prob. of being a field star for mixture model)
    Pfield = 0.25

    # Terms going into construction of the Gaussian term of the likelihood function (described in model.ipynb):
    sigma = phot_uncert
    const_factor = 1.0 / np.sqrt(2.0 * np.pi * sigma**2.0)
    residual = data_mag - model_mag
    exponent = -0.25 * (residual / sigma)**2.0

    # Uniform distribution from which magnitudes may be drawn in the case of a field star:
    field_distribution = 1.0 / (data_mag_max - data_mag_min)
    
    # Likelihood functions for the ith data point compared to the ith model point in the single filter:
    cluster_likelihood = (1 - Pfield) * const_factor * np.exp(exponent)
    field_likelihood = Pfield * field_distribution

    # Return the total likelihood function:
    result = cluster_likelihood + field_likelihood
    
    if calc_log:
        return np.log(result)
    else:
        return result

def joint_likelihood(calc_log=False):

    # The joint likelihood for the entire dataset. This is a sum over the log-likelihoods for each magnitude and the product of each resulting band filter log-likelihood (e.g. sum of log-likelihood of all observations in UBVRI 
    # individually, giving likelihoods for each band, and then the produc of those). Again, if the calc_lofg flag is set, return the log-likelihood; this turns the product into a sum.
    
    #if calc_log:
     #   lnLikelihood = likelihood()

# When making calculations, I need to be able to interpolate between magnitudes supplied by the model file. So, say the data point suggests a areitcular magnitude...I will need to be able to grab that magnitude to check the
# what the model says about that value...I.e., what is the mass? What is the FeH?, etc. All of this will need to be interpolated.

   # Need a function to loop through and do the likelihood for each magnitude. 

def calc():

   # Band is an array holding all observed apparent magnitudes and their photometric uncertainties for the current band of interest.

   max_appmag = np.amax(band[0])
   min_appmag = np.amin(band[0]) 

   for data_magnitude, phot_uncert in band:
       # How should model_magnitude be selected?
       # Make model_magnitude a function that looks up a magnitude based on the currently used initial mass, FeH, age, (rotation), If the point does not exist exactly, will need to interpolate.
       # So in the likelihood function I should change it to take in theta (the parameters) and have it look up the corresponding model prediction for those params. This will be the model point.
       # init mass, age, and FeH are all parameters that will be sampled via MCMC...
       getIsomag(init_mass, FeH, age)
       # So I need to have these values stored as metadata...age and initial mass are parameters in the tables but metallicity is a property of the runs...so this is stored as metadata.
       # the function will check the model's cmdset object and look up the right magnitude based on the given mass, FeH, and age. Then in the case it doesnt exist, I need to figure out
       # an interpolation scheme...probably linear.

       lnLikelihood = likelihood(data_magnitude, model_magnitude, phot_uncert, max_appmag, min_appmag, calc_log = True)
