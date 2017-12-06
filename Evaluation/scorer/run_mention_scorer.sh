#!/bin/sh

SYSTEMDIR="$1"
GOLDDIR="$2"
OUTPUTDIR="$3"

SCORERDIR="reference-coreference-scorers"

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
    rm "$OUTPUTDIR"/*
fi

### CHECKS done ###

MCOUNTER=0
pwd
cwd=$(pwd)
for goldfile in "${GOLDDIR}"/*.conll
do
    sysfile="$SYSTEMDIR/${goldfile##*/}"
    if [ ! -f $sysfile ]; then
        echo "WARN: System answer missing for gold file $goldfile."
    else
        (( MCOUNTER++ ))
        for metric in muc bcub ceafm ceafe blanc; do
            outfile="$OUTPUTDIR/${metric}.${goldfile##*/}"
            perl "${cwd}"/program/scorer.pl $metric $goldfile $sysfile > $outfile
            tail -2 $outfile | head -1 >> "$OUTPUTDIR/${metric}_all.conll"
        done
    fi
done

echo
if [ $MCOUNTER -eq 0 ]; then
    echo "*** None of the gold-annotated questions with mentions is answered by the system. Skipping mention-level evaluation... ***"
else
    echo "*** Number of gold-annotated questions with mentions answered by the system: $MCOUNTER"
fi
