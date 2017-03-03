
# coding: utf-8

# In[1]:

import pickle
import pandas
from collections import Counter, defaultdict
import operator
import utils
from geopy.geocoders import Nominatim
from newspaper import Article
import requests
from urllib.parse import urlencode, quote_plus
import time


# In[2]:

import classes


# In[3]:

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
CORPUS_NAME = 'the_violent_corpus'


# In[4]:

frames = []
for df_path, url in urls_and_paths:
    with open(df_path, 'rb') as infile:
        df = pickle.load(infile)
        frames.append(df)
df = pandas.concat(frames)
len(df)


# In[5]:

def get_sources(dataframe):
    """

    :param dataframe:
    :return:
    """
    sources = set()
    for index, row in dataframe.iterrows():
        sources.add(row['source_url'])
        sources.update(row['incident_sources'])
    return sources


# In[6]:

def generate_archive_uri(article_uri):
    archive_api='http://archive.org/wayback/available?'
    params={'url': article_uri}
    encoded_uri=archive_api + urlencode(params)
    print(encoded_uri)
    r=requests.get(encoded_uri)
    j=r.json()
    try:
        closest=j['archived_snapshots']['closest']
        if all([closest['available'], closest['status']=='200']):
            return closest['url']
    except:
        return ''

archive_uri=generate_archive_uri('http://www.wdam.com/story/27682998/1-dead-4-injured-in-nightclub-shooting')


# In[7]:

def download_and_parse_uri(url):
    language='en'
    a=Article(url, language)
    a.download()
    a.parse()
    title=a.title
    content=a.text
    dct=a.publish_date or a.meta_data['date']

    news_item=classes.NewsItem(
        title=title,
        content=content,
        dct=dct
    )
    return news_item

item=download_and_parse_uri(archive_uri)


# In[ ]:

cooldown_time=0.1

sources=get_sources(df)
has_archive_version=0
no_archive_version=0
no_date_articles=0
extraction_error=0
for index, source in enumerate(sources):
    print("article no.", index)
    if source!='':
        archive_uri=generate_archive_uri(source)
        if archive_uri:
            has_archive_version+=1
            try: 
                item=download_and_parse_uri(archive_uri)
            except:
                extraction_error+=1
                continue
            if not item.dct:
                print("No date information found!")
                no_date_articles+=1
        else:
            no_archive_version+=1
            #print("No archive.org versions found!")

        time.sleep(cooldown_time)

print(has_archive_version, no_archive_version, no_date_articles, extraction_error)
