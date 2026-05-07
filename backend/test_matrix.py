import pickle
with open('model.pkl', 'rb') as f:
    model = pickle.load(f)

for jw in [0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0]:
    prob = model.predict_proba([[jw, 1.0, 1, 0]])[:, 1][0]
    print(f"JW: {jw:.2f} -> Prob: {prob:.4f}")
