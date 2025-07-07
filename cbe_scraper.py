# cbe_scraper.py
import pandas as pd
from io import StringIO
from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import logging
from typing import Optional

import constants as C
from db_manager import DatabaseManager

# Configure logging for this module
logger = logging.getLogger(__name__)

def setup_driver() -> Optional[webdriver.Chrome]:
    """
    Sets up a Selenium Chrome driver.
    It attempts to initialize a standard Chrome driver first (for production/GitHub Actions)
    and falls back to Brave if available locally.

    Returns:
        An instance of selenium.webdriver.Chrome, or None if setup fails.
    """
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"user-agent={C.USER_AGENT}")

    try:
        logger.info("Initializing Selenium driver...")
        # Selenium 4.6+ handles driver management automatically
        driver = webdriver.Chrome(options=options)
        logger.info("Selenium driver initialized successfully.")
        return driver
    except WebDriverException as e:
        logger.error(f"Failed to initialize Selenium driver: {e}", exc_info=True)
        return None

def parse_cbe_html(page_source: str) -> Optional[pd.DataFrame]:
    """
    Parses the HTML source of the CBE page to extract T-bill data.

    Args:
        page_source (str): The HTML content of the page.

    Returns:
        A DataFrame with tenor, yield, and session date, or None on failure.
    """
    soup = BeautifulSoup(page_source, "lxml")
    
    # Find the main results table to get tenors and session dates
    results_header = soup.find(lambda tag: tag.name == "h2" and "النتائج" in tag.get_text())
    if not results_header:
        logger.error("Could not find the 'النتائج' (Results) header.")
        return None
    results_table = results_header.find_next("table")
    if not results_table:
        logger.error("Could not find the table following the 'Results' header.")
        return None
        
    results_df = pd.read_html(StringIO(str(results_table)))[0]
    tenors = pd.to_numeric(results_df.columns[1:], errors='coerce').dropna().astype(int).tolist()
    session_date_row = results_df[results_df.iloc[:, 0] == "تاريخ الجلسة"]
    if session_date_row.empty:
        logger.error("Could not find 'تاريخ الجلسة' row.")
        return None
    session_dates = session_date_row.iloc[0, 1:len(tenors) + 1].tolist()

    # Find the accepted bids table to get yields
    accepted_bids_header = soup.find(lambda tag: tag.name in ["p", "strong"] and C.ACCEPTED_BIDS_KEYWORD in tag.get_text())
    if not accepted_bids_header:
        logger.error("Could not find the 'العروض المقبولة' header.")
        return None
    accepted_bids_table = accepted_bids_header.find_next("table")
    if not accepted_bids_table:
        logger.error("Could not find the table following 'Accepted Bids' header.")
        return None

    accepted_df = pd.read_html(StringIO(str(accepted_bids_table)))[0]
    
    # -- CORRECTED LINE: Added regex=False to perform a literal search and fix the warning/error --
    yield_row = accepted_df[accepted_df.iloc[:, 0].str.contains(C.YIELD_ANCHOR_TEXT, na=False, regex=False)]
    
    if yield_row.empty:
        logger.error(f"Could not find row containing '{C.YIELD_ANCHOR_TEXT}'.")
        return None
    yields = pd.to_numeric(yield_row.iloc[0, 1:len(tenors) + 1], errors='coerce').dropna().astype(float).tolist()

    if not (len(tenors) == len(yields) == len(session_dates)):
        logger.error("Data mismatch between tenors, yields, and session dates.")
        return None

    # Create and return the final DataFrame
    final_df = pd.DataFrame({
        C.TENOR_COLUMN_NAME: tenors,
        C.YIELD_COLUMN_NAME: yields,
        C.SESSION_DATE_COLUMN_NAME: session_dates
    }).sort_values(by=C.TENOR_COLUMN_NAME).reset_index(drop=True)
    
    final_df[C.DATE_COLUMN_NAME] = datetime.now().strftime("%Y-%m-%d")
    return final_df

def fetch_data_from_cbe(db_manager: DatabaseManager) -> None:
    """
    Main function to fetch T-bill data using Selenium, parse it, and save it.

    Args:
        db_manager (DatabaseManager): An instance of the database manager for saving data.
    """
    driver = None
    try:
        driver = setup_driver()
        if not driver:
            raise RuntimeError("Driver setup failed. Aborting scrape.")

        logger.info(f"Navigating to {C.CBE_DATA_URL}")
        driver.get(C.CBE_DATA_URL)
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        page_source = driver.page_source
        final_df = parse_cbe_html(page_source)

        if final_df is not None:
            db_manager.save_data(final_df)
            logger.info("Data successfully scraped and saved.")
        else:
            logger.error("Parsing failed. No data was saved.")

    except TimeoutException:
        logger.error("Page load timed out. The website might be down or slow.", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred during scraping: {e}", exc_info=True)
    finally:
        if driver:
            logger.info("Closing Selenium driver.")
            driver.quit()
