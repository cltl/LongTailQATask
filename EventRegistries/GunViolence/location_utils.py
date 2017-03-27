from SPARQLWrapper import SPARQLWrapper, JSON
import Levenshtein
from geocoder import google

sparql = SPARQLWrapper("http://dbpedia.org/sparql")

def compose_query(coordinates):
    min_long=coordinates[0]
    min_lat=coordinates[1]
    max_long=coordinates[2]
    max_lat=coordinates[3]
    query="""
    select * where
    {
    ?a a <http://dbpedia.org/ontology/Settlement> ;
    <http://dbpedia.org/ontology/isPartOf>* ?state .
    ?state <http://purl.org/dc/terms/subject> <http://dbpedia.org/resource/Category:States_of_the_United_States> .
    ?a <http://www.w3.org/2003/01/geo/wgs84_pos#lat> ?lat ;
     <http://www.w3.org/2003/01/geo/wgs84_pos#long> ?long ;
     <http://www.w3.org/2000/01/rdf-schema#label> ?label .
     FILTER (?long>=%f) .
     FILTER (?long<=%f) .
     FILTER (?lat>=%f) .
     FILTER (?lat<=%f) .
     FILTER (lang(?label) = "en")
    }
    """ % (min_long, max_long, min_lat, max_lat)
    return query

def geocoder_address_to_links(address_string):
    address_geo = google(address_string)
    city_string = address_geo.city + ', ' + address_geo.state + ', ' + address_geo.country
    city_geo = google(city_string)
    bbox=city_geo.geojson['bbox']
    q=compose_query(bbox)
    link, state=sparql_select_best_link(q, city_geo.geojson['properties']['city'])
    to_return={'city': link, 'state': state}
    return to_return

def get_json_results(sparql_query):
    """
    perform sparql query to dbpedia
    and return json

    :rtype: dict
    :return: json results
    """

    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    return results


def get_state_sf2dbpedia_uri(df):
    """
    create mapping from states as surface forms in Gub Violence
    to Dbpedia uris

    :param pandas.core.frame.DataFrame df: gunviolence dataframes

    :rtype: dict
    :return: mapping state to dbpedia uri
    """
    state_query = '''
    SELECT DISTINCT ?state
    WHERE {
            ?state <http://purl.org/dc/terms/subject> <http://dbpedia.org/resource/Category:States_of_the_United_States> .
            ?state <http://dbpedia.org/ontology/country> <http://dbpedia.org/resource/United_States>
    }
    '''

    states_info = get_json_results(state_query)
    states_uris = {
        result['state']['value']
        for result in states_info["results"]["bindings"]
        }

    gv_sf_state2uri = {
        'Georgia': 'http://dbpedia.org/resource/Georgia_(U.S._state)',
        'Washington': 'http://dbpedia.org/resource/Washington_(state)',
    }

    gv_states = set(df['state'])

    for gv_sf_state in gv_states:
        for state_uri in states_uris:
            state_for_matching = gv_sf_state.replace(' ', '_')
            if state_uri.endswith('/' + state_for_matching):
                gv_sf_state2uri[gv_sf_state] = state_uri

    return gv_sf_state2uri


def possible_db_uris_for_city_county(city_or_county, state_uri):
    """
    given city_or_county and state, this function returns possible dbpedia
    uris

    :param str city_or_county: e.g. Rochester
    :param str state_uri: e.g. http://dbpedia.org/resource/New_York

    :rtype: set
    :return: set of possible dbpedia uris
    """
    query = '''
    SELECT DISTINCT ?uri
    WHERE {
    ?uri <http://dbpedia.org/ontology/isPartOf>* <%s> .
    ?uri rdfs:label ?label .
    filter strStarts(?label, "%s")
    }
    ''' % (state_uri, city_or_county)

    json_result = get_json_results(query)

    results = {
        result['uri']['value']
        for result in json_result["results"]["bindings"]
        }

    return results
