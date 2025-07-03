# This is the content for update_data.py
from db_manager import DatabaseManager
from cbe_scraper import fetch_data_from_cbe

if __name__ == "__main__":
    print("Initializing Database Manager to update data...")
    db_manager = DatabaseManager()
    
    print("Starting data fetching process...")
    # We pass the db_manager instance to the fetching function
    # The fetching function will now handle saving the data directly
    fetch_data_from_cbe(db_manager)
    
    print("Data update process finished.")