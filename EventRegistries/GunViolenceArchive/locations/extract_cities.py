import pickle
from geocoder import google

filename="raw_addresses.p"
city_filename='city_addresses.p' 
county_filename='county_addresses.p' 
addresses=pickle.load(open(filename, 'rb')) # this is a set of addresses
try:
    addresses_to_city=pickle.load(open(city_filename, 'rb'))
except:
    addresses_to_city={}
try:
    addresses_to_county=pickle.load(open(county_filename, 'rb'))
except:
    addresses_to_county={}

print(len(addresses)) # 3449 unique addresses

for address in addresses:
    if (address not in addresses_to_city or addresses_to_city[address]=="") and (address not in addresses_to_county or addresses_to_county[address]==""):
        try:
            address_geo = google(address)
            if address_geo.city:
                city_string = address_geo.city + ', ' + address_geo.state + ', ' + address_geo.country
                addresses_to_city[address]=city_string
            elif address_geo.county:
                county_string=address_geo.county + ', ' + address_geo.state + ', ' + address_geo.country
                addresses_to_county[address]=county_string
            else:
                print('error with %s' % address)
        except:
            continue
            
pickle.dump(addresses_to_city, open(city_filename, 'wb'))
pickle.dump(addresses_to_county, open(county_filename, 'wb'))
