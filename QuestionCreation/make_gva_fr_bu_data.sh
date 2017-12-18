#!/usr/bin/env bash
rm -rf logs & mkdir logs
bindir="gva_fr_bu_bin"
datadir="gva_fr_bu_output"
framefile_gva="../EventRegistries/GunViolenceArchive/frames/all"
framefile_fr="../EventRegistries/FireRescue1/firerescue_v3.pickle"
frame_file_bu="../EventRegistries/BusinessNews/business.pickle"

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


#python3 CreateQ.py -d $framefile -e killing_injuring -s 1 -o $bindir  # 1> "logs/1_gva_frkilling_injuring.out" 2>"logs/1_gva_frkilling_injuring.err"
python3 CreateQ.py -d $framefile_gva  -e killing -s 1 -o $bindir  1>"logs/1_gva_fr_killing.out" 2>"logs/1_gva_fr_killing.err"
python3 CreateQ.py -d $framefile_gva  -e injuring -s 1 -o $bindir 1>"logs/1_gva_fr_injuring.out" 2>"logs/1_gva_fr_injuring.err"

#python3 CreateQ.py -d $framefile -e killing_injuring -s 2 -o $bindir # 1>"logs/2_gva_fr_killing_injuring.out" 2>"logs/2_gva_fr_killing_injuring.err"
python3 CreateQ.py -d $framefile_gva  -e killing -s 2 -o $bindir 1>"logs/2_gva_fr_killing.out" 2>"logs/2_gva_fr_killing.err"
python3 CreateQ.py -d $framefile_gva  -e injuring -s 2 -o $bindir 1>"logs/2_gva_fr_injuring.out" 2>"logs/2_gva_fr_injuring.err"

#python3 CreateQ.py -d $framefile -e killing_injuring -s 3 -o $bindir # 1>"logs/3_gva_frkilling_injuring.out" 2>"logs/3_gva_frkilling_injuring.err"
python3 CreateQ.py -d $framefile_gva -e killing -s 3 -o $bindir 1>"logs/3_gva_fr_killing.out" 2>"logs/3_gva_fr_killing.err"
python3 CreateQ.py -d $framefile_gva -e injuring -s 3 -o $bindir 1>"logs/3_gva_fr_injuring.out" 2>"logs/3_gva_fr_injuring.err"


rm -f "$bindir"/cache

python3 CreateQ.py -d $framefile_gva -f $framefile_fr -e fire_burning -s 1 -o $bindir 1>"logs/1_gva_fr_burning.out" 2>"logs/1_gva_fr_burning.err"
python3 CreateQ.py -d $framefile_gva -f $framefile_fr -e fire_burning -s 2 -o $bindir  1>"logs/1_gva_fr_burning.out" 2>"logs/1_gva_fr_burning.err"


rm -f "$bindir"/cache

python3 CreateQ.py -d $framefile_gva -f $framefile_fr -b $frame_file_bu -e job_firing -s 1 -o $bindir  1>"logs/bu_1.out" 2>"logs/bu_1.err"
python3 CreateQ.py -d $framefile_gva -f $framefile_fr -b $frame_file_bu -e job_firing -s 2 -o $bindir  1>"logs/bu_2.out" 2>"logs/bu_2.err"

if [ ! -d $datadir ]; then
    mkdir $datadir
fi

python3 create_task_data.py -d $bindir -o $datadir 1>"logs/gva_fr_task_data.out" 2>"logs/gva_fr_task_data.err"
