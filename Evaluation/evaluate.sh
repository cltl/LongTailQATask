#!/bin/sh

SCORERDIR="reference-coreference-scorers"

if [ -z "$1" ]; then
    DATADIR="../Data"
else
    DATADIR="$1"
fi
GOLDDIR="$DATADIR/gold/"
SYSTEMDIR="$DATADIR/system/"

if [ ! -d "$SCORERDIR" ]; then
    echo "*** The coreference scorer directory was not detected. Now cloning ... ***"
    echo 
    git clone https://github.com/cltl/reference-coreference-scorers/ > git.log 2>&1
    success=$?
    if [[ $success -eq 0 ]];
    then
        echo "*** The coreference scorer was cloned successfuly! ***"
    else
        cat git.log
        echo "Something went wrong! Exiting now..."
        exit
    fi
    echo
else
    echo "*** The reference scorer directory already exists. Now evaluating ... ***"
    echo
fi

### CHECKS ###

if [ ! -d $DATADIR ]; then
    echo "$DATADIR does not exist. Nothing to evaluate here! Exiting now..."
    exit
fi

goldfiles=$(shopt -s nullglob dotglob; echo $GOLDDIR/*)
if (( ${#goldfiles} )); then
    echo "GOLD directory exists and is not empty!"
else
    echo "GOLD directory does not exist or is empty. Nothing to evaluate here! Exiting now..."
    exit
fi

sysfiles=$(shopt -s nullglob dotglob; echo $SYSTEMDIR/*)
if (( ${#sysfiles} )); then
    echo "SYSTEM directory exists and is not empty!"
else
    echo "SYSTEM directory does not exist or is empty. Nothing to evaluate here! Exiting now..."
    exit
fi

if [ ! -d "$DATADIR/scores" ]; then
    mkdir "$DATADIR/scores"
else
    #for metric in muc bcub ceafm ceafe blanc; do
    rm "$DATADIR/scores"/*
    #done
fi

### MENTION - LEVEL EVALUATION ###

for sysfile in "$SYSTEMDIR"/*
do
    goldfile="$GOLDDIR/${sysfile##*/}"
    if [ ! -f $goldfile ]; then
        echo "ERROR: GOLD file missing for $sysfile. Exiting now..."
        exit
    fi
    for metric in muc bcub ceafm ceafe blanc; do
        outfile="$DATADIR/scores/${metric}.${goldfile##*/}"
        perl reference-coreference-scorers/scorer.pl $metric $goldfile $sysfile > $outfile
        tail -2 $outfile | head -1 >> "$DATADIR/scores/${metric}_all.conll"
    done
done

#ABSDATADIR="$(cd "$(dirname "$DATADIR")"; pwd)/$(basename "$DATADIR")"
python3 evaluate_more.py $DATADIR
