# constants.py
"""
Centralized constants for the Treasury Calculator application.
This file consolidates all magic strings, column names, URLs, and default values
to improve maintainability and prevent errors.
"""

# --- Column Names ---
TENOR_COLUMN_NAME = "tenor"
YIELD_COLUMN_NAME = "yield"
DATE_COLUMN_NAME = "scrape_date"
SESSION_DATE_COLUMN_NAME = "session_date"

# --- Database ---
DB_FILENAME = "cbe_historical_data.db"
TABLE_NAME = "cbe_t_bills"

# --- Web Scraping ---
CBE_DATA_URL = "https://www.cbe.org.eg/ar/auctions/egp-t-bills"
# -- CORRECTED LINE: Made the search text more general to avoid errors --
YIELD_ANCHOR_TEXT = "متوسط العائد المرجح"  # Text to find the yield row
ACCEPTED_BIDS_KEYWORD = "المقبولة"  # Keyword to find the accepted bids table
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"

# --- Financial ---
DAYS_IN_YEAR = 365.0
DEFAULT_TAX_RATE_PERCENT = 20.0

# --- Initial Data (Fallback) ---
# Used only if the database is empty or inaccessible
INITIAL_DATA = {
    TENOR_COLUMN_NAME: [91, 182, 273, 364],
    YIELD_COLUMN_NAME: [26.0, 26.5, 27.0, 27.5],  # Example yields
    SESSION_DATE_COLUMN_NAME: ["N/A", "N/A", "N/A", "N/A"],
}

# --- UI Constants ---
APP_TITLE = "🏦 حاسبة أذون الخزانة المصرية"
APP_HEADER = "تطبيق تفاعلي لحساب وتحليل عوائد أذون الخزانة المصرية"
SIDEBAR_TITLE = "خيارات التحكم"
PRIMARY_CALCULATOR_TITLE = "🧮 حاسبة العائد الأساسية (الشراء والاحتفاظ)"
SECONDARY_CALCULATOR_TITLE = "⚖️ حاسبة تحليل البيع في السوق الثانوي"
HELP_TITLE = "💡 شرح ومساعدة (أسئلة شائعة)"
AUTHOR_NAME = "Mohamed AL-QaTri"

# --- Paths ---
CSS_FILE_PATH = "css/style.css"
