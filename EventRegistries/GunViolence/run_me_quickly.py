import utils
import pickle
import pandas
from collections import Counter
import operator
import time
from newspaper import Article
from datetime import datetime
from dateutil import parser

import classes

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

def get_archive_uri(original_url):
    if not original_url:
        return None
    if not utils.is_archive_uri(original_url):
        url=utils.generate_archive_uri(original_url)
        return url
    else:
        return original_url
    

def website_extraction(original_url, max_sec=10, debug=False):
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
    global no_archive_version
    global no_date_articles
    global extraction_error
    global all_good 

    url=get_archive_uri(original_url)

    if not url:
        utils.log_no_archive(original_url)
        no_archive_version+=1
        return classes.NewsItem(
            title='',
            content='',
            dct=None,
            id=None,
            uri=''
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
                dct=None,
                id=None,
                uri=''
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
        dct=dct,
        id=utils.hash_uri(url),
        uri=url
    )
    return news_item

DATES_CACHE='date_cache.p'
GVDB_DATES_CACHE='gvdb_date_cache.p'

dates_api=pickle.load(open(DATES_CACHE, 'rb'))
dates_gvdb=pickle.load(open(GVDB_DATES_CACHE, 'rb'))

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

#urls_and_paths = [('frames/mass_shootings_2015', 'http://www.gunviolencearchive.org/reports/mass-shootings/2015')]

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
	    # all_sources contain all the html links

no_archive_version=0
no_date_articles=0
extraction_error=0
all_good=0

ERRORS_FILE="logs/errors.txt"
errors=open(ERRORS_FILE, "a+")
utils.reset_files()
for index,sources in all_incidents.items():
    my_dir=utils.reset_dir(index)
    for source in sources:
        article=website_extraction(source)
        if article and article.id:
            target_file="%s%s.json" % (my_dir, article.id)
            article.toJSON(target_file)
            print("Article %s written!" % article.uri)
        else:
            errors.write(source + '\n')

t2=time.time()
print("Time elapsed", t2-t1)
