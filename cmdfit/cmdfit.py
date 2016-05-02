import numpy as np
from . import data
import emcee
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import corner
from cmdfit.statistics import MCMC
from cmdfit.processing import interp
from . import isochrone as iso

def fitall(mode = 'data'):

    """
    This function determines the likelihood of the data being produced by a
    given model within CMD space (i.e., magnitude vs. color, or color vs.
    color, etc.). Data represent the individual observations of stars and
    models are reresented by isochrones (single age stellar populations).

    Input:

    Output:

    WIP...
    
    """
    if mode == 'data':
        # load an observed cmd:
        data_cmdset = data.cmdset('data')
    
    # Confine data's magnitude range to lie within isochrone's range for now...
    data_cmdset.datacutmags(1, 10)
    
    # Load a set of model cmds; the user will select which directory to load from:
    allmodel_cmdsets = data.all_modelcmdsets()
    
    # Arranging cmds in ascending order according to metallicity; this is necesary
    # for the finding function in interp.py to work...
    FeH_list = [cmdset.FeH for cmdset in allmodel_cmdsets]
    sortedFeH_list = np.array(sorted(FeH_list))    

    allmodel_cmdsets.sort(key=lambda model: model.FeH)

    ndim = 2
    # Run MCMC with the supplied models and observed data:
    sampler, nwalkers, nsteps, model_params = MCMC.getsamples(data_cmdset, allmodel_cmdsets, sortedFeH_list, mode = 'all', ndim=ndim)

    fig, (ax_feh, ax_age) = plt.subplots(2)
    ax_feh.set(ylabel='[Fe/H]')
    ax_age.set(ylabel='log10 Age')

    for i in range(ndim):
        sns.tsplot(sampler.chain[i,:,0], ax=ax_feh)
        sns.tsplot(sampler.chain[i,:,1], ax=ax_age)
    
    sns.plt.show()

    burnin_cut = eval(input("Enter an integer for where to cutoff the burn-in period: "))    

    samps = s.chain[:,burnin_cut:,:]
    traces = samps.reshape(-1,4).T

    param_samples = pd.DataFrame({'z': traces[0], 'logage':traces[1], 'm1':traces[2], 'm2':traces[3]})
    jkde = sns.jointplot(x='z', y='logage', data=param_samples, kind='kde', ax = fehvage)

    sns.plt.show()

    return param_samples

