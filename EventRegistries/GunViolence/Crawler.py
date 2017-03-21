
# coding: utf-8

# In[1]:

import requests
from lxml import etree
import pickle
import pandas
from datetime import datetime
import csv
import json
from newspaper import Article
from dateutil import parser
from collections import Counter
import time

import utils
import classes


# In[2]:

# File mappings
DIRECTORY='GVDB/gvdb-aggregated-db'
article_info="%s/Articles-with-extracted-info.tsv" % DIRECTORY

def get_gvdb_sources():
    with open(article_info, 'r') as csvfile:
        spamreader = csv.reader(csvfile, delimiter='\t', quotechar='"')
        gvdb_sources={}
        for index,row in enumerate(spamreader):
            if row[0]=='Article url':
                continue
            url=row[0]
            ann=json.loads(row[3])
            gvdb_sources[url]=ann
        return gvdb_sources


# In[3]:

gvdb_sources=get_gvdb_sources()


# In[4]:

def get_gvdb_annotation(gva_src):
    if gva_src in gvdb_sources:
        return gvdb_sources[gva_src]
    else:
        return None


# In[5]:

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


# In[6]:

def get_archive_uri(original_url):
    if not original_url:
        return None
    if not utils.is_archive_uri(original_url):
        url=utils.generate_archive_uri(original_url)
        if not url:
            utils.log_no_archive(original_url)
        return url
    else:
        return original_url


# In[7]:

def validate_date(d):
    return d and d.year>=2013 and d.year<=2017


# In[8]:

def website_extraction(original_url, url, max_sec=10, debug=False):
    if not url:
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
    dct_cached_api=None
    dct_cached_gvdb=None
    dct_newspaper=a.publish_date or a.meta_data['date'] or a.meta_data['published_time']
    if a.publish_date:
        if validate_date(a.publish_date.date()):
            dct_newspaper=a.publish_date.date()
    elif a.meta_data['date']:
        if validate_date(parser.parse(a.meta_data['date']).date()):
            dct_newspaper=parser.parse(a.meta_data['date']).date()
    elif a.meta_data['published_time']:
        if validate_date(a.meta_data['published_time'].date()):
            dct_newspaper=a.meta_data['published_time'].date()
    if validate_date(get_cached_dct_api(original_url)):
        dct_cached_api=get_cached_dct_api(original_url)
    if validate_date(get_cached_dct_gvdb(original_url)):
        dct_cached_gvdb=get_cached_dct_gvdb(original_url)

    dct=dct_cached_api or dct_cached_gvdb or dct_newspaper
    if not dct:
        utils.log_no_date(url)
        return classes.NewsItem(
            title='',
            content='',
            dct=None,
            id=None,
            uri=''
        )
    else:
        diff_date=False
        for date_option in [dct_cached_api,dct_cached_gvdb,dct_newspaper]:
            if date_option and date_option!=dct:
                diff_date=True
                break
        if diff_date:
            return classes.NewsItem(
                title='',
                content='',
                dct=None,
                id=None,
                uri=''
            )
        else:
            return classes.NewsItem(
                title=title,
                content=content,
                dct=dct,
                id=utils.hash_uri(url),
                uri=url
            )


# In[9]:

