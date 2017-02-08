import utils
import pickle
import pandas
from collections import Counter
import operator
import time

t1=time.time()

urls_and_paths = [('frames/children_killed', 'http://www.gunviolencearchive.org/children-killed'),
                  ('frames/children_injured', 'http://www.gunviolencearchive.org/children-injured'),
                  ('frames/teens_killed', 'http://www.gunviolencearchive.org/teens-killed'),
                  ('frames/teens_injured', 'http://www.gunviolencearchive.org/teens-injured'),
                  ('frames/accidental_deaths', 'http://www.gunviolencearchive.org/accidental-deaths'),
                  ('frames/accidental_injuries', 'http://www.gunviolencearchive.org/accidental-injuries'),
                  ('frames/accidental_deaths_children', 'http://www.gunviolencearchive.org/accidental-child-deaths'),
                  ('frames/accidental_injuries_children', 'http://www.gunviolencearchive.org/accidental-child-injuries'),
                  ('frames/accidental_deaths_teens', 'http://www.gunviolencearchive.org/accidental-teen-deaths'),
                  ('frames/accidental_injuries_teens', 'http://www.gunviolencearchive.org/accidental-teen-injuries'),
                  ('frames/officer_involved_shootings', 'http://www.gunviolencearchive.org/officer-involved-shootings'),
                  ('frames/mass_shootings_2013', 'http://www.gunviolencearchive.org/reports/mass-shootings/2013'),
                  ('frames/mass_shootings_2014', 'http://www.gunviolencearchive.org/reports/mass-shootings/2014'),
                  ('frames/mass_shootings_2015', 'http://www.gunviolencearchive.org/reports/mass-shootings/2015'),
                  ('frames/mass_shootings', 'http://www.gunviolencearchive.org/mass-shooting')]

frames = []
for df_path, url in urls_and_paths:
    with open(df_path, 'rb') as infile:
        df = pickle.load(infile)
        frames.append(df)
df = pandas.concat(frames)

all_incidents={}
uris = set()
for index, row in df.iterrows():
	if row['incident_uri'] not in uris:
		i=row['incident_uri']
		all_incidents[i] = row['incident_sources']
		all_incidents[i].add(row['source_url'])
		uris.add(i)
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
