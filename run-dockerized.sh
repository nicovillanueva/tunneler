#!/bin/bash

# $1 -> config

if [ -z $1 ]; then
    echo 'Provide the path to a yaml config!'
    echo "Example: $0 /path/to/config.yaml"
    exit 1
fi

IMGNAME='nicovillanueva/tunneler'

VOLUME_CONFIG="-v $1:/data/config.yml"
VOLUME_KEY=$(python3 $PWD/src/resolve-key.py $1)

docker run -ti --rm --net=host $VOLUME_CONFIG $VOLUME_KEY tunneler /data/config.yml
