#!/bin/sh

# $1 -> config

if [ -z "$1" ]; then
    echo 'Provide the path to a yaml config!'
    echo "Example: $0 /path/to/config.yaml"
    exit 1
fi

IMGNAME='nicovillanueva/tunneler'
CFG_FILE=$(readlink -f "$1")
VOLUME_KEY=$(python3 "$PWD/src/resolve-key.py" "$CFG_FILE")
docker run -ti --rm --net=host -v "$CFG_FILE":"/data/config.yml" $VOLUME_KEY $IMGNAME /data/config.yml
