import os
import pickle
import pandas as pd
import numpy as np
import psycopg2
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import jellyfish
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return psycopg2.connect(os.getenv("SUPABASE_DB_URL"))

def fetch_data():
    conn = get_db_connection()
    query = """
    SELECT id, source_system, company_name, address, pin_code, pan_number, gstin 
    FROM labour
    UNION ALL
    SELECT id, source_system, company_name, address, pin_code, pan_number, gstin 
    FROM bescom
    UNION ALL
    SELECT id, source_system, company_name, address, pin_code, pan_number, gstin 
    FROM kspcb
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def generate_pairs(df):
    """Generate positive and negative pairs for training."""
    pairs = []
    
    # Positive pairs (Same Golden ID base)
    # The golden ID is the part after the source system prefix
    df['base_id'] = df['id'].apply(lambda x: x.split('_', 1)[1] if '_' in x else x)
    
    # Group by base_id to create positive pairs
    for base_id, group in df.groupby('base_id'):
        records = group.to_dict('records')
        for i in range(len(records)):
            for j in range(i+1, len(records)):
                pairs.append({'record_a': records[i], 'record_b': records[j], 'label': 1})
                
    # Negative pairs (Different Golden ID base)
    all_bases = df['base_id'].unique()
    num_negatives = len(pairs) * 2 # Generate twice as many negatives
    
    for _ in range(num_negatives):
        base_a, base_b = np.random.choice(all_bases, 2, replace=False)
        record_a = df[df['base_id'] == base_a].sample(1).iloc[0].to_dict()
        record_b = df[df['base_id'] == base_b].sample(1).iloc[0].to_dict()
        pairs.append({'record_a': record_a, 'record_b': record_b, 'label': 0})
        
    return pairs

def extract_features(record_a, record_b):
    """Extract similarity features between two records."""
    name_a = str(record_a.get('company_name', '') or '')
    name_b = str(record_b.get('company_name', '') or '')
    name_jaro_winkler = jellyfish.jaro_winkler_similarity(name_a, name_b)
    
    addr_a = str(record_a.get('address', '') or '')
    addr_b = str(record_b.get('address', '') or '')
    address_levenshtein = 1 - (jellyfish.levenshtein_distance(addr_a, addr_b) / max(len(addr_a), len(addr_b), 1))
    
    pan_a = str(record_a.get('pan_number', '') or '')
    pan_b = str(record_b.get('pan_number', '') or '')
    tax_id_exact = 1 if (pan_a and pan_b and pan_a == pan_b) else 0
    
    is_missing_pan = 1 if not pan_a or not pan_b else 0
    
    return {
        'name_jaro_winkler': name_jaro_winkler,
        'address_levenshtein': address_levenshtein,
        'tax_id_exact': tax_id_exact,
        'is_missing_pan': is_missing_pan
    }

def train_and_save_model():
    print("Fetching data from database...")
    df = fetch_data()
    
    print("Generating training pairs...")
    pairs = generate_pairs(df)
    
    print("Extracting features...")
    X = []
    y = []
    for pair in pairs:
        features = extract_features(pair['record_a'], pair['record_b'])
        X.append(list(features.values()))
        y.append(pair['label'])
        
    X = np.array(X)
    y = np.array(y)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training XGBoost model...")
    model = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    print(f"Model Accuracy on Test Set: {accuracy_score(y_test, y_pred):.2f}")
    
    print("Saving model to model.pkl...")
    with open('model.pkl', 'wb') as f:
        pickle.dump(model, f)
        
    print("Training completed!")

if __name__ == "__main__":
    train_and_save_model()
