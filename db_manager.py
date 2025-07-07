# db_manager.py
import sqlite3
import pandas as pd
import os
import logging
from datetime import datetime
from typing import Tuple

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
        self.db_filename = os.path.join(os.getcwd(), db_filename)
        logger.info(f"Database path set to: {self.db_filename}")
        self._init_db()

    def _init_db(self) -> None:
        """Initializes the DB and creates the T-bills table with a composite primary key."""
        try:
            with sqlite3.connect(self.db_filename) as conn:
                cursor = conn.cursor()
                # Composite PRIMARY KEY on scrape_date and tenor prevents duplicate entries for the same day.
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
        Saves a DataFrame with T-bill data to the database using an "upsert" logic.
        This deletes today's data before inserting the new data to prevent duplicates.

        Args:
            df (pd.DataFrame): The DataFrame containing the T-bill data to save.
        """
        if not isinstance(df, pd.DataFrame) or df.empty:
            logger.warning("Received an empty or invalid DataFrame. Nothing to save.")
            return

        today_str = datetime.now().strftime("%Y-%m-%d")
        logger.info(f"Attempting to save {len(df)} rows for date: {today_str}")

        try:
            with sqlite3.connect(self.db_filename) as conn:
                cursor = conn.cursor()
                # Delete any existing records for today to prevent conflicts
                cursor.execute(
                    f'DELETE FROM "{C.TABLE_NAME}" WHERE "{C.DATE_COLUMN_NAME}" = ?',
                    (today_str,),
                )
                logger.info(f"Deleted {cursor.rowcount} old records for today.")

                # Append the new data
                df.to_sql(C.TABLE_NAME, conn, if_exists="append", index=False)
                logger.info(
                    f"Successfully saved {len(df)} new records for {today_str}."
                )

        except sqlite3.Error as e:
            logger.error(f"Failed to save data to SQLite: {e}", exc_info=True)
            raise

    def load_latest_data(self) -> Tuple[pd.DataFrame, str]:
        """
        Loads the most recent data set from the SQLite database.
        This is optimized to only query for data matching the latest scrape date.

        Returns:
            A tuple containing a DataFrame with the latest data and a status message.
        """
        fallback_df = pd.DataFrame(C.INITIAL_DATA)
        if not os.path.exists(self.db_filename):
            logger.warning("Database file not found. Returning initial data.")
            return fallback_df, "البيانات الأولية (قاعدة بيانات غير موجودة)"

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

        except (sqlite3.Error, pd.errors.DatabaseError) as e:
            logger.error(f"Error loading data: {e}", exc_info=True)
            return fallback_df, f"خطأ في تحميل البيانات: {e}"
