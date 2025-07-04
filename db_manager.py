import sqlite3
import pandas as pd
import os
import traceback
from datetime import datetime
import constants as C
import logging


class DatabaseManager:
    """A class to manage all SQLite database operations."""

    def __init__(self, db_filename=C.DB_FILENAME):
        self.db_filename = os.path.join(os.getcwd(), db_filename)
        logging.info(f"Database path set to: {self.db_filename}")
        self.init_db()

    def init_db(self):
        """Initializes the SQLite database and creates the table with all required columns."""
        try:
            with sqlite3.connect(self.db_filename) as conn:
                # This is the corrected CREATE TABLE statement with the new column
                conn.execute(
                    f"""
                CREATE TABLE IF NOT EXISTS "{C.TABLE_NAME}" (
                    "{C.DATE_COLUMN_NAME}" TEXT NOT NULL,
                    "{C.TENOR_COLUMN_NAME}" INTEGER NOT NULL,
                    "{C.YIELD_COLUMN_NAME}" REAL NOT NULL,
                    "{C.SESSION_DATE_COLUMN_NAME}" TEXT,
                    PRIMARY KEY ("{C.DATE_COLUMN_NAME}", "{C.TENOR_COLUMN_NAME}")
                )
                """
                )
                conn.commit()
            print(
                f"INFO: Database '{self.db_filename}' initialized and table '{C.TABLE_NAME}' is ready."
            )
        except sqlite3.Error as e:
            print(f"ERROR: Database initialization failed: {e}")

    def save_data(self, df: pd.DataFrame):
        """Saves a DataFrame with T-bill data to the database, replacing old data."""
        if df.empty:
            logging.warning("Received an empty DataFrame. Nothing to save.")
            return

        logging.info(f"Attempting to save a DataFrame with {len(df)} rows.")
        try:
            with sqlite3.connect(self.db_filename) as conn:
                # Use if_exists='replace' to clear old data before inserting new data
                # This also helps avoid unique constraint errors if the script is run multiple times a day
                df.to_sql(C.TABLE_NAME, conn, if_exists="replace", index=False)
            print(
                f"INFO: Data for {df[C.DATE_COLUMN_NAME].iloc[0]} successfully saved/updated in SQLite."
            )
        except Exception as e:
            print(f"ERROR: Failed to save data to SQLite: {e}")
            traceback.print_exc()

    def load_latest_data(self):
        """Loads the most recent data from the SQLite database."""
        if not os.path.exists(self.db_filename):
            return (
                pd.DataFrame(C.INITIAL_DATA),
                "البيانات الأولية (قاعدة بيانات غير موجودة)",
            )
        try:
            with sqlite3.connect(self.db_filename) as conn:
                query = f'SELECT * FROM "{C.TABLE_NAME}"'
                latest_df = pd.read_sql_query(query, conn)

                if latest_df.empty:
                    return (
                        pd.DataFrame(C.INITIAL_DATA),
                        "البيانات الأولية (قاعدة بيانات فارغة)",
                    )

            # Get the update date from the loaded data itself
            update_date = latest_df[C.DATE_COLUMN_NAME].iloc[0]
            last_update = datetime.strptime(update_date, "%Y-%m-%d").strftime(
                "%d-%m-%Y"
            )
            return latest_df, f"بتاريخ {last_update}"
        except Exception as e:
            return pd.DataFrame(C.INITIAL_DATA), f"خطأ في تحميل البيانات: {e}"
