#!/bin/bash

PYVERSION=`python3 --version 2>&1 | sed 's:Python ::;s:\.[0-9]\+$::'`
PYPLATFORM=`python3 -m sysconfig | grep Platform | sed 's/Platform: *"//;s:"::'`

export PYTHONPATH=..:../../waymarkedtrails-shields:../../osgende:../../pyosmium/build/lib.${PYPLATFORM}-${PYVERSION}

if [ "x$1" == "x-n" ]; then
    shift
    pytest "$@"
elif [ "x$1" == "x-s" ]; then
    shift
    pg_virtualenv -s pytest "$@"
else
    pg_virtualenv pytest "$@"
fi
