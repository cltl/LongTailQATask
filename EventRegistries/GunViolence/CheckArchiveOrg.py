
# coding: utf-8

# In[1]:

import pickle
import pandas
from multiprocessing.dummy import Pool as ThreadPool
from collections import Counter, defaultdict
import operator
import utils
from geopy.geocoders import Nominatim
from newspaper import Article
import requests
from urllib.parse import urlencode, quote_plus
import time

cooldown_time=0.05

# In[2]:

import classes

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
    try:
        r=requests.get(encoded_uri)
        j=r.json()
        closest=j['archived_snapshots']['closest']
        if all([closest['available'], closest['status']=='200']):
            return closest['url']
    except:
        print("No archive version for %s" % article_uri)
        return ''

def website_extraction(original_url, max_sec=5, debug=False):
    """
    attempt to obtain:
    1. title
    2. document
    3. document creation time
    
    :param str url: url of news article
    :param int max_sec: maximum number of seconds to wait for a response after downloading
    :param bool debug: if debug, print info to stdout
    
    :rtype: dict
    :return: dict containing keys 
    1. 'title', 
    2. 'document'
    3. [most reliable] 'publish_date'
    4. [slightly less reliable] 'published_time'
    5. [slightly slightly less reliable] 'date'
    """
    if not original_url:
        return classes.NewsItem(
	    title='',
	    content='',
	    dct=None
        )
    global no_archive_version
    global no_date_articles
    global extraction_error
    global all_good

    url=generate_archive_uri(original_url)
    if not url:
        no_archive_version+=1
        return classes.NewsItem(
                title='',
                content='',
                dct=None
            )
    language='en'
    a=Article(url, language)
    a.download()
    attempts = 0

    while not a.is_downloaded:
        time.sleep(1)
        attempts += 1
        
        if attempts == max_sec:
            extraction_error+=1
            print("Extraction error with the article %s" % url)
            return classes.NewsItem(
                title='',
                content='',
                dct=None
            )

    a.parse()
    title=a.title
    content=a.text
    dct=a.publish_date or a.meta_data['date'] or a.meta_data['published_time']
    if not dct:
        print("No date found for article %s" % url)
        no_date_articles+=1
    else:
        all_good+=1
    news_item=classes.NewsItem(
        title=title,
        content=content,
        dct=dct
    )
    return news_item

def article_iterable(sources, num_sources=None):
    """
    article generator
    
    :param pandas.core.frame.DataFrame df: gunviolence dataframe
    :param int maximum: restrict to num_source, if None all will be returned
    
    :rtype: generator
    :return: generator of news articles
    """
    counter = 0
    for source in sources:
                
        if num_sources is None:
            yield source
        else:
            if counter < num_sources:
                yield source
            else:
                break
        counter += 1


t1=time.time()

frames = [
          #'mass_shootings',
          #'mass_shootings_2013',
          #'mass_shootings_2014',
          'mass_shootings_2015']
df = pandas.concat([pandas.read_pickle('frames/' + frame)
                    for frame in frames])

no_archive_version=0
no_date_articles=0
extraction_error=0
all_good=0

sources=get_sources(df)
"""
iterable = article_iterable(sources, num_sources=100)
pool = ThreadPool(1) 
results = pool.map(website_extraction, iterable)
"""

for index, source in enumerate(sources):
    print("article no.", index)
    if source!='':
        results=website_extraction(source)
        time.sleep(cooldown_time)

t2=time.time()
print("Time elapsed", t2-t1)
print(all_good, no_archive_version, no_date_articles, extraction_error)
