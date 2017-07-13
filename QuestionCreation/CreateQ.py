import sys
import os
import pandas

import look_up_utils
import createq_utils
import pickle
import argparse

import pandas
import hashlib
import pickle
import spacy_to_naf
import json
from spacy.en import English
from datetime import datetime, date
from collections import defaultdict
import operator

def text2conll_one_file(nlp, doc_id, discourse, text, pre=False):
    """
    use spacy to output text (tokenized) in conll

    :param str doc_id: document identifier
    :param str discourse: TITLE | BODY
    :param str text: content (either title or context of news article)
    """
    doc = spacy_to_naf.text_to_NAF(text, nlp)
    output = []

    for wf_el in doc.xpath('text/wf'):
        sent_id = wf_el.get('sent')
        token_id = wf_el.get('id')[1:]
        id_ = '{doc_id}.{sent_id}.{token_id}'.format_map(locals())

        if pre:
            info = [id_, wf_el.get('offset'), wf_el.get('length')]
            output.append('\t'.join(info) + '\n')
        else:
            info = [id_, wf_el.text, discourse, '-']
            output.append('\t'.join(info) + '\n')

    return output



def pretokenize(df, accepted_years, accepted_char_range, date_range):
    """
    pretokenize news articles using spacy
    and convert to conll

    :param pandas.core.frame.DataFrame df: gva archive
    :param list accepted_years: list of accepted years
    :param range accepted_char_range: how many characters a document is allowed to have

    :rtype: dict
    :return: source_url -> list of strings (conll output)
    """
    news_article_template = '../EventRegistries/GunViolenceArchive/the_violent_corpus/{incident_uri}/{the_hash}.json'
    doc_id2conll = dict()
    not_found = set()
    nlp = English()
    distribution = defaultdict(int)
    dcts = []
    start_date, end_date = date_range


    num_removed_due_to_length = 0
    rows_to_keep = []
    num_removed = 0


    for index, row in df.iterrows():
        to_check = False
        if any([row['date'].endswith(year)
                for year in accepted_years]):

            to_check = True
            clean_incident_sources = dict()
            for source_url, row_dct in row['incident_sources'].items():

                # create path to newsitem object
                hash_obj = hashlib.md5(source_url.encode())
                the_hash = hash_obj.hexdigest()
                incident_uri = row['incident_uri']
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

                if news_article_obj.dct.year == 2016:
                    print(source_url)
                    input('continue?')

                # title
                title_conll = text2conll_one_file(nlp, the_hash, 'TITLE', news_article_obj.title)
                if not title_conll:
                    continue
                conll.extend(title_conll)

                # body
                body_conll = text2conll_one_file(nlp, the_hash, 'BODY', news_article_obj.content)
                if not body_conll:
                    continue
                conll.extend(body_conll)

                body_length = len(news_article_obj.content)
                rounded = round(body_length, -2) # round to nearest 100
                distribution[rounded] += 1

                if body_length not in accepted_char_range:
                    num_removed_due_to_length += 1

                # end
                conll.append('#end document\n')

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
    parser.add_argument('-d', dest='path_gva_df', required=True, help='path to gva frame (../EventRegistries/GunViolenceArchive/frames/all)')
    parser.add_argument('-e', dest='event_types', required=True, help='event types separated by underscore e.g. killing_injuring')
    parser.add_argument('-s', dest='subtask', required=True, help='1 | 2 | 3')
    parser.add_argument('-o', dest='output_folder', required=True, help='folder where output will be stored')
    args = parser.parse_args()


    # accepted character length range for articles
    accepted_char_range = range(300, 4000)

    # accepted dct range
    date_range = (date(2016, 12, 31), date(2017, 4, 20))

    event_types = args.event_types.split('_')
    subtask = int(args.subtask)
    all_candidates = set()
    df = pandas.read_pickle(args.path_gva_df)
    df = df.reset_index(drop=True) # reset indices

    # load arguments
    confusion_tuples = [('location', 'time'),
                        ('participant', 'time'),
                        ('location', 'participant')
                        ]
    if subtask == 3:
        confusion_tuples = [('location', 'time'),
                            #('participant', 'time'),
                            #('location', 'participant')
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
        doc_id2conll, df = pretokenize(df, ['2017'], accepted_char_range, date_range)

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
    for confusion_tuple in confusion_tuples:
        look_up, parameters2incident_uris = look_up_utils.create_look_up(df,
                                                                         discard_ambiguous_names=True,
                                                                         allowed_incident_years={2017},
                                                                         check_name_in_article=True)

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

