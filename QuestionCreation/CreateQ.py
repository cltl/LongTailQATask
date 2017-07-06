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
from datetime import datetime

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



def pretokenize(df, accepted_years):
    """
    pretokenize news articles using spacy
    and convert to conll

    :param pandas.core.frame.DataFrame df: gva archive
    :param list accepted_years: list of accepted years

    :rtype: dict
    :return: source_url -> list of strings (conll output)
    """
    news_article_template = '../EventRegistries/GunViolenceArchive/the_violent_corpus/{incident_uri}/{the_hash}.json'
    doc_id2conll = dict()
    not_found = set()
    nlp = English()

    for index, row in df.iterrows():
        if any([row['date'].endswith(year)
                for year in accepted_years]):
            for source_url in row['incident_sources']:

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

                info = [the_hash + '.DCT', str(news_article_obj.dct), 'DCT', '-']
                conll.append('\t'.join(info) + '\n')

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

                # end
                conll.append('#end document\n')

                doc_id2conll[source_url] = conll

    return doc_id2conll

if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Create data for SemEval-2018 task 5')
    parser.add_argument('-d', dest='path_gva_df', required=True, help='path to gva frame (../EventRegistries/GunViolenceArchive/frames/all)')
    parser.add_argument('-e', dest='event_types', required=True, help='event types separated by underscore e.g. killing_injuring')
    parser.add_argument('-s', dest='subtask', required=True, help='1 | 2 | 3')
    parser.add_argument('-o', dest='output_folder', required=True, help='folder where output will be stored')
    args = parser.parse_args()

    # load arguments
    confusion_tuples = [('location', 'time'),
                        ('participant', 'time'),
                        ('location', 'participant')
                        ]
    event_types = args.event_types.split('_')
    subtask = int(args.subtask)
    all_candidates = set()
    df = pandas.read_pickle(args.path_gva_df)

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
    path_cache_tokenization = '%s/tokenization.cache' % args.output_folder
    if not os.path.exists(path_cache_tokenization):
        doc_id2conll = pretokenize(df, ['2017'])

        with open(path_cache_tokenization, 'wb') as outfile:
            pickle.dump(doc_id2conll, outfile)

    # set min and max number of incidents
    min_num_answer_incidents = 0
    max_num_answer_incidents = 99999

    if subtask==1:
        min_num_answer_incidents = 1
        max_num_answer_incidents = 1
    elif subtask==2:
        min_num_answer_incidents = 2

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

