==============================================================
# IMPORTANT:
==============================================================
Right now two functions are responsible for running MCMC and 
determining fits for the data and models.

 + cmdfit.fitsingle()
 + cmdfit.fitall()

Respectively, these find a single star's likely cluster [Fe/H],
log10 age, primary/seconday initial mass or the parameters of a
collection of observed stars comprising a stellar population.

**I WOULD NOT RUN cmdfit.fitall() RIGHT NOW.**

It takes a long time to complete, but I am working to resolve
this.

The other function cmdfit.fitsingle() is working however,
although I would like to continue testing to make sure that
it is being sensible.

**Also, not all model files are currently available on the
github repo.**

==============================================================
# TO DO:
==============================================================

 + Finish automating plotting routines.
 + Ensure that the MCMC sampling is working correctly.
 + Provide more tools for the user to access the data
   they have loaded.
 + Improve instructions on how to run the code.
 + General improvements to things like data table navigation.
 + Comments, organization, and probably some more things...

==============================================================
# OVERVIEW:
==============================================================

Tools for fitting stellar models to stellar cluster data and determining the underlying parameters of the cluster of interest 
through a Bayesian statistical framework outlined as follows:

 * Using a likelihood function (described below) and set of priors, this code will perform MCMC samplings of the parameter space
provided by a set of stellar evolution models (e.g. isochrones,or the individual points that comprise the isochrone which 
represent individual model stars).

 * In the singular case, the sampling is meant to compare the range of models provided to a particular data point and find a 
best fitting model for that point. However, more often we will be fitting models to an entire data set, rather than a single 
data point. The basic idea is the same though: we match a model to data using MCMC sampling, however we now consider the joint 
likelihood of all fits to all data points. 

 * In the end, we will arrive at an overall best fitting parameter set and corresponding model for the entire data set. This is 
our posterior, and it allows us to explore the most likely parameters for our models.

In the context of the problem considered in this code, we are fitting the outputs of stellar evolution codes (our models) to 
observations of real stars (data), in order to derive the most likley parameters of the entire stellar population (via the 
posterior) from which our data has been taken. This allows data to inform our theories on stellar evolution and open clusters.

## Data Specification
---------------------------------------------------------------

This code uses data in the form of magnitude measurements of stars. Typically, this is contained in data tables compiled from
the results of observations with a magnitude measurement for each star and often these  measurements are available in a set of 
filters such as UBVRI or 2MASS JHK.


## Model Specification
---------------------------------------------------------------

The models considered in this code are simualted stars evolved with stellar evolution code, e.g. MESA; in a typical simulation,
a model star may begin on the pre-main sequence (PMS) and is allowed to evolve, giving the evolution of various stellar parameters
as output.

The output that we are interested in here will be the magnitude of a model star at particular points during its evolution. So,
models used here must be able to produce predictions of the magnitude of a star at any period of interest during its evolution. 
These predictions will be compared to the input data magnitudes. 


## Likelihood
---------------------------------------------------------------

The likelihood is meant to capture how well a model is able to reproduce the data that it is meant to simulate. This 
code uses a likelihood function that is similar to one used in the paper by van Dyk et al, 2009.


## Priors
---------------------------------------------------------------

A selection of priors is necessary for the model parameters used here. Thus, priors have been selected as follows:
(this also follows something similar to what van Dyk et al. 2009 use)

The parameters log10 age, metallicity ([Fe/H]), and rotation will have flat priors in the range of their maximum and
minimum sampling ranges. The initial mass will be split into a prior on initial primar mass and another for secondary
mass, in order to account for the possibility of a data point being a binary system. 

The primary star's mass will be considered as the more massive star, and it will have a Gaussian prior, with a mean and
variance derived from the Miller & Scalo (1979) initial mass function (IMF); this is also what is done in van Dyk et al.
2009. 

The secondary star's prior has been selected as a uniform prior in the range of 0 to the primary member's initial mass value.

Posterior Calculation (I WILL UPDATE THIS SOON)
---------------------------------------------------------------

...

===============================================================
# DIRECTORY STRUCTURE:
===============================================================

(THIS NEEDS TO BE UPDATED TOO)

All code that handles data and model input/output, calculations, etc. reside in the /CMDfit/cmdfit directory. The various packages
which handle the tasks necessary are sub-divded as follows:

.../statistics
---------------------------------------------------------------

This directory contains the following files:

     -- likelihood.py
     	+++++++++++++
	This file holds the definition of the likelihood function used to compare input data to input model points. (Described
	above and in /CMDfit/model.ipynb)
    
     -- priors.py
        +++++++++++++
        Holds definitions of the priors used in order to arrive at a posterior distribution for the model parameters.

.../processing
--------------------------------------------------------------

This directory contains the following files:

     ... TBD

.../data
--------------------------------------------------------------

This directory should contain the files tabulating a set of observed magnitudes for a stellar cluster. MENTION FORMAT, ETC...

.../model
--------------------------------------------------------------

This directory should contain the files tabulating magnitudes predicted by one's stellar model. FORMAT, ETC...

.../tests
--------------------------------------------------------------

This is a directory for unit tests and their respective files.
