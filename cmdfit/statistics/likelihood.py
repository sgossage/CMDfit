import numpy as np
import emcee
from collections import Counter
import cmdfit.processing.interp as interp
import matplotlib.pyplot as plt
import seaborn as sns
from . import priors
import cmdfit.data as data
import cmdfit.isochrone as iso

# Calculates the likelihood of a single star, i.e. a single magnitude, given the set of parameters theta.
def likelihood(star_theta, data_mag, phot_uncert, data_bandindex, allmodel_cmdsets, FeH_list, data_mag_range, FeH, age, calc_log = True, mode ='single'):

    """
      The form used here is based on the likelihood function used by van Dyk et al. 2009. This function generates a model 
    magnitude from the selection of models available in allmodel_cmdsets given an age, metallicity, initial primary mass, 
    and initial secondary mass. 

    INPUT:
    =====================================================================================================

        mass_theta (float, tuple):
        ++++++++++++++++++++++++++
          A tuple of two floats representing primary (0th ekement) and secondary mass (1st element).
        This tuple is generated by EnsembleSampler() from the emcee package, as these are two of the
        parameters with which we want to sample the posterior distribution via MCMC.   

        data_mag (float):
        +++++++++++++++++++++++++
          A number taken from a data table. Meant to be the value of a measured magnitude
        for an observed star in a stellar cluster (our definition of a data point).

        phot_uncert (float):
        ++++++++++++++++++++++
          The photometric uncertainties recorded along with the supplied data. This is photon shot noise
        essentially and represents the variance of the distribution from which our data has been drawn.
        
        data_bandindex (int):
        +++++++++++++++++++++
          An int signifying the current color band that we are operating within and from which to
        draw model generated magnitudes.

        allmodel_cmdsets (cmdset, list):
        +++++++++++++++++++++++++++++++++
          A list holding the loaded model cmdset objects as its elements. These are passed so that appro-
        priate model magnitudes may be looked up.

        FeH_list (float, list):
        +++++++++++++++++++++++
          An list (forced into ascending order) of all metallcities supplied by the model cmdsets loaded 
        in by the user. This is used to determine which, if any metallicities need to be interpolated during
        the MCMC sampling routine when we look up model magnitudes.

        data_mag_range (float, tuple):
        ++++++++++++++++++++++++++++++
          A tuple of two floats whose values are the minimum and maximum magnitude values in the current band,
        as determined by the magnitude range observed in the data for the current color band.

        FeH (float):
        +++++++++++++++++++++
          The current metallicity being considered in the sampling process. This is used to retrieve the 
        appropriate model magnitude to compare to the data point at this current metallicity value.

        age (float):
        +++++++++++++++++++++
          Similar to FeH, this number is generated by emcee's EnsembleSampler() and is used to look up the
        magnitude of a model star at this age in order to compare it to a data point and determine a 
        likelihood.
    
    OUTPUT:
    ======================================================================================================

        return (float):
        +++++++++++++++++++
          If the input value for FeH is within bounds of the available FeH values supplied by the model 
        cmdsets, a magnitude will either be retrieved directly or else interpolated. This function returns
        the result of the likelihood calculation. This is the probability of the model being a good 
        representation of the data.
          If the input FeH value is not within the valid range supplied, this function will return
        -infinity for likelihood to give this selection of FeH zero probability (if calc_log == True),
        or 0.0 (if calc_log == False).

    OPTIONS:
    ======================================================================================================

        calc_log (bool):
        +++++++++++++++++++
          Default: False

          If set to True, this option will set the returned value to be the log (base e) of the calculated
        likelihood function.

    """
    if mode == 'single':
        if len(star_theta) == 2:
            initmass = star_theta[0]
            Pfield=star_theta[1]
            secondarymass = None
        elif len(star_theta) == 3:
            initmass = star_theta[0]
            secondarymass = star_theta[1]
            Pfield = star_theta[2]

    elif mode == 'all':
        if isinstance(star_theta, np.ndarray) or isinstance(star_theta, list):
            if len(star_theta) == 1:
                initmass = star_theta[0]
                Pfield = 0.0
                secondarymass = None
            if len(star_theta) == 2:
                initmass = star_theta[0]
                secondarymass = star_theta[1]
                Pfield = 0.0
            elif len(star_theta) == 3:
                initmass = star_theta[0]
                secondarymass = star_theta[1]
                Pfield = star_theta[2]
        else:
            initmass = star_theta
            Pfield = 0.0
            secondarymass = None

    # Get a magnitude given the model parameters:
    model_mag = data.getcmdsetsmag(allmodel_cmdsets, age, initmass, FeH, FeH_list, data_bandindex, secondarymass = secondarymass)  

    if not np.isfinite(model_mag):
        if calc_log:
            return -np.inf
        else:
            return 0.0

    # Terms going into construction of the Gaussian term of the likelihood function (described in model.ipynb):
    sigma = phot_uncert
    const_factor = 1.0 / np.sqrt(2.0 * np.pi * sigma**2.0)
    residual = data_mag - model_mag
    exponent = -0.5 * (residual / sigma)**2.0

    # Uniform distribution from which magnitudes may be drawn in the case of a field star:
    data_mag_min, data_mag_max = data_mag_range
    field_distribution = 1.0 / (data_mag_max - data_mag_min)
    
    # Likelihood functions for the ith data point compared to the ith model point in the single filter:
    cluster_likelihood = (1 - Pfield) * const_factor * np.exp(exponent)
    field_likelihood = Pfield * field_distribution

    # Return the total likelihood function:
    likelihood = cluster_likelihood + field_likelihood
    
    if calc_log:
        return np.log(likelihood)
    else:
        return likelihood

