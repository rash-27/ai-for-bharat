import os
import csv
from datetime import datetime
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from neo4j import GraphDatabase
from algoliasearch.search_client import SearchClient
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Darpan Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to Neo4j
neo4j_driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
)

# Connect to Algolia
algolia_client = SearchClient.create(
    os.getenv("ALGOLIA_APP_ID"), 
    os.getenv("ALGOLIA_SEARCH_API_KEY") # Use search key for querying
)
algolia_write_client = SearchClient.create(
    os.getenv("ALGOLIA_APP_ID"), 
    os.getenv("ALGOLIA_WRITE_API_KEY") # Use write key for updates
)
index = algolia_client.init_index('business_records')
write_index = algolia_write_client.init_index('business_records')

class ReviewDecision(BaseModel):
    node_a_id: str
    node_b_id: str
    decision: str # "MERGE" | "REJECT"
    features: list[float] = None

@app.get("/api/dashboard-stats")
def get_dashboard_stats():
    query = """
    MATCH (n:BusinessRecord)
    WITH count(n) AS total_records, count(DISTINCT n.assigned_ubid) AS total_ubids
    OPTIONAL MATCH ()-[r:PENDING_REVIEW]->()
    WITH total_records, total_ubids, count(r) AS pending_reviews
    RETURN total_records, pending_reviews, total_ubids
    """
    with neo4j_driver.session() as session:
        result = session.run(query).single()
        if result:
            return {
                "total_records": result["total_records"],
                "total_ubids": result["total_ubids"],
                "pending_reviews": result["pending_reviews"]
            }
        return {"total_records": 0, "total_ubids": 0, "pending_reviews": 0}

@app.get("/api/pending-reviews")
def get_pending_reviews():
    query = """
    MATCH (a:BusinessRecord)-[r:PENDING_REVIEW]->(b:BusinessRecord)
    RETURN a, b, r.score AS score, r.features AS features
    """
    with neo4j_driver.session() as session:
        results = session.run(query)
        reviews = []
        for record in results:
            reviews.append({
                "node_a": dict(record["a"]),
                "node_b": dict(record["b"]),
                "score": record["score"],
                "features": record.get("features")
            })
        return reviews

def log_active_learning(features, label):
    """Log manual review decisions for future ML training."""
    if not features:
        return
    log_file = "training_logs.csv"
    file_exists = os.path.isfile(log_file)
    with open(log_file, "a", newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["name_jaro_winkler", "address_levenshtein", "tax_id_exact", "is_missing_pan", "label"])
        writer.writerow([*features, label])

@app.post("/api/resolve-review")
def resolve_review(payload: ReviewDecision):
    with neo4j_driver.session() as session:
        if payload.decision == "MERGE":
            # Delete PENDING_REVIEW and draw SAME_AS
            session.run("""
            MATCH (a:BusinessRecord {id: $id_a})-[r:PENDING_REVIEW]->(b:BusinessRecord {id: $id_b})
            DELETE r
            MERGE (a)-[new_r:SAME_AS]->(b)
            SET new_r.manual = true
            """, id_a=payload.node_a_id, id_b=payload.node_b_id)
            
            # Fetch node A's UBID and node B's old UBID
            node_a = session.run("MATCH (a:BusinessRecord {id: $id}) RETURN a.assigned_ubid AS ubid", id=payload.node_a_id).single()
            node_b = session.run("MATCH (b:BusinessRecord {id: $id}) RETURN b.assigned_ubid AS ubid", id=payload.node_b_id).single()
            
            if node_a and node_b:
                new_ubid = node_a["ubid"]
                old_ubid = node_b["ubid"]
                
                # 1. Update ALL nodes in Neo4j that had Node B's old UBID
                session.run("""
                MATCH (n:BusinessRecord {assigned_ubid: $old_ubid})
                SET n.assigned_ubid = $new_ubid
                """, old_ubid=old_ubid, new_ubid=new_ubid)
                
                # 2. Sync ALL affected nodes in Algolia
                affected_nodes = session.run("MATCH (n:BusinessRecord {assigned_ubid: $new_ubid}) RETURN n.id AS id", new_ubid=new_ubid)
                
                algolia_updates = []
                for record in affected_nodes:
                    algolia_updates.append({
                        "objectID": record["id"],
                        "assigned_ubid": new_ubid
                    })
                write_index.partial_update_objects(algolia_updates)
                
            # Log Active Learning
            log_active_learning(payload.features, 1)
            
            return {"status": "merged"}
            
        elif payload.decision == "REJECT":
            # Delete PENDING_REVIEW
            session.run("""
            MATCH (a:BusinessRecord {id: $id_a})-[r:PENDING_REVIEW]->(b:BusinessRecord {id: $id_b})
            DELETE r
            MERGE (a)-[new_r:REJECTED_MATCH]->(b)
            """, id_a=payload.node_a_id, id_b=payload.node_b_id)
            
            # Log Active Learning
            log_active_learning(payload.features, 0)
            
            return {"status": "rejected"}
            
        else:
            raise HTTPException(status_code=400, detail="Invalid decision")

@app.get("/api/search")
def search_businesses(query: str):
    res = index.search(query, {
        'attributesToRetrieve': ['node_id', 'company_name', 'assigned_ubid'],
        'hitsPerPage': 10
    })
    return res['hits']

@app.get("/api/ubid/{ubid_id}")
def get_ubid_details(ubid_id: str):
    query = """
    MATCH (n:BusinessRecord {assigned_ubid: $ubid})
    RETURN n
    """
    with neo4j_driver.session() as session:
        results = session.run(query, ubid=ubid_id)
        nodes = [dict(record["n"]) for record in results]
        
        if not nodes:
            raise HTTPException(status_code=404, detail="UBID not found")
            
        # Determine Activity Status based on events
        status = "DORMANT"
        latest_event = None
        for n in nodes:
            # Parse created_at / updated_at
            event_date_str = n.get("updated_at") or n.get("created_at")
            if event_date_str:
                dt = datetime.fromisoformat(event_date_str)
                if not latest_event or dt > latest_event:
                    latest_event = dt
                    
        if latest_event:
            delta_months = (datetime.now(latest_event.tzinfo) - latest_event).days / 30
            if delta_months <= 18:
                status = "ACTIVE"
                
        # Build chronological event timeline (newest first)
        timeline = []
        for n in nodes:
            event_date_str = n.get("updated_at") or n.get("created_at")
            if event_date_str:
                dt = datetime.fromisoformat(event_date_str)
                age_months = (datetime.now(dt.tzinfo) - dt).days / 30
                timeline.append({
                    "source_system": n.get("source_system", "unknown"),
                    "company_name": n.get("company_name"),
                    "event_date": dt.isoformat(),
                    "age_months": round(age_months, 1),
                    "is_deciding_event": (dt == latest_event),
                })
        # Sort newest → oldest
        timeline.sort(key=lambda x: x["event_date"], reverse=True)

        # Consolidate master profile
        master_profile = {
            "ubid": ubid_id,
            "company_name": nodes[0].get("company_name"),
            "status": status,
            "latest_event_date": latest_event.isoformat() if latest_event else None,
            "nodes": nodes,
            "event_timeline": timeline,
        }
        
        return master_profile
