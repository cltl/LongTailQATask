import sys
import pickle
from geocoder import google

import location_utils

city_filename='city_addresses.p'
county_filename='county_addresses.p'
try:
    addresses_to_city=pickle.load(open(city_filename, 'rb'))
except:
    addresses_to_city={}
try:
    addresses_to_county=pickle.load(open(county_filename, 'rb'))
except:
    addresses_to_county={}

city_bbox_filename='city_bboxes.p'
county_bbox_filename='county_bboxes.p'
try:
    city_to_bbox=pickle.load(open(city_bbox_filename, 'rb'))
except:
    city_to_bbox={}
try:
    county_to_bbox=pickle.load(open(county_bbox_filename, 'rb'))
except:
    county_to_bbox={}

city_uri_filename='city_uris.p'
county_uri_filename='county_uris.p'
try:
    city_to_uri=pickle.load(open(city_uri_filename, 'rb'))
except:
    city_to_uri={}
try:
    county_to_uri=pickle.load(open(county_uri_filename, 'rb'))
except:
    county_to_uri={}

if sys.argv[1]=="city":
    for city_string in set(addresses_to_city.values()):
        if city_string=="":
            continue
        if city_string in city_to_bbox and city_to_bbox[city_string]:
            bbox=city_to_bbox[city_string]
        else:
            try:
                city_geo = google(city_string)
                bbox=city_geo.geojson['bbox']
                city_to_bbox[city_string]=bbox
            except:
                continue
                print('error obtaining the bbox for %s' % city_string)
        if city_string not in city_to_uri or not city_to_uri[city_string]:
            q=location_utils.compose_query(bbox)
            link, state=location_utils.sparql_select_best_link(q, city_string.split(',')[0])
            link_state_json={'city': link, 'state': state}
            city_to_uri[city_string]=link_state_json

    pickle.dump(city_to_bbox, open(city_bbox_filename, 'wb'))
    pickle.dump(city_to_uri, open(city_uri_filename, 'wb'))
elif sys.argv[1]=="county":
    for county_string in set(addresses_to_county.values()):
        if county_string=="":
            continue
        if county_string in county_to_bbox and county_to_bbox[county_string]:
            bbox=county_to_bbox[county_string]
        else:
            try:
                county_geo = google(county_string)
                bbox=county_geo.geojson['bbox']
                county_to_bbox[county_string]=bbox
            except:
                continue
                print('error obtaining the bbox for %s' % county_string)
        if county_string not in county_to_uri or not county_to_uri[county_string]:
            q=location_utils.compose_query(bbox)
            link, state=location_utils.sparql_select_best_link(q, county_string.split(',')[0])
            link_state_json={'county': link, 'state': state}
            county_to_uri[county_string]=link_state_json
    pickle.dump(county_to_bbox, open(county_bbox_filename, 'wb'))
    pickle.dump(county_to_uri, open(county_uri_filename, 'wb'))

