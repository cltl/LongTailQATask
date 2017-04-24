#  PostCoder Web Service V3 example
#  Allies Computing Ltd 2014
#  
#  This demo shows how to perform an address lookup in Python.
#	
  
import json
import urllib

searchkey 	= 'PCWG9-MWKT2-7GMZZ-JYW6G'; # your search key
searchterm  = '4214 Pinhook Road, Mount Olivet, Kentucky';   # string to use for an address search

print ("PostCoder Web V3 Python Client Snippet\n\n")

url = 'http://ws.postcoder.com/pcw/' + searchkey + '/address/US/'
# for other uri options see http://developers.alliescomputing.com

try:
    # For Python 3.0 and later
    from urllib.request import urlopen
    url = url + urllib.parse.quote(searchterm)
    response = urlopen(url).read().decode('utf-8')
except ImportError:
    # Fall back to Python 2
    from urllib import urlopen
    url = url + urllib.quote(searchterm)
    response = urlopen(url).read()

structure = json.loads(response)
print(json.dumps(structure, indent=2))


