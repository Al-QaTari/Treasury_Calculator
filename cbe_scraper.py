# cbe_scraper.py (النسخة النهائية والمحسنة باستخدام webdriver-manager)
import pandas as pd
from io import StringIO
from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import logging
import time
from typing import Optional

# --- IMPROVEMENT: Use webdriver-manager for automatic driver handling ---
from webdriver_manager.chrome import ChromeDriverManager

import constants as C
from db_manager import DatabaseManager

# Configure logging for this module
logger = logging.getLogger(__name__)


# --- IMPROVEMENT: Simplified and more robust driver setup ---
def setup_driver() -> Optional[webdriver.Chrome]:
    """
    Sets up a Selenium Chrome driver automatically using webdriver-manager.
    This works on local machines (Windows/macOS/Linux) and servers
    as long as Google Chrome or Chromium is installed.
    """
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"user-agent={C.USER_AGENT}")

    try:
        logger.info("Setting up Selenium driver using webdriver-manager...")
        # webdriver-manager will download the correct driver version and cache it.
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        logger.info("Selenium driver initialized successfully.")
        return driver
    except WebDriverException as e:
        logger.error(
            "Failed to initialize Selenium driver. "
            "Please ensure Google Chrome or Chromium browser is installed on this system. "
            f"Error: {e}",
            exc_info=True,
        )
        return None


def parse_cbe_html(page_source: str) -> Optional[pd.DataFrame]:
    """
    Parses the HTML source of the CBE page to extract T-bill data.
    """
    logger.info("Starting to parse HTML content...")
    soup = BeautifulSoup(page_source, "lxml")

    results_header = soup.find(
        lambda tag: tag.name == "h2" and "النتائج" in tag.get_text()
    )
    if not results_header:
        logger.error("Parse Error: Could not find the 'النتائج' (Results) header.")
        return None
    results_table = results_header.find_next("table")
    if not results_table:
        logger.error(
            "Parse Error: Could not find the table following the 'Results' header."
        )
        return None

    results_df = pd.read_html(StringIO(str(results_table)))[0]
    tenors = (
        pd.to_numeric(results_df.columns[1:], errors="coerce")
        .dropna()
        .astype(int)
        .tolist()
    )
    session_date_row = results_df[results_df.iloc[:, 0] == "تاريخ الجلسة"]
    if session_date_row.empty:
        logger.error("Parse Error: Could not find 'تاريخ الجلسة' row.")
        return None
    session_dates = session_date_row.iloc[0, 1 : len(tenors) + 1].tolist()

    accepted_bids_header = soup.find(
        lambda tag: tag.name in ["p", "strong"]
        and C.ACCEPTED_BIDS_KEYWORD in tag.get_text()
    )
    if not accepted_bids_header:
        logger.error("Parse Error: Could not find the 'العروض المقبولة' header.")
        return None
    accepted_bids_table = accepted_bids_header.find_next("table")
    if not accepted_bids_table:
        logger.error(
            "Parse Error: Could not find the table following 'Accepted Bids' header."
        )
        return None

    accepted_df = pd.read_html(StringIO(str(accepted_bids_table)))[0]
    yield_row = accepted_df[
        accepted_df.iloc[:, 0].str.contains(C.YIELD_ANCHOR_TEXT, na=False, regex=False)
    ]

    if yield_row.empty:
        logger.error(
            f"Parse Error: Could not find row containing '{C.YIELD_ANCHOR_TEXT}'."
        )
        return None
    yields = (
        pd.to_numeric(yield_row.iloc[0, 1 : len(tenors) + 1], errors="coerce")
        .dropna()
        .astype(float)
        .tolist()
    )

    if not (len(tenors) == len(yields) == len(session_dates)):
        logger.error(
            f"Data Mismatch: Found {len(tenors)} tenors, {len(yields)} yields, and {len(session_dates)} dates."
        )
        return None

    logger.info(f"Successfully parsed data for {len(tenors)} tenors.")
    final_df = (
        pd.DataFrame(
            {
                C.TENOR_COLUMN_NAME: tenors,
                C.YIELD_COLUMN_NAME: yields,
                C.SESSION_DATE_COLUMN_NAME: session_dates,
            }
        )
        .sort_values(by=C.TENOR_COLUMN_NAME)
        .reset_index(drop=True)
    )

    final_df[C.DATE_COLUMN_NAME] = datetime.now().strftime("%Y-%m-%d")
    return final_df


def fetch_data_from_cbe(db_manager: DatabaseManager) -> None:
    """
    Main function to fetch T-bill data using Selenium, parse it, and save it.
    """
    # --- IMPROVEMENT: Use constants for retries and delays ---
    retries = C.SCRAPER_RETRIES
    delay_seconds = C.SCRAPER_RETRY_DELAY_SECONDS

    for attempt in range(retries):
        driver = None
        logger.info(f"--- Starting scrape attempt {attempt + 1} of {retries} ---")
        try:
            driver = setup_driver()
            if not driver:
                raise RuntimeError("Driver setup failed. Aborting this attempt.")

            logger.info(f"Navigating to {C.CBE_DATA_URL}")
            driver.get(C.CBE_DATA_URL)

            WebDriverWait(driver, C.SCRAPER_TIMEOUT_SECONDS).until(
                EC.presence_of_element_located((By.TAG_NAME, "h2"))
            )

            page_source = driver.page_source
            final_df = parse_cbe_html(page_source)

            if final_df is not None:
                db_manager.save_data(final_df)
                logger.info(
                    "Data successfully scraped and saved. Mission accomplished."
                )
                return  # Exit after success
            else:
                logger.error("Parsing failed. No data was saved for this attempt.")

        except TimeoutException:
            logger.warning(
                f"Page load timed out on attempt {attempt + 1}.", exc_info=True
            )
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during attempt {attempt + 1}: {e}",
                exc_info=True,
            )
        finally:
            if driver:
                logger.info("Closing Selenium driver for this attempt.")
                driver.quit()

        if attempt < retries - 1:
            logger.info(f"Waiting for {delay_seconds} seconds before next attempt...")
            time.sleep(delay_seconds)

    logger.critical(
        f"All {retries} attempts to fetch data from CBE failed. Please check logs for details."
    )
