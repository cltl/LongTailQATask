import utils
import pickle
import pandas
from collections import Counter
import operator
import time

t1=time.time()

df_paths = [#'frames/mass_shootings_2013',
            #'frames/mass_shootings_2014',
            'frames/mass_shootings_2015']
frames = []
for df_path in df_paths:
    with open(df_path, 'rb') as infile:
        df = pickle.load(infile)
        frames.append(df)
df = pandas.concat(frames)

all_incidents={}
for index, row in df.iterrows():
	i=row['incident_uri']
	all_incidents[i] = row['incident_sources']
	all_incidents[i].add(row['source_url'])
#	if index==20:
#		break
    # all_sources contain all the html links

ERRORS_FILE="errors.txt"
errors=open(ERRORS_FILE, "a+")
utils.reset_files()
for index,sources in all_incidents.items():
    my_dir=utils.reset_dir(index)
    for source in sources:
        article=utils.whats_behind_a_uri(source)
        if article:
            utils.dump_to_file(article, my_dir)
        else:
            errors.write(source + '\n')

t2=time.time()
print("Time elapsed", t2-t1)
