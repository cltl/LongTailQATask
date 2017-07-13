#!/usr/bin/env bash
bindir="trial_bin"
datadir="output"
framefile="../EventRegistries/GunViolenceArchive/frames/all"

if [ ! -f $framefile ]; then
    echo "The frame file does not exist. Exiting now..."
    exit
fi

if [ ! -d $bindir ]; then
    mkdir $bindir
else
    rm -f "$bindir"/*.bin
fi


python3 CreateQ.py -d $framefile -e killing_injuring -s 1 -o $bindir  # 1> "logs/1_killing_injuring.out" 2>"logs/1_killing_injuring.err"
python3 CreateQ.py -d $framefile -e killing -s 1 -o $bindir # 1>"logs/1_killing.out" 2>"logs/1_killing.err"
python3 CreateQ.py -d $framefile -e injuring -s 1 -o $bindir # 1>"logs/1_injuring.out" 2>"logs/1_injuring.err"

python3 CreateQ.py -d $framefile -e killing_injuring -s 2 -o $bindir # 1>"logs/2_killing_injuring.out" 2>"logs/2_killing_injuring.err"
python3 CreateQ.py -d $framefile -e killing -s 2 -o $bindir # 1>"logs/2_killing.out" 2>"logs/2_killing.err"
python3 CreateQ.py -d $framefile -e injuring -s 2 -o $bindir # 1>"logs/2_injuring.out" 2>"logs/2_injuring.err"

python3 CreateQ.py -d $framefile -e killing_injuring -s 3 -o $bindir # 1>"logs/3_killing_injuring.out" 2>"logs/3_killing_injuring.err"
python3 CreateQ.py -d $framefile -e killing -s 3 -o $bindir # 1>"logs/3_killing.out" 2>"logs/3_killing.err"
python3 CreateQ.py -d $framefile -e injuring -s 3 -o $bindir # 1>"logs/3_injuring.out" 2>"logs/3_injuring.err"

if [ ! -d $datadir ]; then
    mkdir $datadir
fi

python3 create_task_data.py -d $bindir -o $datadir # 1>"logs/task_data.out" 2>"logs/task_data.err"
