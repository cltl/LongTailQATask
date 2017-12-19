import subprocess
import os
import json
import pickle
import operator
import pandas
import string

from glob import glob
from collections import defaultdict
from collections import Counter
from datetime import datetime

from iaa import IAA


# folder rm and mkdir
def reset(test_data):
    """
    remove folder 'input' if it exists and create this structure:
    test_data
        input
            s1
            s2
            s3
        dev_data
            s1
            s2
            s3

    :param str test_data: path to test_data folder containg both the .json files and the docs.conll files
    """

    commands = ['rm -rf test_data && mkdir test_data',
                'mkdir -p test_data/input/s1',
                'cp {test_data}/1_questions.json test_data/input/s1/questions.json'.format_map(locals()),
                'mkdir -p test_data/input/s2',
                'cp {test_data}/2_questions.json test_data/input/s2/questions.json'.format_map(locals()),
                'mkdir -p test_data/input/s3',
                'cp {test_data}/3_questions.json test_data/input/s3/questions.json'.format_map(locals()),
                'mkdir -p test_data/dev_data/s1',
                'cp {test_data}/1_answers.json test_data/dev_data/s1/answers.json'.format_map(locals()),
                'mkdir -p test_data/dev_data/s2',
                'cp {test_data}/2_answers.json test_data/dev_data/s2/answers.json'.format_map(locals()),
                'mkdir -p test_data/dev_data/s3',
                'cp {test_data}/3_answers.json test_data/dev_data/s3/answers.json'.format_map(locals()),

                'cp {test_data}/system_input/docs.conll test_data/input/s1/docs.conll'.format_map(locals()),
                'cp {test_data}/system_input/docs.conll test_data/input/s2/docs.conll'.format_map(locals()),
                'cp {test_data}/system_input/docs.conll test_data/input/s3/docs.conll'.format_map(locals()),
                ]

    for command in commands:
        try:
            subprocess.check_output(command, shell=True)
        except subprocess.CalledProcessError as e:
            print(e)


def load_disqualified_docs(path_dis_areum_men,
                           path_dis_ngan_men,
                           debug=False):
    """
    load set of disqualified documents

    :param str path_dis_areum_men: basename will be dis_areum_men.json
    :param str path_dis_ngan_men: basename will be dis_ngan_men.json
    """
    dis_areum = json.load(open(path_dis_areum_men))
    dis_ngan = json.load(open(path_dis_ngan_men))

    disqualified_ngan = set()
    for dis_docs in dis_ngan.values():
        disqualified_ngan.update(dis_docs)

    disqualified_areum = set()
    for dis_docs in dis_areum.values():
        disqualified_areum.update(dis_docs)

    disqualified_docs = disqualified_ngan | disqualified_areum
    overlap = disqualified_ngan & disqualified_areum

    if debug:
        print()
        print('# overlap', len(overlap))
        print('# disqualified ngan', len(disqualified_ngan))
        print('# disqualified areum', len(disqualified_areum))
        print('# disqualified docs', len(disqualified_docs))

    return disqualified_docs

# load conll
def load_conll(conll_path,
               cache_path,
               overwrite=False,
               debug=False):
    """
    load all docs from all conll from all subtasks

    :param str conll_path: one conll file with all documents
    :param str cache_path: path where load_conll will be cached
    :param bool overwrite: if True, reload_conll


    :rtype: tuple
    :return: (subtask2conll, token_id2token)
    """
    if all([os.path.exists(cache_path),
            not overwrite]):
        with open(cache_path, 'rb') as infile:
            subtask2conll, token_id2token = pickle.load(infile)
            if debug:
                print()
                print('load_conll from cache')
                print('num unique docs', len(subtask2conll))
            return subtask2conll, token_id2token

    subtask2conll = dict()
    token_id2token = dict()

    with open(conll_path) as infile:

        doc_id2conll = defaultdict(list)

        for line in infile:

            token_id = None

            if not line.startswith('#'):
                token_id, token, discourse, anno = line.strip().split('\t')
                token_id2token[token_id] = token

            elif line.startswith('#begin document'):
                doc_id = line[17:-3]

            doc_id2conll[doc_id].append((token_id, line))

            if line.startswith('#end document'):
                if doc_id not in subtask2conll:
                    subtask2conll[doc_id] = doc_id2conll[doc_id]


    if debug:
        print()
        print('recomputed load_conll')
        print('num unique docs', len(subtask2conll))

    with open(cache_path, 'wb') as outfile:
        pickle.dump((subtask2conll, token_id2token),
                     outfile)

    return subtask2conll, token_id2token


