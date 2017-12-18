
# coding: utf-8

# * disagreement info:
#     * disqualify FR103355 is https://en.wikipedia.org/wiki/Compton,_California
#     * disqualify FR104709
#     * FR105075 : Marten did not enter date because there was no location
#     * FR14030: Filip did not enter date, but there is **this evening** in the text -> include
#     * FR110835: Marten made a mistake, Filip is correct
#     * FR107266: Filip is correct, Marten made a mistake
#     * FR13862: Marten used **Los Angeles** in title -> include it
#     * FR10705: Marten mistake time
#     * FR111907: disqualify

# In[1]:

disagreement_info = {
    'FR103355': 'discard',
    'FR104709': 'discard',
    'FR105075': 'discard',
    'FR110835': 'filip',
    'FR107266': 'filip',
    'FR13862' : 'marten',
    'FR10705' : 'filip',
    'FR111907': 'discard',
    'FR14030': 'marten'
}


# In[2]:

class NewsItem:

    def __init__(self, title='',
                 content='',
                 dct='',
                 id=None,
                 uri=''):
        self.title = title
        self.content = content
        self.dct = dct
        self.id = id
        self.uri = uri

    def toJSON(self, targetFile):
        pickle.dump(self, open(targetFile, 'wb'))


# In[3]:

import json
import pickle
import pandas
from datetime import datetime
from datetime import date
import hashlib
import os
from collections import Counter
from SPARQLWrapper import SPARQLWrapper, JSON


# In[4]:

path_fr = 'firerescue_v2.pickle'
fr_df = pandas.read_pickle(path_fr)


# In[5]:

def document_quality(body, title):
    """
    check document quality with respect to

    :param list body: list of strings (representing sentences)
    a. first sentence should be longer than two tokens
    b. number of characters in body should be between 300 and 4000
    :param str title: title of article

    :rtype: body, title, reason (if it fails)
    """
    include = False
    reason = None

    # number of characters check
    if not row['incident']:
        return None, None, 'num_characters'

    # first sentence check
    first_sentence = row['incident'][0]
    if first_sentence:
        tokens = first_sentence.split()

        if tokens:
            if all([len(tokens) <= 5,
                    tokens[0] == 'At']):
                return None, None, 'first sentence too short'

    # again number of characters check
    cleaned_body = []
    num_tokens = 0
    for sentence in row['incident']:
        if sentence:
            for token in sentence.split():
                num_tokens += 1

            cleaned_body.append(sentence)

    if num_tokens not in range(100, 4000):
        return None, None, 'not in character range: %s' % num_tokens


    the_cleaned_body = '\n'.join(cleaned_body)

    return the_cleaned_body, title, 'succes'


# In[6]:

def get_disqualified(dis_info, subset=set()):
    """
    given a dict:
    {"FR102920":["FR102920_1"],"FR102640":["FR102640_1"]}

    return identifiers that have a disqualified document in them

    :param dict dis_info: see above

    :rtype: set
    :return: set of identifiers
    """
    disqualified = set()

    for id_, doc_info in dis_info.items():

        if subset:
            if id_ not in subset:
                continue

        if doc_info:
            disqualified.add(id_)

    return disqualified


# In[7]:

sparql = SPARQLWrapper("http://dbpedia.org/sparql")

