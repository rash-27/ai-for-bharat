import time
from seed_data import setup_tables, generate_and_insert_data

if __name__ == "__main__":
    setup_tables()
    # Run continuous ingestion without initial bulk seeding
    generate_and_insert_data(0, continuous=True)
