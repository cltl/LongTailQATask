import argparse
import pandas
import json
import os
import hashlib
import sys
import os

import utils
from utils import NewsItem
import sparql_utils

parser = argparse.ArgumentParser(description='Insert structured data annotations into dataframe')
parser.add_argument('-i', dest='path_input', required=True, help='path to input dataframe')
parser.add_argument('-pr', dest='prefix', required=True, help='supported: FR | BU | GVA_dummy')
parser.add_argument('-fa', dest='path_filip_anno', required=True, help='path to annotations filip')
parser.add_argument('-fd', dest='path_filip_dis', required=True, help='path to disqualifications filip')
parser.add_argument('-ma', dest='path_marten_anno', required=True, help='path to annotations marten')
parser.add_argument('-md', dest='path_marten_dis', required=True, help='path to disqualifications marten')
parser.add_argument('-dis', dest='path_to_agreement', required=True, help='path to json with agreement info')
parser.add_argument('-oc', dest='path_output_corpus', required=True, help='path to where output corpus is stored')
parser.add_argument('-od', dest='path_output_df', required=True, help='path where output df will be stored')
parser.add_argument('-d', dest='debug_value', default=0, type=int, help='supported: 0 1 2')
parser.add_argument('--rt', dest='path_ref_texts_json', nargs='?', const='', help='path where reference texts are stored')
parser.add_argument('--bo', dest='path_bu_original_json', nargs='?', const='', help='path where BU documents are stored')
parser.add_argument('--ba', dest='path_bu_annotations', nargs='?', const='', help='path where BU annotations are stored')
parser.add_argument('--df', dest='path_gva_all_df', nargs='?', const='', help='path to gva df all')
args = parser.parse_args()

if args.debug_value >= 1:
    print()
    print('arguments:')
    for key, value in args.__dict__.items():
        if not value:
            continue
        print(key, value)
        if all([key.startswith('path'),
                key != 'path_output_df']):
            assert os.path.exists(value), 'path: %s does not exist' % value

## loading of dataframe
if args.prefix == 'FR':
    df = pandas.read_pickle(args.path_input)

    if args.debug_value >= 1:
        print()
        print('loaded', args.path_input)
        print('num rows', len(df))

## load annotations
if args.prefix in {'FR', 'BU'}:
    anno_filip = utils.open_json(args.path_filip_anno, prefix=args.prefix, debug=args.debug_value)
    anno_marten = utils.open_json(args.path_marten_anno, prefix=args.prefix, debug=args.debug_value)
    dis_filip = utils.open_json(args.path_filip_dis, prefix=args.prefix, debug=args.debug_value)
    dis_marten = utils.open_json(args.path_marten_dis, prefix=args.prefix, debug=args.debug_value)

if args.prefix == 'FR':
    # load disqualified
    ids_dis_marten = utils.get_disqualified(dis_marten)
    ids_dis_filip = utils.get_disqualified(dis_filip)

    # check if we agree
    overlap = set(ids_dis_filip) & set(ids_dis_marten)
    assert overlap == set(ids_dis_filip), 'there are dis ids by filip that were not noticed by marten'


# load mapping inc_id to info
agreement_info = json.load(open(args.path_to_agreement))

if args.prefix == 'FR':
    the_json = utils.fr_annotations_to_json(df,
                                            anno_marten,
                                            anno_filip,
                                            ids_dis_marten,
                                            agreement_info,
                                            debug=args.debug_value)
elif args.prefix == 'BU':
    the_json = json.load(open(args.path_input))
    df = utils.create_df(the_json, args.debug_value)


elif args.prefix == 'GVA_dummy':

    id2reftexts = utils.load_reftexts(args.path_ref_texts_json)

    the_json = utils.load_gva_dummy_json(args.path_input,
                                         args.path_bu_original_json,
                                         args.path_bu_annotations,
                                         args.path_gva_all_df,
                                         id2reftexts,
                                         debug=args.debug_value)

    utils.check_overlap_gva_and_dummy_gva(args.path_gva_all_df,
                                          the_json)

    df = utils.create_df(the_json, debug=args.debug_value)


