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

def fitall(mode = 'data', test_age = 9.0):

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
        data_cmdset.datacutmags(4, 7)
        # Grab 3 random points:
        data_cmdset.randsamp(3)

    if mode == 'modeltest':
        data_cmdset = data.cmdset('modeltest')
        data_cmdset = iso.isochrone(data_cmdset, test_age)
        data_cmdset.isorandsamp(3)
    
    # Load a set of model cmds; the user will select which directory to load from:
    allmodel_cmdsets = data.all_modelcmdsets()
    
    # Arranging cmds in ascending order according to metallicity; this is necesary
    # for the finding function in interp.py to work...
    FeH_list = [cmdset.FeH for cmdset in allmodel_cmdsets]
    sortedFeH_list = np.array(sorted(FeH_list))    

    # Sort models into ascending order in [Fe/H]:
    allmodel_cmdsets.sort(key=lambda model: model.FeH)

    ndim = 2

    # Run MCMC with the supplied models and observed data:
    sampler, nwalkers, nsteps = MCMC.getsamples(data_cmdset, allmodel_cmdsets, sortedFeH_list, mode = 'all', ndim=ndim)

    fig, (ax_feh, ax_age) = plt.subplots(2)
    ax_feh.set(ylabel='[Fe/H]')
    ax_age.set(ylabel='log10 Age')

    if nwalkers >=10:
        N = 10
    else:
        N = nwalkers

    for i in range(N):
        sns.tsplot(sampler.chain[i,:,0], ax=ax_feh)
        sns.tsplot(sampler.chain[i,:,1], ax=ax_age)
    
    sns.plt.show()

    burnin_cut = eval(input("Enter an integer for where to cutoff the burn-in period: "))    

    samples = sampler.chain[:,burnin_cut:,:]
    traces = samples.reshape(-1,2).T

    param_samples = pd.DataFrame({'[Fe/H]': traces[0], 'log10 Age':traces[1]})

    q = param_samples.quantile([0.16, 0.50, 0.84], axis=0)
    print(q) 
    print()

    # Plot the isochrones corresponding to the MAP values:
    plot_foundisos(q, sortedFeH_list, data_cmdset, allmodel_cmdsets, ndim, random_index = None)

    jkde = sns.jointplot(x='[Fe/H]', y='log10 Age', data=param_samples, kind='kde')

    sns.plt.show()

    return param_samples, sampler

def fitsingle(mode, ndim = 3):

    if mode == 'data':
        # load an observed cmd:
        data_cmdset = data.cmdset('data')

        # Confine data's magnitude range to a small range
        # near MSTO for now...
        data_cmdset.datacutmags(4, 7)
        data_cmdset.cutuncert(0, 0.5)

        random_index = np.random.random_integers(len(data_cmdset.magnitudes.values)) 

    if mode == 'modeltest':
        # For testing I will load a magnitude from the models; I know the age/mass, etc. for this star so I can check that
        # answers are correct...
        data_cmdset = data.cmdset('modeltest')
        random_index = 20450

    # Load a set of model cmds; the user will select which directory to load from
    # and cut models with ages below log 10 age = 8.0:
    allmodel_cmdsets = data.all_modelcmdsets(agecut = 8.0)
    print('\nMODELS LOADED...')

    # Arranging cmds in ascending order according to metallicity; this is necesary
    # for the finding function in interp.py to work...

    # Make a list of available FeH values in ascending order:
    FeH_list = [cmdset.FeH for cmdset in allmodel_cmdsets]
    sortedFeH_list = np.array(sorted(FeH_list))    
    
    # Sort the models in ascending order of FeH:
    allmodel_cmdsets.sort(key=lambda model: model.FeH)

    # Run MCMC with the supplied models and observed data (should make magindex selectable):
    if mode == 'modeltest':
        sampler, nwalkers, nsteps, model_params = MCMC.getsamples(data_cmdset, allmodel_cmdsets, sortedFeH_list,
                                                                    mode='single', magindex= random_index,ndim= ndim)
    else:
        sampler, nwalkers, nsteps = MCMC.getsamples(data_cmdset, allmodel_cmdsets, sortedFeH_list, 
                                                      mode='single', magindex= random_index,ndim= ndim)

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
    
    if ndim == 5:
        fig, (ax_feh, ax_age, ax_M1, ax_M2, ax_Pf) = plt.subplots(ndim)
        ax_feh.set(ylabel='[Fe/H]')
        ax_age.set(ylabel='log10 Age')
        ax_M1.set(ylabel='Primary Mass [Msun]')
        ax_M2.set(ylabel='Secondary Mass [Msun]')
        ax_Pf.set(ylabel='Cluster Membership')

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
            if ndim == 5:
                sns.tsplot(sampler.chain[i,:,4], ax=ax_Pf)

    sns.plt.show()
    burnin_cut = eval(input("Enter an integer for where to cut off the burn-in period: "))    

    samples = sampler.chain[:,burnin_cut:,:]
    traces = samples.reshape(-1, ndim).T

    if ndim == 3:
        param_samples = pd.DataFrame({'[Fe/H]': traces[0], 'log10 Age':traces[1], 'Primary Mass':traces[2]})
    if ndim == 4:
        param_samples = pd.DataFrame({'[Fe/H]': traces[0], 'log10 Age':traces[1], 
                                      'Primary Mass':traces[2], 'Secondary Mass':traces[3]})
    if ndim == 5:
        param_samples = pd.DataFrame({'[Fe/H]': traces[0], 'log10 Age':traces[1], 'Primary Mass':traces[2], 
                                      'Secondary Mass':traces[3], 'Pfield':traces[4]})
    
    q = param_samples.quantile([0.16, 0.50, 0.84], axis=0)
    print('\nMAP Values:')
    print(q)
    print()   

    # Plot the isochrones corresponding to the MAP values:
    plot_foundisos(q, sortedFeH_list, data_cmdset, allmodel_cmdsets, ndim, random_index = random_index)

    if mode == 'modeltest':
        
        print("\nOriginal Model Parameters:")
        print(model_params)
        print()

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

