#!/bin/bash
set -e
if command -v docker &> /dev/null
then
    if docker info > /dev/null 2>&1 ; 
    then
        echo "copying rollout data and notebooks into rollout-data and rollout-output-notebooks"
        mkdir -p $(pwd)/rollout-data
        mkdir -p $(pwd)/rollout-output-notebooks
        docker pull alpine:latest
        docker run -d --rm --name povmap-temp -v povmap-data:/root/povmap/data alpine tail -f /dev/null
        docker cp povmap-temp:/root/povmap/data/rollout $(pwd)/rollout-data
        docker cp povmap-temp:/root/povmap/data/output-notebooks $(pwd)/rollout-output-notebooks
        docker stop povmap-temp
        echo "please check the rollout output in 'rollout-output-data' && 'rollout-output-notebooks'"
        echo "done!"
    else
        echo "docker daemon doesnt seem be running. start it first before running this script!"
    fi
else
    echo "docker doesnt seem to be installed. please install docker first before running this script!"
fi

