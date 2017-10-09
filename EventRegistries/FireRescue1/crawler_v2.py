
# coding: utf-8

# In[1]:

import requests
from lxml import etree
from datetime import datetime
import pandas


# In[2]:

def extract_paragraphs_city_state(url):
    """
    extract text from firerescue article
    
    :param str url: firerescue incident report
    
    :rtype: tuple
    :return: (paragraphs, city, state)
    """
    try:
        call = requests.get(url)
    except:
        print('max entry')
        return None, None, None
    
    incident_doc = etree.HTML(call.text)
    text_el = incident_doc.xpath('//span[@class="text"]')[0]
    paragraphs = [p_el.text for p_el in text_el.iterfind('p')]
    
    loc_els = incident_doc.xpath('//p/b')
    city, state = loc_els[0].tail[4: -1].rsplit(', ', 1)
    if state == 'N/A':
        state = ''
    
    return paragraphs, city, state


# In[3]:

url = 'https://web.archive.org/web/20160914192409/http://www.firerescue1.com/incident-reports/'
base_url = 'https://web.archive.org'


# In[4]:

call = requests.get(url)


# In[5]:

doc = etree.HTML(call.text)


# In[10]:

list_of_lists = []
headers = ['incident_uri', 'date', 'title',
           'state', 'city_or_county', 'address',
           'incident_url', 'source_url',
           'incident_sources', 'participants',
           'incident', 'fire_department', 'incident_reporting_date']

counter = 0
for a_el in doc.xpath('//a[starts-with(@href, "/web") and contains(@href, "incident-reports")]'): 
    href = a_el.get('href')
    
    if href.endswith('submit/'):
        continue
        
    title = a_el.find('br').tail
    
    counter += 1
    if counter % 50 == 0:
        print(counter, datetime.now())
        
    fire_department = a_el.find('b').text
    incident_url = base_url + a_el.get('href')
    incident_sources = set()
    incident_uri = 'FR' + incident_url.replace(url, '').split('-')[0]
    
    main_span_el = a_el.find('span[@class="redDateText"]')
    child_span_el = main_span_el.find('span')
    data_timestamp = child_span_el.get('data-timestamp')
    incident_date = datetime.fromtimestamp(int(data_timestamp))
    date = incident_date.strftime('%B %d, %Y')
    
    # city, state_abbr = main_span_el.tail[2:-1].rsplit(', ', 1)
    
    incident, city, state = extract_paragraphs_city_state(incident_url)
    address = ''
    participants = dict()
    
    one_row = [incident_uri, date, title,
               state, city, address, 
               incident_url, incident_url,
               incident_sources, participants,
               incident, fire_department, incident_date]
    list_of_lists.append(one_row)


# In[7]:

df = pandas.DataFrame(list_of_lists, columns=headers)


# In[8]:

df.head(5)


# In[9]:

df.to_pickle('firerescue_v2.pickle')


