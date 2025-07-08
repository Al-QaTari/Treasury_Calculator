# utils.py (النسخة المحسنة مع دوال مساعدة إضافية)
import streamlit as st
import os
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


# --- الدالة الأصلية (لا تزال مفيدة كطبقة تجريد) ---
def prepare_arabic_text(text: str) -> str:
    """
    This function now does nothing because the system handles Arabic correctly.
    It just returns the text as it is.
    """
    return str(text)


# --- الدالة الأصلية ---
def load_css(file_path: str) -> None:
    """
    Loads an external CSS file into the Streamlit app for custom styling.
    """
    if os.path.exists(file_path):
        with open(file_path, encoding='utf-8') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        logger.warning(f"CSS file not found at path: {file_path}")


# --- IMPROVEMENT 1: Centralized Logging Configuration ---
def setup_logging(level: int = logging.INFO) -> None:
    """
    Configures the root logger for consistent formatting across all modules.
    Should be called once when the application starts.
    """
    # Prevents adding handlers multiple times in Streamlit's rerun cycle
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[logging.StreamHandler()]
        )
        logger.info("Logging configured successfully.")


# --- IMPROVEMENT 2: Currency Formatter Utility ---
def format_currency(value: Optional[float], currency_symbol: str = "جنيه") -> str:
    """
    Formats a numeric value into a standardized currency string.

    Args:
        value (Optional[float]): The number to format.
        currency_symbol (str): The currency symbol or text to append.

    Returns:
        A formatted currency string (e.g., "12,345.68 جنيه").
    """
    if value is None:
        return f"- {prepare_arabic_text(currency_symbol)}"
    try:
        return f"{value:,.2f} {prepare_arabic_text(currency_symbol)}"
    except (ValueError, TypeError):
        return str(value)


# --- IMPROVEMENT 3: Reusable UI Component Builder ---
def create_metric_box(title: str, value: Any, unit: str = "", color: str = "#8ab4f8", value_font_size: str = "1.9rem") -> str:
    """
    Generates the HTML for a styled metric box.

    Args:
        title (str): The title of the metric.
        value (Any): The value to display.
        unit (str): The unit for the value (e.g., "جنيه", "%").
        color (str): The CSS color for the value text.
        value_font_size (str): The CSS font size for the value.

    Returns:
        An HTML string to be used with st.markdown.
    """
    prepared_title = prepare_arabic_text(title)
    prepared_unit = prepare_arabic_text(unit)
    
    return f"""
    <div style="text-align: center; background-color: #495057; padding: 10px; border-radius: 10px; height: 100%;">
        <p style="font-size: 1rem; color: #adb5bd; margin-bottom: 0px;">{prepared_title}</p>
        <p style="font-size: {value_font_size}; color: {color}; font-weight: 600; line-height: 1.2; margin-top: 5px;">
            {value} <span style='font-size: 1rem;'>{prepared_unit}</span>
        </p>
    </div>
    """
