framefile="../EventRegistries/GunViolenceArchive/frames/all"

bindir="test/"
datadir="test_output/"

#python3 CreateQ.py -d $framefile -e killing -s 1 -o $bindir

python3 create_task_data.py -d $bindir -o $datadir
