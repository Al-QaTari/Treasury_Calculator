# db_manager.py (النسخة المحسنة)
import sqlite3
import pandas as pd
import os
import logging
from datetime import datetime
from typing import Tuple, List, Any

import constants as C

# Configure logging for this module
logger = logging.getLogger(__name__)


class DatabaseManager:
    """A robust class to manage all SQLite database operations for the T-bill data."""

    def __init__(self, db_filename: str = C.DB_FILENAME):
        """
        Initializes the DatabaseManager.

        Args:
            db_filename (str): The name of the SQLite database file.
        """
        # Ensure the path is absolute
        self.db_filename = os.path.abspath(db_filename)
        logger.info(f"Database path set to: {self.db_filename}")
        self._init_db()

    def _init_db(self) -> None:
        """Initializes the DB and creates the T-bills table with a composite primary key."""
        try:
            with sqlite3.connect(self.db_filename) as conn:
                cursor = conn.cursor()
                # Using a composite PRIMARY KEY on (scrape_date, tenor) allows us
                # to use "INSERT OR REPLACE" for efficient upserts.
                cursor.execute(
                    f"""
                CREATE TABLE IF NOT EXISTS "{C.TABLE_NAME}" (
                    "{C.DATE_COLUMN_NAME}" TEXT NOT NULL,
                    "{C.TENOR_COLUMN_NAME}" INTEGER NOT NULL,
                    "{C.YIELD_COLUMN_NAME}" REAL NOT NULL,
                    "{C.SESSION_DATE_COLUMN_NAME}" TEXT NOT NULL,
                    PRIMARY KEY ("{C.DATE_COLUMN_NAME}", "{C.TENOR_COLUMN_NAME}")
                )
                """
                )
                conn.commit()
                logger.info(
                    f"Database '{self.db_filename}' and table '{C.TABLE_NAME}' are ready."
                )
        except sqlite3.Error as e:
            logger.critical(f"Database initialization failed: {e}", exc_info=True)
            raise

    def save_data(self, df: pd.DataFrame) -> None:
        """
        Saves a DataFrame to the database using an efficient "INSERT OR REPLACE" strategy.
        This will insert new rows or replace existing rows with the same primary key.

        Args:
            df (pd.DataFrame): The DataFrame containing the T-bill data to save.
        """
        if not isinstance(df, pd.DataFrame) or df.empty:
            logger.warning("Received an empty or invalid DataFrame. Nothing to save.")
            return

        # Ensure required columns exist
        required_cols = [C.DATE_COLUMN_NAME, C.TENOR_COLUMN_NAME, C.YIELD_COLUMN_NAME, C.SESSION_DATE_COLUMN_NAME]
        if not all(col in df.columns for col in required_cols):
            logger.error(f"DataFrame is missing one of the required columns: {required_cols}")
            return
            
        # Convert DataFrame to a list of tuples for executemany
        data_to_save: List[Tuple[Any, ...]] = [tuple(x) for x in df[required_cols].to_numpy()]
        
        logger.info(f"Attempting to upsert {len(data_to_save)} rows.")

        try:
            with sqlite3.connect(self.db_filename) as conn:
                cursor = conn.cursor()
                
                # --- IMPROVEMENT: Using "INSERT OR REPLACE" is more atomic and efficient ---
                # This command inserts a row, or if a row with the same PRIMARY KEY
                # (scrape_date, tenor) already exists, it replaces it.
                query = f"""
                    INSERT OR REPLACE INTO "{C.TABLE_NAME}" 
                    ("{C.DATE_COLUMN_NAME}", "{C.TENOR_COLUMN_NAME}", "{C.YIELD_COLUMN_NAME}", "{C.SESSION_DATE_COLUMN_NAME}") 
                    VALUES (?, ?, ?, ?)
                """
                
                cursor.executemany(query, data_to_save)
                conn.commit()
                
                logger.info(
                    f"Successfully upserted {cursor.rowcount} rows into the database."
                )

        except sqlite3.DatabaseError as e:
            logger.error(f"Failed to save data to SQLite: {e}", exc_info=True)
            raise

    def load_latest_data(self) -> Tuple[pd.DataFrame, str]:
        """
        Loads the most recent complete data set from the SQLite database.
        This is optimized to only query for data matching the latest scrape date.

        Returns:
            A tuple containing a DataFrame with the latest data and a status message.
        """
        fallback_df = pd.DataFrame(C.INITIAL_DATA)

        try:
            with sqlite3.connect(self.db_filename) as conn:
                # Optimized query to get only the data for the latest scrape date
                query = f"""
                    SELECT * FROM "{C.TABLE_NAME}"
                    WHERE "{C.DATE_COLUMN_NAME}" = (SELECT MAX("{C.DATE_COLUMN_NAME}") FROM "{C.TABLE_NAME}")
                """
                latest_df = pd.read_sql_query(query, conn)

                if latest_df.empty:
                    logger.warning("Database is empty. Returning initial data.")
                    return fallback_df, "البيانات الأولية (قاعدة بيانات فارغة)"

                update_date_str = latest_df[C.DATE_COLUMN_NAME].iloc[0]
                update_date_dt = datetime.strptime(update_date_str, "%Y-%m-%d")
                status_message = f"بتاريخ {update_date_dt.strftime('%d-%m-%Y')}"
                logger.info(
                    f"Successfully loaded {len(latest_df)} records from {update_date_str}."
                )
                return latest_df, status_message

        except sqlite3.Error as e:
            # This will catch issues like a corrupt database file
            logger.error(f"A database error occurred while loading data: {e}", exc_info=True)
            return fallback_df, f"خطأ في قاعدة البيانات: {e}"
        except Exception as e:
            # Catch any other unexpected errors
            logger.error(f"An unexpected error occurred while loading data: {e}", exc_info=True)
            return fallback_df, f"خطأ غير متوقع: {e}"
