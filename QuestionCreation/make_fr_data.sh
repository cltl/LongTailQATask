#!/usr/bin/env bash
bindir="fr_bin"
datadir="fr_output"
framefile="../EventRegistries/FireRescue1/firerescue_v3.pickle"

if [ ! -f $framefile ]; then
    echo "The frame file does not exist. Exiting now..."
    exit
fi

if [ ! -d $bindir ]; then
    mkdir $bindir
else
    rm -f "$bindir"/*.bin
    rm -f "$bindir"/cache
fi


python3 CreateQ.py -f $framefile -e fire_burning -s 1 -o $bindir  1>"logs/fr_1_burning.out" 2>"logs/fr_1_burning.err"

python3 CreateQ.py -f $framefile -e fire_burning -s 2 -o $bindir  1>"logs/fr_2_burning.out" 2>"logs/fr_2_burning.err"


if [ ! -d $datadir ]; then
    mkdir $datadir
fi

python3 create_task_data.py -d $bindir -o $datadir  1>"logs/fr_task_data.out" 2>"logs/fr_task_data.err"
