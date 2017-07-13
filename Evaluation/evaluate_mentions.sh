#!/bin/sh

SCORERDIR="reference-coreference-scorers"

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo "Please supply 3 arguments to this script: DATADIR, SYSTEMDIR, GOLDDIR. Usage: bash evaluate.sh <DATADIR> <SYSTEMDIR> <GOLDDIR>"
    exit
fi

DATADIR="$1"
SYSTEMDIR="$2"
GOLDDIR="$3"


GOLDJSONDIR="$DATADIR/answers.json"
SYSJSONDIR="$SYSTEMDIR/answers.json"

##### 1) INCIDENT- and DOCUMENT-LEVEL EVALUATION #####

if [ ! -f "$GOLDJSONDIR" ]; then
    echo "The gold JSON file with answers does not exist. Exiting now..."
    exit
fi

if [ ! -f "$SYSJSONDIR" ]; then
    echo "The gold JSON file with answers does not exist. Exiting now..."
    exit
fi

### CHECKS ###

if [ ! -d $DATADIR ]; then
    echo "WARN: $DATADIR does not exist. Creating it now..."
    mkdir $DATADIR
fi

if [ ! -d "$DATADIR/scores" ]; then
    echo "WARN: $DATADIR/scores does not exist. Creating it now..."
    mkdir "$DATADIR/scores"
else
    #for metric in muc bcub ceafm ceafe blanc; do
    rm "$DATADIR/scores"/*
    #done
fi

### CHECKS done ###

python3 evaluate_answers.py $DATADIR $SYSJSONDIR $GOLDJSONDIR

##### 2) MENTION-LEVEL EVALUATION #####

echo "Incident- and document-level evaluation is finished. Now evaluating your mentions..."

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

### CHECKS done. ###

MCOUNTER=0
for goldfile in "${GOLDDIR}"/*.conll
do
    sysfile="$SYSTEMDIR/${goldfile##*/}"
    if [ ! -f $sysfile ]; then
        echo "WARN: System answer missing for gold file $goldfile."
    else
        (( MCOUNTER++ ))
        for metric in muc bcub ceafm ceafe blanc; do
            outfile="$DATADIR/scores/${metric}.${goldfile##*/}"
            perl reference-coreference-scorers/scorer.pl $metric $goldfile $sysfile > $outfile
            tail -2 $outfile | head -1 >> "$DATADIR/scores/${metric}_all.conll"
        done
    fi
done

echo
if [ $MCOUNTER -eq 0 ]; then
    echo "*** None of the gold-annotated questions with mentions is answered by the system. Skipping mention-level evaluation... ***"
else
    echo "*** Number of gold-annotated questions with mentions answered by the system: $MCOUNTER"
    #ABSDATADIR="$(cd "$(dirname "$DATADIR")"; pwd)/$(basename "$DATADIR")"
    python3 evaluate_mentions.py $DATADIR $SYSTEMDIR $GOLDDIR
fi


