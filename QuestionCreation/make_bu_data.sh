#!/usr/bin/env bash
bindir="bu_bin"
datadir="bu_output"
framefile="../EventRegistries/BusinessNews/business.pickle"

if [ ! -f $framefile ]; then
    echo "The frame file does not exist. Exiting now..."
    exit
fi

if [ ! -d $bindir ]; then
    mkdir $bindir
else
    rm -f "$bindir"/*.bin
    #rm -f "$bindir"/cache
fi


python3 CreateQ.py -b $framefile -e job_firing -s 1 -o $bindir  #1>"logs/bu_1.out" 2>"logs/bu_1.err"

python3 CreateQ.py -b $framefile -e job_firing -s 2 -o $bindir  #1>"logs/bu_2.out" 2>"logs/bu_2.err"


if [ ! -d $datadir ]; then
    mkdir $datadir
fi

python3 create_task_data.py -d $bindir -o $datadir  #1>"logs/fr_task_data.out" 2>"logs/fr_task_data.err"