def load_mappings_mentions2solution(path_excel_file):
    """
    load solution proposed by Roxane to map mentions to either
    1) delete
    2) map to new event type

    :param str path_to_excel_file: path to excel file
    (now in resources/InputData_annotation_improvement.xlsx)

    :rtype: tuple
    :return: (set of mentions of which annotations should be deleted,
              mapping from mention -> new eventtype)
    """
    delete = set()
    old2new_eventtype = dict()

    df = pandas.read_excel(path_excel_file, sheetname='Sheet3')
    for index, row in df.iterrows():

        if row['auto'] == 'auto':

            category = row['category']
            mention = row['mention'][2:-1]

            if category == 'delete':
                delete.add(mention)

            elif category == 'ETM':
                new_eventtype = row['new_eventtype'].replace("'", "")
                old2new_eventtype[mention] = new_eventtype

    return delete, old2new_eventtype


# create new questions.json + save
def get_q_stats_info(subtask, total_num_docs):
    """

    :param str subtask: s1 | s2 | s3
    :param int total_num_docs: number of test data documents

    """
    answers_json_path = 'test_data/dev_data/%s/answers.json' % subtask
    answers = json.load(open(answers_json_path))

    stats_input = {}
    event_type2q_ids = defaultdict(set)

    for q_id, q_info in answers.items():

        num_answer_docs = sum([len(docs)
                               for docs in q_info['answer_docs'].values()
                               ])


        for inc_id in q_info['answer_docs']:

            if inc_id.startswith('BU'):
                eventtype = 'BU'
            elif inc_id.startswith('FR'):
                eventtype = 'FR'
            elif len(inc_id) <= 6:
                eventtype = 'GVA'
            else:
                eventtype = 'GVA_dummy'

        num_noise_docs = total_num_docs - num_answer_docs

        assert (num_answer_docs + num_noise_docs) == total_num_docs, 'total: %s, answer: %s, noise: %s' % (total_num_docs,
                                                                                                           num_answer_docs,
                                                                                                           num_noise_docs)

        q_stats_info = {
            'answer' : q_info['numerical_answer'],
            'num_answer_docs' : num_answer_docs,
            'num_noise_docs' : num_noise_docs,
            'eventtype' : eventtype
        }

        stats_input[q_id] = q_stats_info

    return stats_input


def mwu_token_list(mwu_ids, inc_id, token_id2token, debug=False):
    """
    given a list of token ids, return the same token ids
    but with missing token ids added,

    e.g. mwu_ids = ['1', '2,', '4'] -> ['1', '2', '3', '4']

    syntax of identifier is 'DOC_ID.SENT_ID.W_ID'
    :param list mwu_ids: e.g.
    ['abc4c58e9b7621b10a4732a98dc273b3.b3.15',
    'abc4c58e9b7621b10a4732a98dc273b3.b3.17',
    'abc4c58e9b7621b10a4732a98dc273b3.b3.18']

    :rtype: list
    :return: list of token ids
    """
    assert len(mwu_ids) >= 2, 'incident_id: %s (token: %s), mwu_ids should be a length 2 at least: %s' % (inc_id,
                                                                                                          token_id2token[mwu_ids[0]],
                                                                                                          mwu_ids)

    new_mwu_ids = []

    first_id = mwu_ids[0]
    doc_id, sent_id, first_token_id = first_id.split('.')

    last_id = mwu_ids[-1]
    doc_id, sent_id, last_token_id = last_id.split('.')

    for w_id in range(int(first_token_id),
                      int(last_token_id) + 1):

        new_id = '{doc_id}.{sent_id}.{w_id}'.format_map(locals())

        if new_id in token_id2token:
            token = token_id2token[new_id]

            if all([token in string.punctuation,
                    token != '-']):
                print('punctuation in mw', inc_id, new_id, token_id2token[new_id])

        new_mwu_ids.append(new_id)


        if debug:
            if new_id not in mwu_ids:
                print()
                print('added', new_id)
                print('old mwu_ids', mwu_ids)

    # assert that they are all part of the same sentence
    sent_ids = set()
    for w_id in new_mwu_ids:
        doc_id, sent_id, last_token_id = w_id.split('.')
        sent_ids.add(sent_id)

    assert len(sent_ids) == 1, 'mw in more than one sentence: %s' % new_mwu_ids

    return new_mwu_ids, doc_id + '.' + sent_id

