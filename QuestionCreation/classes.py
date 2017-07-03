import metrics
import datetime
import pickle
import hashlib
import spacy_to_naf
from lxml import etree
from spacy.en import English
from collections import defaultdict
import json
import os

nlp = English()

def get_sources(dataframe):
    """
    extract sources


    :param pandas.core.frame.DataFrame dataframe:

    :rtype: set
    :return: set of archive.org links
    """
    sources = set()
    for index, row in dataframe.iterrows():
        sources.update(row['incident_sources'].keys())
    return sources

def get_dcts(dataframe):
    """
    set of datetime objects

    :param pandas.core.frame.DataFrame dataframe:

    :rtype: list
    :return: list of datetime.date instances
    """
    dcts = []
    for index, row in dataframe.iterrows():
        for date in row['incident_sources'].values():
            if type(date) == datetime.date:
                dcts.append(date)

    dcts = [datetime.datetime(d.year, d.month, d.day)
            for d in dcts]

    return dcts


def text2conll_one_file(outfile, doc_id, discourse, text, pre=False):
    """
    use spacy to output text (tokenized) in conll

    :param _io.TextIOWrapper outfile: outfile
    :param str doc_id: document identifier
    :param str discourse: TITLE | BODY
    :param str text: content (either title or context of news article)
    """
    doc = spacy_to_naf.text_to_NAF(text, nlp)

    for wf_el in doc.xpath('text/wf'):
        sent_id = wf_el.get('sent')
        token_id = wf_el.get('id')[1:]
        id_ = f'{doc_id}.{sent_id}.{token_id}'

        if pre:
            info = [id_, wf_el.get('offset'), wf_el.get('length')]
            outfile.write('\t'.join(info) + '\n')
        else:
            info = [id_, wf_el.text, discourse, '-']
            outfile.write('\t'.join(info) + '\n')