# Calculates the likelihood for all datapoints in a given band. This is what I need to run 
def band_lnLikelihood(theta, band_magnitudes, band_uncertainties, bandindex, allmodel_cmdsets, FeH_list, mode = 'all', magindex = None):

    """
      This likelihood function is a part of the form of the likelihood used by van Dyk et al. 2009. This
    function calls stardata_lnprobability() in order to calculate the log likelihood of all data points 
    in the current color band. 
      It runs an MCMC sampler in order to sample the mass parameter of each data point; it then determines 
    the highest probability found by the sampler and takes this as the likelihood for star in the current 
    color band. These likelihoods are combined to form a joint log-likelihood of all stars in the current 
    band and this is returned as the final result.

    INPUT:
    =====================================================================================================

        theta (float, tuple):
        ++++++++++++++++++++++++++
          A tuple of two floats representing metallicity, or FeH, (0th ekement) and age (1st element).
        This tuple is generated by EnsembleSampler() from the emcee package, as these are two of the
        parameters with which we want to sample the posterior distribution via MCMC.   

        band_magnitudes (float, array):
        +++++++++++++++++++++++++++++++
          A numpy array holding all observed magnitudes read in from the data table under consideration
        for the current color band (e.g. U, B, V, R, or I).

        phot_uncert (float, array):
        +++++++++++++++++++++++++++
          A numpy array holding all of the recorded photometric uncertainties for each data point; this
        also comes from the data table of interest, or else it is generated bby the user using the
        nominal value of +/- 0.1 dex.
        
        bandindex (int):
        +++++++++++++++++++++
          An int signifying the current color band that we are operating within and from which to
        draw model generated magnitudes.

        allmodel_cmdsets (cmdset, list):
        +++++++++++++++++++++++++++++++++
          A list holding the loaded model cmdset objects as its elements. These are passed so that appro-
        priate model magnitudes may be looked up.

        FeH_list (float, list):
        +++++++++++++++++++++++
          An list (forced into ascending order) of all metallcities supplied by the model cmdsets loaded 
        in by the user. This is used to determine which, if any metallicities need to be interpolated during
        the MCMC sampling routine when we look up model magnitudes.
    
    OUTPUT:
    ======================================================================================================

        return (float):
        +++++++++++++++++++
          The returned value represents the joint probability calculated for all data points in the current
        band, as determined by the maximum probability found during MCMC sampling of mass, given the age
        and metallicity supplied via the theta parameter.

    """
    
    # Band is an array holding all observed apparent magnitudes and their photometric uncertainties for the current band of interest.
    max_appmag = np.amax(band_magnitudes)
    min_appmag = np.amin(band_magnitudes) 

    # Range of magnitudes in this band; necessary for field star probability.
    band_mag_range = (min_appmag, max_appmag)
    
    if mode == 'all':

        # Extract current metallicity and age:
        FeH = theta[0]
        age = theta[1]

        # Here the primary and secondary mass are sampled:
        ndim = 1
        nwalkers = 4
        nsteps = 4
  
        # Make an isochrone of the proposed age:
        if 8.0 < age < 10.0:
            currentiso = iso.isochrone(allmodel_cmdsets[0], age, silent=True)
            massbounds = (min(currentiso.initmasses.values), max(currentiso.initmasses.values))
        # if the age proposition is out of range, return 0 probability:
        else:
            return -np.inf

        if ndim == 1:
            init_positions = [1.0 + 1e-4*np.random.randn(ndim) for i in range(nwalkers)]

        elif ndim == 2:
            # For [primary mass, secondary mass]:
            init_positions = [1.0, 0.4]
            # Set up the walkers in a Gaussian ball around the initial positions:
            init_positions = [init_positions + 1e-4*np.random.randn(ndim) for i in range(nwalkers)]
        
        for i in range(nwalkers):
            if init_positions[i][0] > massbounds[1]:
                init_positions[i][0] = massbounds[1]
            if init_positions[i][0] < massbounds[0]:
                init_positions[i][0] = massbounds[0]

            if ndim >= 2:
                if init_positionis[i][1] < massbounds[0]:
                    init_positons[i][1] = massbounds[0]
                if init_positions[i][1] > init_positions[0]:
                    init_positions[i][1] = init_positions[0]

        # Loop through and calculate the probabilities of each star, comparing each to 
        # all masses on the current isochrone and finding the most likely:
        lnLikelihood = []
        for i in range(len(band_magnitudes)):

            # Calculate the log likelihood for all stars in this band:
            # For each star, I need to run MCMC to figure out the most likely mass sampling. 
            # The lnprob returned by this sampling is the log likelihood for that star. 
            # So replace likelihood() with a new function which is likelihood() * (mass priors) and do mcmc on that; get the lnprob from it.
        
            sampler = emcee.EnsembleSampler(nwalkers, ndim, stardata_lnprobability, 
                                              args = (band_magnitudes[i], band_uncertainties[i], 
                                                bandindex, allmodel_cmdsets, FeH_list, band_mag_range, FeH, age, mode))
            
            print("RUNNING MCMC FOR STAR # {:d} OUT OF {:d} IN BAND {:d}...".format(i, len(band_magnitudes), bandindex))
            sampler.run_mcmc(init_positions, nsteps)
            # Gather sampled probabilities and cut out the burn in period. I took a look and it seems to be around 100...
            lnprob = sampler.lnprobability[:,:]
            lnprob = lnprob.reshape(-1)

            # Now pick out the most common probability to find an approximation of the probability well the walkers fell into
            probcounter = Counter(lnprob)
            lnprob = probcounter.most_common(1)[0][0]
       
            lnLikelihood.append(lnprob)
        
        # lnLikelihood has all of the likelihood calculations for every magnitude in the current band. 
        # Sum the loglikilihoods to get the full log-likelihood for the band:
        full_lnLikelihood = np.sum(np.array(lnLikelihood))

    elif mode == 'single':
 
        # In this mode, a fit is made to a single observed star using all models.
        if len(theta == 3):
            FeH = theta[0]
            age = theta[1]
            M1 = theta[2]
            Pfield = 0.0
            star_theta = (M1, Pfield)
        elif len(theta >= 4):
            FeH = theta[0]
            age = theta[1]
            M1 = theta[2]
            M2 = theta[3]
            if len(theta == 4):
                Pfield = 0.0 
            elif len(theta == 5):
                Pfield = theta[4]

            star_theta = (M1, M2, Pfield)

        # For mode == 'single', pick out ONLY ONE magnitude and uncertainty to
        # compare to the model set within the current band:
        band_mag = band_magnitudes[magindex]
        band_uncert = band_uncertainties[magindex]

        # Compare this single magnitude to all models to figure out which model most likely matches, 
        # and thus determin the data's parameters:
        full_lnLikelihood = stardata_lnprobability(star_theta, band_mag, band_uncert, bandindex, allmodel_cmdsets,
                                                     FeH_list, band_mag_range, FeH, age, mode='single')

    else:
        # Placeholder error message...
        return 'ERROR: mode must be \'single\' or \'all\'.'

    return full_lnLikelihood

