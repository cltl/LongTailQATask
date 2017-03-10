import itertools
import pandas
from collections import defaultdict
from nameparser import HumanName
from datetime import datetime


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
    """
    incident_uri = row['incident_uri']
    parts_gran_levels = ['first', 'last', 'full_name']

    for gran_level in parts_gran_levels:
        sf_dict[gran_level] = ''
        m_dict[gran_level] = ''

    full_name = part_obj['Name']
    if full_name:
        name_obj = HumanName(full_name)

        for gran_level in parts_gran_levels:
            value = getattr(name_obj, gran_level)

            sf_dict[gran_level] = value
            m_dict[gran_level] = (incident_uri, value)


def create_look_up(df):
    """
    create look_up for:
    1. location: state | city | address
    2. participant: first | last | full_name
    3. time: day | month | year
    4. combination of participant, location, and time

    :param df: dataframe containing possibly frames from Gun Violence | FireRescue

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

    for index, row in df.iterrows():

        incident_uri = row['incident_uri']
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
                                # update sf_dict m_dict with participant info
                                update_sf_m_dict_with_participant(row, part_obj, sf_dict, m_dict)

                                # SF_KEY M_KEY + UPDATE DICTIONARY
                                sf_key = tuple([sf_dict[gran_level] for gran_level in gran_comb])
                                if any([item in {'', 'N/A'} for item in sf_key]):
                                    continue

                                if sf_key not in look_up[categories][gran_comb]:
                                    look_up[categories][gran_comb][sf_key] = defaultdict(set)

                                parameters2incident_uris[categories][gran_comb][sf_key].add(incident_uri)

                                m_key = tuple(m_dict[gran_level] for gran_level in gran_comb)
                                look_up[categories][gran_comb][sf_key][m_key].add(incident_uri)

    return look_up, parameters2incident_uris


if __name__ == "__main__":
    frames = ['mass_shootings',
              'mass_shootings_2013',
              'mass_shootings_2014',
              'mass_shootings_2015']
    look_up, parameters2incident_uris = create_look_up(frames)
