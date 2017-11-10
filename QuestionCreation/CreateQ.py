import sys
import os
import pandas

import look_up_utils
import createq_utils
import pickle
import argparse
from lxml import etree

import pandas
import hashlib
import pickle
import spacy_to_naf
import json
from spacy.en import English
from datetime import datetime, date
from collections import defaultdict
import operator
from collections import Counter
from collections import defaultdict

def get_the_incident_years(doc_settings):
    start_year = 3000
    end_year = 0

    for repo, repo_info in doc_settings.items():

        if repo_info['date_range'][0].year < start_year:
            start_year = repo_info['date_range'][0].year

        if repo_info['date_range'][1].year > end_year:
            end_year = repo_info['date_range'][1].year

    the_accepted_incident_years = {year
                                   for year in range(start_year, end_year + 1)}
    return the_accepted_incident_years

def piek(output_path, doc):
    """
    """    
    raw = ' '.join([token_el.text 
                    for token_el in doc.iterfind('text/wf')])
    raw = raw.replace('NEWLINE', '\n')
    raw_value = raw
    raw_el = etree.Element('raw')
    raw_el.text = raw_value
    doc.append(raw_el)
    
    for child_string in ['nafHeader/linguisticProcessors', 'text', 'terms', 'entities', 'deps', 'chunks']:
        els = doc.findall(child_string)
        for el in els:
            el.getparent().remove(el)
        
    root = doc.getroottree()
    with open(output_path, 'wb') as outfile:
        root.write(outfile,
                   pretty_print=True,
                   xml_declaration=True,
                   encoding='utf-8')

def get_duplicate_sents(doc, threshold, verbose=False):
    """
    get sentence identifiers of sentences
    which occur more than threshold in the text

    :param lxml.etree._Element doc: parsed NAF

    :rtype: set
    :return: set of sentence identifiers to ignore
    """
    sent_ids_to_ignore = set()

    sent_id2sent_tokens = defaultdict(list)
    for wf_el in doc.iterfind('text/wf'):
        sent_id = wf_el.get('sent')
        sent_id2sent_tokens[sent_id].append(wf_el.text)

    sent2sent_ids = defaultdict(set)
    for sent_id, tokens in sent_id2sent_tokens.items():
        sent = ' '.join(tokens)
        sent2sent_ids[sent].add(sent_id)

    for sent, sent_ids in sent2sent_ids.items():
        freq = len(sent_ids)
        if freq >= threshold:
            sent_ids_to_ignore.update(sent_ids)
            if verbose:
                print('ignored with freq %s: %s' % (freq, sent))

    return sent_ids_to_ignore

def text2conll_one_file(nlp, incident_uri, doc_id, discourse, text, pre=False):
    """
    use spacy to output text (tokenized) in conll

    :param str doc_id: document identifier
    :param str discourse: TITLE | BODY
    :param str text: content (either title or context of news article)
    """
    doc = spacy_to_naf.text_to_NAF(text, nlp)

    
    sent_ids2ignore = get_duplicate_sents(doc, threshold=3, verbose=True)
    output = []
    num_chars = 0
    prev_sent_id = 1
    token_id = 0
    unique_ids = defaultdict(int)

    for wf_el in doc.xpath('text/wf'):
        sent_id = wf_el.get('sent')

        if sent_id in sent_ids2ignore:
            continue

        if prev_sent_id != int(sent_id):
            token_id = 0
        elif prev_sent_id == int(sent_id):
            token_id += 1

        prev_sent_id = int(sent_id)

        if discourse == 'BODY':
            id_ = '{doc_id}.b{sent_id}.{token_id}'.format_map(locals())
        if discourse == 'TITLE':
            id_ = '{doc_id}.t{sent_id}.{token_id}'.format_map(locals())

        unique_ids[id_] += 1

        if pre:
            info = [id_, wf_el.get('offset'), wf_el.get('length')]
            output.append('\t'.join(info) + '\n')
        else:
            num_chars += len(wf_el.text)
            info = [id_, wf_el.text, discourse, '-']
            output.append('\t'.join(info) + '\n')

    for id_, freq in unique_ids.items():
        if freq >= 2:
            raise AssertionError('id %s occurs %s times' % (id_, freq))

    return output, num_chars

