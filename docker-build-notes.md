# Notes on building docker images for Poverty Mapping
* create a docker image by running the following command
```
docker build .
docker tag <sha-256-id> povmap
```
* run the docker image by running
```
docker run povmap
```
* run docker with port 8888 open
```
docker run -it -p 8888:8888 povmap-test /bin/bash

```
* run jupyter inside docker
```
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password=''
```
* run jupyter in docker directly
```
docker run  -p 8888:8888 povmap-test "jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password=''"
```
* run papermill on test rollout notebook
```
papermill ./notebooks/run_rollout_test.ipynb ./output-notebooks/run_rollout_test.ipynb -p REGION philippines -p country_osm philippines -p ookla_year 2020 -p nightlights_year 2020
```
* run papermill on timor leste generate grids
```
papermill ./notebooks/2023-02-21-single-country-rollouts/tl/2_tl_generate_grids.ipynb ./output-notebooks/2_tl_generate_grids.ipynb -p COUNTRY_CODE tl
```

* run papermill on timor leste rollout for 
default parameters
```
papermill ./notebooks/2023-02-21-single-country-rollouts/tl/3_tl_rollout_model.ipynb ./output-notebooks/3_tl_rollout_model.ipynb
```

## Docker environment
* Environment variables
  - EOG_USER, EOG_PASSWORD - register dummy at EOG and hardcode usage
* Mount volumes:
  - directories
  ``` 
$HOME/.cache/geowrangler
$HOME/.eog_creds
$PROJECT/data
$PROJECT/output-notebooks
$PROJECT/notebooks

* Run jupyter with mounts and env
```
docker run  -p 8888:8888 -v $(pwd)/notebooks:/root/povmap/notebooks -v $(pwd)/output-notebooks:/root/povmap/output-notebooks -v $HOME/.cache:/root/.cache -v $(pwd)/eog_cache:/root/.eog_creds -v $(pwd)/data:/root/povmap/data -e EOG_USER -e EOG_PASSWORD  povmap-test "jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password=''"
```

###  Run papermill with mounts and env
* Run generate training data on tl
```
docker run  -v $(pwd)/notebooks:/root/povmap/notebooks -v $(pwd)/output-notebooks:/root/povmap/output-notebooks -v $HOME/.cache:/root/.cache -v $HOME/.cache/geowrangler:/root/.geowrangler -v $(pwd)/eog_cache:/root/.eog_creds -v $(pwd)/data:/root/povmap/data -e EOG_USER -e EOG_PASSWORD  povmap-test "papermill ./notebooks/2023-02-21-single-country-rollouts/tl/0_generate_training_data.ipynb ./output-notebooks/0_generate_training_data.ipynb -p COUNTRY_CODE tl -p ROLLOUT_DATE 2023-05-22"

```
* Run train model on tl
```
docker run  -v $(pwd)/notebooks:/root/povmap/notebooks -v $(pwd)/output-notebooks:/root/povmap/output-notebooks -v $HOME/.cache:/root/.cache -v $HOME/.cache/geowrangler:/root/.geowrangler -v $(pwd)/eog_cache:/root/.eog_creds -v $(pwd)/data:/root/povmap/data -e EOG_USER -e EOG_PASSWORD  povmap-test "papermill ./notebooks/2023-02-21-single-country-rollouts/tl/1_tl_train_model.ipynb ./output-notebooks/1_tl_train_model.ipynb -p COUNTRY_CODE tl -p ROLLOUT_DATE 2023-05-22"

```
* Run grid generation on TL
```
docker run  -v $(pwd)/notebooks:/root/povmap/notebooks -v $(pwd)/output-notebooks:/root/povmap/output-notebooks -v $HOME/.cache:/root/.cache -v $HOME/.cache/geowrangler:/root/.geowrangler -v $(pwd)/eog_cache:/root/.eog_creds -v $(pwd)/data:/root/povmap/data -e EOG_USER -e EOG_PASSWORD  povmap-test "papermill ./notebooks/2023-02-21-single-country-rollouts/tl/2_tl_generate_grids.ipynb ./output-notebooks/2_tl_generate_grids.ipynb -p COUNTRY_CODE tl -p ROLLOUT_DATE 2023-05-22"

