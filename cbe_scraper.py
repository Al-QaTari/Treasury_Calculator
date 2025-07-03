# cbe_scraper.py
import pandas as pd
from io import StringIO
from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException
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
        return None

def fetch_data_from_cbe(_db_manager: DatabaseManager):
    """Fetches T-bill data using a highly robust parsing method that targets the 'Accepted' bids table."""
    driver = setup_driver()
    if not driver:
        # If driver setup fails, raise an exception to fail the workflow
        raise RuntimeError("Failed to setup Selenium driver.")

    try:
        logging.info(f"Navigating to {C.CBE_DATA_URL}")
        driver.get(C.CBE_DATA_URL)
        
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        page_source = driver.page_source
        
        all_dfs = pd.read_html(StringIO(page_source))
        logging.info(f"Pandas found {len(all_dfs)} table(s) on the page.")

        ACCEPTED_BIDS_KEYWORD = "المقبولة"
        target_df = None
        for df in all_dfs:
            df_string = df.to_string()
            if not df.empty and C.YIELD_ANCHOR_TEXT in df_string and ACCEPTED_BIDS_KEYWORD in df_string:
                target_df = df.copy()
                logging.info("Found the correct 'Accepted Bids' table.")
                break
        
        if target_df is None:
            raise ValueError("Parsing failed: Could not find the 'Accepted Bids' table.")

        tenors_list = []
        for col in target_df.columns:
            numbers = re.findall(r'\d+', str(col))
            if numbers:
                tenors_list.append(int(numbers[0]))
        
        logging.info(f"Extracted tenors from headers: {tenors_list}")

        yield_row_series = None
        for index, row in target_df.iterrows():
            if isinstance(row.iloc[0], str) and C.YIELD_ANCHOR_TEXT in row.iloc[0]:
                yield_row_series = row
                break
        
        if yield_row_series is None:
            raise ValueError("Could not find the yield data row in the target table.")
            
        yields_list = pd.to_numeric(yield_row_series.iloc[1:len(tenors_list)+1], errors='coerce').dropna().astype(float).tolist()
        logging.info(f"Extracted yields from data row: {yields_list}")

        if not tenors_list or len(tenors_list) != len(yields_list):
            raise ValueError(f"Data mismatch after extraction: Tenors ({len(tenors_list)}), Yields ({len(yields_list)})")

        final_df = pd.DataFrame({
            C.TENOR_COLUMN_NAME: tenors_list,
            C.YIELD_COLUMN_NAME: yields_list
        })
        final_df[C.DATE_COLUMN_NAME] = datetime.now().strftime("%Y-%m-%d")
        
        _db_manager.save_data(final_df)
        logging.info("Data successfully scraped and passed to be saved.")

    except Exception as e:
        logging.error(f"An error occurred during scraping: {e}", exc_info=True)
        with open("error_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logging.info("Saved the page source to error_page.html for debugging.")
        # --- السطر الجديد والمهم ---
        # هذا السطر سيجبر الـ workflow على الفشل بشكل صحيح
        raise e
    finally:
        if driver:
            driver.quit()
