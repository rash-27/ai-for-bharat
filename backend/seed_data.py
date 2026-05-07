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

def degrade_record(record, source, base_id, heavy_noise=False):
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

    # ADD SEVERE NOISE FOR CONTINUOUS STREAM OR HEAVY NOISE INITIAL BATCH
    if heavy_noise:
        noise_type = random.random()
        if noise_type > 0.7:
            # Suffix truncation (Jaro-Winkler ~0.90 -> Auto-link)
            degraded['company_name'] = degraded['company_name'][:len(degraded['company_name'])//2]
        elif noise_type > 0.4:
            # Keep ONLY the first word (Jaro-Winkler ~0.83 -> PENDING_REVIEW)
            words = degraded['company_name'].split()
            if len(words) > 1:
                degraded['company_name'] = words[0]
            else:
                degraded['company_name'] = degraded['company_name'][:len(degraded['company_name'])//2]
                
        # Scramble PAN slightly
        if degraded.get('pan_number') and random.random() > 0.5:
            # Change the last character to a random letter
            pan = degraded['pan_number']
            degraded['pan_number'] = pan[:-1] + random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
            
        # Address degradation
        if random.random() > 0.5:
            addr_noise = random.random()
            if addr_noise > 0.6:
                # Drop all vowels to simulate terrible data entry
                degraded['address'] = "".join(c for c in degraded['address'] if c.lower() not in 'aeiou')
            elif addr_noise > 0.3:
                # Truncate address (drop second half completely)
                degraded['address'] = degraded['address'][:len(degraded['address']) // 2]
            else:
                # Shuffle the words in the address randomly
                words = degraded['address'].split()
                random.shuffle(words)
                degraded['address'] = " ".join(words)
        if random.random() > 0.3:
            # Severe address degradation
            words = degraded['address'].split()
            if len(words) > 2:
                degraded['address'] = " ".join(words[1:len(words)//2])

    return degraded

def generate_and_insert_data(num_golden_records=1000, continuous=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    def insert_batch(count, heavy_noise=False):
        for _ in range(count):
            base_id = str(uuid.uuid4())
            pan = fake.pystr_format('?????####?')
            gstin = f"29{pan}1Z{fake.pystr_format('?')}"
            
            from datetime import timedelta
            
            golden_status = random.choice(['ACTIVE', 'INACTIVE', 'DORMANT'])
            
            if golden_status == 'ACTIVE':
                updated = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 365))
            elif golden_status == 'INACTIVE':
                updated = datetime.now(timezone.utc) - timedelta(days=random.randint(600, 1000))
            else:
                updated = datetime.now(timezone.utc) - timedelta(days=random.randint(1100, 2000))
            
            golden_record = {
                'company_name': fake.company(),
                'address': fake.address().replace('\n', ', '),
                'pin_code': fake.postcode(),
                'pan_number': pan,
                'gstin': gstin,
                'status': golden_status,
                'created_at': updated - timedelta(days=random.randint(30, 365)),
                'updated_at': updated
            }
            
            if random.random() > 0.1:
                # Randomly inject heavy noise 50% of the time to train model on ambiguity
                hn = heavy_noise or (random.random() > 0.5)
                r = degrade_record(golden_record, 'labour', base_id, hn)
                cursor.execute(
                    """INSERT INTO labour (id, source_system, company_name, address, pin_code, pan_number, gstin, status, created_at, updated_at) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (r['id'], r['source_system'], r['company_name'], r['address'], r['pin_code'], r['pan_number'], r['gstin'], r['status'], r['created_at'], r['updated_at'])
                )
                
            if random.random() > 0.2:
                hn = heavy_noise or (random.random() > 0.5)
                r = degrade_record(golden_record, 'bescom', base_id, hn)
                cursor.execute(
                    """INSERT INTO bescom (id, source_system, company_name, address, pin_code, pan_number, gstin, status, created_at, updated_at) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (r['id'], r['source_system'], r['company_name'], r['address'], r['pin_code'], r['pan_number'], r['gstin'], r['status'], r['created_at'], r['updated_at'])
                )
                
            if random.random() > 0.4:
                hn = heavy_noise or (random.random() > 0.5)
                r = degrade_record(golden_record, 'kspcb', base_id, hn)
                cursor.execute(
                    """INSERT INTO kspcb (id, source_system, company_name, address, pin_code, pan_number, gstin, status, created_at, updated_at) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (r['id'], r['source_system'], r['company_name'], r['address'], r['pin_code'], r['pan_number'], r['gstin'], r['status'], r['created_at'], r['updated_at'])
                )
        conn.commit()

    if num_golden_records > 0:
        print(f"Seeding initial {num_golden_records} records for training data...")
        insert_batch(num_golden_records, heavy_noise=False)
        print("Initial data seeded successfully!")

    if continuous:
        import time
        print("Starting continuous data stream (1 record every 10 seconds)...")
        while True:
            time.sleep(10)
            insert_batch(1, heavy_noise=True)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Inserted 1 new record.")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    setup_tables()
    # Only seed initial data (1000)
    generate_and_insert_data(1000, continuous=False)