def fitsingle(mode, ndim = 3):

    if mode == 'data':
        # load an observed cmd:
        data_cmdset = data.cmdset('data')
    
    if mode == 'modeltest':
        # For testing I will load a magnitude from the models; I know the age/mass, etc. for this star so I can check that
        # answers are correct...
        data_cmdset = data.cmdset('modeltest')    

    # Load a set of model cmds; the user will select which directory to load from:
    allmodel_cmdsets = data.all_modelcmdsets(agecut = 8.0)
    print('\nMODELS LOADED...')

    # Arranging cmds in ascending order according to metallicity; this is necesary
    # for the finding function in interp.py to work...

    # Make a list of available FeH values in ascending order:
    FeH_list = [cmdset.FeH for cmdset in allmodel_cmdsets]
    sortedFeH_list = np.array(sorted(FeH_list))    
    
    # Sort the models in ascending order of FeH:
    allmodel_cmdsets.sort(key=lambda model: model.FeH)

    random_index = 20450#np.random.random_integers(len(data_cmdset.magnitudes.values))

    # Run MCMC with the supplied models and observed data (should make magindex selectable):
    sampler, nwalkers, nsteps, model_params = MCMC.getsamples(data_cmdset, allmodel_cmdsets, sortedFeH_list, mode='single', magindex= random_index,ndim= ndim) #28100)    

    if ndim == 3:
        fig, (ax_feh, ax_age, ax_M1) = plt.subplots(ndim)
        ax_feh.set(ylabel='[Fe/H]')
        ax_age.set(ylabel='log10 Age')
        ax_M1.set(ylabel='Primary Mass [Msun]')

    if ndim == 4:
        fig, (ax_feh, ax_age, ax_M1, ax_M2) = plt.subplots(ndim)
        ax_feh.set(ylabel='[Fe/H]')
        ax_age.set(ylabel='log10 Age')
        ax_M1.set(ylabel='Primary Mass [Msun]')
        ax_M2.set(ylabel='Secondary Mass [Msun]')

    if nwalkers >=10:
        N = 10
    else:
        N = nwalkers

    for i in range(N):
        sns.tsplot(sampler.chain[i,:,0], ax=ax_feh)
        sns.tsplot(sampler.chain[i,:,1], ax=ax_age)
        sns.tsplot(sampler.chain[i,:,2], ax=ax_M1)
        if ndim >= 4:
            sns.tsplot(sampler.chain[i,:,3], ax=ax_M2)

    sns.plt.show()
    burnin_cut = eval(input("Enter an integer for where to cut off the burn-in period: "))    

    samples = sampler.chain[:,burnin_cut:,:]
    traces = samples.reshape(-1, ndim).T

    if ndim == 3:
        param_samples = pd.DataFrame({'[Fe/H]': traces[0], 'log10 Age':traces[1], 'Primary Mass':traces[2]})
    if ndim == 4:
        param_samples = pd.DataFrame({'[Fe/H]': traces[0], 'log10 Age':traces[1], 'Primary Mass':traces[2], 'Secondary Mass':traces[3]})
    if ndim == 5:
        param_samples = pd.DataFrame({'[Fe/H]': traces[0], 'log10 Age':traces[1], 'Primary Mass':traces[2], 'Secondary Mass':traces[3], 'Pfield':traces[4]})
    
    q = param_samples.quantile([0.16, 0.50, 0.84], axis=0)
    print(q)   

    # Right now this stuff tries to plot the star input with the MAP isochrone found.
    # Its not done in a great way right now, need to interpolate to be more accurate maybe.
    MAPfeh = q['[Fe/H]'][0.50]
    FeHrich, FeHpoor, FeHrich_index, FeHpoor_index = interp.find_closestFeHs(MAPfeh, sortedFeH_list)
    modelset = allmodel_cmdsets[FeHpoor_index]

    isofound = iso.isochrone(modelset, q['log10 Age'][0.50])
    foundstar_mags = [isofound.isogetmag(q['Primary Mass'][0.50], i) for i in range(modelset.numbands)]

    if ndim == 4:
        foundstar2_mags = [isofound.isogetmag(q['Secondary Mass'][0.50], i) for i in range(modelset.numbands)]
        fullmag = [-2.5 * np.log10(10**(-foundstar_mags[i]/2.5) + 10**(-foundstar2_mags[i]/2.5)) for i in range(modelset.numbands)]
        if np.isfinite(fullmag[0]) and np.isfinite(fullmag[1]):
            plt.errorbar(foundstar2_mags[0] - foundstar2_mags[1], foundstar2_mags[1], color = 'b', fmt = 'o')
            plt.errorbar(fullmag[0] - fullmag[1], fullmag[1], color='k', fmt='o')
        else:
            print("The magnitudes found for the secondary star: {}.".format(fullmag))

    plt.errorbar(foundstar_mags[0] - foundstar_mags[1], foundstar_mags[1], color='r', fmt='o')
    isofound.isoplotCMD(0, 1, data_cmdset, random_index)

    print(model_params)

    if ndim == 3:
        fig = corner.corner(samples.reshape(-1, ndim), labels=["$[Fe/H]$", "$log_{10} Age$", "$M_1$"], truths=model_params)
    if ndim == 4:
        fig = corner.corner(samples.reshape(-1, ndim), labels=["$[Fe/H]$", "$log_{10} Age$", "$M_1$", "$M_2$"], truths=model_params)
    if ndim == 5:
        fig = corner.corner(samples.reshape(-1, ndim), labels=["$[Fe/H]$", "$log_{10} Age$", "$M_1$", "$M_2$"," $P_{field}$"], truths=model_params)
   
    sns.plt.show()

    jkde = sns.jointplot(x='[Fe/H]', y='log10 Age', data=param_samples, kind='kde')

    sns.plt.show() 

    return param_samples, sampler
