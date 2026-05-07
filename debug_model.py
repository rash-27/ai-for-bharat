import pickle
import numpy as np

# Load model
with open('backend/model.pkl', 'rb') as f:
    model = pickle.load(f)

print("Model classes:", model.classes_)

# Test a few feature combinations
# Features: [name_jaro_winkler, address_levenshtein, tax_id_exact, is_missing_pan]
test_cases = [
    [1.0, 1.0, 1, 0],   # Perfect match
    [0.95, 0.9, 1, 0],  # Slight typos, PAN matches
    [0.85, 0.8, 1, 0],  # Moderate typos, PAN matches
    [1.0, 1.0, 0, 1],   # Perfect name/address, PAN missing
    [0.9, 0.9, 0, 1],   # Typos, PAN missing
    [0.6, 0.5, 0, 0],   # Bad match, PAN doesn't match
    [0.4, 0.3, 0, 0],   # Terrible match
]

print("Predictions for test cases:")
for i, case in enumerate(test_cases):
    prob = model.predict_proba([case])[0][1]
    print(f"Case {i} {case}: {prob}")

# Dump the trees to see how complex the model is
booster = model.get_booster()
dump = booster.get_dump()
print(f"\nNumber of trees: {len(dump)}")
if len(dump) > 0:
    print("Tree 0 structure:")
    print(dump[0])