def get_state_sf2dbpedia_uri(df):
    """
    create mapping from states as surface forms in Gun Violence
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


# ## load tool data

# In[8]:

anno_filip = json.load(open('annotations/ann_filip_str.json'))
anno_marten = json.load(open('annotations/ann_marten_str.json'))
dis_filip = json.load(open('annotations/dis_filip_str.json'))
dis_marten = json.load(open('annotations/dis_marten_str.json'))


# In[9]:

ids_dis_filip = get_disqualified(dis_filip)
ids_anno_filip = set(anno_filip.keys())
ids_anno_dis_filip = ids_dis_filip | ids_anno_filip


# ## compare disqualified

# In[10]:

ids_dis_marten = get_disqualified(dis_marten, ids_anno_dis_filip)
ids_dis_filip = get_disqualified(dis_filip, ids_anno_dis_filip)


# In[11]:

ids_dis_filip


# In[12]:

ids_dis_marten


# In[13]:

ids_dis_marten == ids_dis_filip


# In[14]:

len(ids_dis_marten)


# ## compare annotations

# In[15]:

id_2info = dict()
dbpedia_states = get_state_sf2dbpedia_uri(fr_df).values()


sparql_query = """
SELECT DISTINCT ?relation ?property
    WHERE {
            <%s> ?relation ?property .
    }
    """

for id_, m_anno_info in anno_marten.items():

    m_anno_info = anno_marten[id_]

    # move on if disqualified
    if id_ in ids_dis_marten:
        continue

    location_match = True
    time_match = True

    if id_ in anno_filip:
        f_anno_info = anno_filip[id_]

        for key in ['time', 'location']:

            if f_anno_info[key] != m_anno_info[key]:

                # print()
                # print(f'incident id: {id_}')
                # print(f'{key} mismatch')
                # print('filip', f_anno_info[key])
                # print('filip', f_anno_info)
                # print('marten', m_anno_info[key])
                # print('marten', m_anno_info)

                # use disagreement info
                if disagreement_info[id_] == 'discard':
                    print('discarded', id_)
                    if key == 'time':
                        time_match = False
                    elif key == 'location':
                        location_match = False

    time = m_anno_info['time']
    location = m_anno_info['location']

    if id_ in disagreement_info:
        if disagreement_info[id_] == 'filip':
            time = f_anno_info['time']
            location = f_anno_info['location']
            print(id_, 'used annotations filip')

    if all([location,
            location_match,
            time,
            time_match]):

        dbpedia_link_city = location.replace('https://en.wikipedia.org/wiki/',
                                             'http://dbpedia.org/resource/')


        city = False
        state = False
        results = get_json_results(sparql_query % dbpedia_link_city)
        for result in results["results"]["bindings"]:

            if all([result['relation']['value'] == 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type',
                    result['property']['value'] == 'http://dbpedia.org/ontology/City']):
                city = True

            if result['relation']['value'] == 'http://dbpedia.org/ontology/isPartOf':
                for possible_state in dbpedia_states:
                    if result['property']['value'] == possible_state:
                        state = result['property']['value']

            if result['property']['value'] in {'http://dbpedia.org/resource/Salem,_Oregon'}:
                city = True

        locations = ''

        if city:
            locations = {'city': dbpedia_link_city}

            if state:
                locations['state'] = state
            else:
                print('state not found for:', dbpedia_link_city, state)

        else:
            print('not a city', dbpedia_link_city)

        y, m, d = time.split('-')
        the_date = date(int(y), int(m), int(d))
        date_string = the_date.strftime('%B %-d, %Y')

        id_2info[id_] = {'locations': locations,
                         'time' : date_string}


# In[16]:

fr_df['date'] = [None for index, row in fr_df.iterrows()]
fr_df['locations'] = [None for index, row in fr_df.iterrows()]

for index, row in fr_df.iterrows():

    id_ = row['incident_uri']

    body, title, reason = document_quality(row['incident'], row['title'])
    if reason != 'succes':
        continue


    reporting_date = row['incident_reporting_date']
    reporting = date(reporting_date.year,
                     reporting_date.month,
                     reporting_date.day)

    news_item_obj = NewsItem(title=row['title'],
                             content=body,
                             dct=reporting)

    incident_sources = {row['source_url'] : reporting }


    hash_obj = hashlib.md5(row['source_url'].encode())
    the_hash = hash_obj.hexdigest()
    incident_uri = id_
    out_dir = 'firerescue_corpus/%s' % (incident_uri)
    out_path = 'firerescue_corpus/%s/%s.json' % (incident_uri, the_hash)

    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)

    news_item_obj.toJSON(out_path)

    if id_ in id_2info:

        fr_df.set_value(index, 'date', id_2info[id_]['time'])
        fr_df.set_value(index, 'locations', id_2info[id_]['locations'])
        fr_df.set_value(index, 'incident_sources', incident_sources)


# In[17]:

counter = 0
for index, row in fr_df.iterrows():
    if all([row['locations'],
            row['date'],
            row['incident_sources']]):
        counter += 1

print('total incident count:', counter)


# In[18]:

fr_df.to_pickle('firerescue_v3.pickle')


# In[ ]:



