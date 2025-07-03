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
        """Initializes the SQLite database and creates the table if it doesn't exist."""
        try:
            with sqlite3.connect(self.db_filename) as conn:
                cursor = conn.cursor()
                conn.execute(f"""
                CREATE TABLE IF NOT EXISTS "{C.TABLE_NAME}" (
                    "{C.DATE_COLUMN_NAME}" TEXT NOT NULL,
                    "{C.TENOR_COLUMN_NAME}" INTEGER NOT NULL,
                    "{C.YIELD_COLUMN_NAME}" REAL NOT NULL,
                    PRIMARY KEY ("{C.DATE_COLUMN_NAME}", "{C.TENOR_COLUMN_NAME}")
                )
                """)
                conn.commit()
            print(f"INFO: Database '{self.db_filename}' initialized and table '{C.TABLE_NAME}' is ready.")
        except sqlite3.Error as e:
            print(f"ERROR: Database initialization failed: {e}")
            traceback.print_exc()

    def save_data(self, df: pd.DataFrame):
        """Saves a DataFrame with T-bill data to the database."""
        if df.empty:
            logging.warning("Received an empty DataFrame. Nothing to save.")
            return
        
        logging.info(f"Attempting to save a DataFrame with {len(df)} rows.")
        try:
            with sqlite3.connect(self.db_filename) as conn:
                # The 'conn' object here is the connection, which is what to_sql expects
                df.to_sql(C.TABLE_NAME, conn, if_exists='append', index=False, method=self._upsert)
            print(f"INFO: Data for {df[C.DATE_COLUMN_NAME].iloc[0]} successfully saved/updated in SQLite.")
        except Exception as e:
            print(f"ERROR: Failed to save data to SQLite: {e}")
            traceback.print_exc()

    @staticmethod
    def _upsert(table, conn, keys, data_iter):
        """Custom upsert method for pandas to_sql to handle INSERT OR REPLACE."""
        # In this specific context, pandas passes a 'sqlalchemy.engine.base.Connection'
        # which can execute commands directly. We don't need to create a cursor.
        data = [dict(zip(keys, row)) for row in data_iter]
        # The line below is the only change. We use 'conn.executemany' directly.
        conn.executemany(f"""
            INSERT OR REPLACE INTO "{table.name}" ({', '.join(f'"{k}"' for k in keys)})
            VALUES ({', '.join('?' for _ in keys)})
        """, [list(d.values()) for d in data])


    def load_latest_data(self):
        """Loads the most recent data from the SQLite database."""
        if not os.path.exists(self.db_filename):
            return pd.DataFrame(C.INITIAL_DATA), "البيانات الأولية (قاعدة بيانات غير موجودة)"
        try:
            with sqlite3.connect(self.db_filename) as conn:
                latest_date_query = f'SELECT MAX("{C.DATE_COLUMN_NAME}") FROM "{C.TABLE_NAME}"'
                latest_date = pd.read_sql_query(latest_date_query, conn).iloc[0, 0]
                if latest_date is None:
                    return pd.DataFrame(C.INITIAL_DATA), "البيانات الأولية (قاعدة بيانات فارغة)"
                query = f'SELECT * FROM "{C.TABLE_NAME}" WHERE "{C.DATE_COLUMN_NAME}" = ?'
                latest_df = pd.read_sql_query(query, conn, params=(latest_date,))
            file_mod_time = os.path.getmtime(self.db_filename)
            last_update = datetime.fromtimestamp(file_mod_time).strftime("%d-%m-%Y %H:%M")
            return latest_df, last_update
        except Exception as e:
            print(f"ERROR: Failed to load data: {e}")
            traceback.print_exc()
            return pd.DataFrame(C.INITIAL_DATA), f"خطأ في تحميل البيانات: {e}"
