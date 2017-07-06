#!/usr/bin/env bash
bindir="trial_bin"
datadir="../Data"
framefile="../EventRegistries/GunViolenceArchive/frames/all"

if [ ! -f $framefile ]; then
    echo "The frame file does not exist. Exiting now..."
    exit
fi

if [ ! -d $bindir ]; then
    mkdir $bindir
else
    rm -f "$bindir"/*
fi


python3 CreateQ.py -d $framefile -e killing_injuring -s 1 -o $bindir
python3 CreateQ.py -d $framefile -e killing -s 1 -o $bindir
python3 CreateQ.py -d $framefile -e injuring -s 1 -o $bindir

python3 CreateQ.py -d $framefile -e killing_injuring -s 2 -o $bindir
python3 CreateQ.py -d $framefile -e killing -s 2 -o $bindir
python3 CreateQ.py -d $framefile -e injuring -s 2 -o $bindir

python3 CreateQ.py -d $framefile -e killing_injuring -s 3 -o $bindir
python3 CreateQ.py -d $framefile -e killing -s 3 -o $bindir
python3 CreateQ.py -d $framefile -e injuring -s 3 -o $bindir

if [ ! -d $datadir ]; then
    mkdir $datadir
fi

python3 create_task_data.py -d $bindir -o $datadir
