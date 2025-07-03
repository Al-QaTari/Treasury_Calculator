import pandas as pd
from io import StringIO
from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import logging
import os
import constants as C
from db_manager import DatabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_driver():
    """Tries to set up a Selenium driver with a common User-Agent."""
    
    # A common User-Agent to mimic a real browser
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    
    try:
        logging.info("Attempt 1: Initializing Google Chrome...")
        options = ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f'user-agent={user_agent}') # Add User-Agent
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        logging.info("Google Chrome initialized successfully.")
        return driver
    except Exception as e:
        logging.warning(f"Google Chrome failed: {e}")

    # Fallback browsers can also be configured if needed, but Chrome on the runner is standard
    return None

def fetch_data_from_cbe(_db_manager: DatabaseManager):
    """Fetches T-bill data using the first available browser."""
    driver = setup_driver()
    if not driver:
        return

    try:
        driver.get(C.CBE_DATA_URL)
        # Increased timeout to 60 seconds
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{C.YIELD_ANCHOR_TEXT}')]"))
        )
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        # ... (Rest of the scraping logic remains the same)
        tables = soup.find_all('table', {'class': 'table'})
        target_table = next((table for table in tables if C.YIELD_ANCHOR_TEXT in table.text), None)
        if not target_table:
            raise ValueError("Could not find the target data table on the page.")

        df = pd.read_html(StringIO(str(target_table)))[0]
        df.columns = [f'col_{i}' for i in range(len(df.columns))]
        tenors_row = df.iloc[0, 1:]
        yields_row = df[df['col_0'] == C.YIELD_ANCHOR_TEXT].iloc[0, 1:]
        tenors_list = pd.to_numeric(tenors_row, errors='coerce').dropna().astype(int).tolist()
        yields_list = pd.to_numeric(yields_row, errors='coerce').dropna().astype(float).tolist()

        if len(tenors_list) != len(yields_list):
            raise ValueError(f"Data mismatch: {len(tenors_list)} tenors, {len(yields_list)} yields.")

        final_df = pd.DataFrame({
            C.TENOR_COLUMN_NAME: tenors_list,
            C.YIELD_COLUMN_NAME: yields_list
        })
        final_df[C.DATE_COLUMN_NAME] = datetime.now().strftime("%Y-%m-%d")
        _db_manager.save_data(final_df)
    except TimeoutException:
        logging.error("TimeoutException: The page took too long to load or the target element was not found.")
    except Exception as e:
        logging.error(f"An error occurred during scraping: {e}", exc_info=True)
    finally:
        if driver:
            driver.quit()