# insert information into df
# TODO: improve locations key for missed cities and states

df['date'] = [None for index, row in df.iterrows()]
df['locations'] = [None for index, row in df.iterrows()]
df['participants'] = [[] for index, row in df.iterrows()]

num_docs = 0

for index, row in df.iterrows():
    id_ = row['incident_uri']

    if id_ in the_json:
        anno_info = the_json[id_]

        # reference texts
        incident_sources = dict()

        for ref_text_info in anno_info['articles']:

            body = ref_text_info['content']
            title = ref_text_info['title']
            source = ref_text_info['source']
            dct = ref_text_info['dct']

            if args.prefix == 'FR':
                body, title, reason = utils.document_quality(body,
                                                             title)
                if reason != 'succes':
                    continue

            incident_sources[source] = dct

            # save reference text to file
            hash_obj = hashlib.md5(ref_text_info['source'].encode())
            the_hash = hash_obj.hexdigest()
            incident_uri = id_
            out_dir = '%s/%s' % (args.path_output_corpus, incident_uri)
            out_path = '%s/%s/%s.json' % (args.path_output_corpus, incident_uri, the_hash)

            if not os.path.isdir(out_dir):
                os.mkdir(out_dir)

            news_item_obj = NewsItem(title=title,
                                     content=body,
                                     dct=dct)

            news_item_obj.toJSON(out_path)
            num_docs += 1

        # add incident_sources column
        df.set_value(index, 'incident_sources', incident_sources)

        # locations
        location = anno_info['location']

        if location in sparql_utils.location2locations:
            locations = sparql_utils.location2locations[location]
            if args.debug_value >= 1:
                print()
                print('loaded locations from manual dict')
                print('for', location)
                print('retrieved', locations)
        else:
            locations = sparql_utils.key_locations(location)
        df.set_value(index, 'locations', locations)

        if locations['city']:
            city_label = sparql_utils.get_label(locations['city'], debug=args.debug_value)
            df.set_value(index, 'city_or_county', city_label)

        if locations['state']:
            state_label = sparql_utils.get_label(locations['state'], debug=args.debug_value)
            df.set_value(index, 'state', state_label)

        # date
        time_dict = utils.time_key(anno_info['time'])
        df.set_value(index, 'date', time_dict)

        if args.prefix == 'BU':
            participants = utils.key_participants(anno_info['participants'])
            df.set_value(index, 'participants', participants)

        if args.prefix == 'GVA_dummy':
            participants = anno_info['participants']
            df.set_value(index, 'participants', participants)



if args.debug_value >= 1:
    columns = set(df.columns)
    needed = {'incident_uri',
              'state',
              'city_or_county',
              'address',
              'date',
              'incident_sources',
              'participants'}

    missing = needed - columns
    assert missing == set(), 'missing columns: %s' % missing

# write df to disk
if args.debug_value:

    print('columns', df.columns)

    counter = 0
    for index, row in df.iterrows():
        if all([row['locations'],
                row['state'] or row['city_or_county'],
                row['date'],
                row['incident_sources']]):
            counter += 1

    print()
    print('written to', args.path_output_df)
    print('total incident count:', counter)
    print('# docs', num_docs)

if args.prefix in {'BU', 'FR'}:
    df.to_pickle(args.path_output_df)
elif args.prefix == 'GVA_dummy':

    gva_df = pandas.read_pickle(args.path_gva_all_df)
    merged_df = pandas.concat([gva_df, df])

    if args.debug_value:
        print()
        print(df['incident_uri'])
        print('# dummy gva', len(df))
        print('# gva', len(gva_df))
        print('# merged', len(merged_df))

    merged_df.to_pickle(args.path_output_df)







