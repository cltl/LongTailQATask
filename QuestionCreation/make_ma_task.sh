bindir="bin"
datadir="../Data"
framefile="../EventRegistries/GunViolenceArchive/frames/all"

if [ ! -f $framefile ]; then
    echo "The frame file does not exist. Exiting now..."
    exit
fi

if [ ! -d $bindir ]; then
    mkdir $bindir
else
    rm "$bindir"/*
fi

python3 CreateQ.py -d $framefile -e killing -s 1 -o $bindir

if [ ! -d $datadir ]; then
    mkdir $datadir
fi

python3 create_task_data.py -d $bindir -o $datadir
