import itertools
import pandas
from collections import defaultdict
from datetime import datetime
import classes
import hashlib
import pickle


def return_number(participants_info, event_type, target_name, gran, debug=False):
    """

    :param list participants_info: list of dictionaries
    :param str event_type: 'killing' | 'injuring'
    :param str target_name: first name | last name | full name
    :param str gran: first | last | full_name

    :rtype: int
    :return: 0 if not match | 1 if match
    """
    answer = 0

    mapping = {'killing': ' Killed',
               'injuring': ' Injured'}

    wanted = mapping[event_type]

    for part_info in participants_info:

        if all(['Name' in part_info,
                'Status' in part_info]):
            full_name = part_info['Name'].strip()
            if full_name:
                name_parts = full_name.strip().split()
                if len(name_parts) == 2:
                    first, last = name_parts

                    if part_info['Status'] == wanted:

                        if all([gran == 'first',
                                first == target_name]):
                            answer += 1

                            if all([answer == 1,
                                    debug]):
                                print()
                                print(part_info)
                                print(gran, first, target_name)

                        if all([gran == 'last',
                                last == target_name]):
                            answer += 1

                            if all([answer == 1,
                                    debug]):
                                print()
                                print(part_info)
                                print(gran, last, target_name)

                        if all([gran == 'full_name',
                                full_name == target_name]):
                            answer += 1

                            if all([answer == 1,
                                    debug]):
                                print()
                                print(part_info)
                                print(gran, full_name, target_name)

    return answer

def parts_with_only_zero_or_two_parts(participants_info):
    """
    Check if all participants have:
    1) either no name
    2) or names with two parts
    3) but NOT names with one part or 3> parts
    
    :param list participants_info: list of dicts with participant info
    
    :rtype: bool
    :return: True if all names have zero parts or two parts
    False in all other conditions
    """
    accept = True
    for part_info in participants_info:
        
        if all(['Name' in part_info,
                'Status' in part_info]):
            full_name = part_info['Name'].strip()
            if full_name:
                name_parts = full_name.strip().split()
                
                if len(name_parts) == 1:
                    accept = False
                
                if len(name_parts) >= 3:
                    accept = False
    
    return accept


def get_sf_m_dict(row):
    """
    extract surface form and meaning dict from a row
    for both surface forms and meanings, the dictionary will contain:

    Location
    1. state
    2. city
    3. address

    Time
    4. day
    5. month
    6. year

    :rtype: tuple
    :return: (sf_dict, m_dict)
    """
    sf_dict = dict()
    m_dict = dict()

    # surface forms locations
    sf_state = row['state']
    sf_city = row['city_or_county']
    sf_address = row['address']

    sf_dict['state'] = sf_state
    sf_dict['city'] = sf_city
    sf_dict['address'] = sf_address

    # meaning locations
    m_dict['state'] = (sf_state,)
    m_dict['city'] = (sf_state, sf_city)
    m_dict['address'] = (sf_state, sf_city, sf_address)

    # surface forms time
    incident_date = row['date']
    dt = datetime.strptime(incident_date, '%B %d, %Y')
    dt_day = dt.strftime("%d/%m/%Y")
    dt_month = dt.strftime("%m/%Y")
    dt_year = dt.strftime("%Y")

    sf_dict['day'] = dt_day
    sf_dict['month'] = dt_month
    sf_dict['year'] = dt_year

    # meanings time
    m_dict['day'] = (dt_day,)
    m_dict['month'] = (dt_month,)
    m_dict['year'] = (dt_year,)

    return sf_dict, m_dict


def update_sf_m_dict_with_participant(row, part_obj, sf_dict, m_dict):
    """
    update sf_dict and m_dict with participant info

    :param pandas.core.series.Series row: row from GunViolence dataframe
    :param dict part_obj: attributes of a victim/suspect from GunViolence database
    :param dict sf_dict: see output get_sf_m_dict
    :param m_dict m_dict: get_sf_m_dict
    
    :rtype: tuple
    :return: first, last, full_name
    """
    incident_uri = row['incident_uri']
    parts_gran_levels = ['first', 'last', 'full_name']

    for gran_level in parts_gran_levels:
        sf_dict[gran_level] = ''
        m_dict[gran_level] = ''

    full_name = part_obj['Name'].strip()
    first = ''
    last = ''
    if full_name:
        
        # filter out all names with three or more components
        name_parts = full_name.strip().split()
        if len(name_parts) == 2:
            first, last = name_parts
            parts_gran_levels = [('first', first),
                                 ('last', last),
                                 ('full_name', full_name)]
           
            for gran_level, value in parts_gran_levels:

                sf_dict[gran_level] = value
                m_dict[gran_level] = (incident_uri, value)

    return first, last, full_name


