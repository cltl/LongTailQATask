
# coding: utf-8

# In[1]:

import geopy
import pandas
import json
from geopy.geocoders import Nominatim
geolocator = Nominatim()
from SPARQLWrapper import SPARQLWrapper, JSON
from datetime import datetime


# In[2]:

sparql = SPARQLWrapper("http://dbpedia.org/sparql")

def get_json_results(sparql_query):
    """
    perform sparql query to dbpedia
    and return json

    :rtype: dict
    :return: json results
    """
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    return results

def get_state_sf2dbpedia_uri(df):
    """
    create mapping from states as surface forms in Gub Violence
    to Dbpedia uris

    :param pandas.core.frame.DataFrame df: gunviolence dataframes

    :rtype: dict
    :return: mapping state to dbpedia uri
    """
    state_query = '''
    SELECT DISTINCT ?state
    WHERE {
            ?state <http://purl.org/dc/terms/subject> <http://dbpedia.org/resource/Category:States_of_the_United_States> .
            ?state <http://dbpedia.org/ontology/country> <http://dbpedia.org/resource/United_States>
    }
    '''

    states_info = get_json_results(state_query)
    states_uris = {
        result['state']['value']
        for result in states_info["results"]["bindings"]
        }

    gv_sf_state2uri = {
        'Georgia': 'http://dbpedia.org/resource/Georgia_(U.S._state)',
        'Washington': 'http://dbpedia.org/resource/Washington_(state)',
    }

    gv_states = set(df['state'])

    for gv_sf_state in gv_states:
        for state_uri in states_uris:
            state_for_matching = gv_sf_state.replace(' ', '_')
            if state_uri.endswith('/' + state_for_matching):
                gv_sf_state2uri[gv_sf_state] = state_uri

    return gv_sf_state2uri


# In[3]:

df = pandas.read_pickle('frames/all')
lat_long = json.load(open('frames/all.lat_long.json'))


# In[4]:

gv_sf_state2uri = get_state_sf2dbpedia_uri(df)


# In[5]:

template = """
select * where
    {
    ?a a <http://dbpedia.org/ontology/Settlement> ;
    <http://dbpedia.org/ontology/isPartOf>* <%s> .
    ?a <http://www.w3.org/2003/01/geo/wgs84_pos#lat> ?lat ;
     <http://www.w3.org/2003/01/geo/wgs84_pos#long> ?long ;
     <http://www.w3.org/2000/01/rdf-schema#label> ?label .
     FILTER (lang(?label) = "en")
    }
"""


# In[6]:

cache = dict()


# In[8]:

incident2city_or_county = dict()
counter = 0

for index, row in df.iterrows():
    
    counter += 1
    if counter % 100 == 0:
        print(counter, datetime.now())
    
    if row['incident_uri'] in lat_long:
        
        state = row['state']
        
        if state == 'District of Columbia':
            continue 
            
        dbpedia_state = gv_sf_state2uri[state]
        
        if dbpedia_state in cache:
            dbpedia_output = cache[dbpedia_state]
        else:
            query = template % dbpedia_state
            dbpedia_output = get_json_results(query)
            cache[dbpedia_state] = dbpedia_output
        
        lat, long = lat_long[row['incident_uri']]
        location = geolocator.reverse(f"{lat}, {long}")
        bbox = location.raw['boundingbox']
        
        gold_lat = (float(bbox[0]) + float(bbox[1])) / 2
        gold_long = (float(bbox[2]) + float(bbox[3])) / 2

        diff = 100
        dbpedia = ''

        for result in dbpedia_output["results"]["bindings"]:
            lat = float(result['lat']['value'])
            long = float(result['long']['value'])

            lat_diff = abs(gold_lat - lat)
            long_diff = abs(gold_long - long)
            total_diff = lat_diff + long_diff
            if total_diff < diff:
                diff = total_diff
                dbpedia = result['a']['value']

        incident2city_or_county[row['incident_uri']] = dbpedia


# In[9]:

with open('frames/all.dbpedia_links', 'w') as outfile:
    json.dump(incident2city_or_county, outfile)


# In[11]:

incident2city_or_county


# In[ ]:



