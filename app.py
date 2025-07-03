import streamlit as st
import pytz
from datetime import datetime
import pandas as pd

# Import from custom modules
from utils import prepare_arabic_text, load_css
from db_manager import DatabaseManager
from cbe_scraper import fetch_data_from_cbe
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
if 'df_data' not in st.session_state:
    st.session_state.df_data, st.session_state.last_update = db_manager.load_latest_data()
data_df = st.session_state.df_data

# --- 4. Top Row: Key Metrics & Update Section ---
top_col1, top_col2 = st.columns(2, gap="large")

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
        st.subheader(prepare_arabic_text("📡 حالة الاتصال بالبنك المركزي"), anchor=False)
        cairo_tz = pytz.timezone('Africa/Cairo')
        now_cairo = datetime.now(cairo_tz)
        days_ar = {'Monday':'الإثنين','Tuesday':'الثلاثاء','Wednesday':'الأربعاء','Thursday':'الخميس','Friday':'الجمعة','Saturday':'السبت','Sunday':'الأحد'}
        day_name_en = now_cairo.strftime('%A')
        day_name_ar = days_ar.get(day_name_en, day_name_en)
        current_time_str = now_cairo.strftime(f"%Y/%m/%d | %H:%M")

        st.write(f"{prepare_arabic_text('**التوقيت المحلي (القاهرة):**')} {prepare_arabic_text(day_name_ar)}، {current_time_str}")
        st.write(f"{prepare_arabic_text('**آخر تحديث مسجل:**')} {st.session_state.last_update}")

        if st.button(prepare_arabic_text("🔄 جلب أحدث البيانات"), use_container_width=True, type="primary"):
            with st.spinner(prepare_arabic_text("جاري تشغيل المتصفح لجلب البيانات...")):
                new_df, status, message = fetch_data_from_cbe(db_manager)
                if status == 'SUCCESS':
                    st.session_state.df_data = new_df
                    st.session_state.last_update = datetime.now(cairo_tz).strftime("%d-%m-%Y %H:%M")
                    st.toast(prepare_arabic_text("✅ تم التحديث بنجاح!"), icon="✅")
                    st.rerun()
                else:
                    st.error(prepare_arabic_text(f"⚠️ {message}"), icon="⚠️")

        st.link_button(prepare_arabic_text("🔗 فتح موقع البنك"), C.CBE_DATA_URL, use_container_width=True)

st.divider()

# --- 5. Main Calculator Section ---
st.header(prepare_arabic_text("🧮 حاسبة العائد الأساسية"))
col_form_main, col_results_main = st.columns(2, gap="large")

with col_form_main:
    with st.container(border=True):
        st.subheader(prepare_arabic_text("1. أدخل بيانات الاستثمار"), anchor=False)
        investment_amount_main = st.number_input(prepare_arabic_text("المبلغ المستثمر (بالجنيه)"), min_value=1000.0, value=100000.0, step=1000.0, key="main_investment")
        
        options = sorted(data_df[C.TENOR_COLUMN_NAME].unique())
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


# --- 6. Secondary Market Sale Calculator ---
st.divider()
st.header(prepare_arabic_text("⚖️ حاسبة البيع في السوق الثانوي"))
col_secondary_form, col_secondary_results = st.columns(2, gap="large")

with col_secondary_form:
    with st.container(border=True):
        st.subheader(prepare_arabic_text("1. أدخل بيانات الإذن الأصلي"), anchor=False)
        face_value_secondary = st.number_input(prepare_arabic_text("القيمة الإسمية للإذن"), min_value=1000.0, value=100000.0, step=1000.0, key="secondary_face_value")
        original_yield_secondary = st.number_input(prepare_arabic_text("عائد الشراء الأصلي (%)"), min_value=1.0, value=29.0, step=0.1, key="secondary_original_yield", format="%.3f")
        
        options = sorted(data_df[C.TENOR_COLUMN_NAME].unique())
        original_tenor_secondary = st.selectbox(prepare_arabic_text("أجل الإذن الأصلي (بالأيام)"), options=options, key="secondary_tenor", index=0)

        tax_rate_secondary = st.number_input(prepare_arabic_text("نسبة الضريبة على الأرباح (%)"), min_value=0.0, max_value=100.0, value=C.DEFAULT_TAX_RATE_PERCENT, step=0.5, format="%.1f", key="secondary_tax")

        st.subheader(prepare_arabic_text("2. أدخل تفاصيل البيع"), anchor=False)
        max_holding_days = int(original_tenor_secondary) - 1 if original_tenor_secondary > 1 else 1
        early_sale_days_secondary = st.number_input(prepare_arabic_text("أيام الاحتفاظ الفعلية (قبل البيع)"), min_value=1, value=min(60, max_holding_days), max_value=max_holding_days, step=1)
        secondary_market_yield = st.number_input(prepare_arabic_text("العائد السائد في السوق للمشتري (%)"), min_value=1.0, value=30.0, step=0.1, format="%.3f")
        
        st.subheader(prepare_arabic_text("3. قم بتحليل قرار البيع"), anchor=False)
        calc_secondary_sale_button = st.button(prepare_arabic_text("حلل سعر البيع الثانوي"), use_container_width=True, type="primary", key="secondary_calc")

