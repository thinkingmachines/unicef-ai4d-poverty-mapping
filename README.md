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

Note: When you are the one updating your python env to follow library changes from other devs (reflected through an updated `requirements.txt` file), simply run `pip-sync requirements.txt`
