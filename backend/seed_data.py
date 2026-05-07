import os
import random
import uuid
from datetime import datetime, timezone
import psycopg2
from faker import Faker
from dotenv import load_dotenv

load_dotenv()

fake = Faker('en_IN')

# Setup PostgreSQL Connection
def get_db_connection():
    return psycopg2.connect(os.getenv("SUPABASE_DB_URL"))

def setup_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    tables = ['labour', 'bescom', 'kspcb']
    for table in tables:
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table} (
                id VARCHAR(255) PRIMARY KEY,
                source_system VARCHAR(50),
                company_name VARCHAR(255),
                address TEXT,
                pin_code VARCHAR(20),
                pan_number VARCHAR(50),
                gstin VARCHAR(50),
                status VARCHAR(50),
                created_at TIMESTAMP WITH TIME ZONE,
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """)
    conn.commit()
    cursor.close()
    conn.close()

def degrade_record(record, source, base_id):
    """Introduce noise for the source systems."""
    degraded = record.copy()
    degraded['source_system'] = source
    degraded['id'] = f"{source}_{base_id}"
    
    # Introduce noise
    if source == 'labour':
        # Labour often misses GSTIN and PAN
        degraded['pan_number'] = None if random.random() > 0.5 else degraded['pan_number']
        degraded['gstin'] = None
        # Typos in address
        if random.random() > 0.3:
            degraded['address'] = degraded['address'].replace("Street", "St.").replace("Road", "Rd")
    elif source == 'bescom':
        # BESCOM often has slight name variations
        if random.random() > 0.3:
            degraded['company_name'] = degraded['company_name'].replace("Pvt Ltd", "Private Limited").replace("Ltd", "Limited")
        degraded['gstin'] = None
    elif source == 'kspcb':
        # KSPCB is usually strict but might miss PAN if GSTIN is present
        if degraded['gstin'] and random.random() > 0.5:
            degraded['pan_number'] = None

    return degraded

def generate_and_insert_data(num_golden_records=100, continuous=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    def insert_batch(count):
        for _ in range(count):
            base_id = str(uuid.uuid4())
            pan = fake.pystr_format('?????####?')
            gstin = f"29{pan}1Z{fake.pystr_format('?')}"
            
            golden_record = {
                'company_name': fake.company(),
                'address': fake.address().replace('\n', ', '),
                'pin_code': fake.postcode(),
                'pan_number': pan,
                'gstin': gstin,
                'status': random.choice(['ACTIVE', 'INACTIVE', 'DORMANT']),
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }
            
            if random.random() > 0.1:
                r = degrade_record(golden_record, 'labour', base_id)
                cursor.execute(
                    """INSERT INTO labour (id, source_system, company_name, address, pin_code, pan_number, gstin, status, created_at, updated_at) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (r['id'], r['source_system'], r['company_name'], r['address'], r['pin_code'], r['pan_number'], r['gstin'], r['status'], r['created_at'], r['updated_at'])
                )
                
            if random.random() > 0.2:
                r = degrade_record(golden_record, 'bescom', base_id)
                cursor.execute(
                    """INSERT INTO bescom (id, source_system, company_name, address, pin_code, pan_number, gstin, status, created_at, updated_at) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (r['id'], r['source_system'], r['company_name'], r['address'], r['pin_code'], r['pan_number'], r['gstin'], r['status'], r['created_at'], r['updated_at'])
                )
                
            if random.random() > 0.4:
                r = degrade_record(golden_record, 'kspcb', base_id)
                cursor.execute(
                    """INSERT INTO kspcb (id, source_system, company_name, address, pin_code, pan_number, gstin, status, created_at, updated_at) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (r['id'], r['source_system'], r['company_name'], r['address'], r['pin_code'], r['pan_number'], r['gstin'], r['status'], r['created_at'], r['updated_at'])
                )
        conn.commit()

    print(f"Seeding initial {num_golden_records} records for training data...")
    insert_batch(num_golden_records)
    print("Initial data seeded successfully!")

    if continuous:
        import time
        print("Starting continuous data stream (1 record every 10 seconds)...")
        while True:
            time.sleep(10)
            insert_batch(1)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Inserted 1 new record.")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    setup_tables()
    # Run continuous ingestion
    generate_and_insert_data(100, continuous=True)
