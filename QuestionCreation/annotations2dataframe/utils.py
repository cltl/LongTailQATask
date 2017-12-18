import json
import pickle
import pandas
from datetime import datetime
from datetime import date

class NewsItem:

    def __init__(self, title='',
                 content='',
                 dct='',
                 id=None,
                 uri=''):
        self.title = title
        self.content = content
        self.dct = dct
        self.id = id
        self.uri = uri

    def toJSON(self, targetFile):
        pickle.dump(self, open(targetFile, 'wb'))

def open_json(path, prefix=None, debug=False):
    """
    load json [and only keep  keys that start with prefix]

    :param str path: path to json file
    :param str prefix: if provided, only keys that start with
    prefix will be added

    :rtype: dict
    :return: mapping key -> value
    """
    dictionary = json.load(open(path))

    if debug:
        print()
        print('loaded', path)
        print('before (all prefixes)', len(dictionary))

    new_dictionary = dict()
    for key, value in dictionary.items():

        if debug == 2:
            print(key, value)

        if not prefix:
            new_dictionary[key] = value

        else:
            if key.startswith(prefix):
                new_dictionary[key] = value

    if debug:
        print('after (only prefix: %s)' % prefix, len(new_dictionary))

    return new_dictionary

def document_quality(body, title):
    """
    check document quality with respect to

    :param list body: list of strings (representing sentences)
    a. first sentence should be longer than two tokens
    b. number of characters in body should be between 300 and 4000
    :param str title: title of article

    :rtype: body, title, reason (if it fails)
    """
    include = False
    reason = None

    # number of characters check
    if not body:
        return None, None, 'num_characters'

    # first sentence check
    first_sentence = body[0]
    if first_sentence:
        tokens = first_sentence.split()

        if tokens:
            if all([len(tokens) <= 5,
                    tokens[0] == 'At']):
                return None, None, 'first sentence too short'

    # again number of characters check
    cleaned_body = []
    num_tokens = 0
    for sentence in body:
        if sentence:
            for _ in sentence.split():
                num_tokens += 1

            cleaned_body.append(sentence)

    if num_tokens not in range(100, 4000):
        return None, None, 'not in character range: %s' % num_tokens


    the_cleaned_body = '\n'.join(cleaned_body)

    return the_cleaned_body, title, 'succes'


# In[6]:

def get_disqualified(dis_info, debug=False):
    """
    given a dict:
    {"FR102920":["FR102920_1"],"FR102640":["FR102640_1"]}

    return identifiers that have a disqualified document in them

    :param dict dis_info: see above

    :rtype: set
    :return: set of identifiers
    """
    disqualified = set()

    for id_, doc_info in dis_info.items():
        if doc_info:
            disqualified.add(id_)

    return disqualified


def fr_time_key(incident_date):
    """
    convert incident_date to dict (dt_day, dt_month, dt_year)

    :param str incident_date: e.g. "November 28, 2001"

    :rtype: dict
    :return: mapping dt_day, dt_month, dt_year to strings
    """
    dt = datetime.strptime(incident_date, '%B %d, %Y')
    dt_day = dt.strftime("%d/%m/%Y")
    dt_month = dt.strftime("%m/%Y")
    dt_year = dt.strftime("%Y")

    time_dict = {
        'dt_day': dt_day,
        'dt_month': dt_month,
        'dt_year': dt_year
    }

    return time_dict


result = {'dt_day': '28/11/2001', 'dt_month': '11/2001', 'dt_year': '2001'}
assert fr_time_key(incident_date="November 28, 2001") == result


def time_key(date):
    """
    given a date, create mapping dt_day, dt_month, dt_year to strings

    :param str date: y or y-m or y-m-d

    :rtype: dict
    :return: mapping dt_day, dt_month, dt_year to strings
    """
    time_dict = {
        'dt_day': None,
        'dt_month' : None,
        'dt_year': None
    }

    if not date:
        return time_dict

    year, *reste = date.split('-')
    assert len(year) == 4, 'year should have 4 characters: %s (date: %s)' % (year, date)

    time_dict = {
        'dt_day': None,
        'dt_month': None,
        'dt_year': year
    }

    if len(reste) >= 1:
        month = reste[0]
        assert len(month) == 2, 'month should have 2 characters: %s' % month

        time_dict['dt_month'] = '{month}/{year}'.format_map(locals())

    if len(reste) == 2:
        day = reste[1]
        assert len(day) == 2, 'day should have 2 characters: %s' % day

        time_dict['dt_day'] = '{day}/{month}/{year}'.format_map(locals())

    return time_dict


