import pickle
import jellyfish

with open('model.pkl', 'rb') as f:
    model = pickle.load(f)

name_a = 'Global Tech Industries Private Limited'
name_b = 'Tech Industries Private Limited'
jw = jellyfish.jaro_winkler_similarity(name_a, name_b)

addr_a = '123 Innovation Drive, Tech Park, Bangalore'
addr_b = '123 Innovation Drive, Tech Park, Bangalore'
lev = 1 - (jellyfish.levenshtein_distance(addr_a, addr_b) / max(len(addr_a), len(addr_b), 1))

features = [[jw, lev, 1, 0]]
print(f"JW: {jw}")
print(f"Prob: {model.predict_proba(features)[:, 1]}")
