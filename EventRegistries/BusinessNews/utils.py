import requests

def create_url(base, args):
    """
    give the base url, add all arguments
    
    :param str base: base url
    :param dict args: mapping keyword argument to value
    
    :rtype: str
    :return: url
    """
    arguments = '&'.join(['%s=%s' % (key, value)
                          for key, value in args.items()
                          if value])
    
    url = ''.join([base, arguments])
    #print(url)
    return url

def extract_hits(url):
    """
    given an url:
    http://news.fii800.lod.labs.vu.nl/news?offset=0&to=2015-09-27T00:00:00Z&media=News&size=1000&from=2015-09-20T00:00:00Z&in=content&q=crash
    
    return all hits
    
    :param str url: the url that return json
    
    :rtype: dict
    :return: dict mapping hit identifier -> the info about each hit
    """
    response = requests.get(url)
    if response.status_code == 200:
        json = response.json()
        results = {hit['_source']['id']: hit
                   for hit in json['hits']['hits']}
    else:
        results = {}
        
    return results

def extract_size(url):
    """
    given an url:
    http://news.fii800.lod.labs.vu.nl/news?offset=0&to=2015-09-27T00:00:00Z&media=News&size=1&from=2015-09-20T00:00:00Z&in=content&q=crash
   
    return the number of hitss
   
    :param str url: the url that return json
   
    :rtype: int
    :return: int
    """
    response = requests.get(url)
    if response.status_code == 200:
        json = response.json()
        result_size = int(json['hits']['total'])
    else:
        result_size = 0
    
    return result_size
    
def get_all_hits(base, args):
    """
    
    given an url:
    http://news.fii800.lod.labs.vu.nl/news?offset=0&to=2015-09-27T00:00:00Z&media=News&size=1000&from=2015-09-20T00:00:00Z&in=content&q=crash
    
    return all hits using pagination
    
    :param str url: the url that return json
    :param dict args: mapping keyword argument to value
    :rtype: dict
    :return: dict mapping hit identifier -> the info about each hit
    """
    all_results = {}
    keep_going = True
    
    while keep_going:
        url = create_url(base, args)
        results = extract_hits(url)
        
        if results:
            all_results.update(results)
            
        else:
            keep_going = False
            
        args['offset'] += args['size']
            
    return all_results
