import psycopg2
import uuid
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return psycopg2.connect(os.getenv("SUPABASE_DB_URL"))

def insert_records():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    base_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    # 1. Insert into labour (Golden record)
    cursor.execute("""
        INSERT INTO labour 
        (id, source_system, company_name, address, pin_code, pan_number, gstin, status, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        f"labour_{base_id}", "labour",
        "Global Tech Industries Private Limited",
        "123 Innovation Drive, Tech Park, Bangalore",
        "560001",
        "ABCDE1234F",
        "29ABCDE1234F1Z5",
        "ACTIVE",
        now, now
    ))
    
    # 2. Insert into bescom (Prefix truncated name -> Ambiguous Match)
    cursor.execute("""
        INSERT INTO bescom 
        (id, source_system, company_name, address, pin_code, pan_number, gstin, status, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        f"bescom_{base_id}", "bescom",
        "Tech Industries Private Limited", # Dropped 'Global '
        "123 Innovation Drive, Tech Park, Bangalore",
        "560001",
        "ABCDE1234F",
        "29ABCDE1234F1Z5",
        "ACTIVE",
        now, now
    ))
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Inserted manual ambiguous pair with base ID: {base_id}")
    print("These records should now be picked up by the CDC worker and routed as PENDING_REVIEW.")

if __name__ == "__main__":
    insert_records()
