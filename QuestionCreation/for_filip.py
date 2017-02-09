import pickle


with open('cache/mass_shootings_2015.pickle', 'rb') as infile:
    look_up = pickle.load(infile)


print(look_up.keys())
