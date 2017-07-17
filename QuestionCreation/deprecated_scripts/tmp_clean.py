import pandas
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

"""
def source_still_online(s):
    req = Request(s)
    try:
        response = urlopen(req)
    except HTTPError as e:
        print('The server couldn\'t fulfill the request.')
        print('Error code: ', e.code)
    except URLError as e:
        print('We failed to reach a server.')
        print('Reason: ', e.reason)
    else:
        print ('Website is working fine')    
"""
def source_still_online(s):
    a=urlopen(s)
    print(a.getcode())

df = pandas.read_pickle('../EventRegistries/GunViolenceArchive/frames/all')

sources=set()
for index, row in df.iterrows():
    sources |= set(row['incident_sources'].keys())
    #input('continue?')
    #sources |= row['incident_sources']

print(len(sources))


source_still_online('http://web.archive.org/web/20170412132524/http://www.chicagotribune.com/news/local/breaking/ct-chicago-shootings-violence-20170309-story.html')
source_still_online('http://web.archive.org/web/20170115155103/http://www.orlandosentinel.com/news/crime/os-one-shot-warren-sapp-20170114-story.html')
source_still_online('http://web.archive.org/web/20170314212446/http://www.jsonline.com/story/news/crime/2017/02/12/kenosha-police-arrest-15-year-old-fatal-shooting/97824936/')