def create_look_up(df,
                   discard_ambiguous_names=True,
                   allowed_incident_years={2013, 2014, 2015, 2016, 2017},
                   check_name_in_article=True,
                   only_names_with_two_parts=True):
    """
    create look_up for:
    1. location: state | city | address
    2. participant: first | last | full_name
    3. time: day | month | year
    4. combination of participant, location, and time

    :param df: dataframe containing possibly frames from Gun Violence | FireRescue
    :param bool discard_ambiguous_names: if True, full names that occur in multiple incidents
    will be ignored
    :param set allowed_incident_years: the incident allowed in the question creation
    :param bool check_name_in_article: if True, it will be checked if the full name occur at least once
    on one of the answer documents

    :rtype: tuple
    :return: (look_up, mapping parameters2incident uris)
    """
    main_categories = ['location', 'participant', 'time']

    main_category2gran_level = {
        'location': ['state', 'city', 'address'],
        'participant': ['first', 'last', 'full_name'],
        'time': ['day', 'month', 'year']
    }

    parameters2incident_uris = dict()
    look_up = dict()
    discarded = defaultdict(set)

    if discard_ambiguous_names:
        participant2freq = defaultdict(int)
        for index, row in df.iterrows():
            for part_obj in row['participants']:
                if 'Name' in part_obj:
                    name = part_obj['Name']
                    if name:
                        participant2freq[name] += 1

    gv_news_article_template = '../EventRegistries/GunViolenceArchive/the_violent_corpus/{incident_uri}/{the_hash}.json'
    fr_news_article_template = '../EventRegistries/FireRescue1/firerescue_corpus/{incident_uri}/{the_hash}.json'

    for index, row in df.iterrows():

        # possibly filter incident based on name parts length
        if only_names_with_two_parts:
            accept = parts_with_only_zero_or_two_parts(row['participants'])
            if not accept:
                continue

        # load news sources
        news_article_objs = set()
        for incident_url in row['incident_sources']:
            hash_obj = hashlib.md5(incident_url.encode())
            the_hash = hash_obj.hexdigest()
            incident_uri = row['incident_uri']

            news_article_template = gv_news_article_template
            if incident_uri.startswith('FR'):
                news_article_template = fr_news_article_template

            path = news_article_template.format_map(locals())

            try:
                with open(path, 'rb') as infile:
                    news_article_obj = pickle.load(infile)
                    news_article_objs.add(news_article_obj)
            except FileNotFoundError:
                continue

        incident_uri = row['incident_uri']

        incident_date = datetime.strptime(row['date'], '%B %d, %Y')
        incident_year = incident_date.year

        if incident_year not in allowed_incident_years:
            continue

        sf_dict, m_dict = get_sf_m_dict(row)

        # for number of combinations
        for num_comb in range(1, 4):
            # for the actual combinations of main categories
            for categories in itertools.combinations(main_categories, num_comb):

                if categories not in look_up:
                    look_up[categories] = dict()
                    parameters2incident_uris[categories] = dict()

                # obtain relevant granualirity levels
                gran_levels = [main_category2gran_level[category]
                               for category in categories]

                # all combinations of granularity levels
                for gran_comb in itertools.product(*gran_levels):

                    if gran_comb not in look_up[categories]:
                        look_up[categories][gran_comb] = dict()
                        parameters2incident_uris[categories][gran_comb] = defaultdict(set)

                    # check location
                    if 'location' in categories:

                        address_match = False
                        city_match = False
                        state_match = False
                        for news_article_obj in news_article_objs:
                            if sf_dict['address'] in news_article_obj.content:
                                address_match = True
                            if sf_dict['city'] in news_article_obj.content:
                                city_match = True
                            if sf_dict['state'] in news_article_obj.content:
                                state_match = True

                        # for adress -> address needs to be at least in there
                        if 'address' in gran_comb:
                            if not address_match:
                                discarded['address'].add(incident_uri)
                                continue

                        # for city -> either address or city needs to be at least in there
                        if 'city' in gran_comb:
                            if not any([address_match, city_match]):
                                discarded['city'].add(incident_uri)

                                continue

                        if 'state' in gran_comb:
                            if not any([address_match, city_match, state_match]):
                                discarded['state'].add(incident_uri)
                                continue

                    # without participant
                    if 'participant' not in categories:
                        sf_key = tuple([sf_dict[gran_level] for gran_level in gran_comb])
                        if any([item in {'', 'N/A'} for item in sf_key]):
                            continue

                        if sf_key not in look_up[categories][gran_comb]:
                            look_up[categories][gran_comb][sf_key] = defaultdict(set)

                        parameters2incident_uris[categories][gran_comb][sf_key].add(incident_uri)

                        m_key = tuple(m_dict[gran_level] for gran_level in gran_comb)
                        look_up[categories][gran_comb][sf_key][m_key].add(incident_uri)

                    # with participant
                    else:  # hence participant in categories
                        for part_obj in row['participants']:
                            if 'Name' in part_obj:

                                if discard_ambiguous_names:
                                    if all([part_obj['Name'],
                                            participant2freq[part_obj['Name']] >= 2
                                            ]):
                                        continue

                                # update sf_dict m_dict with participant info
                                first, last, full = update_sf_m_dict_with_participant(row, part_obj, sf_dict, m_dict)

                                # SF_KEY M_KEY + UPDATE DICTIONARY
                                sf_key = tuple([sf_dict[gran_level] for gran_level in gran_comb])
                                if any([item in {'', 'N/A'} for item in sf_key]):
                                    continue

                                # check if name actually occurs in documents
                                if check_name_in_article:
                                    match = False
                                    for news_article_obj in news_article_objs:
                                        if full in news_article_obj.content:
                                            match = True

                                    if not match:
                                        continue

                                if sf_key not in look_up[categories][gran_comb]:
                                    look_up[categories][gran_comb][sf_key] = defaultdict(set)

                                parameters2incident_uris[categories][gran_comb][sf_key].add(incident_uri)

                                m_key = tuple(m_dict[gran_level] for gran_level in gran_comb)
                                look_up[categories][gran_comb][sf_key][m_key].add(incident_uri)


    #print('ignored due to locational expressions not occuring in gold docs')
    #for key, value in discarded.items():
    #    print(key, len(value))

    return look_up, parameters2incident_uris


if __name__ == "__main__":
    frames = ['mass_shootings',
              'mass_shootings_2013',
              'mass_shootings_2014',
              'mass_shootings_2015']
    look_up, parameters2incident_uris = create_look_up(frames)