assert time_key('2006-02-02') == {'dt_day': '02/02/2006', 'dt_month': '02/2006', 'dt_year': '2006'}
assert time_key('2006-02') == {'dt_day': None, 'dt_month': '02/2006', 'dt_year': '2006'}
assert time_key('2006') == {'dt_day': None, 'dt_month': None, 'dt_year': '2006'}



def fr_annotations_to_json(df,
                           anno_marten,
                           anno_filip,
                           ids_dis_marten,
                           agreement_info,
                           debug=False):
    """
    convert firerescue df to json format
    inc_id ->
     * "time" : separated by dashes
     * "location": starting with https://en.wikipedia.org/wiki/
     * "participants": names separated by comma's
     * "numparticipants" : integer as string
     * "articles": list of
         * "source" source url
         * "dct": dct
         * "title" title
         * "content" : content

    :param anno_marten:
    :param anno_filip:
    :param ids_dis_marten:
    :param agreement_info:

    :rtype: dict
    :return: see top of docstring
    """
    if debug:
        print()
        print('fire rescue info:')
        print()

    inc_id2inc_info = dict()

    for index, row in df.iterrows():

        id_ = row['incident_uri']
        if id_ in anno_marten:

            m_anno_info = anno_marten[id_]

            # move on if disqualified
            if id_ in ids_dis_marten:
                continue

            location_match = True
            time_match = True

            if id_ in anno_filip:
                f_anno_info = anno_filip[id_]

                for key in ['time', 'location']:

                    if f_anno_info[key] != m_anno_info[key]:

                        # use disagreement info
                        if agreement_info[id_] == 'discard':

                            if debug >= 1:
                                print(id_, 'discarded')

                            if key == 'time':
                                time_match = False
                            elif key == 'location':
                                location_match = False

            time = m_anno_info['time']
            location = m_anno_info['location']

            if id_ in agreement_info:
                if agreement_info[id_] == 'filip':
                    if debug >= 1:
                        print(id_, 'used annotations filip')

                    time = f_anno_info['time']
                    location = f_anno_info['location']

            if all([location,
                    location_match,
                    time,
                    time_match]):

                reporting_date = row['incident_reporting_date']
                reporting = date(reporting_date.year,
                                 reporting_date.month,
                                 reporting_date.day)

                articles = [{'title' : row['title'],
                             'dct' : reporting,
                             'source': row['source_url'],
                             'content': row['incident']}]

                inc_id2inc_info[id_] = {
                    'time' : time,
                    'location' : location,
                    'participants' : '',
                    'numparticipants' : '',
                    'articles' : articles
                }


    if debug >= 1:
        print('fr json #', len(inc_id2inc_info))

    return inc_id2inc_info


def date_string2date_obj(date_string):
    """
    given datestring of either:
    a) "2015-09-01T22:23:50Z"
    b) "2015-09-24"

    return a datetime.date object

    :rtype: datetime.date
    :return: datetime.date object
    """

    target = date_string[:10]
    year, month, day = target.split('-')

    date_obj = date(int(year), int(month), int(day))

    return date_obj


assert date_string2date_obj('2015-09-24') == date(2015, 9, 24)
assert date_string2date_obj('2015-09-01T22:23:50Z') == date(2015, 9, 1)


def key_participants(participant_names):
    """
    create list of participants info

    :param str participant_names: e.g. 'Hugh Britton, Tom Cruise'

    :rtype: list
    :return: list of dicts, e.g.
    [{'Name': 'Hugh Britton', 'Status': ' unemployed'},
     {'Name': 'Tom Cruise', 'Status': ' unemployed'}]


    """
    participants = []

    if not participant_names.strip():
        return participants

    for participant_name in participant_names.split(','):
        part_info = {
            'Name': participant_name.strip(),
            'Status': ' unemployed'
        }

        participants.append(part_info)

    return participants


assert key_participants('Hugh Britton, Tom Cruise') == [{'Name': 'Hugh Britton', 'Status': ' unemployed'},
                                                        {'Name': 'Tom Cruise', 'Status': ' unemployed'}]
assert key_participants('') == []


def load_reftexts(path_ref_texts_json):
    """
    load articles from ref_texts.json

    :param str path_ref_texts_json: path to ref_texts.json

    :rtype: dict
    :return: id_ -> list of dicts (each representing an article)
    """
    reference_texts = json.load(open(path_ref_texts_json))
    id2reftexts = dict()
    for identifier, texts in reference_texts.items():
        id_ = identifier.split(':')[3]
        articles = eval(texts)
        id2reftexts[id_] = articles
    return id2reftexts


