import numpy as np

def likelihood(data_mag, model_mag, phot_uncert, data_mag_max, data_mag_min):

    """
    The form used here is based on the likelihood function used by van Dyk et al. 2009.

    INPUT:
    =====================================================================================================
    
        data_mag (float):
        +++++++++++++++++++++
          A number taken from a data table. Meant to be the value of a measured magnitude
        for an observed star in a stellar cluster (our definition of a data point).
         
        model_mag (float):
        ++++++++++++++++++++++
          A number taken from a file holding tabulated magnitudes from a stellar evolution model simulation.

        phot_uncert (float):
        ++++++++++++++++++++++
          The photometric uncertainties recorded along with the supplied data. This is photon shot noise
        essentially and represents the variance of the distribution from which our data has been drawn.

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

    """
    # MAKE THIS INPUT SETH <><@! (prob. of being a field star for mixture model)
    Pfield = 0.25

    # Terms going into construction of the Gaussian term of the likelihood function (described in model.ipynb):
    const_factor = 1.0 / np.sqrt(2.0 * np.pi * sigma**2.0)
    residual = data_mag - model_mag
    sigma = phot_uncert
    exponent = -0.25 * (residual / sigma)**2.0

    # Uniform distribution from which magnitudes may be drawn in the case of a field star:
    field_distribution = 1.0 / (data_mag_max - data_mag_min)
    
    # Likelihood functions for the ith data point compared to the ith model point in the single filter:
    cluster_likelihood = (1 - Pfield) * const_factor * np.exp(exponent)
    field_likelihood = Pfield * field_distribution

    # Return the total likelihood function:
    return cluster_likelihood + field_likelihood
