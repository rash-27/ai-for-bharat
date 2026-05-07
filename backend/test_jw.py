import jellyfish
import random

name = "Global Tech Industries Private Limited"

# Drop last word
w1 = " ".join(name.split()[:-1])
print(f"Drop last word: {jellyfish.jaro_winkler_similarity(name, w1)}")

# Replace 2 random chars
w2 = list(name)
w2[10] = 'X'
w2[15] = 'Y'
w2 = "".join(w2)
print(f"Replace 2 chars: {jellyfish.jaro_winkler_similarity(name, w2)}")

# Drop 3 chars from middle
w3 = name[:10] + name[13:]
print(f"Drop 3 chars middle: {jellyfish.jaro_winkler_similarity(name, w3)}")

# Typo swap adjacent chars
w4 = list(name)
w4[5], w4[6] = w4[6], w4[5]
w4 = "".join(w4)
print(f"Swap adjacent: {jellyfish.jaro_winkler_similarity(name, w4)}")