def assert_ann_info(ann_info):
    """
    check for an annotation, e.g.
    {'cardinality': 'UNK', 'eventtype': 'd', 'participants': ['2']}

    1. if no 'participants' -> 'UNK'

    assert:
    B (ALL)
    G (UNK)
    O (UNK)
    S (not explicit, but always NO participants. I think the label is NULL, but please check!)

    :param dict ann_info: e.g. {'cardinality': 'UNK', 'eventtype': 'd', 'participants': ['2']}

    :rtype: dict
    :return: ann_info updated
    """

    # update all missing participant to 'UNK'
    if 'participants' not in ann_info:
        ann_info['participants'] = 'UNK'

    event_type = ann_info['eventtype']

    # HACK replace participants info from Areums for the event label ’s’ to UNK
    if event_type == 's':
        ann_info['participants'] = 'UNK'

    participants = ann_info['participants']


    if event_type == 'b':
        assert participants == 'ALL', 'participants for b should be ALL: %s' % ann_info

    if event_type == 'g':
        assert participants == 'UNK', 'participants for g should be UNK: %s' % ann_info

    if event_type == 'o':
        assert participants == 'UNK', 'participants for o should be UNK: %s' % ann_info

    if event_type == 's':
        assert participants == 'UNK', 'participants for s should be UNK: %s' % ann_info


    return ann_info


