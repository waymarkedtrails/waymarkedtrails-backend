#!/bin/bash -e

export PYTHONPATH=~/osm/dev/pyosmium/build/lib.linux-x86_64-3.7:~/osm/dev/osgende:~/osm/dev/waymarkedtrails

export ROUTEMAPDB_CONF_MODULE=maps.hiking

if [[ ! -d /tmp/symbols ]]; then
    mkdir /tmp/symbols
fi

cd ~/osm/dev/waymarkedtrails
python3 db/common/symbols.py /tmp/symbols
#for fl in /tmp/symbols/*.svg; do
#    convert $fl ${fl/svg/png}
#done
