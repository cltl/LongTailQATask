import utils
import pickle
import pandas
from collections import Counter
import operator

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
    all_incidents[index] = row['incident_sources']
    all_incidents[index].add(row['source_url'])
    # all_sources contain all the html links
    if index==9:
        break
    

ERRORS_FILE="errors.txt"
errors=open(ERRORS_FILE, "a+")
utils.reset_files()
for index in all_incidents:
    my_dir=utils.reset_dir(index)
    for source in all_incidents[index]:
        article=utils.whats_behind_a_uri(source)
        if article:
            utils.dump_to_file(article, my_dir)
        else:
            errors.write(source + '\n')