# load annotations
def load_men_annotations(user_annotations,
                         token_id2token,
                         delete,
                         old2new_eventtype,
                         disqualified_docs,
                         disqualified_incidents={'387194'},
                         debug=False):
    """
    load mention annotations

    :param dict user_annotations: mapping inc_id -> inc_info
    :param dict token_id2token: mapping token_id -> token
    :param set delete: mentions of which annotations should be deleted (i.d. ignored)
    :param dict old2new_eventtype: mapping mention -> new eventtype
    :param set disqualified_docs: see output load_disqualified_docs
    :param set disqualified_incidents: default is {'387194'}
    :param str user: supported: 'areum' | 'ngan'

    :rtype: dict
    :return: token_id -> annotation info
    """
    token_id2anno = dict()
    vocabulary = defaultdict(int)

    documents_not_in_test_data = set()
    mw2sent_id = defaultdict(list)

    num_anno_from_dis_docs = 0

    for inc_id, inc_info in user_annotations.items():

        if inc_id in disqualified_incidents:

            if debug_value:
                print()
                print(inc_id, 'ignored')
            continue

        if debug >= 2:
            print(inc_id, len(inc_info))

        for token_id, ann_info in inc_info.items():

            doc_id, sent_id, t_id = token_id.split('.')
            if doc_id in disqualified_docs:

                if debug_value >= 2:
                    print(token_id, 'is part of disqualified documents')

                num_anno_from_dis_docs += 1
                continue

            ann_info = assert_ann_info(ann_info)
            event_type = ann_info['eventtype']

            local_token_id2anno = dict()
            all_token_ids_in_test_document = True

            if 'mwu' not in ann_info:
                anno_template = '(%s)'
                local_token_id2anno[token_id] = (inc_id, ann_info, anno_template)


                if token_id not in token_id2token:
                    a_doc_id = token_id.split('.')[0]
                    documents_not_in_test_data.add(a_doc_id)
                    all_token_ids_in_test_document = False
                else:
                    mention = token_id2token[token_id]

            else:

                try:
                    mwu_ids, sent_id = mwu_token_list(ann_info['mwu'], inc_id, token_id2token, debug=False)
                except AssertionError as e:
                    print(e)
                    continue

                # uncomment to see sentences that have multiple mwu's
                #if sent_id in mw2sent_id:
                #    #print('more than one mwu in sentence: %s' % sent_id)
                mw2sent_id[sent_id].append(mwu_ids)

                mw_length = len(mwu_ids)
                mention_parts = []

                for index, token_id in enumerate(mwu_ids, 1):

                    if index == 1:
                        anno_template = '(%s'
                    elif index == mw_length:
                        anno_template = '%s)'
                    else:
                        anno_template = '%s'

                    local_token_id2anno[token_id] = (inc_id, ann_info, anno_template)

                    if token_id not in token_id2token:
                        a_doc_id = token_id.split('.')[0]
                        documents_not_in_test_data.add(a_doc_id)
                        all_token_ids_in_test_document = False
                        continue

                    mention_part = token_id2token[token_id]
                    mention_parts.append(mention_part)

                mention = ' '.join(mention_parts)


            # check if all token_id are in test documents
            if not all_token_ids_in_test_document:
                continue

            # apply strategies 'delete' and 'emt'
            emt = False

            if mention in delete:

                if debug >= 2:
                    print()
                    print('delete %s' % mention, local_token_id2anno)

                continue


            elif all([mention in old2new_eventtype,
                      event_type != 'o']):

                new_event_type = old2new_eventtype[mention]
                if event_type != new_event_type:

                    event_type = new_event_type
                    emt = True

                    if debug >= 2:
                        print()
                        print('emt from %s' % mention, local_token_id2anno)

                    for ann_info in local_token_id2anno.values():
                        ann_info[1]['eventtype'] = event_type

                    if debug >= 2:
                        print('emt to %s %s' % (mention, event_type), local_token_id2anno)

            if all([emt,
                    debug >= 2]):
                print()
                print(inc_id, 'local token_id2anno', local_token_id2anno)

            token_id2anno.update(local_token_id2anno)
            vocabulary[(mention, event_type)] += 1

    if debug_value:
        print('missing documents', documents_not_in_test_data)

    if debug_value:
        print('num anno ignored due to being in disqualified docs', num_anno_from_dis_docs)

    return token_id2anno, vocabulary

def save_vocab_to_file(vocabulary, output_path):
    """
    save vocabulary to file

    :param dict vocabulary: mapping (mention, eventtype) -> freq
    """
    with open(output_path, 'w') as outfile:
        for key, value in sorted(vocabulary.items(),
                                 reverse=True,
                                 key=operator.itemgetter(1)):
            out_line = '{key}\t{value}'.format_map(locals())
            outfile.write(out_line + '\n')

