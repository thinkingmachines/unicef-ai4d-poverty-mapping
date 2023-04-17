.PHONY: help conda-env setup requirements requirements-dev test
.DEFAULT_GOAL := help
-include .env

help:
	@awk -F ':.*?## ' '/^[a-zA-Z]/ && NF==2 {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

conda-env:
	mamba env create --prefix ./env -f environment.yml --no-default-packages

setup:
	mamba install -c conda-forge gdal -y
	pip install pip-tools
	pip-sync requirements.txt
	pip install -e .

requirements:
	pip-compile requirements.in -o requirements.txt -v
	pip-sync requirements.txt
	pip install -e .

test:
	pytest tests -v 
