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
import logging
import os
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
    """Fetches T-bill data using a more robust parsing method."""
    driver = setup_driver()
    if not driver:
        return
    
    try:
        logging.info(f"Navigating to {C.CBE_DATA_URL}")
        driver.get(C.CBE_DATA_URL)
        
        # Wait for a generic part of the page to ensure it's loaded
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        page_source = driver.page_source
        
        # Let pandas find all tables on the page directly
        all_dfs = pd.read_html(StringIO(page_source))
        logging.info(f"Pandas found {len(all_dfs)} table(s) on the page.")

        target_df = None
        for df in all_dfs:
            if not df.empty and C.YIELD_ANCHOR_TEXT in df.to_string():
                target_df = df.copy()
                logging.info("Found the target table containing the anchor text.")
                break
        
        if target_df is None:
            raise ValueError("Smarter parsing failed: No table with the anchor text was found.")

        # Re-map columns for consistency and extract data
        target_df.columns = [f'col_{i}' for i in range(len(target_df.columns))]
        tenors_row = target_df.iloc[0, 1:]
        yields_row = target_df[target_df['col_0'] == C.YIELD_ANCHOR_TEXT].iloc[0, 1:]
        
        tenors_list = pd.to_numeric(tenors_row, errors='coerce').dropna().astype(int).tolist()
        yields_list = pd.to_numeric(yields_row, errors='coerce').dropna().astype(float).tolist()

        if not tenors_list or not yields_list or len(tenors_list) != len(yields_list):
            raise ValueError(f"Data extraction failed. Found {len(tenors_list)} tenors and {len(yields_list)} yields.")

        final_df = pd.DataFrame({
            C.TENOR_COLUMN_NAME: tenors_list,
            C.YIELD_COLUMN_NAME: yields_list
        })
        final_df[C.DATE_COLUMN_NAME] = datetime.now().strftime("%Y-%m-%d")
        
        _db_manager.save_data(final_df)
        logging.info("Data successfully scraped and passed to be saved.")

    except Exception as e:
        logging.error(f"An error occurred during scraping: {e}", exc_info=True)
        # Save the page source for debugging if an error occurs
        with open("error_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logging.info("Saved the page source to error_page.html for debugging.")
    finally:
        if driver:
            driver.quit()
