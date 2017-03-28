import pickle
from geocoder import google

filename="addresses.p"
addresses_to_city=pickle.load(open(filename, 'rb'))
cities=set()
print(len(addresses_to_city)) # 3449 unique addresses

no_city=0
for address, city in addresses_to_city.items():
    if city=="":
        no_city+=1
    else:
        cities.add(city)
        #print(address, city)
print(no_city)
print(len(cities))
