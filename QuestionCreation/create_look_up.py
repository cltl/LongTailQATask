# # Limitations
# * nameparser is not always correct wrt middle vs last name

# # Requirements
# * install **nameparser**

import pandas
from collections import defaultdict
from nameparser import HumanName
import pickle

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

df = pandas.read_pickle('../EventRegistries/GunViolence/frames/mass_shootings_2015')
output_path = 'cache/mass_shootings_2015.pickle'

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

    # update dictionary
    loc_info = [('state', sf_state, m_state),
                ('city', sf_city, m_city),
                ('address', sf_address, m_address)]
    for gran_level, sf, m in loc_info:
        look_up[('location',)][gran_level][sf].setdefault(m, set()).add(incident_uri)

    # participant
    for part_obj in row['participants']:
        if 'Name' in part_obj:
            full_name = part_obj['Name']
            if full_name:
                name_obj = HumanName(full_name)

                if name_obj.first:
                    sf_name = name_obj.first
                    m_name = (incident_uri, name_obj.first)
                    look_up[('participant',)]['first'][sf_name].setdefault(m_name,
                                                                          set()).add(incident_uri)

                    # add combination of location and participant
                    part_level = 'first'
                    for loc_level, sf_loc, m_loc in loc_info:
                        look_up[('location', 'participant')][(loc_level, part_level)][(sf_loc, sf_name)].setdefault((m_loc, m_name),
                                                                                                                     set()).add(incident_uri)

                if name_obj.last:
                    sf_name = name_obj.last
                    m_name = (incident_uri, name_obj.last)
                    look_up[('participant',)]['last'][sf_name].setdefault(m_name,
                                                                          set()).add(incident_uri)

                    # add combination of location and participant
                    part_level = 'last'
                    for loc_level, sf_loc, m_loc in loc_info:
                        look_up[('location', 'participant')][(loc_level, part_level)][(sf_loc, sf_name)].setdefault((m_loc, m_name),
                                                                                                                     set()).add(incident_uri)


                if name_obj.full_name:
                    sf_name = name_obj.full_name
                    m_name = (incident_uri, name_obj.full_name)

                    look_up[('participant',)]['last'][sf_name].setdefault(m_name,
                                                                          set()).add(incident_uri)

                    # add combination of location and participant
                    part_level = 'full_name'
                    for loc_level, sf_loc, m_loc in loc_info:
                        look_up[('location', 'participant')][(loc_level, part_level)][(sf_loc, sf_name)].setdefault((m_loc, m_name),
                                                                                                                     set()).add(incident_uri)

with open(output_path, 'wb') as outfile:
    pickle.dump(look_up, outfile)
