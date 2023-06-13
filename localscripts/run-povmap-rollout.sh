#!/bin/bash
set -e
if command -v docker &> /dev/null 
then
    if docker info &> /dev/null 
    then
        docker pull ghcr.io/butchtm/povmap-jupyter:latest
        docker volume create povmap-data
        docker run -it --rm --name povmap-rollout -e DEBUG=true -v povmap-data:/root/povmap/data ghcr.io/butchtm/povmap-jupyter:latest "python scripts/run_rollout.py"
        echo "rollout run completed. please check the rollout and output-notebooks folders in the docker volume povmap-data"
        echo "run 'copy-rollout-to-local.sh' to copy the rollout and output-notebooks to your local machine"
    else
        echo "docker daemon doesnt seem be running. start it first before running this script!"
    fi
else
    echo "docker doesnt seem to be installed. please install docker first before running this script!"
fi

