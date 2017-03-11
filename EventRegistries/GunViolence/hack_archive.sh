FILE="archive_test_urls.tsv"

for line in $(cat $FILE); do
	echo $line
	bash hack.bashrc $line $line
done