```

* Run rollout on TL
```
docker run  -v $(pwd)/notebooks:/root/povmap/notebooks -v $(pwd)/output-notebooks:/root/povmap/output-notebooks -v $HOME/.cache:/root/.cache -v $HOME/.cache/geowrangler:/root/.geowrangler -v $(pwd)/eog_cache:/root/.eog_creds -v $(pwd)/data:/root/povmap/data -e EOG_USER -e EOG_PASSWORD  povmap-test "papermill ./notebooks/2023-02-21-single-country-rollouts/tl/3_tl_rollout_model.ipynb ./output-notebooks/3_tl_rollout_model.ipynb -p COUNTRY_CODE tl -p ROLLOUT_DATE 2023-05-22"
```

### Standardized single country models:
* Same notebook for all 4 single country models
* Run generate training data for TL
```
docker run  -v $(pwd)/notebooks:/root/povmap/notebooks -v $(pwd)/output-notebooks:/root/povmap/output-notebooks -v $HOME/.cache:/root/.cache -v $HOME/.cache/geowrangler:/root/.geowrangler -v $(pwd)/eog_cache:/root/.eog_creds -v $(pwd)/data:/root/povmap/data -e EOG_USER -e EOG_PASSWORD  povmap-test "papermill ./notebooks/single-country/0_generate_training_data.ipynb ./output-notebooks/tl_0_generate_training_data.ipynb -p COUNTRY_CODE tl -p COUNTRY_OSM east-timor -p OOKLA_YEAR 2019 -p NIGHTLIGHTS_YEAR 2016 -p DHS_DTA_PREFIX TLHR71DT/TLHR71FL -p DHS_GEO_PREFIX TLGE71FL/TLGE71FL -p ROLLOUT_DATE 2023-05-23"
```
* Run train model for TL
```
docker run  -v $(pwd)/notebooks:/root/povmap/notebooks -v $(pwd)/output-notebooks:/root/povmap/output-notebooks -v $HOME/.cache:/root/.cache -v $HOME/.cache/geowrangler:/root/.geowrangler -v $(pwd)/eog_cache:/root/.eog_creds -v $(pwd)/data:/root/povmap/data -e EOG_USER -e EOG_PASSWORD  povmap-test "papermill ./notebooks/single-country/1_train_model.ipynb ./output-notebooks/tl_1_train_model.ipynb -p COUNTRY_CODE tl -p ROLLOUT_DATE 2023-05-23"
```
* Run generate grids for TL
```
docker run  -v $(pwd)/notebooks:/root/povmap/notebooks -v $(pwd)/output-notebooks:/root/povmap/output-notebooks -v $HOME/.cache:/root/.cache -v $HOME/.cache/geowrangler:/root/.geowrangler -v $(pwd)/eog_cache:/root/.eog_creds -v $(pwd)/data:/root/povmap/data -e EOG_USER -e EOG_PASSWORD  povmap-test "papermill ./notebooks/single-country/2_generate_grids.ipynb ./output-notebooks/tl_2_generate_grids.ipynb -p COUNTRY_CODE tl -p ROLLOUT_DATE 2023-05-23"
```
* Run rollout-model for TL using previously trained model
```
docker run  -v $(pwd)/notebooks:/root/povmap/notebooks -v $(pwd)/output-notebooks:/root/povmap/output-notebooks -v $HOME/.cache:/root/.cache -v $HOME/.cache/geowrangler:/root/.geowrangler -v $(pwd)/eog_cache:/root/.eog_creds -v $(pwd)/data:/root/povmap/data -e EOG_USER -e EOG_PASSWORD  povmap-test "papermill ./notebooks/single-country/3_rollout_model.ipynb ./output-notebooks/tl_3_rollout_model.ipynb -p COUNTRY_CODE tl -p COUNTRY_OSM east-timor  -p OOKLA_YEAR 2019 -p NIGHTLIGHTS_YEAR 2016 -p ROLLOUT_DATE 2023-05-23"
```

### Run single country notebook for other countries

* Run generate training data for PH
```
docker run  -v $(pwd)/notebooks:/root/povmap/notebooks -v $(pwd)/output-notebooks:/root/povmap/output-notebooks -v $HOME/.cache:/root/.cache -v $HOME/.cache/geowrangler:/root/.geowrangler -v $(pwd)/eog_cache:/root/.eog_creds -v $(pwd)/data:/root/povmap/data -e EOG_USER -e EOG_PASSWORD  povmap-test "papermill ./notebooks/single-country/0_generate_training_data.ipynb ./output-notebooks/ph_0_generate_training_data.ipynb -p COUNTRY_CODE ph -p COUNTRY_OSM philippines -p OOKLA_YEAR 2019 -p NIGHTLIGHTS_YEAR 2017 -p DHS_DTA_PREFIX PHHR71DT/PHHR71FL -p DHS_GEO_PREFIX PHGE71FL/PHGE71FL -p ROLLOUT_DATE 2023-05-23"
```
* Run train model for PH
```
docker run  -v $(pwd)/notebooks:/root/povmap/notebooks -v $(pwd)/output-notebooks:/root/povmap/output-notebooks -v $HOME/.cache:/root/.cache -v $HOME/.cache/geowrangler:/root/.geowrangler -v $(pwd)/eog_cache:/root/.eog_creds -v $(pwd)/data:/root/povmap/data -e EOG_USER -e EOG_PASSWORD  povmap-test "papermill ./notebooks/single-country/1_train_model.ipynb ./output-notebooks/ph_1_train_model.ipynb -p COUNTRY_CODE ph -p ROLLOUT_DATE 2023-05-23"
```
* Run generate grids for PH
```
docker run  -v $(pwd)/notebooks:/root/povmap/notebooks -v $(pwd)/output-notebooks:/root/povmap/output-notebooks -v $HOME/.cache:/root/.cache -v $HOME/.cache/geowrangler:/root/.geowrangler -v $(pwd)/eog_cache:/root/.eog_creds -v $(pwd)/data:/root/povmap/data -e EOG_USER -e EOG_PASSWORD  povmap-test "papermill ./notebooks/single-country/2_generate_grids.ipynb ./output-notebooks/ph_2_generate_grids.ipynb -p COUNTRY_CODE ph -p ROLLOUT_DATE 2023-05-23"
```
* Run rollout-model for PH using previously trained model
```
docker run  -v $(pwd)/notebooks:/root/povmap/notebooks -v $(pwd)/output-notebooks:/root/povmap/output-notebooks -v $HOME/.cache:/root/.cache -v $HOME/.cache/geowrangler:/root/.geowrangler -v $(pwd)/eog_cache:/root/.eog_creds -v $(pwd)/data:/root/povmap/data -e EOG_USER -e EOG_PASSWORD  povmap-test "papermill ./notebooks/single-country/3_rollout_model.ipynb ./output-notebooks/ph_3_rollout_model.ipynb -p COUNTRY_CODE ph -p COUNTRY_OSM philippines  -p OOKLA_YEAR 2019 -p NIGHTLIGHTS_YEAR 2017 -p ROLLOUT_DATE 2023-05-23"
```

* Run generate training data for KH
```
docker run  -v $(pwd)/notebooks:/root/povmap/notebooks -v $(pwd)/output-notebooks:/root/povmap/output-notebooks -v $HOME/.cache:/root/.cache -v $HOME/.cache/geowrangler:/root/.geowrangler -v $(pwd)/eog_cache:/root/.eog_creds -v $(pwd)/data:/root/povmap/data -e EOG_USER -e EOG_PASSWORD  povmap-test "papermill ./notebooks/single-country/0_generate_training_data.ipynb ./output-notebooks/kh_0_generate_training_data.ipynb -p COUNTRY_CODE kh -p COUNTRY_OSM cambodia -p OOKLA_YEAR 2019 -p NIGHTLIGHTS_YEAR 2014 -p DHS_DTA_PREFIX KHHR73DT/KHHR73FL -p DHS_GEO_PREFIX KHGE71FL/KHGE71FL -p ROLLOUT_DATE 2023-05-23"
```
* Run train model for KH
```
docker run  -v $(pwd)/notebooks:/root/povmap/notebooks -v $(pwd)/output-notebooks:/root/povmap/output-notebooks -v $HOME/.cache:/root/.cache -v $HOME/.cache/geowrangler:/root/.geowrangler -v $(pwd)/eog_cache:/root/.eog_creds -v $(pwd)/data:/root/povmap/data -e EOG_USER -e EOG_PASSWORD  povmap-test "papermill ./notebooks/single-country/1_train_model.ipynb ./output-notebooks/kh_1_train_model.ipynb -p COUNTRY_CODE kh -p ROLLOUT_DATE 2023-05-23"
```
* Run generate grids for KH
```
docker run  -v $(pwd)/notebooks:/root/povmap/notebooks -v $(pwd)/output-notebooks:/root/povmap/output-notebooks -v $HOME/.cache:/root/.cache -v $HOME/.cache/geowrangler:/root/.geowrangler -v $(pwd)/eog_cache:/root/.eog_creds -v $(pwd)/data:/root/povmap/data -e EOG_USER -e EOG_PASSWORD  povmap-test "papermill ./notebooks/single-country/2_generate_grids.ipynb ./output-notebooks/kh_2_generate_grids.ipynb -p COUNTRY_CODE kh -p ROLLOUT_DATE 2023-05-23"
```
* Run rollout-model for KH using previously trained model
```
docker run  -v $(pwd)/notebooks:/root/povmap/notebooks -v $(pwd)/output-notebooks:/root/povmap/output-notebooks -v $HOME/.cache:/root/.cache -v $HOME/.cache/geowrangler:/root/.geowrangler -v $(pwd)/eog_cache:/root/.eog_creds -v $(pwd)/data:/root/povmap/data -e EOG_USER -e EOG_PASSWORD  povmap-test "papermill ./notebooks/single-country/3_rollout_model.ipynb ./output-notebooks/kh_3_rollout_model.ipynb -p COUNTRY_CODE kh -p COUNTRY_OSM cambodia  -p OOKLA_YEAR 2019 -p NIGHTLIGHTS_YEAR 2014 -p ROLLOUT_DATE 2023-05-23"
```
## Simplified Run Rollout commands

* Run generate grids for TL
```
docker run  -v $(pwd)/notebooks:/root/povmap/notebooks -v $(pwd)/output-notebooks:/root/povmap/output-notebooks -v $HOME/.cache:/root/.cache -v $HOME/.cache/geowrangler:/root/.geowrangler -v $(pwd)/eog_cache:/root/.eog_creds -v $(pwd)/data:/root/povmap/data -e EOG_USER -e EOG_PASSWORD  povmap-test "papermill ./notebooks/single-country/2_generate_grids.ipynb ./output-notebooks/tl_2_generate_grids.ipynb -p COUNTRY_CODE tl -p ROLLOUT_DATE 2023-05-23"
```
* Run rollout-model for TL using previously trained model
```
docker run  -v $(pwd)/notebooks:/root/povmap/notebooks -v $(pwd)/output-notebooks:/root/povmap/output-notebooks -v $HOME/.cache:/root/.cache -v $HOME/.cache/geowrangler:/root/.geowrangler -v $(pwd)/eog_cache:/root/.eog_creds -v $(pwd)/data:/root/povmap/data -e EOG_USER -e EOG_PASSWORD  povmap-test "papermill ./notebooks/single-country/3_rollout_model.ipynb ./output-notebooks/tl_3_rollout_model.ipynb -p COUNTRY_CODE tl -p COUNTRY_OSM east-timor  -p OOKLA_YEAR 2019 -p NIGHTLIGHTS_YEAR 2016 -p ROLLOUT_DATE 2023-05-23"
```
### Simplified run docker commands

* Create a persistent volume

```
docker volume create povmap-data

```
* Pull povmap-jupyter docke image

```
docker pull ghcr.io/butchtm/povmap-jupyter:latest

```

* Run jupyter (read-only notebooks with caching)

```
docker run -v povmap-data:/root/povmap/data -p 8888:8888 ghcr.io/butchtm/povmap-jupyter

```
* Run generate grids and rollout

```
docker run -it -v povmap-data:/root/povmap/data ghcr.io/butchtm/povmap-jupyter "python scripts/run_rollout.py"
```

## Run remote localscripts via curl
```
curl -s https://raw.githubusercontent.com/thinkingmachines/unicef-ai4d-poverty-mapping/main/localscripts/run-povmap-rollout.sh > run-povmap-rollout.sh && \ 
chmod +x ./run-povmap-rollout.sh && \
./run-povmap-rollout.sh
