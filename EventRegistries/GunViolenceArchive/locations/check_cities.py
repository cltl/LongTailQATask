import pickle
from geocoder import google

filename="raw_addresses.p"
city_filename='city_addresses.p'
county_filename='county_addresses.p'
addresses=pickle.load(open(filename, 'rb'))
cities=pickle.load(open(city_filename, 'rb'))
counties=pickle.load(open(county_filename, 'rb'))

print(len(addresses)) # 3449 unique addresses

not_found=0
for address, city in addresses.items():
    if (address not in cities or cities[address]=="") and (address not in counties or counties[address]==""):
        not_found+=1
print(not_found)