# The joint likelihood from all bands:
def allband_lnLikelihood(theta, data_cmdset, allmodel_cmdsets, FeH_list, mode='all', magindex = None):

    """
      This likelihood function is a part of the form of the likelihood used by van Dyk et al. 2009. This
    function calls band_lnLikelihood() once for each color band in consideration. In this way is obtains
    the likelihood for each color band; it then combines them to form the full joint log-likelihood of
    all stars and their observed magnitudes in all color bands.

    INPUT:
    =====================================================================================================

        theta (float, tuple):
        ++++++++++++++++++++++++++
          A tuple of two floats representing metallicity, or FeH, (0th ekement) and age (1st element).
        This tuple is generated by EnsembleSampler() from the emcee package, as these are two of the
        parameters with which we want to sample the posterior distribution via MCMC.   

        data_cmdset (cmdset):
        ++++++++++++++++++++++
          A cmdset object holding the data read in from a data table. This information corresponds to
        what has been observed.

        allmodel_cmdsets (cmdset, list):
        +++++++++++++++++++++++++++++++++
          A list holding the loaded model cmdset objects as its elements. These are passed so that appro-
        priate model magnitudes may be looked up. These cmdsets hold the information provided by the
        models.

        FeH_list (float, list):
        +++++++++++++++++++++++
          An list (forced into ascending order) of all metallcities supplied by the model cmdsets loaded 
        in by the user. This is used to determine which, if any metallicities need to be interpolated during
        the MCMC sampling routine when we look up model magnitudes.
    
    OUTPUT:
    ======================================================================================================

        return (float):
        +++++++++++++++++++
          The returned value represents the joint log-probability calculated for all data points in all color
        bands under consideration. This is the full log-likelihood of the data compared to the models.

    """

    # For how ever many bands input, sum the log-likelihoods of all bands to get the joint likelihood of all input observations compared to models.
    band_lnLikelihoods = []

    for i in range(data_cmdset.numbands):

        # Make a band -- i.e. an array with the observed magnitudes in column 1 and their uncertainties in column 2:
        band = data_cmdset.makeBand(i)
        # Calculate the log-likelihood for the current band and store it in an array:
        band_lnLikelihoods.append( band_lnLikelihood(theta, band[0], band[1], i, allmodel_cmdsets, FeH_list, mode, magindex)  )
    
    # Having calculated a likelihood for each band, sum the log-likelihoods to obtain 
    # the full joint log-likelihood (which accounts for all bands and their magnitudes):
    fulljoint_lnLikelihood = np.sum(np.array(band_lnLikelihoods))

    return fulljoint_lnLikelihood

