#!/bin/sh

##### 2) MENTION-LEVEL EVALUATION #####

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo "Please supply 3 arguments to this script: DATADIR, SYSTEMDIR, GOLDDIR."
    echo "Usage: "
    echo "bash evaluate.sh <SYSTEMDIR> <GOLDDIR> <OUTPUTDIR>"
    exit
fi

SYSTEMDIR="$1"
GOLDDIR="$2"
OUTPUTDIR="$3"

SCORERDIR="reference-coreference-scorers"

### CHECKS ###

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

if [ ! -d "$OUTPUTDIR" ]; then
    echo "WARN: $OUTPUTDIR does not exist. Creating it now..."
    mkdir "$OUTPUTDIR"
else
    #for metric in muc bcub ceafm ceafe blanc; do
    rm "$OUTPUTDIR"/*
    #done
fi

if [ ! -d "$OUTPUTDIR" ]; then
    echo "Problem with creating the output directory. Exiting ..."
    exit
fi

### CHECKS done ###

MCOUNTER=0
for goldfile in "${GOLDDIR}"/*.conll
do
    sysfile="$SYSTEMDIR/${goldfile##*/}"
    if [ ! -f $sysfile ]; then
        echo "WARN: System answer missing for gold file $goldfile."
    else
        (( MCOUNTER++ ))
        for metric in muc bcub ceafm ceafe blanc; do
            outfile="$OUTPUTDIR/${metric}.${goldfile##*/}"
            perl reference-coreference-scorers/scorer.pl $metric $goldfile $sysfile > $outfile
            tail -2 $outfile | head -1 >> "$OUTPUTDIR/${metric}_all.conll"
        done
    fi
done

echo
if [ $MCOUNTER -eq 0 ]; then
    echo "*** None of the gold-annotated questions with mentions is answered by the system. Skipping mention-level evaluation... ***"
else
    echo "*** Number of gold-annotated questions with mentions answered by the system: $MCOUNTER"
    #ABSDATADIR="$(cd "$(dirname "$DATADIR")"; pwd)/$(basename "$DATADIR")"
    python3 evaluate_mentions.py $SYSTEMDIR $GOLDDIR $OUTPUTDIR
fi

