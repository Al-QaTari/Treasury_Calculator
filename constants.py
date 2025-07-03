# --- Centralized Constants ---

# Column Names
TENOR_COLUMN_NAME = "المدة (الأيام)"
YIELD_COLUMN_NAME = "متوسط العائد المرجح المقبول (%)"
DATE_COLUMN_NAME = "تاريخ العطاء"

# Database
DB_FILENAME = "cbe_historical_data.db"
TABLE_NAME = "cbe_bids"

# Web Scraping
CBE_DATA_URL = "https://www.cbe.org.eg/ar/auctions/egp-t-bills"
YIELD_ANCHOR_TEXT = "متوسط العائد المرجح (%)"

# Financial
DAYS_IN_YEAR = 365
DEFAULT_TAX_RATE_PERCENT = 20.0

# Initial Data (Fallback)
INITIAL_DATA = {
    TENOR_COLUMN_NAME: [91, 182, 273, 364],
    YIELD_COLUMN_NAME: [26.914, 27.151, 26.534, 24.994]
}