def stardata_lnprobability(star_theta, star_magnitude, star_sigma, bandindex, allmodel_cmdsets, FeH_list, band_mag_range, FeH, age, mode = 'single'):

    """
      This function calls the likelihood() function (i.e., in order to calculate the probability of an indvidual star)
    being reproduced by the models) and the mass_lnpriors() function. This is the portion of the full likelihood funct-
    ion which handles examining the mass parameters for each star at a given age and metallicity sampling.  

    INPUT:
    =====================================================================================================

        mass_theta (float, tuple):
        ++++++++++++++++++++++++++
          A tuple of two floats representing primary (0th ekement) and secondary mass (1st element).
        This tuple is generated by EnsembleSampler() from the emcee package, as these are two of the
        parameters with which we want to sample the posterior distribution via MCMC.   

        star_magnitude (float):
        +++++++++++++++++++++++++
          A number taken from a data table. Meant to be the value of a measured magnitude
        for an observed star in a stellar cluster (our definition of a data point).

        star_sigma (float):
        ++++++++++++++++++++++
          The photometric uncertainties recorded along with the supplied data. This is photon shot noise
        essentially and represents the variance of the distribution from which our data has been drawn.
        
        bandindex (int):
        +++++++++++++++++++++
          An int signifying the current color band that we are operating within and from which to
        draw model generated magnitudes.

        allmodel_cmdsets (cmdset, list):
        +++++++++++++++++++++++++++++++++
          A list holding the loaded model cmdset objects as its elements. These are passed so that appro-
        priate model magnitudes may be looked up.

        FeH_list (float, list):
        +++++++++++++++++++++++
          An list (forced into ascending order) of all metallcities supplied by the model cmdsets loaded 
        in by the user. This is used to determine which, if any metallicities need to be interpolated during
        the MCMC sampling routine when we look up model magnitudes.

        data_mag_range (float, tuple):
        ++++++++++++++++++++++++++++++
          A tuple of two floats whose values are the minimum and maximum magnitude values in the current band,
        as determined by the magnitude range observed in the data for the current color band.

        FeH (float):
        +++++++++++++++++++++
          The current metallicity being considered in the sampling process. This is used to retrieve the 
        appropriate model magnitude to compare to the data point at this current metallicity value.

        age (float):
        +++++++++++++++++++++
          Similar to FeH, this number is generated by emcee's EnsembleSampler() and is used to look up the
        magnitude of a model star at this age in order to compare it to a data point and determine a 
        likelihood.
    
    OUTPUT:
    ======================================================================================================

        return (float):
        +++++++++++++++++++
          This function returns the log-probability that comes from the combination of the mass (primary
        and secondary) priors and the likelihood of each individual star compared to the models at the
        given age and metallicity.
          Values of mass (or age/metallicity, as handled by likelihood()) outside of the range of values
        determined to be valid will return a negative infinity -- i.e., a probability of zero.

    """

    # The logarithm of the likelihood of the ith star in the jth band times its prior on mass

    lnp = priors.star_lnprior(star_theta, mode = mode)

    if not np.isfinite(lnp):
        return -np.inf

    return lnp + likelihood(star_theta, star_magnitude, star_sigma, bandindex, allmodel_cmdsets, 
                              FeH_list, band_mag_range, FeH, age, calc_log=True, mode=mode)
