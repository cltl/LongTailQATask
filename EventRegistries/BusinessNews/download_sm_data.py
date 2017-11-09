
# coding: utf-8

# In[3]:


import json
import utils
import operator
# topics: http://www.newsreader-project.eu/files/2013/01/NWR-2014-1.pdf


# In[27]:


base = 'http://smnews.fii800.lod.labs.vu.nl/news?'
terms = ['worker', 'employee', 'labourer', 'workman', 'fired', 'discharged', 'dismissed']#, 'pink-slipped', 'layed-off']
args = {
    'q' : ' '.join(terms),#'fired worker', # the query terms to look for
    'in' : 'content', # look in title, content or both (supported values are: "title", "content", "both")
    'from' : '2015-09-01T00:00:00Z', # from->starting datetime point
    'to' : '2015-09-30T00:00:00Z', # ending datetime point
    'source' : '', # source -> which source
 #   'media' : 'News', # media -> media type ("Blog" or "News")
    'size' : 500, # size -> amount of results to return
    'offset' : 0,  # offset ->skip the first offset results (useful for pagination)
    'match' : 'terms'
}


# In[28]:


url=utils.create_url(base, args)
all_results = utils.extract_hits(url)
len(all_results)


# In[29]:


# ignore this
utils.extract_size('http://snews.fii800.lod.labs.vu.nl/news?offset=0&to=2015-09-27T00:00:00Z&media=News&size=1&from=2015-09-20T00:00:00Z&in=content&q=crash')


# ### Which articles are too long/short or have the exact same content

# In[30]:


to_remove=set()
min_len=100
max_len=4000
ls=0
same=0
for e1, val1 in all_results.items():
    data1=all_results[e1]['_source']['content']
    if len(data1)>max_len or len(data1)<min_len:# if too long or short
        ls+=1
        to_remove.add(e1)
        continue
    for e2, val2 in all_results.items():
        if e1<e2: # this is a trick to avoid checking the same thing twice
            data2=all_results[e2]['_source']['content']
            if data1==data2:
                to_remove.add(e1)
                same+=1
                break
print(ls, same)


# In[31]:


len(to_remove)


# In[32]:


for k in to_remove:
    del all_results[k]


# In[34]:


print(len(all_results))


# ### Which articles have similarity higher than a threshold -> create chains

# In[35]:


import spacy
from collections import defaultdict
nlp = spacy.load('en')
entities=defaultdict(set)
for key, value in all_results.items():
    data=value['_source']
    doc = nlp(data['title'] + '\n' + data['content'])
    for ent in doc.ents:
        entities[key].add(ent.text)
#        print(ent.label_, ent.text)


# In[52]:


c=0
o=0
l=0
coref=[]
for e1, ents1 in entities.items():
    data1=all_results[e1]['_source']['content']
    for e2, ents2 in entities.items():
        if e1<e2:
            overlap=ents1 & ents2
            if len(overlap)>min(len(ents1),len(ents2))*2/3:
                found=False
                for chain in coref:
                    if e1 in chain or e2 in chain:
                        chain.add(e1)
                        chain.add(e2)
                        found=True
                if not found: coref.append(set([e1,e2]))
                o+=1
            c+=1
print(l,o,c)


# ### Merge chains

# In[53]:


# merge chains
for index, chain in enumerate(coref):
    for index2, chain2 in enumerate(coref):
        if index!=index2 and chain & chain2:
            chain |=chain2
        if index!=index2 and chain==chain2:
            chain2.clear()
            print("YO")
#            print(chain, chain2)


# ### Inspect chains

# In[54]:


cnt=0
for chain in coref:
    if len(chain):
        print(len(chain))
        cnt+=1
cnt

# OLD CHAINS: 
# 1) Jeremy Clarkson's comeback (2)
# 2) Taco Bell firing an employee (2)
# 3) Taylor Swift's bottom (10)
# 4) Students angry over tax increase (2)
# 5) Worker killed in South Africa (2)
# 6) Mixed reports and promotions (2)
# 7) Bombarding in Aleppo (2)
# 8) Taylor Swift's bottom AGAIN (0)
# 9) Someone won in soccer (fired used here in an entirely different sense) (2)
# 10) Firing a weapon on someone (2)
# 11) Sheriff's deputy shot and killed (4)


# In[59]:


chain=coref[-4]
for e in chain:
    data=all_results[e]['_source']['content']
    print("DOCUMENT\n",data)
    print()


# ### Store the data to redis

# In[52]:


import uuid
import redis

def make_redis_key():
    return "incinitstr:BU%s" % uuid.uuid4().hex

pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
r = redis.Redis(connection_pool=pool)

stored = set()
for chain in coref:
    incident_data={"estimated_incident_date": "", "estimated_location": "", "articles":[]}
    for article in chain:
        this_article={}
        this_article["body"]=all_results[article]['_source']['content']
        this_article["title"]=all_results[article]['_source']['title']
        this_article["dct"]=all_results[article]['_source']['published']
        incident_data["articles"].append(this_article)
        stored.add(article)
    rkey=make_redis_key()
    rval=json.dumps(incident_data)
    r.set(rkey, rval)
print(len(stored))

# non-chained
for article, val in all_results.items():
    incident_data={"estimated_incident_date": "", "estimated_location": "", "articles":[]}
    if article not in stored:
        this_article={}
        this_article["body"]=all_results[article]['_source']['content']
        this_article["title"]=all_results[article]['_source']['title']
        this_article["dct"]=all_results[article]['_source']['published']
        incident_data["articles"].append(this_article)
        stored.add(article)
        rkey=make_redis_key()
        rval=json.dumps(incident_data)
        r.set(rkey, rval)
print(len(stored))


# In[ ]:




