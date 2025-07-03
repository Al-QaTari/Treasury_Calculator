# scraper.py
from db_manager import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    logging.info("SCRAPER: Initializing Database Manager to update data...")
    db_manager = DatabaseManager()
    
    logging.info("SCRAPER: Starting data fetching process...")
    fetch_data_from_cbe(db_manager)
    
    logging.info("SCRAPER: Data update process finished.")
