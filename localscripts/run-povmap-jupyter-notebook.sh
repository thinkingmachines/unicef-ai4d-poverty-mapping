#!/bin/bash
set -e
if command -v docker &> /dev/null 
then
    if docker info &> /dev/null 
    then
        docker pull ghcr.io/butchtm/povmap-jupyter:latest
        docker volume create povmap-data
        docker run -d  --rm --name povmap-jupyter -v povmap-data:/root/povmap/data -p 8888:8888 ghcr.io/butchtm/povmap-jupyter:latest
        echo "jupyter notebook is running. open a browser to http://localhost:8888"
        echo "run 'docker stop povmap-jupyter' to stop the jupyter notebook"
    else
        echo "docker daemon doesnt seem be running. start it first before running this script!"
    fi
else
    echo "docker doesnt seem to be installed. please install docker first before running this script!"
fi

