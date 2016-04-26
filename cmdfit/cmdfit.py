import numpy as np
from . import data
import emcee
import matplotlib.pyplot as plt
import seaborn as sns
from cmdfit.statistics import MCMC

def fitall():

    """
    This function determines the likelihood of the data being produced by a
    given model within CMD space (i.e., magnitude vs. color, or color vs.
    color, etc.). Data represent the individual observations of stars and
    models are reresented by isochrones (single age stellar populations).

    Input:

    Output:

    WIP...
    
    """
    # load an observed cmd:
    data_cmdset = data.cmdset('data')
    
    # Load a set of model cmds; the user will select which directory to load from:
    allmodel_cmdsets = data.all_modelcmdsets()
    
    # Arranging cmds in ascending order according to metallicity; this is necesary
    # for the finding function in interp.py to work...
    FeH_list = [cmdset.FeH for cmdset in allmodel_cmdsets]
    sortedFeH_list = np.array(sorted(FeH_list))    

    temporary_cmdsets = [None]*len(allmodel_cmdsets)

    for i in range(len(allmodel_cmdsets)):
        temporary_cmdsets[np.where(sortedFeH_list == allmodel_cmdsets[i].FeH)[0]] = allmodel_cmdsets[i] 

    allmodel_cmdsets = temporary_cmdsets

    # Run MCMC with the supplied models and observed data:
    sampler = MCMC.getsamples(data_cmdset, allmodel_cmdsets, sortedFeH_list)

    fig, (ax_feh, ax_age) = plt.subplots(2)
    ax_feh.set(ylabel='[Fe/H]')
    ax_age.set(ylabel='log10 Age')

    for i in range(4):
        sns.tsplot(sampler.chain[i,:,0], ax=ax_feh)
        sns.tsplot(sampler.chain[i,:,1], ax=ax_age)

    sns.plt.show()

    return

def fitsingle():

    # load an observed cmd:
    data_cmdset = data.cmdset('data')
    
    # Load a set of model cmds; the user will select which directory to load from:
    allmodel_cmdsets = data.all_modelcmdsets()
    
    # Arranging cmds in ascending order according to metallicity; this is necesary
    # for the finding function in interp.py to work...
    FeH_list = [cmdset.FeH for cmdset in allmodel_cmdsets]
    sortedFeH_list = np.array(sorted(FeH_list))    

    temporary_cmdsets = [None]*len(allmodel_cmdsets)

    for i in range(len(allmodel_cmdsets)):
        temporary_cmdsets[np.where(sortedFeH_list == allmodel_cmdsets[i].FeH)[0]] = allmodel_cmdsets[i] 

    allmodel_cmdsets = temporary_cmdsets

    # Run MCMC with the supplied models and observed data (should make magindex selectable):
    sampler = MCMC.getsamples(data_cmdset, allmodel_cmdsets, sortedFeH_list, mode='single', magindex=0)

    fig, (ax_feh, ax_age, ax_M1, ax_M2) = plt.subplots(4)
    ax_feh.set(ylabel='[Fe/H]')
    ax_age.set(ylabel='log10 Age')
    ax_M1.set(ylabel='Primary Mass [Msun]')
    ax_M2.set(ylabel='Secondary Mass [Msun]')

    for i in range(10):
        sns.tsplot(sampler.chain[i,:,0], ax=ax_feh)
        sns.tsplot(sampler.chain[i,:,1], ax=ax_age)
        sns.tsplot(sampler.chain[i,:,2], ax=ax_M1)
        sns.tsplot(sampler.chain[i,:,3], ax=ax_M2)

    sns.plt.show()

    return sampler
