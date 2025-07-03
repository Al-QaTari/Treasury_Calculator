# app.py
import streamlit as st
import pytz
from datetime import datetime
import pandas as pd

# Import from custom modules
from utils import prepare_arabic_text, load_css
from db_manager import DatabaseManager
from calculations import calculate_primary_yield, analyze_secondary_sale
import constants as C

# --- 1. App Configuration and Initialization ---
st.set_page_config(layout="wide", page_title="حاسبة أذون الخزانة", page_icon="🏦")
load_css('css/style.css')

db_manager = DatabaseManager()

# --- 2. Header ---
st.markdown(f"""
<div class="app-title">
    <h1>{prepare_arabic_text("🏦 حاسبة أذون الخزانة")}</h1>
    <p>{prepare_arabic_text("تطبيق تفاعلي لحساب وتحليل عوائد أذون الخزانة")}</p>
</div>
""", unsafe_allow_html=True)

# --- 3. Data Loading ---
# The app now simply loads the latest data available in the database
st.session_state.df_data, st.session_state.last_update = db_manager.load_latest_data()
data_df = st.session_state.df_data

# --- 4. Top Row: Key Metrics & Update Section ---
top_col1, top_col2 = st.columns([2, 1]) # Adjusted column ratio

with top_col1:
    with st.container(border=True):
        st.subheader(prepare_arabic_text("📊 أحدث العوائد المعتمدة"), anchor=False)
        if not data_df.empty:
            sorted_tenors = sorted(data_df[C.TENOR_COLUMN_NAME].unique())
            cols = st.columns(len(sorted_tenors) if sorted_tenors else 1)
            tenor_icons = {91: "⏳", 182: "🗓️", 273: "📆", 364: "🗓️✨"}
            for i, tenor in enumerate(sorted_tenors):
                with cols[i]:
                    icon = tenor_icons.get(int(tenor), "🪙")
                    rate = data_df[data_df[C.TENOR_COLUMN_NAME] == tenor][C.YIELD_COLUMN_NAME].iloc[0]
                    st.metric(label=prepare_arabic_text(f"{icon} أجل {tenor} يوم"), value=f"{rate:.3f}%")
        else:
            st.warning(prepare_arabic_text("لم يتم تحميل البيانات أو أن البيانات غير مكتملة."))

with top_col2:
    with st.container(border=True):
        st.subheader(prepare_arabic_text("📡 حالة البيانات"), anchor=False)
        st.write(f"{prepare_arabic_text('**آخر تحديث مسجل:**')} {st.session_state.last_update}")
        st.info(prepare_arabic_text("يتم تحديث البيانات تلقائيًا بشكل دوري."), icon="ℹ️")
        st.link_button(prepare_arabic_text("🔗 فتح موقع البنك"), C.CBE_DATA_URL, use_container_width=True)

st.divider()

# --- 5. Main Calculator Section ---
st.header(prepare_arabic_text("🧮 حاسبة العائد الأساسية"))
col_form_main, col_results_main = st.columns(2, gap="large")

with col_form_main:
    with st.container(border=True):
        st.subheader(prepare_arabic_text("1. أدخل بيانات الاستثمار"), anchor=False)
        investment_amount_main = st.number_input(prepare_arabic_text("المبلغ المستثمر (بالجنيه)"), min_value=1000.0, value=100000.0, step=1000.0, key="main_investment")

        options = sorted(data_df[C.TENOR_COLUMN_NAME].unique()) if not data_df.empty else [91, 182, 273, 364]
        selected_tenor_main = st.selectbox(prepare_arabic_text("اختر مدة الاستحقاق (بالأيام)"), options=options, key="main_tenor")

        tax_rate_main = st.number_input(prepare_arabic_text("نسبة الضريبة على الأرباح (%)"), min_value=0.0, max_value=100.0, value=C.DEFAULT_TAX_RATE_PERCENT, step=0.5, format="%.1f", key="main_tax")

        st.subheader(prepare_arabic_text("2. قم بحساب العائد"), anchor=False)
        calculate_button_main = st.button(prepare_arabic_text("احسب العائد الآن"), use_container_width=True, type="primary", key="main_calc")

results_placeholder_main = col_results_main.empty()

if calculate_button_main and selected_tenor_main:
    yield_rate_row = data_df[data_df[C.TENOR_COLUMN_NAME] == selected_tenor_main]
    if not yield_rate_row.empty:
        yield_rate = yield_rate_row[C.YIELD_COLUMN_NAME].iloc[0]
        results = calculate_primary_yield(investment_amount_main, selected_tenor_main, yield_rate, tax_rate_main)

        with results_placeholder_main.container(border=True):
            st.subheader(prepare_arabic_text(f"✨ تفاصيل أجل {selected_tenor_main} يوم"), anchor=False)
            st.markdown(f'<p style="font-size: 1.0rem; color: #adb5bd;">{prepare_arabic_text("العائد الصافي بعد الضريبة")}</p><p style="font-size: 2.0rem; color: #49c57a; font-weight: 700;">{results["net_return"]:,.2f} {prepare_arabic_text("جنيه")}</p>', unsafe_allow_html=True)
            st.markdown('<hr style="border-color: #495057;">', unsafe_allow_html=True)
            st.markdown(f'<table style="width:100%; font-size: 1.0rem;"><tr><td style="padding-bottom: 8px;">{prepare_arabic_text("💰 المبلغ المستثمر")}</td><td style="text-align:left;">{investment_amount_main:,.2f} {prepare_arabic_text("جنيه")}</td></tr><tr><td style="padding-bottom: 8px; color: #8ab4f8;">{prepare_arabic_text("📈 العائد الإجمالي")}</td><td style="text-align:left; color: #8ab4f8;">{results["gross_return"]:,.2f} {prepare_arabic_text("جنيه")}</td></tr><tr><td style="padding-bottom: 15px; color: #f28b82;">{prepare_arabic_text(f"💸 ضريبة الأرباح ({tax_rate_main}%)")}</td><td style="text-align:left; color: #f28b82;">- {results["tax_amount"]:,.2f} {prepare_arabic_text("جنيه")}</td></tr></table>', unsafe_allow_html=True)
            st.markdown(f'<div style="background-color: #495057; padding: 10px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center;"><span style="font-size: 1.1rem;">{prepare_arabic_text("🏦 إجمالي المستلم")}</span><span style="font-size: 1.2rem;">{results["total_payout"]:,.2f} {prepare_arabic_text("جنيه")}</span></div>', unsafe_allow_html=True)
    else:
         with results_placeholder_main.container(border=True):
            st.error(prepare_arabic_text("لم يتم العثور على عائد للأجل المحدد."))
else:
    with results_placeholder_main.container(border=True):
        st.info(prepare_arabic_text("✨ نتائج العائد الأساسي ستظهر هنا بعد ملء النموذج والضغط على زر الحساب."))
