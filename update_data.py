# update_data.py
import logging
from db_manager import DatabaseManager
from cbe_scraper import fetch_data_from_cbe

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("update_data.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def run_update() -> None:
    """
    Main function to run the entire data update process.
    It initializes the database manager and triggers the web scraper.
    """
    logger.info("=" * 50)
    logger.info("Starting data update process...")

    try:
        # Initialize the database manager which handles all DB operations
        db_manager = DatabaseManager()

        # Pass the db_manager instance to the fetching function
        # The fetching function will now handle saving the data directly
        fetch_data_from_cbe(db_manager)

        logger.info("Data update process finished successfully.")

    except Exception as e:
        logger.critical(
            f"A critical error occurred in the main update script: {e}", exc_info=True
        )
    finally:
        logger.info("=" * 50)


if __name__ == "__main__":
    run_update()
