<div align="center">

# UNICEF AI4D Poverty Mapping Project

</div>

<a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/badge/-Python 3.9-blue?style=for-the-badge&logo=python&logoColor=white"></a>
<a href="https://black.readthedocs.io/en/stable/"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-black.svg?style=for-the-badge&labelColor=gray"></a>

<br/>
<br/>


# 📜 Description

The UNICEF AI4D Poverty Mapping Project aims to develop open datasets and machine learning (ML) models 
for poverty mapping estimation across nine countries in Southeast Asia (SEA).

We also aim to open source all the scripts, experiments and other artifacts used for 
developing these datasets and models, in order to allow others to replicate our work,
as well as to collaborate and extend our work for their own use cases.

This project is part of [Thinking Machines's overall push for open science through the AI4D
(AI for Development) Research Bank](https://stories.thinkingmachin.es/unicef-ai4d-research-bank/) 
which aims to accelerate the development and adoption of effective machine learning (ML) models for 
development across Southeast Asia.

We also publish our interim (work in progress) and final notebooks [here](https://thinkingmachines.github.io/unicef-ai4d-poverty-mapping)
<br/>
<br/>

## Data Access and Downloads

Due to the sensitive nature of the data and the DHS program terms of use, we cannot provide the raw DHS data. 

You can, however, request for access to raw data yourself on the [DHS website](https://dhsprogram.com/data/new-user-registration.cfm). In that case, you can use GeoWrangler's [DHS processing utils](https://geowrangler.thinkingmachin.es/tutorial.dhs.html) help perform the said pre-processing. 

The notebooks assume that the DHS Stata and Shape Files are located in `data/dhs/<iso-country-code>/`
where the `<iso-country-code>` is the two-letter ISO country code. 

The only other data access requirement is the EOG Nightlights Data which requires [registering for an account](https://eogdata.mines.edu/products/register). The nightlights download require the use of these credentials (user name and password) to download the nightlights data automatically.

All the other datasets used in this projects are publically available and the notebooks all provide the code necessary to download as well
cache the data.

Due to the size of the downloaded datasets, please make sure you have enough disk space (minimum 4OGB-50GB) to accommodate all the datasets used in building the models.

<br/>
<br/>

# ⚙️ Local Setup for Development

This repo assumes the use of [conda/mamba](https://github.com/conda-forge/miniforge#mambaforge) for simplicity in installing GDAL.


## Requirements

1. Python 3.9
2. make
3. mamba/conda


## 🐍 One-time Set-up
Run this the very first time you are setting-up the project on a machine to set-up a local Python environment for this project.

1. Install [mamba](https://github.com/conda-forge/miniforge#mambaforge) for your environment if you don't have it yet.
```bash
wget "https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-$(uname)-$(uname -m).sh"
bash Mambaforge-$(uname)-$(uname -m).sh
```

2. Create a local conda env and activate it. This will create a conda env folder in your project directory.
```
make conda-env
conda activate ./env
```

3. Run the one-time set-up make command.
```
make setup
```

4. To test if the setup was successful, run the tests.
```
make test
```

You should get a message that the tests passed.

## 🐍 Testing
To run automated tests, simply run `make test`.

## 📦 Dependencies

Over the course of development, you will likely introduce new library dependencies. This repo uses [pip-tools](https://github.com/jazzband/pip-tools) to manage the python dependencies.

There are two main files involved:
* `requirements.in` - contains high level requirements; this is what we should edit when adding/removing libraries
* `requirements.txt` - contains exact list of python libraries (including depdenencies of the main libraries) your environment needs to follow to run the repo code; compiled from `requirements.in`


When you add new python libs, please do the ff:

1. Add the library to the `requirements.in` file. You may optionally pin the version if you need a particular version of the library.

2. Run `make requirements` to compile a new version of the `requirements.txt` file and update your python env.

3. Commit both the `requirements.in` and `requirements.txt` files so other devs can get the updated list of project requirements.

> Note: When you are the one updating your python env to follow library changes from other devs (reflected through an updated `requirements.txt` file), simply run `pip-sync requirements.txt`


## 📜Documentation 

We are using [Quarto](https://quarto.org/) to maintain the Unicef AI4D Poverty Mapping [documentation site](https://thinkingmachines.github.io/unicef-ai4d-poverty-mapping/) 

Here are some quick tips to running quarto/updating the doc site:

* Download: 
[quarto download](https://quarto.org/docs/get-started/)

* Install:
```
sudo dpkg -i quarto-1.2.247-linux-amd64.deb
```

* Preview the site locally (view in [http://localhost:4444](http://localhost:4444)) :
```
quarto preview --port 4444 --no-browser
```

* Update the site (must have maintainer role):
```
quarto publish gh-pages --no-browser
```
* **Pro-tip** : If you are using VS Code as your code editor, install the [Quarto extension](https://marketplace.visualstudio.com/items?itemName=quarto.quarto) to make editing/previewing the doc site a lot smoother.


