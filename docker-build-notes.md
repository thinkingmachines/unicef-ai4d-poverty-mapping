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
* Run 

### Simplifying the docker run command

* Create default EOG_USER and EOG_PASSWORD - maybe store token maybe fetch token from github url with auto refresh on scheduled gh action?
* Remove eog_cache as external mount?
* Load notebooks (no need to )

```
docker run  -v $(pwd)/output-notebooks:/root/povmap/output-notebooks  -v $(pwd)/data:/root/povmap/data povmap-single-country-rollout -e PARAMS="-p COUNTRY_CODE ph -p ROLLOUT_DATE 2023-05-22 -p OSM_COUNTRY "
```