# lumping function
def lump(inc_id, anno, debug=False):
    """
    convert an annotation, e.g.
    {'cardinality': 'UNK', 'eventtype': 'd', 'participants': ['2']}

    to an integer.

    the eventtypes 'b' and 's' are lumped to 'bs'


    :rtype: str
    :return: an integer as a string


    """
    for key in {'cardinality',
                'eventtype'}:
        assert key in anno, '%s not in anno: %s' % (key, anno)

    event_type = anno['eventtype']
    cardinality = anno['cardinality']
    if 'participants' not in anno:
        participants = 'UNK'
    else:
        participants = anno['participants']

    # prefix
    if event_type == 'g':
        return '0'
    elif event_type == 'o':
        prefix = '1'
    elif event_type in {'b', 'd', 'h', 'i', 'm', 's'}:
        prefix = '2'
    else:
        assert False, 'event_type %s not in accepted eventtypes' % event_type

    # event types
    event_type_ord = str(ord(event_type))
    if event_type in {'b', 's'}:

        if debug:
            print()
            print('before lumping', event_type, cardinality, participants)

        if event_type == 'b':
            assert participants == 'ALL', '{participants} should be ALL with b'.format_map(locals())

            cardinality = 'UNK'
            participants = 'UNK'
            event_type = 'bs'
            event_type_ord = str(ord('b')) + str(ord('s'))

        elif all([event_type == 's',
                  type(participants) != list]):

            cardinality = 'UNK'
            participants = 'UNK'

            event_type = 'bs'
            event_type_ord = str(ord('b')) + str(ord('s'))

        if debug:
            print('after lumping', event_type, cardinality, participants)

    # participants
    part_string = ''.join(participants)
    if type(participants) != list:
        part_string = ''.join([str(ord(char))
                               for char in cardinality])

    # cardinality
    card_ord = ''.join([str(ord(char))
                        for char in cardinality])

    # to integer
    the_integer = '999'.join([prefix,
                              inc_id,
                              card_ord,
                              event_type_ord,
                              part_string
                              ])

    if debug:
        print('prefix', prefix)
        print('cardinality', cardinality, card_ord)
        print('event_type', event_type, event_type_ord)
        print('participants', participants, part_string)
        print('integer', the_integer)

    return the_integer


# output conll with and without annotations (same time two files)
def to_conll(subtask, subtask2conll, user2token_id2anno, iaa_incidents):
    """
    write one conll file:
    a) test_data/SUBTASK/docs.conll -> with annotations

    :param str subtask: s1 | s2 | s3
    :param dict subtask2conll: output of load_conll function
    :param dict user2token_id2anno: mapping of user -> output of load_men_annotations function
    :param set iaa_incidents: set of iaa incident identifiers

    """
    added = set()
    chains = defaultdict(int)

    anno_output_path = 'test_data/dev_data/%s/docs.conll' % subtask
    with open(anno_output_path, 'w') as outfile_anno:

        for doc_id, conll_info in subtask2conll.items():
            for token_id, line in conll_info:

                written_line = False
                add = False

                if token_id in user2token_id2anno['areum']:
                    inc_id, ann_info, anno_template = user2token_id2anno['areum'][token_id]
                    add = True

                elif token_id in user2token_id2anno['ngan']:
                    inc_id, ann_info, anno_template = user2token_id2anno['ngan'][token_id]
                    if inc_id not in iaa_incidents:
                        add = True

                if add:
                    integer = lump(inc_id, ann_info)

                    splitted = line.strip().split('\t')
                    splitted[3] = anno_template % integer

                    added.add(token_id)
                    chains[anno_template % integer] += 1

                    outfile_anno.write('\t'.join(splitted) + '\n')
                    written_line = True

                if not written_line:
                    outfile_anno.write(line)

    print('num chains', len(chains))
    print('distr', Counter(chains.values()))

    return added

def compute_stats(stats_input, output_path=None, debug=False):
    """
    compute stats:
    a) avg num of gold incidents
    b) avg num of gold docs
    c) 1 to n noise documents

    :param dict stats_input: mapping of q_id ->
    {
            'answer' : q_info['numerical_answer']
            'num_answer_docs' : num_answer_docs,
            'num_noise_docs' : num_noise_docs
        }

    :rtype: dict
    :return:
    """
    stats = dict()

    for metric_name, input_key in [('gold_incidents', 'answer'),
                                   ('gold_docs', 'num_answer_docs'),
                                   ('noise_docs', 'num_noise_docs')
                                   ]:

        the_sum = sum([q_info[input_key]
                       for q_info in stats_input.values()])
        the_avg = the_sum / len(stats_input)

        stats[metric_name] = (the_sum, round(the_avg, 2))


    num_noise_docs_per_gold_document = stats['noise_docs'][0] / stats['gold_docs'][0]
    stats['num_noise_docs_per_gold_document'] = round(num_noise_docs_per_gold_document, 2)

    if debug:
        print()
        print(stats)
        print()
        print('eventtypes distribution')
        distr = Counter([q_info['eventtype']
                        for q_info in stats_input.values()])
        print(distr)


    if output_path:
        with open(output_path, 'w') as outfile:
            json.dump(stats, outfile, indent=4, sort_keys=True)


