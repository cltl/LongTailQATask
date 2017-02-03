import glob
import pickle
from collections import defaultdict
from lxml import etree

def create_iterable(root_folder, titles=False, content=False):
    """
    create iterable of .naf paths
    
    :param str root_folder: the root folder
    :param bool titles: include .title.naf files
    :param bool content: include .content.naf files
    
    :rtype: set
    :return: set .naf paths
    """
    nafs = set()
   
    if titles: 
    	for naf_path in glob.glob(root_folder + '/**/*.title.naf', recursive=True):
            nafs.add(naf_path)
    if content:
        for naf_path in glob.glob(root_folder + '/**/*.content.naf', recursive=True):
            nafs.add(naf_path)

    return nafs


def lemma_freqs(paths):
    """
    create lemma freqs
    
    :param set paths: set of .naf paths
    
    :rtype: collections.defaultdict
    :return: mapping lemma -> freq
    """
    lemma2freq = defaultdict(dict)
    
    for path in paths:
        doc = etree.parse(path)
        
        for term_el in doc.iterfind('terms/term'):
            lemma = term_el.get('lemma')
            pos = term_el.get('pos')
            if lemma not in lemma2freq[pos]:
                lemma2freq[pos][lemma] = 0
            if lemma not in lemma2freq['ALL']:
                lemma2freq['ALL'][lema] = 0

            lemma2freq[pos][lemma] += 1
            lemma2freq['ALL'][lemma] += 1
            
    return lemma2freq
            
        

root_folder = 'the_violent_corpus'

naf_paths = create_iterable(root_folder, titles=True, content=True)
lemma2freq = lemma_freqs(naf_paths)
with open('output/lemma2freq_titles_content.pickle', 'wb') as outfile:
    pickle.dump(lemma2freq, outfile)

    
    
    
    
