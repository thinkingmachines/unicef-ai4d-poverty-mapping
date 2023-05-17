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
* run papermill on test rollout notebook
```
papermill ./notebooks/run_rollout_test.ipynb ./output-notebooks/run_rollout_test.ipynb -p REGION philippines -p country_osm philippines -p ookla_year 2020 -p nightlights_year 2020
```

