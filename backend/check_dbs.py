import os
import json
import psycopg2
from neo4j import GraphDatabase
from algoliasearch.search_client import SearchClient
from dotenv import load_dotenv

load_dotenv()

print("=== POSTGRESQL (Latest Labour Record) ===")
try:
    conn = psycopg2.connect(os.getenv("SUPABASE_DB_URL"))
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM labour ORDER BY created_at DESC LIMIT 1;")
    col_names = [desc[0] for desc in cursor.description]
    row = cursor.fetchone()
    if row:
        print(json.dumps(dict(zip(col_names, [str(x) for x in row])), indent=2))
    else:
        print("No records found.")
    conn.close()
except Exception as e:
    print(f"Postgres Error: {e}")

print("\n=== NEO4J GRAPH (Latest Business Record Node) ===")
try:
    driver = GraphDatabase.driver(os.getenv("NEO4J_URI"), auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")))
    with driver.session() as session:
        result = session.run("MATCH (n:BusinessRecord) RETURN n ORDER BY n.created_at DESC LIMIT 1")
        record = result.single()
        if record:
            print(json.dumps(dict(record["n"]), indent=2))
        else:
            print("No records found.")
except Exception as e:
    print(f"Neo4j Error: {e}")

print("\n=== ALGOLIA SEARCH (Search for 'Global' or any recent keyword) ===")
try:
    client = SearchClient.create(os.getenv("ALGOLIA_APP_ID"), os.getenv("ALGOLIA_SEARCH_API_KEY"))
    index = client.init_index('business_records')
    res = index.search('', {'hitsPerPage': 1})
    if res['hits']:
        print(json.dumps(res['hits'][0], indent=2))
    else:
        print("No records found.")
except Exception as e:
    print(f"Algolia Error: {e}")
