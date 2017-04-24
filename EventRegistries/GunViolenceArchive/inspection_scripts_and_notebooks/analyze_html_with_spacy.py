import glob
import json
import os
import pickle
import spacy_to_naf
from lxml import etree
from spacy.en import English
nlp = English()
from multiprocessing.dummy import Pool as ThreadPool
from datetime import datetime

def json2spacy2naf(json_path):
    """
    analyze crawled html with spacy and save both processed title
    and content as naf files:

    e.g. given bla.json

    these two files will be created:
    bla.title.naf
    bla.content.naf

    :param str json_path: json output from crawling html with diffbot api
    """
    title_path = json_path.replace('.json', '.title.naf')
    content_path = json_path.replace('.json', '.content.naf')

    json_obj = json.load(open(json_path))

    naf_title = spacy_to_naf.text_to_NAF(json_obj['title'], nlp)
    naf_content = spacy_to_naf.text_to_NAF(json_obj['content'], nlp)

    for naf_obj, path in [(naf_title, title_path),
                          (naf_content, content_path)]:
        with open(path, 'wb') as outfile:
            roottree = naf_obj.getroottree()

            roottree.write(outfile,
                           pretty_print=True,
                           xml_declaration=True,
                           encoding='utf-8')

print('start', datetime.now())
iterable = glob.glob('../the_violent_corpus/**/*.json', recursive=True)
pool = ThreadPool(5)
results = pool.map(json2spacy2naf, iterable)
print('end', len(results), datetime.now())
