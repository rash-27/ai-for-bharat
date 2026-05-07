import os
import psycopg2
from neo4j import GraphDatabase
from algoliasearch.search_client import SearchClient
from dotenv import load_dotenv

load_dotenv()

print("Clearing Postgres...")
try:
    conn = psycopg2.connect(os.getenv("SUPABASE_DB_URL"))
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE labour, bescom, kspcb;")
    conn.commit()
    cursor.close()
    conn.close()
    print("Postgres cleared.")
except Exception as e:
    print(f"Error clearing Postgres: {e}")

print("Clearing Neo4j...")
try:
    neo4j_driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
    )
    with neo4j_driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    print("Neo4j cleared.")
except Exception as e:
    print(f"Error clearing Neo4j: {e}")

print("Clearing Algolia...")
try:
    algolia_client = SearchClient.create(
        os.getenv("ALGOLIA_APP_ID"), 
        os.getenv("ALGOLIA_WRITE_API_KEY")
    )
    index = algolia_client.init_index('business_records')
    index.clear_objects()
    print("Algolia cleared.")
except Exception as e:
    print(f"Error clearing Algolia: {e}")