class Question:
    """
    represents one instance of a question
    with metrics valued computed
    """

    def __init__(self,
                 q_id,
                 confusion_factors,
                 granularity,
                 sf,
                 meanings,
                 gold_loc_meaning,
                 answer,
                 oa_info,
                 answer_df,
                 answer_incident_uris,
                 confusion_df,
                 confusion_incident_uris):
        self.q_id = int(q_id)
        self.confusion_factors = confusion_factors
        self.granularity = granularity
        self.sf = sf
        self.meanings = meanings
        self.gold_loc_meaning = gold_loc_meaning
        self.answer = answer
        self.oa_info = oa_info
        self.answer_df = answer_df
        self.answer_incident_uris = answer_incident_uris
        self.confusion_df = confusion_df
        self.confusion_incident_uris = confusion_incident_uris
        self.to_include_in_task = True

    @property
    def participant_confusion(self):
        return 'participant' in self.confusion_factors

    @property
    def time_confusion(self):
        return 'time' in self.confusion_factors

    @property
    def location_confusion(self):
        return 'location' in self.confusion_factors

    @property
    def num_both_sf_overlap(self):
        return len(self.meanings)

    def question(self, subtask, event_types, debug=False):

        system_input = {'subtask': subtask,
                        'event_types': event_types}

        time_chunk = ''
        location_chunk = ''
        participant_chunk = ''

        for index, (confusion_factor, a_sf) in enumerate(zip(self.confusion_factors,
                                                             self.sf)):
            if confusion_factor == 'time':
                time_chunk = 'in %s (%s) ' % (self.sf[index], self.granularity[index])
                system_input['time'] = (self.sf[index], self.granularity[index])
            elif confusion_factor == 'location':
                location_chunk = 'in %s (%s) ' % (self.gold_loc_meaning, self.granularity[index])
                gran_level = self.granularity[index]
                all_dbpedia_links = {row['locations'][gran_level]
                                     for index, row in self.answer_df.iterrows()
                                     if gran_level in row['locations']}

                if len(all_dbpedia_links) == 1:
                    the_dbpedia_link = all_dbpedia_links.pop()
                    system_input['location'] = (the_dbpedia_link, gran_level)
                else:
                    print('multiple or no dbpedia options for %s: %s' % (self.q_id, all_dbpedia_links))
                    system_input['location'] = (None, None)
                    self.to_include_in_task = False

            elif confusion_factor == 'participant':
                participant_chunk = 'that involve the name %s (%s) ' % (self.sf[index], self.granularity[index])
                system_input['participant'] = (self.sf[index], self.granularity[index])

        the_question = 'How many {event_types} events happened {time_chunk}{location_chunk}{participant_chunk}?'.format_map(locals())

        if debug:
            print(the_question)

        self.verbose_question = the_question.strip()

        if self.to_include_in_task:
            system_input['verbose_question'] = self.verbose_question
            return system_input
        else:
            return None

    @property
    def c2s_ratio(self):
        confusion_e = self.confusion_incident_uris
        answer_e = self.answer_incident_uris
        return metrics.get_ratio___confusion_e2answer_e(confusion_e,
                                                        answer_e)

    @property
    def a_sources(self):
        return get_sources(self.answer_df)

    @property
    def a_avg_num_sources(self):
        return len(self.a_sources) / len(self.answer_incident_uris)

    @property
    def num_a_sources(self):
        return len(self.a_sources)

    @property
    def c_sources(self):
        return get_sources(self.confusion_df)

    @property
    def num_c_sources(self):
        return len(self.c_sources)

    @property
    def c_avg_num_sources(self):
        if self.confusion_incident_uris:
            return len(self.c_sources) / len(self.confusion_incident_uris)
        else:
            return 0

    @property
    def a_avg_date_spread(self):
        sources_dcts = get_dcts(self.answer_df)
        return metrics.get_dct_spread(sources_dcts)

    @property
    def c_avg_date_spread(self):
        confusion_dcts = get_dcts(self.confusion_df)
        return metrics.get_dct_spread(confusion_dcts)

    def oa(self, confusion_factor):
        try:
            confusion_index = self.confusion_factors.index(confusion_factor)
        except ValueError:
            return 0

        return len({meaning[confusion_index]
                            for meaning in self.meanings})

    @property
    def loc_oa(self):
        return self.oa('location')

    @property
    def time_oa(self):
        return self.oa('time')

    @property
    def gvdb_annotations(self):
        gvdb_objects = set()
        for index, row in self.answer_df.iterrows():
            if row['gvdb_annotation']:
                for archive_org_link, gvdb_annotation in row['gvdb_annotation'].items():
                    gvdb_instance = GVDB(gvdb_annotation)
                    gvdb_objects.add(gvdb_instance)

        return gvdb_objects

    @property
    def num_gvdb_part_annotations(self):
        total = 0
        for gvdb_instance in self.gvdb_annotations:
            total += gvdb_instance.num_victim_annotations
            total += gvdb_instance.num_shooter_annotations

        return total


    def to_conll_one_file_per_question(self, dfs, output_path, debug=False):
        """
        create one conll file per question, which serves as input file
        for task participants

        :param list dfs: [('gold', gold_df), ('confusion', confusion_df)]
        :param str output_path: output path where conll file will be stored
        :param bool debug: set to True for debugging
        """
        news_article_template = '../EventRegistries/GunViolenceArchive/the_violent_corpus/{incident_uri}/{the_hash}.json'

        outfile = open(output_path, 'w')
        self.all_doc_ids = defaultdict(list)

        for type_df, df in dfs:
            for index, row in df.iterrows():
                for source_url in row['incident_sources']:
                    hash_obj = hashlib.md5(source_url.encode())
                    the_hash = hash_obj.hexdigest()
                    incident_uri = row['incident_uri']

                    path = news_article_template.format_map(locals())
                    try:
                        with open(path, 'rb') as infile:
                            news_article_obj = pickle.load(infile)
                    except FileNotFoundError:
                        continue

                    if type_df == 'gold':
                        self.all_doc_ids[incident_uri].append(source_url)

                    # write begin document
                    outfile.write('#begin document ({the_hash});\n'.format_map(locals()))

                    # write dct
                    info = [the_hash + '.DCT', str(news_article_obj.dct), 'DCT', '-']
                    outfile.write('\t'.join(info) + '\n')

                    # write title
                    text2conll_one_file(outfile, the_hash, 'TITLE', news_article_obj.title)

                    # write body
                    text2conll_one_file(outfile, the_hash, 'BODY', news_article_obj.content)


                    # write end document
                    outfile.write('#end document\n')

        outfile.close()






    def to_conll(self, a_df, output_folder, debug=False):
        """
        given a pandas dataframe, convert articles to conll

        :param pandas.core.frame.DataFrame a_df:
        :param str output_folder: the output folder
        """
        news_article_template = '../EventRegistries/GunViolenceArchive/the_violent_corpus/{incident_uri}/{the_hash}.json'
        path_doc_id2article = f'{output_folder}/pre/doc_id2article_url.json'

        if not os.path.exists(path_doc_id2article):
            doc_id2article = dict()
        else:
            doc_id2article = json.load(open(path_doc_id2article))


        for index, row in a_df.iterrows():

            # load news sources
            news_article_objs = set()
            for source_url in row['incident_sources']:
                hash_obj = hashlib.md5(source_url.encode())
                the_hash = hash_obj.hexdigest()
                incident_uri = row['incident_uri']

                path = news_article_template.format_map(locals())

                try:
                    with open(path, 'rb') as infile:
                        news_article_obj = pickle.load(infile)
                        news_article_objs.add(news_article_obj)

                        phase = 'pre'
                        doc_id = the_hash

                        content_type = 'body'
                        output_path = f'{output_folder}/{phase}/{doc_id}.{content_type}.conll'
                        text2conll(output_path, the_hash, news_article_obj.content)

                        content_type = 'title'
                        output_path = f'{output_folder}/{phase}/{doc_id}.{content_type}.conll'
                        text2conll(output_path, the_hash, news_article_obj.title)

                        content_type = 'dct'
                        phase = 'post'
                        output_path = f'{output_folder}/{phase}/{doc_id}.{content_type}.conll'
                        with open(output_path, 'w') as outfile:
                            outfile.write(str(news_article_obj.dct))

                        doc_id2article[the_hash] = source_url

                        hash_obj = hashlib.md5(news_article_obj.content.encode())
                        content_hash = hash_obj.hexdigest()

                        hash_obj = hashlib.md5(news_article_obj.title.encode())
                        title_hash = hash_obj.hexdigest()

                        content_type = 'checksum'
                        phase = 'pre'
                        output_path = f'{output_folder}/{phase}/{doc_id}.{content_type}.conll'

                        print(incident_uri)
                        input('continue?')
                        checksum_info = {'title': title_hash,
                                         'incident_id' : row['incident_uri'],
                                         'body': content_hash}

                        with open(output_path, 'w') as outfile:
                            json.dump(checksum_info, outfile)


                        if debug:
                            break

                except FileNotFoundError:
                    continue

        with open(path_doc_id2article, 'w') as outfile:
            json.dump(doc_id2article, outfile)


    def set_all_attributes(self):
        vars(self)


