import os
import json
import time
from datetime import datetime, timezone
import psycopg2
from confluent_kafka import Producer
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return psycopg2.connect(os.getenv("SUPABASE_DB_URL"))

producer_conf = {
    'bootstrap.servers': os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
    'client.id': 'cdc-worker'
}
producer = Producer(producer_conf)

def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

def poll_postgres(last_checked):
    conn = get_db_connection()
    cursor = conn.cursor()
    tables = ['labour', 'bescom', 'kspcb']
    
    new_records = []
    for table in tables:
        cursor.execute(f"""
            SELECT id, source_system, company_name, address, pin_code, pan_number, gstin, status, created_at, updated_at
            FROM {table}
            WHERE updated_at > %s
        """, (last_checked,))
        
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        for row in rows:
            record = dict(zip(columns, row))
            # Convert datetime to ISO string for JSON serialization
            record['created_at'] = record['created_at'].isoformat()
            record['updated_at'] = record['updated_at'].isoformat()
            new_records.append(record)
            
    cursor.close()
    conn.close()
    return new_records

def main():
    # In a real app, you'd store this in a database or file so it persists across restarts
    # For this prototype, we'll just start from the beginning of time if we want all records
    # Or just use the current time to only get new ones. Let's use a very old time to pick up seeded data.
    last_checked = datetime(2000, 1, 1, tzinfo=timezone.utc)
    
    print("CDC Worker started. Polling for new records...")
    while True:
        try:
            records = poll_postgres(last_checked)
            if records:
                for record in records:
                    # Update last_checked to the max updated_at we've seen
                    record_time = datetime.fromisoformat(record['updated_at'])
                    if record_time > last_checked:
                        last_checked = record_time
                        
                    # Push to Kafka
                    payload = json.dumps(record)
                    producer.produce('raw-business-events', payload.encode('utf-8'), callback=delivery_report)
                
                producer.flush()
                print(f"Pushed {len(records)} new records to Kafka.")
            
            time.sleep(5) # Poll every 5 seconds
        except Exception as e:
            print(f"Error in CDC worker: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
