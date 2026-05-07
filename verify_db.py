import os
from neo4j import GraphDatabase
from algoliasearch.search_client import SearchClient
from dotenv import load_dotenv

load_dotenv('backend/.env')

print("Checking Neo4j...")
try:
    neo4j_driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
    )
    with neo4j_driver.session() as session:
        count = session.run("MATCH (n:BusinessRecord) RETURN count(n) AS cnt").single()["cnt"]
        print(f"Neo4j BusinessRecord count: {count}")
except Exception as e:
    print(f"Neo4j Error: {e}")

print("Checking Algolia...")
try:
    algolia_client = SearchClient.create(
        os.getenv("ALGOLIA_APP_ID"), 
        os.getenv("ALGOLIA_SEARCH_API_KEY")
    )
    index = algolia_client.init_index('business_records')
    res = index.search('', {'hitsPerPage': 0})
    print(f"Algolia total records: {res.get('nbHits')}")
except Exception as e:
    print(f"Algolia Error: {e}")