class GVDB:
    """
    compute stats about gun violence database annotation
    """

    def __init__(self, gvdb_info):
        self.gvdb_info = gvdb_info

    @property
    def city(self):
        value = self.gvdb_info['date-and-time']['city']['value']
        city = None
        if value:
            city = value

        return city

    @property
    def date(self):
        value = self.gvdb_info['date-and-time']['date']

        date = None
        if value:
            date = datetime.datetime.strptime(value, '%Y-%m-%d')

        return date

    @property
    def state(self):
        value = self.gvdb_info['date-and-time']['state']

        state = None
        if value:
            state = value

        return state

    def num_part_annotations(self, key):
        num_annotations = 0
        for victim_annotation in self.gvdb_info[key]:

            for category, annotation in victim_annotation.items():
                if type(annotation) == dict:
                    if annotation['startIndex'] != -1:
                        num_annotations += 1

        return num_annotations

    @property
    def num_victim_annotations(self):
        return self.num_part_annotations('victim-section')

    @property
    def num_shooter_annotations(self):
        return self.num_part_annotations('shooter-section')


class NewsItem:

    def __init__(self, title='',
                 content='',
                 dct='', id=None,
                 uri=''):
        self.title=title
        self.content=content
        self.dct=dct
        self.id=id
        self.uri=uri

    def toJSON(self, targetFile):
        pickle.dump(self, open(targetFile, 'wb'))