def get_gunviolence_page(url):
    """
    create pandas.dataframe from one page of gunviolence e.g.
    http://www.gunviolencearchive.org/reports/mass-shootings/2014
    
    :param str url: gunviolence output page
    http://www.gunviolencearchive.org/reports/mass-shootings/2014
    
    :rtype: pandas.core.frame.DataFrame
    :return: info from the violence page in a dataframe
    
    """
    call = requests.get(url)
    doc = etree.HTML(call.text)
    
    headers = ['incident_uri',
               'date', 'state', 'city_or_county',
               'address', 'num_killed', 'num_injured',
               'incident_url', 'incident_sources',
               'participants', 'gvdb_annotation']
    list_of_reports = []

    for tr_el in doc.xpath('//tr[@class="even" or @class="odd"]'):
        td_els = tr_el.getchildren()

        date = td_els[0].text
        state = td_els[1].text
        city_or_county = td_els[2].text
        address = td_els[3].text
        num_killed = int(td_els[4].text)
        num_injured = int(td_els[5].text)

        operations_el = td_els[6]
        a_els = operations_el.findall('ul/li/a')

        # get incident url
        incident_base = 'http://www.gunviolencearchive.org'
        incident_ending = a_els[0].get('href')
        incident_url = incident_base + incident_ending
        incident_uri = incident_url.split('/')[-1]

        # get source url
        source_url = ''
        if len(a_els) == 2:
            source_url = a_els[1].get('href')

        # get incident sources
        incident_call = requests.get(incident_url)
        incident_doc = etree.HTML(incident_call.text)

        incident_sources = set()
        for li_el in incident_doc.xpath('//li'):
            if li_el.text is not None:
                if 'URL:' in li_el.text:
                    for a_el in li_el.xpath('a'):
                        incident_sources.add(a_el.get('href'))
                        
        # get participants information
        div_els = incident_doc.xpath('//div[h2[text()="Participants"]]')
        div_el = div_els[0]
        participants = []

        for ul_el in div_el.iterfind('div/ul'):
            participant = dict()
            for li_el in ul_el.iterfind('li'):
                attr, value = li_el.text.split(':')
                participant[attr] = value
            participants.append(participant)
            
            
        # Cleanup the directory
        my_dir=utils.reset_dir(incident_uri)
            
        # gather news sources
        sources=set()
        sources.add(source_url)
        sources.update(incident_sources)
        
        # extract sources data
        ready_sources={}
        annotations={}
        for src in sources:
            archive_src=get_archive_uri(src)
            if archive_src:
                article=website_extraction(src, archive_src)
                if article and article.id and article.dct:
                    target_file="%s%s.json" % (my_dir, article.id)
                    article.toJSON(target_file)
                    print("Article %s written!" % article.uri)
                    ready_sources[archive_src]=article.dct
                    gvdb_ann=get_gvdb_annotation(src)
                    if gvdb_ann:
                        annotations[archive_src]=gvdb_ann
                else:
                    errors.write(src + '\n')
        
        if len(ready_sources):
            incident_report = [incident_uri,
                               date, state, city_or_county,
                               address, num_killed, num_injured,
                               incident_url, ready_sources, 
                               participants, annotations]
            list_of_reports.append(incident_report)
    
    df = pandas.DataFrame(list_of_reports, columns=headers)
    return df


# In[10]:

def paginate(base_url, debug=False):
    """
    paginate over gunviolence urls
    
    :param str base_url: paginate over gunviolence urls
    
    :rtype: pandas.core.frame.DataFrame
    :return: all results from one category
    
    """
    frames = []
    previous_df = get_gunviolence_page(base_url)
    frames.append(previous_df)

    keep_going = True
    counter = 1
    while keep_going:
        url = base_url + '?page=' + str(counter)
        print(url)
        
        df = get_gunviolence_page(url)
        counter += 1

        if df.equals(previous_df):
            keep_going = False
        else:
            frames.append(df)
            previous_df = df

    df = pandas.concat(frames)
    return df


# In[11]:

DATES_CACHE='date_cache.p'
GVDB_DATES_CACHE='gvdb_date_cache.p'
ERRORS_FILE="logs/errors.txt"
errors=open(ERRORS_FILE, "a+")

dates_api=pickle.load(open(DATES_CACHE, 'rb'))
dates_gvdb=pickle.load(open(GVDB_DATES_CACHE, 'rb'))

utils.reset_files()


# In[12]:

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
                  ('frames/mass_shootings', 'http://www.gunviolencearchive.org/mass-shooting')
                  ]

#urls_and_paths = [('frames/mass_shootings_2015', 'http://www.gunviolencearchive.org/reports/mass-shootings/2015')]
for output_path, base_url in urls_and_paths:
    print()
    print('starting', output_path, datetime.now())
    df = paginate(base_url)
    with open(output_path, 'wb') as outfile:
        pickle.dump(df, outfile)
    print('done', output_path, datetime.now())


# In[13]:

#for index, row in df.iterrows():
#    print(row)
#    input('continue?')


# In[ ]:



