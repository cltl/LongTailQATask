FILE=$1

for line in $(cat $FILE); do
	echo $line
	bash hack.bashrc $line $line
done
