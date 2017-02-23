# # Limitations
# * nameparser is not always correct wrt middle vs last name

# # Requirements
# * install **nameparser**

import pandas
from collections import defaultdict
#from nameparser import HumanName


def create_look_up(frames):
    """
    create look_up for:
    1. location: state | city | address
    2. participant: first | last | full_name
    3. combination of participant and location

    :param frames: categories of gunviolence to consider

    :rtype: tuple
    :return: (look_up, mapping parameters2incident uris)
    """
    df = pandas.concat([pandas.read_pickle('../EventRegistries/GunViolence/frames/' + frame)
                        for frame in frames])

    print(df)
    look_up = {
        ('location',): {
            'state': defaultdict(dict),
            'city' : defaultdict(dict),
            'address' : defaultdict(dict)
        },
        ('participant',): {
            'first' : defaultdict(dict),
            'last' : defaultdict(dict),
            'full_name' : defaultdict(dict)
        },
	('time',): {
            'day': defaultdict(dict),
            'week': defaultdict(dict),
            'month': defaultdict(dict)
	},
        ('location', 'participant') : {
            ('state', 'first'): defaultdict(dict),
            ('state', 'last'): defaultdict(dict),
            ('state', 'full_name') : defaultdict(dict),
            ('city', 'first'): defaultdict(dict),
            ('city', 'last'): defaultdict(dict),
            ('city', 'full_name') : defaultdict(dict),
            ('address', 'first'): defaultdict(dict),
            ('address', 'last') : defaultdict(dict),
            ('address', 'full_name') : defaultdict(dict),
        },
        ('location', 'time'): {
            ('state', 'day'): defaultdict(dict),
            ('state', 'week'): defaultdict(dict),
            ('state', 'month') : defaultdict(dict),
            ('city', 'day'): defaultdict(dict),
            ('city', 'week'): defaultdict(dict),
            ('city', 'month') : defaultdict(dict),
            ('address', 'day'): defaultdict(dict),
            ('address', 'week') : defaultdict(dict),
            ('address', 'month') : defaultdict(dict),
        },
        ('time', 'participant'): {
            ('day', 'first'): defaultdict(dict),
            ('day', 'last'): defaultdict(dict),
            ('mday', 'full_name') : defaultdict(dict),
            ('week', 'first'): defaultdict(dict),
            ('week', 'last'): defaultdict(dict),
            ('week', 'full_name') : defaultdict(dict),
            ('month', 'first'): defaultdict(dict),
            ('month', 'last') : defaultdict(dict),
            ('month', 'full_name') : defaultdict(dict),
        }
    }

    parameters2incident_uris = {
        ('location',): {
            'state': defaultdict(set),
            'city' : defaultdict(set),
            'address' : defaultdict(set)
        },
        ('participant',): {
            'first' : defaultdict(set),
            'last' : defaultdict(set),
            'full_name' : defaultdict(set)
        },
        ('time',): {
            'day': defaultdict(dict),
            'week': defaultdict(dict),
            'month': defaultdict(dict)
        },
        ('location', 'participant') : {
            ('state', 'first'): defaultdict(set),
            ('state', 'last'): defaultdict(set),
            ('state', 'full_name') : defaultdict(set),
            ('city', 'first'): defaultdict(set),
            ('city', 'last'): defaultdict(set),
            ('city', 'full_name') : defaultdict(set),
            ('address', 'first'): defaultdict(set),
            ('address', 'last') : defaultdict(set),
            ('address', 'full_name') : defaultdict(set),
        },
        ('location', 'time'): {
            ('state', 'day'): defaultdict(dict),
            ('state', 'week'): defaultdict(dict),
            ('state', 'month') : defaultdict(dict),
            ('city', 'day'): defaultdict(dict),
            ('city', 'week'): defaultdict(dict),
            ('city', 'month') : defaultdict(dict),
            ('address', 'day'): defaultdict(dict),
            ('address', 'week') : defaultdict(dict),
            ('address', 'month') : defaultdict(dict),
        },
        ('time', 'participant'): {
            ('day', 'first'): defaultdict(dict),
            ('day', 'last'): defaultdict(dict),
            ('mday', 'full_name') : defaultdict(dict),
            ('week', 'first'): defaultdict(dict),
            ('week', 'last'): defaultdict(dict),
            ('week', 'full_name') : defaultdict(dict),
            ('month', 'first'): defaultdict(dict),
            ('month', 'last') : defaultdict(dict),
            ('month', 'full_name') : defaultdict(dict),
        }
    }


    # ### structure of dictionary
    # * category
    #     * granularity level
    #         * surface form
    #             * meaning -> set of incident uris
    #
    # * location
    #     * state      -> meaning : (state)                    -> set of incident uris
    #     * city       -> meaning : (state, city)              -> set of incident uris
    #     * address    -> meaning : (state, city, address)     -> set of incident uris
    #
    # * participant
    #     * first      -> meaning:  (incident_uri, first)      -> set of incident uris
    #     * last       -> meaning:  (incident_uri, last)       -> set of incident uris
    #     * full_name  -> meaning:  (incident_uri, full_name)  -> set of incident uris
    #
    # * (participant, location)
    #     * ('state', 'first')
    #         * (sf_state, sf_first)
    #              * (m_state, m_first) -> set of uris
    #


    for index, row in df.iterrows():

        incident_uri = row['incident_uri']

        # location

        # surface forms
        sf_state = row['state']
        sf_city = row['city_or_county']
        sf_address = row['address']

        # meanings
        m_state = (sf_state,)
        m_city = (sf_state, sf_city)
        m_address = (sf_state, sf_city, sf_address)

        loc_info = [('state', sf_state, m_state),
                    ('city', sf_city, m_city),
                    ('address', sf_address, m_address)]

        # update location info
        for gran_level, sf, m in loc_info:
            if sf != 'N/A':
                look_up[('location',)][gran_level][sf].setdefault(m, set()).add(incident_uri)
                parameters2incident_uris[('location'),][gran_level][sf].add(incident_uri)

        # time
        incident_date=row['date']
        dt_day = datetime.strptime(incident_date, '%B %d, %Y') 
        dt_month=dt.replace(day=1)

        look_up['time']['day'].setdefault()
        look_up['time']['month'].setdefault()

        # participant
        for part_obj in row['participants']:
            if 'Name' in part_obj:
                full_name = part_obj['Name']
                if full_name:
                    name_obj = HumanName(full_name)

                    # for sf_name, m_name in ...
                    for part_level, sf_name, m_name in [('first', name_obj.first, (incident_uri, name_obj.first)),
                                                        ('last', name_obj.last, (incident_uri, name_obj.last)),
                                                        ('full_name', name_obj.full_name, (incident_uri, name_obj.full_name))]:

                        # if name not empty string
                        if sf_name:

                            # add participant info
                            look_up[('participant',)][part_level][sf_name].setdefault(m_name,
                                                                                   set()).add(incident_uri)
                            parameters2incident_uris[('participant'),][part_level][sf].add(incident_uri)

                            # add combination of location and participant
                            for loc_level, sf_loc, m_loc in loc_info:
                                if sf_loc != 'N/A':
                                    look_up[('location', 'participant')][(loc_level, part_level)][(sf_loc, sf_name)].setdefault((m_loc, m_name),set()).add(incident_uri)
                                    parameters2incident_uris[('location', 'participant')][(loc_level, part_level)][(sf_loc, sf_name)].add(incident_uri)

    return look_up, parameters2incident_uris
