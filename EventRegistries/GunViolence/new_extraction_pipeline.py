
# coding: utf-8

# In[1]:

from dateutil import parser
import pickle
import pandas
from multiprocessing.dummy import Pool as ThreadPool
from collections import Counter, defaultdict
import operator
from geopy.geocoders import Nominatim
from newspaper import Article
import requests
from urllib.parse import urlencode, quote_plus
import time
import sys
from datetime import datetime

import classes
import utils


cooldown_time=0.05
DATES_CACHE='date_cache.p'
GVDB_DATES_CACHE='gvdb_date_cache.p'

dates_api=pickle.load(open(DATES_CACHE, 'rb'))
dates_gvdb=pickle.load(open(GVDB_DATES_CACHE, 'rb'))

# In[2]:

def get_cached_dct_api(url):
    hashed_url=utils.hash_uri(url)
    if hashed_url in dates_api and dates_api[hashed_url]!='NODATE':
        return datetime.strptime(dates_api[hashed_url], '%a, %d %b %Y %H:%M:%S GMT').date()
    else:
        return None

def get_cached_dct_gvdb(url):
    if url in dates_gvdb and dates_gvdb[url]:
        return dates_gvdb[url]
    else:
        return None

#test_url='http://www.wdam.com/story/27682998/1-dead-4-injured-in-nightclub-shooting'
#print(get_cached_dct(test_url))
#sys.exit()
    
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
    original_url=original_url.strip()
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

    if not utils.is_archive_uri(original_url):
        url=generate_archive_uri(original_url)
        if not url:
            utils.log_no_archive(original_url)
            no_archive_version+=1
            return classes.NewsItem(
                    title='',
                    content='',
                    dct=None
                )
    else:
        url=original_url
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
    dct_newspaper=None
    dct_newspaper=a.publish_date or a.meta_data['date'] or a.meta_data['published_time']
    if a.publish_date:
        print(a.publish_date)
        print('case A')
        dct_newspaper=a.publish_date.date()
    elif a.meta_data['date']:
        print(a.meta_data['date'] + 'case B')
        dct_newspaper=parser.parse(a.meta_data['date']).date()
    elif a.meta_data['published_time']:
        print(a.meta_data['published_time'] + 'case C')
        dct_newspaper=a.meta_data['published_time'].date()
    dct_cached_api=get_cached_dct_api(original_url)
    dct_cached_gvdb=get_cached_dct_gvdb(original_url)
    dct=dct_cached_api or dct_cached_gvdb or dct_newspaper
    if not dct:
        utils.log_no_date(url)
        print("No date found for article %s" % url)
        no_date_articles+=1
    else:
        for date_option in [dct_cached_api,dct_cached_gvdb,dct_newspaper]:
            if date_option and date_option!=dct:
                utils.log_different_date(url, str(dct_cached_api) or "NODATE", str(dct_cached_gvdb) or "NODATE", str(dct_newspaper) or "NODATE")
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
          'mass_shootings',
          'mass_shootings_2013',
          'mass_shootings_2014',
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

