def primary_mass_prior(primary_mass):
    """
    Miller & Scalo (1979) IMF informed Gaussian prior on log of the primary mass.
    """

    # The Gaussian prior on primary initial mass; constants derived from Miller & Scalo IMF.
    return np.exp( -0.5 * ((np.log(primary_mass) + 1.02) / 0.677)**2.0 )

def secondary_mass_prior(primary_mass):
    """
    This is a flat prior between 0 and the primary mass. The primary mass is treated as the more
    (or equally) massive component of the stellar system.
    """

    return 1.0 / primary_mass

def rotation_prior(vvcrit_max, vvcrit_min):
    """
    Uniform...
    """ 
    return 1.0 / (vvcrit_max - vvcrit_min)

def metallicity_prior(FeH_max, FeH_min):
    
    """
    Uniform in Z range?...
    """
    
    return 1.0 / (FeH_max - FeH_min)

def age_prior(age_max, age_min)
    
    """
    Uniform in log10 age...
    """
    
    return 1.0 / (age_max - age_min)
