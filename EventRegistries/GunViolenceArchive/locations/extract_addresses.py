import pickle
import pandas

filename="raw_addresses.p"
addresses=set()

urls_and_paths = [('../frames/children_killed', 'http://www.gunviolencearchive.org/children-killed'),
                  ('../frames/children_injured', 'http://www.gunviolencearchive.org/children-injured'),
                  ('../frames/teens_killed', 'http://www.gunviolencearchive.org/teens-killed'),
                  ('../frames/teens_injured', 'http://www.gunviolencearchive.org/teens-injured'),
                  ('../frames/accidental_deaths', 'http://www.gunviolencearchive.org/accidental-deaths'),
                  ('../frames/accidental_injuries', 'http://www.gunviolencearchive.org/accidental-injuries'),
                  ('../frames/accidental_deaths_children', 'http://www.gunviolencearchive.org/accidental-child-deaths'),
                  ('../frames/accidental_injuries_children', 'http://www.gunviolencearchive.org/accidental-child-injuries'),
                  ('../frames/accidental_deaths_teens', 'http://www.gunviolencearchive.org/accidental-teen-deaths'),
                  ('../frames/accidental_injuries_teens', 'http://www.gunviolencearchive.org/accidental-teen-injuries'),
                  ('../frames/officer_involved_shootings', 'http://www.gunviolencearchive.org/officer-involved-shootings'),
                  ('../frames/mass_shootings_2013', 'http://www.gunviolencearchive.org/reports/mass-shootings/2013'),
                  ('../frames/mass_shootings_2014', 'http://www.gunviolencearchive.org/reports/mass-shootings/2014'),
                  ('../frames/mass_shootings_2015', 'http://www.gunviolencearchive.org/reports/mass-shootings/2015'),
                  ('../frames/mass_shootings', 'http://www.gunviolencearchive.org/mass-shooting')]

frames = []
for df_path, url in urls_and_paths:
    with open(df_path, 'rb') as infile:
        df = pickle.load(infile)
        frames.append(df)
df = pandas.concat(frames)

for index, row in df.iterrows():
    location=row['address'] + ', ' + row['city_or_county'] + ', ' + row['state']
    addresses.add(location)


pickle.dump(addresses, open(filename, 'wb'))
