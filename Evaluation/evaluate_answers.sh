#!/bin/sh

##### 1) INCIDENT- and DOCUMENT-LEVEL EVALUATION #####

### CHECKS ###

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo "Please supply 3 arguments to this script: SYSTEM JSON FILE, GOLD JSON FILE, OUTPUT JSON." 
    echo "Usage: "
    echo "bash evaluate_answers.sh <SYSTEMJSON> <GOLDJSON> <OUTPUTJSON>"
    exit
fi

SYSJSON="$1"
GOLDJSON="$2"
OUTPUTJSON="$3"

echo "$GOLDJSON"

if [ ! -f "$GOLDJSON" ]; then
    echo "The gold JSON file with answers does not exist. Exiting now..."
    exit
fi

if [ ! -f "$SYSJSON" ]; then
    echo "The gold JSON file with answers does not exist. Exiting now..."
    exit
fi

if [ -f "$OUTPUTJSON" ]; then
    rm "$OUTPUTJSON"
    #done
fi

### CHECKS done ###

python3 evaluate_answers.py $SYSJSON $GOLDJSON $OUTPUTJSON

