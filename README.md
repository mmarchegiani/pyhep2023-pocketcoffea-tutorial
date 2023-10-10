# PocketCoffea @ PyHEP 2023
Notebook tutorial on PocketCoffea for the PyHEP 2023 workshop

PocketCoffea is an analysis framework to perform analysis with CMS data in the NanoAOD format with a configuration scheme built on top of the Coffea package. All the usual operations of CMS analyses are shared in a common base code, including the creation of datasets, the application of selection cuts, the event reweighting, the computation of systematic uncertainty and the production of Data/MC plots.
In this tutorial, the main features of the package are presented.
A toy $Z\rightarrow\mu\mu$ analysis is implemented, using the CMS Opendata datasets from the 2012 data at $\sqrt{s}= $ 8 TeV.

Here is a list of useful links:

- Main GitHub repo: [PocketCoffea](https://github.com/PocketCoffea/PocketCoffea)
- Configs GitHub repo: [AnalysisConfigs](https://github.com/PocketCoffea/AnalysisConfigs)
- Documentation with analysis example: [pocketcoffea.readthedocs.io](https://pocketcoffea.readthedocs.io/en/latest/)

**Disclaimer**: For demonstration purposes, we will apply corrections to MC based on the Run-2 datasets to this older datasets.


## Define the analysis processor

The core of the analysis is the `processor` object. This is an object defined in `Coffea` and it defines the function that will be called taking all the events as input.

In PocketCoffea, all processors can be derived from an abstract base processor class called `BaseProcessorABC`, that is a `Coffea` processor with a well defined structure:

- **Skim events**: apply lumi mask, triggers and a loose selection to reduce the number of events processed in the following analysis steps
- **Object preselection**: define the "good" object on which will be performed the final analysis
- **Event preselection**: define the baseline selection of the analysis
- **Categorization**: split events passing the preselection into different categories (e.g. signal + control region)
- **MC reweighting**: compute the correction weights to be applied to MC samples
- **Fill histograms** in all categories

For this demo, a dedicated `OpendataBaseProcessor` is implemented in `base_processor.py` to handle the specific structure of the 2012 Opendata CMS files.

A new processor inherited from the `OpendataBaseProcessor` can then be defined to run the $Z\rightarrow\mu\mu$ analysis. We don't need to rewrite the whole analysis processor, but only the methods that we want to override for our specific application.
In this case we just redefine:
- **apply_object_preselection()**: implement the dedicated muon selection
- **define_common_variables_after_presel()**: build the dimuon object and compute its invariant mass
- **count_objects()**: count the "good" objects


## Define analysis parameters

The parameters scheme is based on composable YAML parameter files managed with the `OmegaConf` package. A nice set of defaults is defined in `pocket_coffea.parameters.defaults`, containing the most common parameters for a Run-2 CMS analysis. These include the event flags, luminosity, triggers, object preselection, plotting style etc.
The user can then customize the parameters by defining their own parameters in the form of YAML files.
The default parameters can be eventually overridden with custom parameters, thanks to the `merge_parameters_from_files()` function, and are eventually stored in a single python dictionary.


## Define datasets

A dictionary containing the datasets information is passed to the `Configurator`. This includes the list of json datasets, together with a dictionary to filter the datasets by the sample key or by year. At this point it is also possible to define **subsamples**, i.e. split samples into different subsets (e.g. split data by the trigger path or split a MC sample into distinct components).

In our example, we split the Drell-Yan MC sample into three distinct subsamples with increasing number of muons in the event.


## Skim, preselection and categorization

All the selection operations are performed by making use of `Cut` objects. These objects are defined by a function of the events and a set of parameters. This way, for a given function we can have multiple cuts by changing the parameters that we pass to the `Cut` constructor.
In our example, a cut function `dimuon()` is used to build three `Cut` objects that define the signal and control regions.


## Weights and systematic variations

Another important ingredient of our analyses is the application of correction to the MC simulation and the proper accounting of systematic uncertainties. In PocketCoffea, a dedicated module `WeightsManager` is handling the application of weights to MC. In the configuration file, the user just needs to list the names of the correction weights to apply and the systematic variations that have to be stored in the output histograms.

The weights can be applied inclusively to all samples or only to a subset of samples. It's also possible to apply a weight only for a specific category (e.g. one category with a specific SF applied and one without it).


## Load Configurator

The core of the configuration is the `Configurator` object that stores all the datasets, parameters, selections and histograms configuration. The configuration can be dumped as a human readable .json file and as a .pkl file so that the same configuration can be loaded to rerun the same analysis in the future. The parameters are also dumped in a .yaml file to store all the parameters that define the analysis.


## Define Runner

The analysis processor in Coffea can be run with multiple executors:

- iterative executor: the event chunks are processed one after the other iteratively
- futures executor: the events chunks are processed by different CPUs in parallel, on the local machine
- scale out on a cluster using a scheduler (e.g. Dask on a SLURM cluster)

A dictionary of options needs to be defined and passed to the constructor of the Runner class.

In this example, we will run with the futures executor over 32 CPUs on the local machine.


## Inspect output

After running the processor, we find the following files in the output folder :
- `output_all.coffea`: the .coffea output file where the histograms are stored together with the metadata of the different samples, the cutflow dictionary and the sum of MC weights.
- `config.json`: the config file dumped in a json human-readable format
- `configurator.pkl`: the pickled version of the `Configurator` object that can be loaded to reproduce the analysis
- `parameters_dump.yaml`: the YAML dictionary containing all the relevant parameters for the analysis


## Produce Data/MC plots

In the .coffea output are stored the dictionaries of histograms and the metadata. These dictionaries are then passed to a `PlotManager` object that manages the plotting of several histograms in different categories.

Each histogram is stored as a `Shape` object, that provides a nice set of default plotting methods for Data/MC plots.

In this example, we load the plotter and then extract the shape corresponding to the dimuon invariant mass, and we plot this distribution in different categories.


## Study systematic uncertainties

In the plotting tools, a dedicated class `SystUnc` is implemented to handle systematic uncertainties. This object stores the nominal, up and down variations for each systematic uncertainty.
The `SystManager` object stores in a dictionary the systematic uncertainties for all the categories.

