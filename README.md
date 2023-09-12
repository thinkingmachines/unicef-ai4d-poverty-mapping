<div align="center">

# UNICEF AI4D Relative Wealth Project

</div>

<a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/badge/-Python 3.9-blue?style=for-the-badge&logo=python&logoColor=white"></a>
<a href="https://black.readthedocs.io/en/stable/"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-black.svg?style=for-the-badge&labelColor=gray"></a>

<br/>
<br/>


# 📜 Description

The UNICEF AI4D Relative Wealth Project aims to develop open datasets and machine learning (ML) models for poverty mapping estimation across nine countries in Southeast Asia (SEA).

We also aim to open source all the scripts, experiments and other artifacts used for developing these datasets and models in order to allow others to replicate our work as well as to collaborate and extend our work for their own use cases.

This project is part of [Thinking Machines's overall push for open science through the AI4D (AI for Development) Research Bank](https://stories.thinkingmachin.es/unicef-ai4d-research-bank/) which aims to accelerate the development and adoption of effective machine learning (ML) models for 
development across Southeast Asia.

Documentation geared towards our methodology and experiments can be found [here](https://thinkingmachines.github.io/unicef-ai4d-relative-wealth).

<br/>
<br/>

# 💻 Replicating model training and rollout for a country

Our final trained models and their use to produce nationwide estimates can replicated through our notebooks, assuming you've followed the `Data` and `Local Development` setup below.


* For countries with available DHS training data (Cambodia, Myanmar, Philippines, and Timor-Leste), please refer to the notebooks here:  https://github.com/thinkingmachines/unicef-ai4d-relative-wealth/tree/main/notebooks/2023-02-21-single-country-rollouts

* For the other countries without DHS training data (Indonesia, Laos, Malaysia, Thailand, and Vietnam), please refer to the notebooks here: https://github.com/thinkingmachines/unicef-ai4d-relative-wealth/tree/main/notebooks/2023-02-21-cross-country-rollouts


All the output files (models, datasets, intermediate files) can all be downloaded from [here](https://drive.google.com/drive/u/0/folders/1QX0xJc6MHxY7dzIsVMDm5TH0F-NwXhBW). 

<br/>
<br/>

# 📚 Data Setup

## DHS Data

Due to the sensitive nature of the data and the DHS program terms of use, we cannot provide the raw DHS data used in our experiments. 

You will have to request for access to raw data yourself on the [DHS website](https://dhsprogram.com/data/new-user-registration.cfm). 

Generally, for all the experiment notebooks in this repo, they assume that the **DHS Stata and Shape** zip files contents are unzipped to its own folder under `data/dhs/<iso-country-code>/` where the `<iso-country-code>` is the two-letter ISO country code.

For example, from the data for the Philippines will have this directory structure:
```
data/
    dhs/
        ph/
            PHGE71FL/
                DHS_README.txt
                GPS_Displacement_README.txt
                PHGE71FL.cpg
                PHGE71FL.dbf
                PHGE71FL.prj
                PHGE71FL.sbn
                PHGE71FL.sbx
                PHGE71FL.shp
                PHGE71FL.shp.xml
                PHGE71FL.shx
            PHHR71DT/
                PHHR71FL.DCT
                PHHR71FL.DO
                PHHR71FL.DTA
                PHHR71FL.FRQ
                PHHR71FL.FRW
                PHHR71FL.MAP
```

*If you create your own notebook, of course you are free to modify these conventions for filepaths yourself. But out-of-the-box, this is what our notebooks assume.*
<br/>
<br/>
## Night Lights from EOG

The only other data access requirement is for the EOG Nightlights Data which requires [registering for an account](https://eogdata.mines.edu/products/register). The notebooks require the use of these credentials (user name and password) to download the nightlights data automatically.
<br/>
<br/>

## General Dataset Notes
All the other datasets used in this project are publically available and the notebooks provide the code necessary to automatically download and cache the data.

Due to the size of the datasets, please make sure you have enough disk space (minimum 40GB-50GB) to accommodate all the data used in building the models.

<br/>
<br/>

# ⚙️ Local Setup for Development

This repo assumes the use of miniconda for simplicity in installing GDAL.


## Requirements

1. Python 3.9
2. make
3. miniconda


## 🐍 One-time Set-up
Run this the very first time you are setting-up the project on a machine to set-up a local Python environment for this project.

1. Install [miniconda](https://docs.conda.io/en/latest/miniconda.html) for your environment if you don't have it yet.
```bash
wget "https://repo.anaconda.com/miniconda/Miniconda3-latest-$(uname)-$(uname -m).sh"
bash Miniconda3-latest-$(uname)-$(uname -m).sh
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

4. To test if the setup was successful, run the tests. You should get a message that all the tests passed.
```
make test
```

At this point, you should be ready to run all the existing notebooks on your local.


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

We are using [Quarto](https://quarto.org/) to maintain the Unicef AI4D Relative Wealth [documentation site.](https://thinkingmachines.github.io/unicef-ai4d-relative-wealth/) 

Here are some quick tips to running quarto/updating the doc site, assuming you're on Linux.

For other platforms, please refer to [Quarto's website](https://quarto.org/docs/get-started/).


* Download: 
```
wget https://github.com/quarto-dev/quarto-cli/releases/download/v1.2.247/quarto-1.2.247-linux-amd64.deb
```

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


## ☸️Running in Docker 

We have created a [docker image](https://github.com/butchtm/unicef-ai4d-relative-wealth/pkgs/container/povmap-jupyter) (`ghcr.io/butchtm/povmap-jupyter`) of the poverty mapping repo for those who want to view the notebooks or rollout the models for new countries and new data (e.g. new nightlights and ookla years)

To run these docker images please copy and paste the following scripts to run on your linux, mac or windows (wsl) terminals:

* **View Jupyter notebooks (Read-only)** This will run a jupyter notebook environment containing the poverty mapping notebooks at http://localhost:8888/lab/tree/notebooks

```bash
curl -s https://raw.githubusercontent.com/thinkingmachines/unicef-ai4d-relative-wealth/main/localscripts/run-povmap-jupyter-notebook.sh > run-povmap-jupyter-notebook.sh && \
chmod +x run-povmap-jupyter-notebook.sh && \
./run-povmap-jupyter-notebook.sh
```
* **Country-wide rollout** This will run an interactive dialog that will rollout the poverty mapping models for different countries
and different time periods

```bash
curl -s https://raw.githubusercontent.com/thinkingmachines/unicef-ai4d-relative-wealth/main/localscripts/run-povmap-rollout.sh > run-povmap-rollout.sh && \
chmod +x run-povmap-rollout.sh && \
./run-povmap-rollout.sh
```

* **Copy rollout to local directory** This will copy the contents of the rollout notebooks and rollout data into your current directory (after running a new rollout) to `rollout-data` and `rollout-output-notebooks`

```bash
curl -s https://raw.githubusercontent.com/thinkingmachines/unicef-ai4d-relative-wealth/main/localscripts/copy-rollout-to-local.sh > copy-rollout-to-local.sh && \
chmod +x copy-rollout-to-local.sh && \
./copy-rollout-to-local.sh
```

> Note: These commands assume that `curl` is installed and will download the scripts, change their permissions to executable as well as run them. After the initial download, you can just rerun the scripts which would would have been downloaded to your current directory.

> Note: The scripts create and use a docker volume named `povmap-data` which contains the outputs as well as caches the data used for generating the features from public datasets

> Note: Rolling out the notebooks requires downloading EOG nightlights data so a user id and password are required as detailed in the previous section above.

