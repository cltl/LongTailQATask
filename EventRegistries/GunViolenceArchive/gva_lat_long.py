from lxml import etree
import requests
import pandas
from datetime import datetime
import json


def get_lat_long(incident_url, incident_uri):
    """
    obtain lat + long for gun violence incident
    
    :param str incident_url: http://www.gunviolencearchive.org/incident/923232
    :param str incident_uri: 923232
    
    :rtype: tuple
    :return: (latitude, longitude)
    """
    call = requests.get(incident_url)
    doc = etree.HTML(call.text)
    
    lat = None
    long = None
    
    for span_el in doc.xpath('//span'):
        if span_el.text is not None:
            if span_el.text.startswith('Geolocation:'):
                lat, long = span_el.text[13:].split(', ')
                lat, long = float(lat), float(long)
    
    return (lat, long)


# load frame
df = pandas.read_pickle('frames/all')

# crawl gva for lat and long information per incident
incident_uri2location = dict()
counter = 0
for index, row in df.iterrows():
    lat, long = get_lat_long(row['incident_url'], row['incident_uri'])
    if all([lat is not None,
            long is not None]):
        incident_uri2location[row['incident_uri']] = (lat, long)
    
    counter += 1
    if counter % 100 == 0:
        print(counter, datetime.now())


# save it
with open('frames/all.lat_long.json', 'w') as outfile:
    json.dump(incident_uri2location, outfile)



