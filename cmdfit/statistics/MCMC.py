import numpy as np
import emcee
import matplotlib.pyplot as plt
import seaborn as sns
from . import priors
from . import likelihood

def lnposterior(theta, data_cmdset, allmodel_cmdsets, FeH_list, FeH_range, age_range, mode = 'all', magindex=None):

    """
      The posterior distribution function; this is built from the priors on log10 age, metallicity, initial
    primary and secondary mass, and the full log-likelihood of all observed stars tested against the avail-
    able models in all color bands of interest. (Form is based on van Dyk et al. 2009)

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

        FeH_range (float, tuple):
        +++++++++++++++++++++++++
          The maximum and minimum metallicities available in the models. Necessary for calculation of the
        metallicity prior.

        age_range (float, tuple):
        +++++++++++++++++++++++++
          The maximum and minimum log10 ages available in the models. Necessary for calculation of the
        log10 age prior.
    
    OUTPUT:
    ======================================================================================================

        return (float):
        +++++++++++++++++++
          The returned value represents the joint log-probability calculated for all data points in all color
        bands under consideration combined with the log-priors on age and metallicity. This is the full log-
        posterior probability function.
          The result will be returned after having run an MCMC sampling of the parameter space in order
        to test various parameter values and map out the log-posterior probability ditribution.

    """   

    # Calculate the priors on metallicity and age:
    lnp = priors.lnprior(theta, FeH_range, age_range)
    # Calculate the log-likelihood:
    lnlikelihood = likelihood.allband_lnLikelihood(theta, data_cmdset, allmodel_cmdsets, FeH_list, mode, magindex)

    # If the sampler picked values out of the valid ranges, assign zero probability
    # for this paritcular sampling:
    if not np.isfinite(lnp) or not np.isfinite(lnlikelihood):
        return -np.inf

    # Or else, return the full posterior. The allband_lnLikelihood() function handles the sampling
    # on primary and secondary initial masses; it also handles the priors of those parameters:
    return lnp + lnlikelihood

def getsamples(data_cmdset, allmodel_cmdsets, FeH_list, mode = 'all', magindex=None):
    
    #print('FORMING [Fe/H] RANGE...')
    # Determine the boundaries of the metallicity range:  
    FeH_range = ( np.amin(np.array(FeH_list)), np.amax(np.array(FeH_list)) )
    #print(FeH_range)

    # For the age range, all model cmdsets should have the same age range, so just look at the 
    # range in the first cmdset:
    #print('FORMING AGE RANGE...')
    #print(allmodel_cmdsets[0].ages)
    #print(allmodel_cmdsets[0].ages.values)
    age_range = ( np.amin(allmodel_cmdsets[0].ages.values), np.amax(allmodel_cmdsets[0].ages.values))
    #print(age_range)
    
    if mode == 'all':
        # emcee sampler parameters:
        ndim = 2
        nwalkers = 6
        nsteps = 3    

        #  [FeH, age]; preliminary values...just based on my understanding of what people believe currently
        # for the Hyades cluster:
        initial_positions = [0.15, 8.6]
        # Set up the walkers in a Gaussian ball around the initial positions:
        initial_positions = [initial_positions + 1e-4*np.random.randn(ndim) for i in range(nwalkers)]

        # Assign the sampler object using parameters from above:
        sampler = emcee.EnsembleSampler(nwalkers, ndim, lnposterior, args=(data_cmdset, allmodel_cmdsets, FeH_list, FeH_range, age_range))
  
        # Run the sampler for the specified number of steps:
        print('\nRunning MCMC...\n')
        sampler.run_mcmc(initial_positions, nsteps)
        print('DONE\n')

    elif mode == 'single':
        # emcee sampler parameters:
        ndim = 5
        nwalkers = 16
        nsteps = 400
       
        #  [FeH, age, primary initial mass, secondary initial mass, and Pfield]
        if data_cmdset.kind == 'modeltest':
            initial_positions = [data_cmdset.FeH, data_cmdset.ages.ix[magindex], data_cmdset.initmasses.ix[magindex], 0.0, 0.0]
            print(initial_positions)
            initial_positions = [0.10, 7.5, 1.0, 0.5, 0.5]

        else:
            initial_positions = [0.10, 7.5, 1.0, 0.5, 0.5]

        # Set up the walkers in a Gaussian ball around the initial positions:
        initial_positions = [initial_positions + 1e-4*np.random.randn(ndim) for i in range(nwalkers)]

        # Assign the sampler object using parameters from above:
        sampler = emcee.EnsembleSampler(nwalkers, ndim, lnposterior, args=(data_cmdset, allmodel_cmdsets, FeH_list, FeH_range, age_range, mode, magindex))
   
        # Run the sampler for the specified number of steps:
        print('\nRunning MCMC...\n')
        sampler.run_mcmc(initial_positions, nsteps)
        print('DONE\n')

    return sampler, ndim, nwalkers, nsteps
