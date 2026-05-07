import os
import json
import pickle
import uuid
import jellyfish
from datetime import datetime
from confluent_kafka import Consumer
from neo4j import GraphDatabase
from algoliasearch.search_client import SearchClient
from dotenv import load_dotenv

load_dotenv()

# Load Model
try:
    with open('model.pkl', 'rb') as f:
        model = pickle.load(f)
except FileNotFoundError:
    model = None
    print("WARNING: model.pkl not found. Please run train_model.py first.")

# Connect to Neo4j
neo4j_driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
)

# Connect to Algolia
algolia_client = SearchClient.create(
    os.getenv("ALGOLIA_APP_ID"), 
    os.getenv("ALGOLIA_WRITE_API_KEY")
)
index = algolia_client.init_index('business_records')

consumer_conf = {
    'bootstrap.servers': os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
    'group.id': 'resolution-engine',
    'auto.offset.reset': 'earliest'
}
consumer = Consumer(consumer_conf)
consumer.subscribe(['raw-business-events'])

def extract_features(record_a, record_b):
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
    
    return [name_jaro_winkler, address_levenshtein, tax_id_exact, is_missing_pan]

def upsert_node_neo4j(tx, record):
    query = """
    MERGE (n:BusinessRecord {id: $id})
    SET n += $props
    RETURN n
    """
    props = {
        'source_system': record.get('source_system'),
        'company_name': record.get('company_name'),
        'address': record.get('address'),
        'pin_code': record.get('pin_code'),
        'pan_number': record.get('pan_number'),
        'status': record.get('status'),
        'created_at': record.get('created_at'),
        'assigned_ubid': record.get('assigned_ubid')
    }
    tx.run(query, id=record['id'], props=props)

def get_candidates(tx, pin_code, record_id):
    query = """
    MATCH (n:BusinessRecord)
    WHERE n.pin_code = $pin_code AND n.id <> $record_id
    RETURN n.id AS id, n.company_name AS company_name, n.address AS address, 
           n.pan_number AS pan_number, n.assigned_ubid AS assigned_ubid
    """
    result = tx.run(query, pin_code=pin_code, record_id=record_id)
    return [dict(record) for record in result]

def draw_edge(tx, id_a, id_b, score, edge_type):
    query = f"""
    MATCH (a:BusinessRecord {{id: $id_a}})
    MATCH (b:BusinessRecord {{id: $id_b}})
    MERGE (a)-[r:{edge_type}]->(b)
    SET r.score = $score
    """
    tx.run(query, id_a=id_a, id_b=id_b, score=score)

def index_algolia(record):
    algolia_record = {
        'objectID': record['id'],
        'node_id': record['id'],
        'company_name': record.get('company_name'),
        'address': record.get('address'),
        'assigned_ubid': record.get('assigned_ubid'),
        'status': record.get('status')
    }
    index.save_object(algolia_record)

def process_message(msg_val):
    record = json.loads(msg_val)
    record_id = record['id']
    pin_code = record.get('pin_code')
    
    # Check if we should assign a new UBID by default
    assigned_ubid = f"UBID-{str(uuid.uuid4())[:8]}"
    record['assigned_ubid'] = assigned_ubid
    
    with neo4j_driver.session() as session:
        # Save new record as a node
        session.execute_write(upsert_node_neo4j, record)
        
        # Block: Find candidates
        candidates = session.execute_read(get_candidates, pin_code, record_id)
        
        best_candidate = None
        best_score = -1
        
        if model and candidates:
            # Featurize and Predict
            X_batch = [extract_features(candidate, record) for candidate in candidates]
            probabilities = model.predict_proba(X_batch)[:, 1] # Probability of match (class 1)
            
            for idx, prob in enumerate(probabilities):
                if prob > best_score:
                    best_score = prob
                    best_candidate = candidates[idx]
        
        # Route
        if best_candidate:
            if best_score >= 0.90:
                print(f"Auto-link! Score: {best_score}. Drawing SAME_AS edge.")
                session.execute_write(draw_edge, best_candidate['id'], record_id, float(best_score), 'SAME_AS')
                # Merge UBID: Adopt candidate's UBID
                assigned_ubid = best_candidate.get('assigned_ubid') or assigned_ubid
                record['assigned_ubid'] = assigned_ubid
                # Update node with new UBID
                session.execute_write(upsert_node_neo4j, record)
            elif 0.70 <= best_score < 0.90:
                print(f"Ambiguous match! Score: {best_score}. Drawing PENDING_REVIEW edge.")
                session.execute_write(draw_edge, best_candidate['id'], record_id, float(best_score), 'PENDING_REVIEW')
            else:
                print(f"No match. Score: {best_score}. Keeping separate.")
        
    # Index to Elasticsearch/Algolia
    index_algolia(record)

def main():
    print("Resolution Engine started. Listening to Kafka...")
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue
        
        print(f"Received message: {msg.value().decode('utf-8')[:50]}...")
        try:
            process_message(msg.value().decode('utf-8'))
        except Exception as e:
            print(f"Error processing message: {e}")

if __name__ == "__main__":
    main()