secondary_results_placeholder = col_secondary_results.empty()

if calc_secondary_sale_button:
    results = analyze_secondary_sale(face_value_secondary, original_yield_secondary, original_tenor_secondary, early_sale_days_secondary, secondary_market_yield, tax_rate_secondary)

    if results.get("error"):
        with secondary_results_placeholder.container(border=True):
            st.error(prepare_arabic_text(results["error"]))
    else:
        with secondary_results_placeholder.container(border=True):
            st.subheader(prepare_arabic_text("✨ تحليل سعر البيع الثانوي"), anchor=False)
            c1, c2 = st.columns(2)
            c1.metric(label=prepare_arabic_text("🏷️ سعر البيع الفعلي للإذن"), value=f"{results['sale_price']:,.2f} جنيه")
            c2.metric(label=prepare_arabic_text("💰 صافي الربح / الخسارة"), value=f"{results['net_profit']:,.2f} جنيه", delta=f"{results['annualized_yield']:.2f}% سنوياً")
            
            # ... (rest of the results and decision card display from original file)

else:
    with secondary_results_placeholder.container(border=True):
        st.info(prepare_arabic_text("✨ أدخل بيانات البيع في النموذج لتحليل قرارك."))


# --- 7. Help Section ---
st.divider()
with st.expander(prepare_arabic_text("💡 شرح ومساعدة (أسئلة شائعة)")):
    st.markdown(prepare_arabic_text("""
    #### **ما الفرق بين "العائد" و "الفائدة"؟**
    - **الفائدة (Interest):** تُحسب على أصل المبلغ وتُضاف إليه دورياً (مثل شهادات الادخار).
    - **العائد (Yield):** في أذون الخزانة، أنت تشتري الإذن بسعر **أقل** من قيمته الإسمية (مثلاً تشتريه بـ 975 وهو يساوي 1000)، وربحك هو الفارق الذي ستحصل عليه في نهاية المدة. الحاسبة تحول هذا الفارق إلى نسبة مئوية سنوية لتسهيل المقارنة.
    ---
    #### **كيف تعمل حاسبة العائد الأساسية؟**
    هذه الحاسبة تجيب على سؤال: "كم سأربح إذا احتفظت بالإذن حتى نهاية مدته؟".
    1.  **حساب إجمالي الربح:** `المبلغ المستثمر × (العائد ÷ 100) × (مدة الإذن ÷ 365)`
    2.  **حساب الضريبة:** `إجمالي الربح × (نسبة الضريبة ÷ 100)`
    3.  **حساب صافي الربح:** `إجمالي الربح - قيمة الضريبة`
    4.  **إجمالي المستلم:** `المبلغ المستثمر + صافي الربح`
    ---
    #### **كيف تعمل حاسبة البيع في السوق الثانوي؟**
    هذه الحاسبة تجيب على سؤال: "كم سيكون ربحي أو خسارتي إذا بعت الإذن اليوم قبل تاريخ استحقاقه؟". سعر البيع هنا لا يعتمد على سعر شرائك، بل على سعر الفائدة **الحالي** في السوق.
    1.  **حساب سعر شرائك الأصلي:** `سعر الشراء = القيمة الإسمية ÷ (1 + (عائد الشراء ÷ 100) × (الأجل الأصلي ÷ 365))`
    2.  **حساب سعر البيع اليوم:** `الأيام المتبقية = الأجل الأصلي - أيام الاحتفاظ`، `سعر البيع = القيمة الإسمية ÷ (1 + (العائد السائد ÷ 100) × (الأيام المتبقية ÷ 365))`
    3.  **النتيجة النهائية:** `الربح أو الخسارة = سعر البيع - سعر الشراء الأصلي`. يتم حساب الضريبة على هذا الربح إذا كان موجباً.
    ---
    ***إخلاء مسؤولية:*** *هذا التطبيق هو أداة استرشادية فقط، والأرقام الناتجة هي تقديرات. للحصول على أرقام نهائية ودقيقة، يرجى الرجوع إلى البنك أو المؤسسة المالية التي تتعامل معها.*
    """))