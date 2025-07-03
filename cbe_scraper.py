# cbe_scraper.py
import pandas as pd
from io import StringIO
from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import logging
import re
import constants as C
from db_manager import DatabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_driver():
    """Sets up a Selenium Chrome driver with appropriate options for automation."""
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    try:
        logging.info("Initializing Google Chrome for automation...")
        options = ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(f'user-agent={user_agent}')
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        logging.info("Google Chrome initialized successfully.")
        return driver
    except Exception as e:
        logging.error(f"FATAL: Could not initialize Chrome driver: {e}")
        raise e

def fetch_data_from_cbe(_db_manager: DatabaseManager):
    """Fetches T-bill data using a targeted, two-table parsing method."""
    driver = setup_driver()
    if not driver:
        return

    try:
        logging.info(f"Navigating to {C.CBE_DATA_URL}")
        driver.get(C.CBE_DATA_URL)
        
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'lxml')

        # --- New, Final, and Correct Parsing Logic ---

        # 1. Find the "Results" (النتائج) table to get the tenors from its header
        results_header = soup.find(lambda tag: tag.name == 'h2' and 'النتائج' in tag.get_text())
        if not results_header:
            raise ValueError("Could not find the 'النتائج' (Results) header.")
        
        results_table = results_header.find_next('table')
        if not results_table:
            raise ValueError("Could not find the table following the 'Results' header.")
            
        results_df = pd.read_html(StringIO(str(results_table)))[0]
        # Tenors are in the header, from the second column onwards
        tenors_list = pd.to_numeric(results_df.columns[1:], errors='coerce').dropna().astype(int).tolist()
        logging.info(f"Successfully extracted tenors from 'Results' table: {tenors_list}")

        # 2. Find the "Accepted Bids" (العروض المقبولة) table to get the correct yields
        accepted_bids_header = soup.find(lambda tag: tag.name in ['p', 'strong'] and 'العروض المقبولة' in tag.get_text())
        if not accepted_bids_header:
            raise ValueError("Could not find the 'العروض المقبولة' (Accepted Bids) header.")
        
        accepted_bids_table = accepted_bids_header.find_next('table')
        if not accepted_bids_table:
            raise ValueError("Could not find the table following the 'Accepted Bids' header.")

        accepted_df = pd.read_html(StringIO(str(accepted_bids_table)))[0]
        
        # 3. Find the yield row within the "Accepted Bids" table
        yield_row_series = None
        for index, row in accepted_df.iterrows():
            if isinstance(row.iloc[0], str) and C.YIELD_ANCHOR_TEXT in row.iloc[0]:
                yield_row_series = row
                break
        
        if yield_row_series is None:
            raise ValueError("Could not find the yield data row in the 'Accepted Bids' table.")
        
        # Extract the correct yields
        yields_list = pd.to_numeric(yield_row_series.iloc[1:len(tenors_list)+1], errors='coerce').dropna().astype(float).tolist()
        logging.info(f"Successfully extracted yields from 'Accepted Bids' table: {yields_list}")

        # 4. Final validation and DataFrame creation
        if not tenors_list or len(tenors_list) != len(yields_list):
            raise ValueError(f"Final data mismatch: Tenors ({len(tenors_list)}), Yields ({len(yields_list)})")

        # Create the final DataFrame and sort it by tenor
        final_df = pd.DataFrame({
            C.TENOR_COLUMN_NAME: tenors_list,
            C.YIELD_COLUMN_NAME: yields_list
        }).sort_values(by=C.TENOR_COLUMN_NAME).reset_index(drop=True)
        
        final_df[C.DATE_COLUMN_NAME] = datetime.now().strftime("%Y-%m-%d")
        
        _db_manager.save_data(final_df)
        logging.info("Data successfully scraped and saved.")

    except Exception as e:
        logging.error(f"An error occurred during scraping: {e}", exc_info=True)
        raise e # Re-raise the exception to fail the workflow
    finally:
        if driver:
            driver.quit()