if __name__ == '__main__':

    # TODO: 2). Multiword token overlap: allow for a minimal token overlap and not a full token overlap. So: “turned the gun” and “turned the gun on” would be fully equivalent. The current IAA calculation is very strict on this.

    # call functions
    debug_value = 1

    # reset directories
    test_data = '/home/filten/LongTailQATask/QuestionCreation/gva_fr_bu_output'
    reset(test_data)

    # load disqualified docs
    disqualified_docs = load_disqualified_docs('resources/dis_areum_men.json',
                                               'resources/dis_ngan_men.json',
                                               debug=debug_value)


    # main loop
    all_added = set()

    # load mentions solutions proposed by Roxane
    delete, old2new_eventtype = load_mappings_mentions2solution('resources/InputData_annotation_improvement.xlsx')


    input_path = '{test_data}/system_input/docs.conll'.format_map(locals())
    cache_path = 'cache/conll.bin'
    subtask2conll,\
    token_id2token = load_conll(input_path,
                                cache_path,
                                overwrite=False,
                                debug=debug_value)
    total_num_docs = len(subtask2conll)

    anno_paths = [('areum', 'resources/ann_areum_men.json', 'output/vocab_areum.txt'),
                  ('ngan', 'resources/ann_ngan_men.json', 'output/vocab_ngan.txt')]
    input_annotations = dict()
    user2token_id2anno = dict()
    for user, input_path, output_path in anno_paths:

        user_annotations = json.load(open(input_path))
        input_annotations[user] = user_annotations

        token_id2anno, vocabulary = load_men_annotations(user_annotations,
                                                         token_id2token,
                                                         delete,
                                                         old2new_eventtype,
                                                         disqualified_docs,
                                                         debug=debug_value)

        user2token_id2anno[user] = token_id2anno

        save_vocab_to_file(vocabulary, output_path)

    # compute IAA
    accepted_incidents = {'578238', '492366', '571210', '512274', '501412',
                          '525119', '548991', '517905', '512877', '566863'}
    stats_output_path = 'output/iaa_week5.xlsx'

    IAA(token_id2token, input_annotations, accepted_incidents, stats_output_path)

    for subtask in [
                    's1',
                    's2',
                    's3'
                    ]:

        if debug_value:
            print()
            print('subtask', subtask)

        stats_input = get_q_stats_info(subtask,
                                       total_num_docs)

        stats_output_path = 'test_data/dev_data/%s/stats.json' % subtask

        compute_stats(stats_input, output_path=None, debug=True)

        if subtask == 's1':
            added = to_conll(subtask,
                             subtask2conll,
                             user2token_id2anno,
                             accepted_incidents)

            all_added.update(added)
        else:
            command = 'cp test_data/dev_data/s1/docs.conll test_data/dev_data/%s/docs.conll' % subtask
            try:
                subprocess.check_output(command, shell=True)
            except subprocess.CalledProcessError as e:
                print(e)



    missing = set(token_id2anno) - all_added
    print('added', len(all_added))
    print('missing', len(missing))
    print(missing)

    # create test data for participants (hence without gold data)
    commands = ['rm -rf test_data_gold',
                'cp -r test_data test_data_gold',
                'rm -r test_data/dev_data',
                'cp resources/README.md test_data',
                'cp resources/README_gold.md test_data_gold']

    for command in commands:
        try:
            subprocess.check_output(command, shell=True)
        except subprocess.CalledProcessError as e:
            print(e)

