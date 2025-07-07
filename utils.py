# utils.py
import streamlit as st
import os
import logging

logger = logging.getLogger(__name__)


def prepare_arabic_text(text: str) -> str:
    """
    This function now does nothing because the system handles Arabic correctly.
    It just returns the text as it is.
    """
    # The modern environment handles reshaping and bidi display automatically.
    # Therefore, no processing is needed.
    return str(text)


def load_css(file_path: str) -> None:
    """
    Loads an external CSS file into the Streamlit app for custom styling.
    """
    if os.path.exists(file_path):
        with open(file_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        logger.warning(f"CSS file not found at path: {file_path}")
