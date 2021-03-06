import urllib.parse
import requests
import os
import shutil
import json
import glob
from urllib.parse import urlencode, quote_plus


API="https://api.diffbot.com/v3/article"
TOKEN="1f5fcfe62127906ba56274d11c019ac8"
CORPUSDIR="the_violent_corpus/"
NODATE_FILE="logs/nodate.txt"
ERRORS_FILE='logs/errors.txt'
DIFF_DATE_FILE="logs/diff_date.tsv"
NO_DATE_FILE="logs/no_date.tsv"
NO_ARCHIVE_FILE="logs/no_archive.tsv"

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

def is_archive_uri(uri):
    return uri.startswith('https://web.archive.org/') or uri.startswith('http://web.archive.org/')

def log_different_date(url, date_cache1, date_cache2, date_np):
    with open(DIFF_DATE_FILE, 'a') as w:
        w.write('%s\t%s\t%s\t%s\n' % (url, date_cache1, date_cache2, date_np))

def log_no_date(url):
    with open(NO_DATE_FILE, 'a') as w:
        w.write('%s\n' % url)

def log_no_archive(url):
    with open(NO_ARCHIVE_FILE, 'a') as w:
        w.write('%s\n' % url)

def check_overlap(keys):
	results=set()
	for c in glob.glob('el_corpora/*.tsv'):
		with open(c, 'r') as rc:
			for line in rc:
				splits=line.split('\t')
				if splits[0] in keys:
					results.add(tuple([c, splits[0], splits[1]]))
	return results

def concat_all_sources(incident_uri):
	text=''
	files_location="%s%s/*.json" % (CORPUSDIR, incident_uri)
	for f in glob.glob(files_location):
		with open(f, 'r') as r:
			a_json=json.load(r)
			text+=a_json['title'] + '\n' + a_json['content'] + '\n'
	return text

def hash_uri(u):
	import hashlib
	hash_obj=hashlib.md5(u.encode())
	return hash_obj.hexdigest()

# Iterate sources and obtain text
def whats_behind_a_uri(my_uri):
	q = {'url': my_uri, 'token': TOKEN, 'paging': 'false'}
	req_url = API + '?' + urllib.parse.urlencode(q)
	r = requests.get(url=req_url)
	if r.status_code!=200:
		return None
	try:
		page = r.json()
		if 'objects' in page:
			my_object=page['objects'][0]
			if 'estimatedDate' in my_object:
				dct=my_object['estimatedDate']
			else:
				dct='NODATE'
				with open(NODATE_FILE, 'a+') as nodate:
					nodate.write(my_uri + '\n')
			article= {'uri': my_uri, 'title': my_object['title'], 'dct': dct, 'content': my_object['text'], 'id': hash_uri(my_uri)}
		else:
			article=None
	except ValueError:
		print("Error with the article %s" % my_uri)
		article=None
	return article

def reset_files():
	if os.path.exists(NODATE_FILE):
		os.remove(NODATE_FILE)
	if os.path.exists(ERRORS_FILE):
		os.remove(ERRORS_FILE)

def reset_dir(index):
	directory="%s%s/" % (CORPUSDIR, str(index))
	if os.path.exists(directory):
		shutil.rmtree(directory)
	os.makedirs(directory)
	return directory