def pretokenize(df, settings):
    """
    pretokenize news articles using spacy
    and convert to conll

    :param pandas.core.frame.DataFrame df: gva archive
    :param dict settings: dict with settings about:
    {'accepted_char_range' : range(300, 4000),$
     'date_range' : (date(2013, 1, 1), date(2016, 12, 31),$
     'accepted_years' : ['2013', '2014', '2015', '2016']$
     }

    :rtype: dict
    :return: source_url -> list of strings (conll output)
    """
    gv_news_article_template = '../EventRegistries/GunViolenceArchive/the_violent_corpus/{incident_uri}/{the_hash}.json'
    fr_news_article_template = '../EventRegistries/FireRescue1/firerescue_corpus/{incident_uri}/{the_hash}.json'
    doc_id2conll = dict()
    not_found = set()
    nlp = English()
    distribution = defaultdict(int)
    dcts = []
    start_date, end_date = settings['date_range']
    accepted_years = settings['accepted_years']
    accepted_char_range = settings['accepted_char_range']


    num_removed_due_to_length = 0
    rows_to_keep = []
    num_removed = 0


    for index, row in df.iterrows():
        to_check = False
        the_date = row['date']
        if the_date is None:
            continue 

        if any([the_date.endswith(year)
                for year in accepted_years]):

            to_check = True
            clean_incident_sources = dict()
            for source_url, row_dct in row['incident_sources'].items():

                # create path to newsitem object
                hash_obj = hashlib.md5(source_url.encode())
                the_hash = hash_obj.hexdigest()
                incident_uri = row['incident_uri']

                news_article_template = gv_news_article_template
                if incident_uri.startswith('FR'):
                    news_article_template = fr_news_article_template
     
                path = news_article_template.format_map(locals())

                if source_url in doc_id2conll:
                    continue

                # load newsitem object if it exists
                try:
                    with open(path, 'rb') as infile:
                        news_article_obj = pickle.load(infile)
                except FileNotFoundError:
                    print(source_url, 'not found')
                    continue

                # tokenize and store conll in list of strings
                conll = []

                # header
                conll.append('#begin document ({the_hash});\n'.format_map(locals()))

                # write dct
                if not news_article_obj.dct:
                    continue

            
                if not start_date < news_article_obj.dct < end_date:
                    print(news_article_obj.dct, 'not in accepted date range')
                    continue

                info = [the_hash + '.DCT', str(news_article_obj.dct), 'DCT', '-']
                conll.append('\t'.join(info) + '\n')
                dcts.append(news_article_obj.dct)

                # title
                title_conll, title_chars = text2conll_one_file(nlp, incident_uri, the_hash, 'TITLE', news_article_obj.title)
                if not title_conll:
                    continue
                conll.extend(title_conll)

                # body
                body_conll, body_length = text2conll_one_file(nlp, incident_uri, the_hash, 'BODY', news_article_obj.content)
                if not body_conll:
                    continue

                conll.extend(body_conll)

                rounded = round(body_length, -2) # round to nearest 100
                distribution[rounded] += 1

                if body_length not in accepted_char_range:
                    num_removed_due_to_length += 1

                # end
                conll.append('#end document\n')

                # save to naf
                #naf_output_path = os.path.join(args.output_folder, 'naf', incident_uri + '---' + the_hash + '.naf')
                #doc = spacy_to_naf.text_to_NAF(news_article_obj.title + '. ' + news_article_obj.content, nlp)
                #piek(naf_output_path, doc)

                clean_incident_sources[source_url] = row_dct
                doc_id2conll[source_url] = conll

        if to_check:
            if clean_incident_sources:
                df.set_value(index, 'incident_sources', clean_incident_sources)
                rows_to_keep.append(index)
            else:
                num_removed += 1

    print('%s incidents removed during cleanup' % num_removed)
    print('%s incidents remain' % len(rows_to_keep))
    df = df[df.index.isin(rows_to_keep)]
    print('number of rows in df: %s' % len(df))
    print('documents removed due to length: %s' % num_removed_due_to_length)
    print('dct range: %s %s' % (min(dcts), max(dcts)))

    #total = sum(distribution.values())
    #for key, value in sorted(distribution.items(),
    #                         key=operator.itemgetter(1),
    #                         reverse=True):
    #    perc = 100 * (value/total)
    #    print(key, value, round(perc, 2))

    return doc_id2conll, df

