# cbe_scraper.py
import pandas as pd
from io import StringIO
from datetime import datetime
import streamlit as st
from selenium import webdriver
from selenium.common.exceptions import WebDriverException

# Imports for browser managers
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager

# Imports for Selenium waits and parsing
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import logging
import os

# Imports from other project files
import constants as C
from db_manager import DatabaseManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_driver():
    """Tries to set up a Selenium driver by checking for available browsers in a specific order."""
    
    # 1. Try Google Chrome
    try:
        logging.info("Attempt 1: Initializing Google Chrome...")
        options = ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        logging.info("Google Chrome initialized successfully.")
        return driver
    except (WebDriverException, FileNotFoundError, ValueError):
        logging.warning("Google Chrome not found or failed to initialize.")

    # 2. Try Brave
    try:
        logging.info("Attempt 2: Initializing Brave Browser...")
        options = ChromeOptions()
        brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
        if os.path.exists(brave_path):
            options.binary_location = brave_path
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            logging.info("Brave Browser initialized successfully.")
            return driver
        else:
            logging.warning("Brave browser executable not found at the specified path.")
    except (WebDriverException, FileNotFoundError, ValueError):
        logging.warning("Brave Browser not found or failed to initialize.")

    # 3. Try Microsoft Edge
    try:
        logging.info("Attempt 3: Initializing Microsoft Edge...")
        options = EdgeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        service = EdgeService(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=options)
        logging.info("Microsoft Edge initialized successfully.")
        return driver
    except (WebDriverException, FileNotFoundError, ValueError):
        logging.warning("Microsoft Edge not found or failed to initialize.")

    # 4. Try Mozilla Firefox
    try:
        logging.info("Attempt 4: Initializing Mozilla Firefox...")
        options = FirefoxOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        service = FirefoxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
        logging.info("Mozilla Firefox initialized successfully.")
        return driver
    except (WebDriverException, FileNotFoundError, ValueError):
        logging.error("All fallback browsers (Firefox) failed to initialize.")

    return None

@st.cache_data(ttl=43200)
def fetch_data_from_cbe(_db_manager: DatabaseManager):
    """Fetches T-bill data using the first available browser."""
    
    driver = setup_driver()

    if not driver:
        return None, 'ERROR', "فشل تشغيل المتصفحات. يرجى التأكد من تثبيت Chrome, Brave, Edge, أو Firefox."

    try:
        driver.set_page_load_timeout(60)
        driver.get(C.CBE_DATA_URL)
        wait_xpath = f"//*[contains(text(), '{C.YIELD_ANCHOR_TEXT}')]"
        WebDriverWait(driver, 45).until(EC.presence_of_element_located((By.XPATH, wait_xpath)))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        tables = soup.find_all('table', {'class': 'table'})
        target_table = next((table for table in tables if C.YIELD_ANCHOR_TEXT in table.text), None)
        
        if not target_table:
            raise ValueError("Could not find the target data table on the page.")

        df_list = pd.read_html(StringIO(str(target_table)))
        df = df_list[0]
        df.columns = [f'col_{i}' for i in range(len(df.columns))]
        tenors_row = df.iloc[0, 1:]
        yields_row = df[df['col_0'] == C.YIELD_ANCHOR_TEXT].iloc[0, 1:]
        tenors_list = pd.to_numeric(tenors_row, errors='coerce').dropna().astype(int).tolist()
        yields_list = pd.to_numeric(yields_row, errors='coerce').dropna().astype(float).tolist()

        if len(tenors_list) != len(yields_list):
            raise ValueError(f"Data mismatch: Found {len(tenors_list)} tenors and {len(yields_list)} yields.")

        final_df = pd.DataFrame({
            C.TENOR_COLUMN_NAME: tenors_list,
            C.YIELD_COLUMN_NAME: yields_list
        })
        
        final_df[C.DATE_COLUMN_NAME] = datetime.now().strftime("%Y-%m-%d")
        
        _db_manager.save_data(final_df)
        return final_df, 'SUCCESS', "تم تحديث البيانات بنجاح!"

    except Exception as e:
        error_message = f"فشل جلب البيانات: {str(e)}"
        logging.error(error_message, exc_info=True)
        return None, 'ERROR', error_message
    finally:
        if driver:
            logging.info("Closing Selenium WebDriver.")
            driver.quit()
