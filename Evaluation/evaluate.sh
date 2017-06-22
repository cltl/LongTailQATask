
SCORERDIR="reference-coreference-scorers"
DATADIR="../Data"

if [ ! -d "$SCORERDIR" ]; then
    echo "*** The coreference scorer directory was not detected. Now cloning ... ***"
    echo 
    git clone https://github.com/conll/reference-coreference-scorers/
    echo "*** The coreference scorer was cloned successfuly! ***"
    echo
else
    echo "*** The reference scorer directory already exists. Now evaluating ... ***"
    echo
fi

### MENTION - LEVEL EVALUATION ###

for goldfile in "$DATADIR"/gold/*
do
    sysfile="$DATADIR/system/${goldfile##*/}"
    if [ -f $sysfile ]; then
        for metric in muc bcub ceafm ceafe blanc; do
            outfile="$DATADIR/scores/${metric}.${goldfile##*/}"
            perl reference-coreference-scorers/scorer.pl $metric $goldfile $sysfile > $outfile
        done
    else
        echo "ERROR: System output missing for $goldfile"
    fi
done

echo "*** Mention-level evaluation done! ***"