if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Create data for SemEval-2018 task 5')
    parser.add_argument('-d', dest='path_gva_df', help='path to gva frame (../EventRegistries/GunViolenceArchive/frames/all)')
    parser.add_argument('-f', dest='path_fr_df', help='path to fr frame (../EventRegistries/FireRescue1/firerescue_v3.pickle)')
    parser.add_argument('-e', dest='event_types', required=True, help='event types separated by underscore e.g. killing_injuring')
    parser.add_argument('-s', dest='subtask', required=True, help='1 | 2 | 3')
    parser.add_argument('-o', dest='output_folder', required=True, help='folder where output will be stored')
    args = parser.parse_args()


    # assertions
    if all([args.path_gva_df is None,
            args.path_fr_df is None]):
        assert False, 'no path to df provided' 

    doc_settings = {
        'gva' : {'accepted_char_range' : range(300, 4000),
                 'date_range' : (date(2013, 1, 1), date(2016, 12, 31)),
                 'accepted_years' : ['2013', '2014', '2015', '2016']
                 },
         'fr' : {'accepted_char_range' : range(100, 4000),
                 'date_range' : (date(2005, 1, 1), date(2009, 12, 31)),
                 'accepted_years' : ['2005', '2006', '2007', '2008', '2009']
         }
    }
    event_types = [args.event_types]
    
    subtask = int(args.subtask)
    all_candidates = set()

    # load arguments
    confusion_tuples = [('location', 'time'),
                        ('participant', 'time'),
                        ('location', 'participant')
                        ]
    if subtask == 3:
        confusion_tuples = [('location', 'time'),
                            ('participant', 'time'),
                            ('location', 'participant')
                            ]

    output_path = '%s/%s---%s.bin' % (args.output_folder, args.subtask, args.event_types)

    if subtask not in {1,2,3}:
        print('invalid subtask: %s' % subtask)
        sys.exit()

    print(datetime.now())
    print(args.__dict__)

    # load question number
    path_to_q_id = '%s/q_id.json' % args.output_folder
    if not os.path.exists(path_to_q_id):
        subtasks2q_id = {'1': 1,
                         '2': 1,
                         '3': 1}
    else:
        with open(path_to_q_id) as infile:
            subtasks2q_id = json.load(infile)

    # create tokenization
    path_cache_tokenization = '%s/cache' % args.output_folder
    if not os.path.exists(path_cache_tokenization):
        print('df + tokenization recomputed')

        dfs = []
        doc_id2conll = dict()

        for repo, repo_path in [('gva', args.path_gva_df),
                                ('fr', args.path_fr_df)]:
            if repo_path:
                print('reading', repo_path)
                a_df = pandas.read_pickle(repo_path)
                a_df = a_df.reset_index(drop=True) # reset indices
                print('len before pretokenize', len(a_df))
                a_doc_id2conll, a_df = pretokenize(a_df, doc_settings[repo])
                print('len after pretokenzie', len(a_df))

                dfs.append(a_df)
                doc_id2conll.update(a_doc_id2conll)
        
        df = pandas.concat(dfs)

        with open(path_cache_tokenization, 'wb') as outfile:
            pickle.dump((doc_id2conll, df), outfile)
    else:
        print('df + tokenization from cache')
        with open(path_cache_tokenization, 'rb') as infile:
            doc_id2conll, df = pickle.load(infile)

    # set min and max number of incidents
    min_num_answer_incidents = 0
    max_num_answer_incidents = 99999

    if subtask==1:
        min_num_answer_incidents = 1
        max_num_answer_incidents = 1
    elif subtask==2:
        min_num_answer_incidents = 2
    elif subtask == 3:
        min_num_answer_incidents = 1

    # create questions
    the_incident_years = get_the_incident_years(doc_settings)

    for confusion_tuple in confusion_tuples:
        look_up, parameters2incident_uris = look_up_utils.create_look_up(df,
                                                                         discard_ambiguous_names=True,
                                                                         allowed_incident_years=the_incident_years,
                                                                         check_name_in_article=True,
                                                                         only_names_with_two_parts=True)
        last_qid, candidates=createq_utils.lookup_and_merge(look_up,
                                                            subtasks2q_id[str(subtask)],
                                                            parameters2incident_uris,
                                                            confusion_tuple,
                                                            min_num_answer_incidents,
                                                            max_num_answer_incidents,
                                                            subtask,
                                                            event_types,
                                                            df,
                                                            debug=False,
                                                            inspect_one=False)
        subtasks2q_id[str(subtask)] = last_qid + 1
        all_candidates.update(candidates)

        print(confusion_tuple, len(candidates))


    # write to file
    with open(output_path, 'wb') as outfile:
        pickle.dump(all_candidates, outfile)

    # write q_id dict to file
    with open(path_to_q_id, 'w') as outfile:
        json.dump(subtasks2q_id, outfile)