def load_gva_dummy_json(path_to_annotations_in_excel,
                        path_bu_original_json,
                        path_bu_annotations,
                        path_gva_all_df,
                        id2reftexts,
                        debug=False):
    """
    load the_json with annotations about dummy gva incidents

    :param str path_to_annotations_in_excel: download excel export of
    https://docs.google.com/spreadsheets/d/1IebhyY630trX648X_Q-mXHk91qyh4YRYeaYEQBlv4E0/edit#gid=0
    :param str path_bu_original_json: path to json with bu articles
    :param str path_bu_annotations: path to json with bu annotations
    :param str path_gva_all_df: df with all gva incidents
    :param dict id2reftexts: output load_reftexts
    """
    df = pandas.read_excel(path_to_annotations_in_excel,
                           sheetname='GVA dummy')
    bu_original = json.load(open(path_bu_original_json))
    bu_annotations = json.load(open(path_bu_annotations))
    gva_all_df = pandas.read_pickle(path_gva_all_df)

    the_json = dict()

    for index, row in df.iterrows():

        id_ = row['Incident ID']
        info = dict()

        # check if in BU
        if all([id_ in bu_annotations,
                debug]):
            print(id_, 'also in BU annotations')

        # time
        time = row['Time']
        info['time'] = time

        # location
        location = row['Location']
        if type(location) == float:
            location = ''
        info['location'] = location

        # num killed and injured
        info['num_killed'] = int(row['Num of ppl killed'])
        info['num_injured'] = int(row['Num of ppl injured'])

        # participants
        participants = []

        if type(row['Names of Killed people']) == str:
            part_info = {
                'Name': row['Names of Killed people'],
                'Status': ' Killed'
            }

            participants.append(part_info)

        if type(row['Names of Injured people']) == str:
            part_info = {
                'Name': row['Names of Injured people'],
                'Status': ' Injured'
            }

            participants.append(part_info)

        info['participants'] = participants

        # reference texts
        articles = []

        if id_ in id2reftexts:
            ref_texts = id2reftexts[id_]
            articles.extend(ref_texts)

        articles_key = 'incinitstr:' + id_
        if articles_key in bu_original:
            original_info = eval(bu_original[articles_key])
            bu_articles = original_info['articles']
            articles.extend(bu_articles)

        assert articles, (id_ + ' does not have articles')

        info['articles'] = articles

        # create new id
        new_id = id_[2:]

        for count, article in enumerate(articles, 1):

            if 'body' in article:
                article['content'] = article['body']
                del article['body']

            if 'source' not in article:
                article['source'] = new_id + '_' + str(count)

        the_json[new_id] = info

    return the_json


def check_overlap_gva_and_dummy_gva(path_gva_all_df,
                                    the_json):
    """
    check if there are dummy gva incidents
    that are coreferential with gva incidents

    info about incidents that share the day are printed
    and to be checked manually

    :param str path_gva_all_df: df with all gva incidents
    :param dict the_json: see output load_gva_dummy_json

    """
    gva_all_df = pandas.read_pickle(path_gva_all_df)

    for index, row in gva_all_df.iterrows():
        gva_date_obj = fr_time_key(row['date'])

        for dummy_gva_info in the_json.values():
            gva_dummy_obj = time_key(dummy_gva_info['time'])

            if gva_date_obj['dt_day'] == gva_dummy_obj['dt_day']:
                print()
                print('matching date, inspect manually')
                print('GVA', row['date'], row['city_or_county'])
                print('GVA dummy', dummy_gva_info['time'], dummy_gva_info['location'])


def create_df(the_json, debug=False):
    """

    :param the_json:
    :return:
    """
    no_time_loc = 0

    for value in the_json.values():
        if not value['time'] and not value['location']:
            no_time_loc += 1

        for article in value['articles']:
            article['dct'] = date_string2date_obj(article['dct'])

    if debug >= 1:
        print()
        print('# incidents', len(the_json))
        print('# no time loc', no_time_loc)
        print('# potential ones', len(the_json) - no_time_loc)

    list_of_lists = [[incident_uri]
                     for incident_uri in the_json]
    headers = ['incident_uri']
    df = pandas.DataFrame(list_of_lists, columns=headers)
    df['incident_sources'] = [dict() for _ in df.iterrows()]
    df['address'] = [None for _ in df.iterrows()]
    df['city_or_county'] = [None for _ in df.iterrows()]
    df['state'] = [None for _ in df.iterrows()]

    return df