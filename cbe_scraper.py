import pandas as pd
from io import StringIO
from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import logging
import os
import constants as C
from db_manager import DatabaseManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def setup_driver():
    """Sets up a Selenium driver using Selenium's modern, built-in driver manager."""
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"

    # 1. Try Google Chrome (for GitHub Actions runner)
    try:
        logging.info("Attempt 1: Initializing Google Chrome...")
        options = ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(f"user-agent={user_agent}")
        # Selenium 4.6+ will handle the driver automatically
        driver = webdriver.Chrome(options=options)
        logging.info("Google Chrome initialized successfully.")
        return driver
    except WebDriverException:
        logging.warning("Google Chrome not found or failed. Trying Brave...")

    # 2. Try Brave (for your local machine)
    try:
        logging.info("Attempt 2: Initializing Brave Browser...")
        options = ChromeOptions()
        brave_path = (
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
        )
        if os.path.exists(brave_path):
            options.binary_location = brave_path
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")
            options.add_argument(f"user-agent={user_agent}")
            # Selenium 4.6+ will automatically find the matching driver for the specified binary
            driver = webdriver.Chrome(options=options)
            logging.info("Brave Browser initialized successfully.")
            return driver
        else:
            logging.warning("Brave browser executable not found at the default path.")
    except WebDriverException as e:
        logging.warning(f"Brave Browser failed to initialize: {e}")

    raise RuntimeError(
        "Could not initialize any supported browser. Please ensure Chrome or Brave is installed correctly."
    )


def fetch_data_from_cbe(_db_manager: DatabaseManager):
    """Fetches T-bill data using a robust parser and driver setup."""
    driver = None
    try:
        driver = setup_driver()

        logging.info(f"Navigating to {C.CBE_DATA_URL}")
        driver.get(C.CBE_DATA_URL)

        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "lxml")

        results_header = soup.find(
            lambda tag: tag.name == "h2" and "النتائج" in tag.get_text()
        )
        if not results_header:
            raise ValueError("Could not find the 'النتائج' (Results) header.")
        results_table = results_header.find_next("table")
        if not results_table:
            raise ValueError("Could not find the table following the 'Results' header.")

        results_df = pd.read_html(StringIO(str(results_table)))[0]
        tenors_list = (
            pd.to_numeric(results_df.columns[1:], errors="coerce")
            .dropna()
            .astype(int)
            .tolist()
        )
        session_date_row = results_df[results_df.iloc[:, 0] == "تاريخ الجلسة"].iloc[0]
        session_dates = session_date_row[1 : len(tenors_list) + 1].tolist()
        logging.info(
            f"Extracted tenors: {tenors_list} and session dates: {session_dates}"
        )

        accepted_bids_header = soup.find(
            lambda tag: tag.name in ["p", "strong"]
            and C.ACCEPTED_BIDS_KEYWORD in tag.get_text()
        )
        if not accepted_bids_header:
            raise ValueError("Could not find the 'العروض المقبولة' header.")
        accepted_bids_table = accepted_bids_header.find_next("table")
        if not accepted_bids_table:
            raise ValueError(
                "Could not find the table following 'Accepted Bids' header."
            )

        accepted_df = pd.read_html(StringIO(str(accepted_bids_table)))[0]

        yield_row_series = next(
            (
                row
                for _, row in accepted_df.iterrows()
                if isinstance(row.iloc[0], str) and C.YIELD_ANCHOR_TEXT in row.iloc[0]
            ),
            None,
        )
        if yield_row_series is None:
            raise ValueError("Could not find the yield data row.")

        yields_list = (
            pd.to_numeric(
                yield_row_series.iloc[1 : len(tenors_list) + 1], errors="coerce"
            )
            .dropna()
            .astype(float)
            .tolist()
        )
        logging.info(f"Extracted yields: {yields_list}")

        if not all([tenors_list, yields_list, session_dates]) or not (
            len(tenors_list) == len(yields_list) == len(session_dates)
        ):
            raise ValueError("Data mismatch between tenors, yields, and session dates.")

        data_map = {
            tenor: {"yield": yields_list[i], "session_date": session_dates[i]}
            for i, tenor in enumerate(tenors_list)
        }
        sorted_tenors = sorted(data_map.keys())

        final_df = pd.DataFrame(
            {
                C.TENOR_COLUMN_NAME: sorted_tenors,
                C.YIELD_COLUMN_NAME: [data_map[t]["yield"] for t in sorted_tenors],
                C.SESSION_DATE_COLUMN_NAME: [
                    data_map[t]["session_date"] for t in sorted_tenors
                ],
            }
        )

        final_df[C.DATE_COLUMN_NAME] = datetime.now().strftime("%Y-%m-%d")
        _db_manager.save_data(final_df)
        logging.info("Data successfully scraped and saved.")

    except Exception as e:
        logging.error(f"An error occurred during scraping: {e}", exc_info=True)
    finally:
        if driver:
            driver.quit()
