import pickle
from geocoder import google

filename="addresses.p"
addresses_to_city=pickle.load(open(filename, 'rb'))

print(len(addresses_to_city)) # 3449 unique addresses

for address, city in addresses_to_city.items():
    if city=="":
        try:
            address_geo = google(address)
            city_string = address_geo.city + ', ' + address_geo.state + ', ' + address_geo.country
            addresses_to_city[address]=city_string
        except:
            continue
            
pickle.dump(addresses_to_city, open(filename, 'wb'))
