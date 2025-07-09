# db_manager.py (النسخة المحسنة مع Caching ودالة جديدة)
import sqlite3
import pandas as pd
import os
import logging
from datetime import datetime
from typing import Tuple, List, Any
import streamlit as st

import constants as C

# Configure logging for this module
logger = logging.getLogger(__name__)


# --- IMPROVEMENT: Cache the DatabaseManager instance itself ---
# This prevents re-initializing the connection on every script rerun.
@st.cache_resource
def get_db_manager(db_filename: str = C.DB_FILENAME) -> "DatabaseManager":
    """Factory function to get a cached instance of DatabaseManager."""
    return DatabaseManager(db_filename)


class DatabaseManager:
    """A robust class to manage all SQLite database operations for the T-bill data."""

    def __init__(self, db_filename: str = C.DB_FILENAME):
        self.db_filename = os.path.abspath(db_filename)
        logger.info(f"Initializing new DB Manager instance for: {self.db_filename}")
        self._init_db()

    def _init_db(self) -> None:
        """Initializes the DB and creates the T-bills table with a composite primary key."""
        try:
            with sqlite3.connect(self.db_filename) as conn:
                cursor = conn.cursor()
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
        """
        if not isinstance(df, pd.DataFrame) or df.empty:
            logger.warning("Received an empty or invalid DataFrame. Nothing to save.")
            return

        required_cols = [
            C.DATE_COLUMN_NAME,
            C.TENOR_COLUMN_NAME,
            C.YIELD_COLUMN_NAME,
            C.SESSION_DATE_COLUMN_NAME,
        ]
        if not all(col in df.columns for col in required_cols):
            logger.error(
                f"DataFrame is missing one of the required columns: {required_cols}"
            )
            return

        data_to_save: List[Tuple[Any, ...]] = [
            tuple(x) for x in df[required_cols].to_numpy()
        ]

        logger.info(f"Attempting to upsert {len(data_to_save)} rows.")

        try:
            with sqlite3.connect(self.db_filename) as conn:
                cursor = conn.cursor()
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
                # --- IMPROVEMENT: Clear caches after updating data ---
                st.cache_data.clear()
                logger.info("Cleared Streamlit data caches after update.")
        except sqlite3.DatabaseError as e:
            logger.error(f"Failed to save data to SQLite: {e}", exc_info=True)
            raise

    # --- IMPROVEMENT: Cache the data loading functions ---
    @st.cache_data
    def load_latest_data(_self) -> Tuple[pd.DataFrame, str]:
        """Loads the most recent complete data set."""
        logger.info("Executing 'load_latest_data' (will be cached).")
        fallback_df = pd.DataFrame(C.INITIAL_DATA)
        try:
            with sqlite3.connect(_self.db_filename) as conn:
                query = f"""
                    SELECT * FROM "{C.TABLE_NAME}"
                    WHERE "{C.DATE_COLUMN_NAME}" = (SELECT MAX("{C.DATE_COLUMN_NAME}") FROM "{C.TABLE_NAME}")
                """
                latest_df = pd.read_sql_query(query, conn)
                if latest_df.empty:
                    return fallback_df, "البيانات الأولية (قاعدة بيانات فارغة)"
                update_date_str = latest_df[C.DATE_COLUMN_NAME].iloc[0]
                update_date_dt = datetime.strptime(update_date_str, "%Y-%m-%d")
                status_message = f"بتاريخ {update_date_dt.strftime('%d-%m-%Y')}"
                return latest_df, status_message
        except Exception as e:
            logger.error(
                f"An error occurred while loading latest data: {e}", exc_info=True
            )
            return fallback_df, f"خطأ في قاعدة البيانات: {e}"

    # --- NEW FUNCTION: To load all data for historical charts ---
    @st.cache_data
    def load_all_historical_data(_self) -> pd.DataFrame:
        """Loads all historical data from the database for charting."""
        logger.info("Executing 'load_all_historical_data' (will be cached).")
        try:
            with sqlite3.connect(_self.db_filename) as conn:
                query = f'SELECT * FROM "{C.TABLE_NAME}"'
                df = pd.read_sql_query(query, conn)
                df[C.DATE_COLUMN_NAME] = pd.to_datetime(df[C.DATE_COLUMN_NAME])
                df[C.TENOR_COLUMN_NAME] = df[C.TENOR_COLUMN_NAME].astype(str)
                return df
        except Exception as e:
            logger.error(f"Failed to load historical data: {e}", exc_info=True)
            return pd.DataFrame()
