import jellyfish

name = "Global Tech Industries Private Limited"

# Drop everything after first word
w1 = name.split()[0]
print(f"Only first word: {jellyfish.jaro_winkler_similarity(name, w1)}")

# Replace first word with something else
w2 = "Local " + " ".join(name.split()[1:])
print(f"Replace first word: {jellyfish.jaro_winkler_similarity(name, w2)}")

# Drop vowels from entire name
w3 = "".join(c for c in name if c.lower() not in 'aeiou')
print(f"Drop vowels: {jellyfish.jaro_winkler_similarity(name, w3)}")

