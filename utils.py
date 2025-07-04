import arabic_reshaper
from bidi.algorithm import get_display
import streamlit as st
import os

def prepare_arabic_text(text: str) -> str:
    """
    Handles Arabic text shaping for correct display in Streamlit widgets.
    """
    if text is None:
        return ""
    try:
        configuration = {'delete_harakat': True, 'support_ligatures': True}
        reshaped_text = arabic_reshaper.reshape(str(text), configuration)
        return get_display(reshaped_text)
    except Exception:
        return str(text)

def load_css(file_path: str):
    """
    Loads an external CSS file into the Streamlit app.
    """
    if os.path.exists(file_path):
        with open(file_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"CSS file not found at path: {file_path}")
