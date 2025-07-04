import streamlit as st
import pytz
from datetime import datetime, timedelta
import pandas as pd
from utils import prepare_arabic_text, load_css
from db_manager import DatabaseManager
from calculations import calculate_primary_yield, analyze_secondary_sale
import constants as C

# --- 1. App Configuration and Initialization ---
st.set_page_config(layout="wide", page_title="حاسبة أذون الخزانة", page_icon="🏦")
load_css('css/style.css') 

db_manager = DatabaseManager()

# --- Function to load/reload data into session state ---
def load_data_into_session():
    st.session_state.df_data, st.session_state.last_update = db_manager.load_latest_data()

# --- Initial Data Loading ---
if 'df_data' not in st.session_state:
    load_data_into_session()
data_df = st.session_state.df_data

# --- 2. Header ---
st.markdown(f"""
<div class="centered-header" style="background-color: #343a40; padding: 20px 10px; border-radius: 15px; margin-bottom: 1rem; box-shadow: 0 4px 12px 0 rgba(0,0,0,0.1);">
    <h1 style="color: #ffffff; margin: 0; font-size: 2.5rem;">{prepare_arabic_text("🏦 حاسبة أذون الخزانة")}</h1>
    <p style="color: #aab8c2; margin: 10px 0 0 0; font-size: 1.1rem;">{prepare_arabic_text("تطبيق تفاعلي لحساب وتحليل عوائد أذون الخزانة المصرية")}</p>
    <div style="margin-top: 20px; font-size: 1rem; color: #999; text-align: center;">
        {prepare_arabic_text("صُمم وبُرمج بواسطة")} 
        <span style="font-weight: bold; color: #00bfff;">Mohamed AL-QaTri</span>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 3. Top Row: Key Metrics & Update Section ---
top_col1, top_col2 = st.columns([2, 1])

with top_col1:
    with st.container(border=True):
        st.subheader(prepare_arabic_text("📊 أحدث العوائد المعتمدة"), anchor=False)
        st.markdown("<hr style='margin-top: -10px; margin-bottom: 15px; border-color: #495057;'>", unsafe_allow_html=True)
        
        # --- FINAL DYNAMIC & COMPACT DISPLAY LOGIC ---
        if not data_df.empty and all(c in data_df.columns for c in [C.TENOR_COLUMN_NAME, C.YIELD_COLUMN_NAME, C.SESSION_DATE_COLUMN_NAME]) and "البيانات الأولية" not in st.session_state.last_update:
            
            day_names_en_ar = {"Sunday": "الأحد", "Monday": "الاثنين", "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء", "Thursday": "الخميس", "Friday": "الجمعة", "Saturday": "السبت"}
            
            try:
                unique_dates = sorted(data_df[C.SESSION_DATE_COLUMN_NAME].unique(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"))
            except TypeError:
                unique_dates = data_df[C.SESSION_DATE_COLUMN_NAME].unique()

            for session_date_str in unique_dates:
                try:
                    session_date_dt = datetime.strptime(session_date_str, "%d/%m/%Y")
                    day_en = session_date_dt.strftime("%A")
                    day_ar = day_names_en_ar.get(day_en, day_en)
                    
                    purchase_info = ""
                    if day_ar == "الأحد":
                        purchase_info = prepare_arabic_text("(يتم شراؤه يوم الخميس السابق)")
                    elif day_ar == "الاثنين":
                        purchase_info = prepare_arabic_text("(يتم شراؤه يوم الأحد السابق)")

                    st.markdown(f"""
                    <div style='text-align:center;'>
                        <h5 style='color:#ffc107; margin-bottom: -2px;'>{prepare_arabic_text(f'عطاءات يوم {day_ar} - {session_date_str}')}</h5>
                        <p style='color:#adb5bd; font-size: 0.9rem; margin-top: 0px;'>{purchase_info}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    tenors_for_this_date = data_df[data_df[C.SESSION_DATE_COLUMN_NAME] == session_date_str].sort_values(by=C.TENOR_COLUMN_NAME)
                    
                    # Use Streamlit's columns for a compact, horizontal layout
                    cols = st.columns(len(tenors_for_this_date))
                    for i, (index, tenor_data) in enumerate(tenors_for_this_date.iterrows()):
                        with cols[i]:
                            rate = tenor_data[C.YIELD_COLUMN_NAME]
                            tenor = tenor_data[C.TENOR_COLUMN_NAME]
                            # Custom styled card inside each column with reduced padding and font sizes
                            st.markdown(f"""
                            <div style="text-align: center; background-color: #495057; padding: 8px 5px; border-radius: 10px; height: 100%;">
                                <p style="font-size: 0.8rem; color: #adb5bd; margin: 0; white-space: nowrap;" title="{prepare_arabic_text(f"تاريخ الجلسة: {tenor_data[C.SESSION_DATE_COLUMN_NAME]}")}">{prepare_arabic_text(f"أجل {tenor} يوم")}</p>
                                <p style="font-size: 1.4rem; color: #ffffff; font-weight: 600; margin: 5px 0 0 0;">{rate:.3f}%</p>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    if session_date_str != unique_dates[-1]:
                        st.markdown("<hr style='border-color: #495057; margin: 10px 0 15px 0;'>", unsafe_allow_html=True)

                except (ValueError, TypeError) as e:
                    st.error(f"Error processing date: {session_date_str}. Error: {e}")
                    continue
        else:
            st.info(prepare_arabic_text("في انتظار ورود البيانات من البنك المركزي..."))

with top_col2:
    with st.container(border=True):
        st.subheader(prepare_arabic_text("📡 حالة البيانات"), anchor=False)
        last_update_message = st.session_state.last_update
        st.write(f"{prepare_arabic_text('**آخر تحديث مسجل:**')} {last_update_message}")
        if st.button("🔄 تحديث عرض البيانات", use_container_width=True):
            load_data_into_session()
            st.toast(prepare_arabic_text("تم تحديث العرض بأحدث البيانات المتاحة."), icon="✅")
            st.rerun()

        if "البيانات الأولية" in last_update_message:
            st.warning(prepare_arabic_text("يقوم الروبوت بجلب البيانات لأول مرة. قد يستغرق الأمر بضع دقائق."), icon="⏳")
        else:
            try:
                last_update_dt = datetime.strptime(last_update_message.replace("بتاريخ ", ""), "%d-%m-%Y")
                cairo_tz = pytz.timezone('Africa/Cairo')
                now_cairo = datetime.now(cairo_tz)
                if (now_cairo.date() - last_update_dt.date()).days > 0:
                     st.warning(prepare_arabic_text("تنبيه: البيانات المعروضة قديمة."), icon="⚠️")
                else:
                     st.success(prepare_arabic_text("البيانات المعروضة محدثة لليوم."), icon="✅")
            except (ValueError, TypeError):
                 st.info(prepare_arabic_text("يتم تحديث قاعدة البيانات تلقائيًا."), icon="ℹ️")
        st.link_button(prepare_arabic_text("🔗 فتح موقع البنك"), C.CBE_DATA_URL, use_container_width=True)

st.divider()

# --- Primary Calculator Section ---
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

if calculate_button_main and selected_tenor_main is not None:
    yield_rate_row = data_df[data_df[C.TENOR_COLUMN_NAME] == selected_tenor_main]
    if not yield_rate_row.empty:
        yield_rate = yield_rate_row[C.YIELD_COLUMN_NAME].iloc[0]
        results = calculate_primary_yield(investment_amount_main, selected_tenor_main, yield_rate, tax_rate_main)
        
        with results_placeholder_main.container(border=True):
            st.subheader(prepare_arabic_text(f"✨ ملخص استثمارك لأجل {selected_tenor_main} يوم"), anchor=False)
            
            st.markdown(f"""
            <div style="text-align: center; margin-bottom: 20px;">
                <p style="font-size: 1.1rem; color: #adb5bd; margin-bottom: 0px;">{prepare_arabic_text("النسبة الفعلية للربح (عن الفترة)")}</p>
                <p style="font-size: 2.8rem; color: #ffffff; font-weight: 700; line-height: 1.2;">{results['real_profit_percentage']:.3f}%</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="text-align: center; background-color: #495057; padding: 10px; border-radius: 10px; margin-bottom: 15px;">
                <p style="font-size: 1rem; color: #adb5bd; margin-bottom: 0px;">{prepare_arabic_text("💰 صافي الربح")}</p>
                <p style="font-size: 1.9rem; color: #28a745; font-weight: 600; line-height: 1.2;">{results['net_return']:,.2f} {prepare_arabic_text("جنيه")}</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander(prepare_arabic_text("عرض تفاصيل الحساب الكاملة")):
                st.markdown(f"""
                <div style="padding: 10px; border-radius: 10px; background-color: #212529;">
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 5px; border-bottom: 1px solid #495057;">
                        <span style="font-size: 1.1rem;">{prepare_arabic_text("المبلغ المستثمر الأصلي")}</span>
                        <span style="font-size: 1.2rem; font-weight: 600;">{investment_amount_main:,.2f} {prepare_arabic_text("جنيه")}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 5px; border-bottom: 1px solid #495057;">
                        <span style="font-size: 1.1rem;">{prepare_arabic_text("العائد الإجمالي (قبل الضريبة)")}</span>
                        <span style="font-size: 1.2rem; font-weight: 600; color: #8ab4f8;">{results['gross_return']:,.2f} {prepare_arabic_text("جنيه")}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 5px;">
                        <span style="font-size: 1.1rem;">{prepare_arabic_text(f"قيمة الضريبة ({tax_rate_main}%)")}</span>
                        <span style="font-size: 1.2rem; font-weight: 600; color: #dc3545;">-{results['tax_amount']:,.2f} {prepare_arabic_text("جنيه")}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style="text-align: center; background-color: #212529; padding: 10px; border-radius: 10px; margin-top:15px;">
                <p style="font-size: 1rem; color: #adb5bd; margin-bottom: 0px;">{prepare_arabic_text("🏦 إجمالي المبلغ المستلم في النهاية")}</p>
                <p style="font-size: 1.9rem; color: #8ab4f8; font-weight: 600; line-height: 1.2;">{results['total_payout']:,.2f} {prepare_arabic_text("جنيه")}</p>
            </div>
            """, unsafe_allow_html=True)

    else:
         with results_placeholder_main.container(border=True):
            st.error(prepare_arabic_text("لم يتم العثور على عائد للأجل المحدد."))
else:
    with results_placeholder_main.container(border=True):
        st.info(prepare_arabic_text("✨ ملخص استثمارك سيظهر هنا بتصميم أنيق بعد الضغط على زر الحساب."))

# --- Secondary Market Sale Calculator ---
st.divider()
st.header(prepare_arabic_text("⚖️ حاسبة البيع في السوق الثانوي"))
col_secondary_form, col_secondary_results = st.columns(2, gap="large")

with col_secondary_form:
    with st.container(border=True):
        st.subheader(prepare_arabic_text("1. أدخل بيانات الإذن الأصلي"), anchor=False)
        face_value_secondary = st.number_input(prepare_arabic_text("القيمة الإسمية للإذن"), min_value=1000.0, value=100000.0, step=1000.0, key="secondary_face_value")
        original_yield_secondary = st.number_input(prepare_arabic_text("عائد الشراء الأصلي (%)"), min_value=1.0, value=29.0, step=0.1, key="secondary_original_yield", format="%.3f")
        options = sorted(data_df[C.TENOR_COLUMN_NAME].unique()) if not data_df.empty else [91, 182, 273, 364]
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
            
            profit_color = "#28a745" if results['net_profit'] >= 0 else "#dc3545"

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div style="text-align: center; background-color: #495057; padding: 10px; border-radius: 10px; height: 100%;">
                    <p style="font-size: 1rem; color: #adb5bd; margin-bottom: 0px;">{prepare_arabic_text("🏷️ سعر البيع الفعلي")}</p>
                    <p style="font-size: 1.9rem; color: #8ab4f8; font-weight: 600; line-height: 1.2;">{results['sale_price']:,.2f} {prepare_arabic_text("جنيه")}</p>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div style="text-align: center; background-color: #495057; padding: 10px; border-radius: 10px; height: 100%;">
                    <p style="font-size: 1rem; color: #adb5bd; margin-bottom: 0px;">{prepare_arabic_text("💰 صافي الربح / الخسارة")}</p>
                    <p style="font-size: 1.9rem; color: {profit_color}; font-weight: 600; line-height: 1.2;">{results['net_profit']:,.2f} {prepare_arabic_text("جنيه")}</p>
                    <p style="font-size: 1rem; color: {profit_color}; margin-top: -5px;">({results['period_yield']:.2f}% {prepare_arabic_text("عن فترة الاحتفاظ")})</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

            with st.expander(prepare_arabic_text("عرض تفاصيل الحساب")):
                st.markdown(f"""
                <div style="padding: 10px; border-radius: 10px; background-color: #212529;">
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 5px; border-bottom: 1px solid #495057;">
                        <span style="font-size: 1.1rem;">{prepare_arabic_text("سعر الشراء الأصلي")}</span>
                        <span style="font-size: 1.2rem; font-weight: 600;">{results['original_purchase_price']:,.2f} {prepare_arabic_text("جنيه")}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 5px; border-bottom: 1px solid #495057;">
                        <span style="font-size: 1.1rem;">{prepare_arabic_text("إجمالي الربح (قبل الضريبة)")}</span>
                        <span style="font-size: 1.2rem; font-weight: 600; color: {'#28a745' if results['gross_profit'] >= 0 else '#dc3545'};">{results['gross_profit']:,.2f} {prepare_arabic_text("جنيه")}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 5px;">
                        <span style="font-size: 1.1rem;">{prepare_arabic_text(f"قيمة الضريبة ({tax_rate_secondary}%)")}</span>
                        <span style="font-size: 1.2rem; font-weight: 600; color: #dc3545;">-{results['tax_amount']:,.2f} {prepare_arabic_text("جنيه")}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if results['gross_profit'] <= 0:
                    st.info(prepare_arabic_text("لا توجد ضريبة على الخسائر الرأسمالية."), icon="ℹ️")

            net_profit = results['net_profit']
            if net_profit > 0:
                decision_html = f"""<div style="background-color: #1e4620; padding: 15px; border-radius: 8px; border: 1px solid #49c57a; text-align: right; margin-top: 15px;"><h5 style="color: #ffffff; margin-bottom: 10px;">{prepare_arabic_text("✅ قرار البيع: مربح")}</h5><p style="color: #e0e0e0; font-size: 0.95rem; margin-bottom: 10px;">{prepare_arabic_text(f"البيع الآن سيحقق لك <b>ربحاً صافياً</b> قدره <b>{net_profit:,.2f} جنيه</b>.")}</p><p style="color: #ffffff; font-size: 1rem; margin-bottom: 0;"><b>{prepare_arabic_text("النصيحة:")}</b> {prepare_arabic_text("قد يكون البيع خياراً جيداً إذا كنت بحاجة للسيولة، أو وجدت فرصة استثمارية أخرى بعائد أعلى.")}</p></div>"""
                st.markdown(decision_html, unsafe_allow_html=True)
            elif net_profit < 0:
                loss_value = abs(net_profit)
                decision_html = f"""<div style="background-color: #4a2a2a; padding: 15px; border-radius: 8px; border: 1px solid #f28b82; text-align: right; margin-top: 15px;"><h5 style="color: #ffffff; margin-bottom: 10px;">{prepare_arabic_text("⚠️ قرار البيع: غير مربح")}</h5><p style="color: #e0e0e0; font-size: 0.95rem; margin-bottom: 10px;">{prepare_arabic_text(f"البيع الآن سيتسبب في <b>خسارة صافية</b> قدرها <b>{loss_value:,.2f} جنيه</b>.")}</p><p style="color: #ffffff; font-size: 1rem; margin-bottom: 0;"><b>{prepare_arabic_text("النصيحة:")}</b> {prepare_arabic_text("يُنصح بالانتظار حتى تاريخ الاستحقاق لتجنب هذه الخسارة وتحقيق عائدك الأصلي.")}</p></div>"""
                st.markdown(decision_html, unsafe_allow_html=True)
            else:
                decision_html = f"""<div style="background-color: #2a394a; padding: 15px; border-radius: 8px; border: 1px solid #8ab4f8; text-align: right; margin-top: 15px;"><h5 style="color: #ffffff; margin-bottom: 10px;">{prepare_arabic_text("⚖️ قرار البيع: متعادل")}</h5><p style="color: #e0e0e0; font-size: 0.95rem; margin-bottom: 10px;">{prepare_arabic_text("البيع الآن لن ينتج عنه أي ربح أو خسارة.")}</p><p style="color: #ffffff; font-size: 1rem; margin-bottom: 0;"><b>{prepare_arabic_text("النصيحة:")}</b> {prepare_arabic_text("يمكنك البيع إذا كنت بحاجة لاسترداد قيمة الشراء مبكراً دون أي تغيير في قيمتها.")}</p></div>"""
                st.markdown(decision_html, unsafe_allow_html=True)
else:
    with secondary_results_placeholder.container(border=True):
        st.info(prepare_arabic_text("✨ أدخل بيانات البيع في النموذج لتحليل قرارك."))

# --- Help Section ---
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