def plot_foundisos(q, sortedFeH_list, data_cmdset, allmodel_cmdsets, ndim, random_index = None):


    # Right now this stuff tries to plot the star input with the MAP isochrone found.
    # Its not done in a great way right now, need to interpolate to be more accurate maybe.
    MAPfeh = q['[Fe/H]'][0.50]
    FeHrich, FeHpoor, FeHrich_index, FeHpoor_index = interp.find_closestFeHs(MAPfeh, sortedFeH_list)
    modelset = allmodel_cmdsets[FeHpoor_index]

    isochronesfound = []
    quantiles = [0.16, 0.50, 0.84]
    rev_quant = quantiles[::-1]
    for j in range(len(quantiles)):
        # The isochrones and primary mass magnitudes found 
        # corresponding to the 16, 50 and 84% quantiles:
        isofound = iso.isochrone(modelset, q['log10 Age'][quantiles[j]])
  
        # If plotting fitting a single data point, find the stars the MAP values are suggesting and show them too:
        if random_index != None:
            foundstar_mags = [isofound.isogetmag(q['Primary Mass'][rev_quant[j]], i) for i in range(modelset.numbands)]

            # If available, plot the secondary mass' magnitude too:
            if ndim == 4:
                # Get partner's magnitudes:
                foundstar2_mags = [isofound.isogetmag(q['Secondary Mass'][rev_quant[j]], i) for i in range(modelset.numbands)]
                # Combine primary and secondary magnitudes:
                fullmag = [-2.5 * np.log10(10**(-foundstar_mags[i]/2.5) + 10**(-foundstar2_mags[i]/2.5)) for i in range(modelset.numbands)]
                if np.isfinite(fullmag[0]) and np.isfinite(fullmag[1]):
                    plt.errorbar(foundstar2_mags[0] - foundstar2_mags[1], foundstar2_mags[1], color = 'b', fmt = 'o', label='Model Star {:d}'.format(j))
                    # Plot the full, combined magnitude point:
                    plt.errorbar(fullmag[0] - fullmag[1], fullmag[1], color='k', fmt='o')
                else:
                    print("The magnitudes found for the secondary star: {}.".format(fullmag))
        
            # Plot the found primary mass' magnitude:
            plt.errorbar(foundstar_mags[0] - foundstar_mags[1], foundstar_mags[1], color='r', fmt='o')

        isochronesfound.append(isofound)

    if random_index != None:
        # Now plot the isochrones at all quantiles, along with the single data point:
        iso.multiisoCMD(isochrone_set=isochronesfound, dataset=data_cmdset, magindex=random_index)
    else:
        iso.multiisoCMD(isochrone_set=isochronesfound, dataset=data_cmdset)

    return
