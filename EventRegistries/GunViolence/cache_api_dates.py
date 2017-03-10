from glob import glob 
import json
import pickle

iterable = glob('the_violent_corpus/**/*.json', recursive=True)
pickle_file='date_cache.p'
pickle_data={}

for f in iterable:
    hash=f.split('/')[-1][:-5]
    with open(f, 'r') as r:
        a_json=json.load(r)
        pickle_data[hash]= a_json['dct']
pickle.dump(pickle_data, open(pickle_file, 'wb'))
