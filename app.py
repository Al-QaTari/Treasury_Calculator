# app.py (نسخة نهائية مع حل مشكلة الـ scroll)
import streamlit as st
import pytz
from datetime import datetime
import plotly.express as px

# Import all the corrected and improved modules
from utils import prepare_arabic_text, load_css
from db_manager import get_db_manager
from calculations import calculate_primary_yield, analyze_secondary_sale
from cbe_scraper import fetch_data_from_cbe
import constants as C


def main():
    # --- 1. App Configuration and Initialization ---
    st.set_page_config(
        layout="wide",
        page_title=prepare_arabic_text("حاسبة أذون الخزانة"),
        page_icon="🏦",
    )
    load_css("css/style.css")

    # Use the cached DB Manager
    db_manager = get_db_manager()

    # --- IMPROVEMENT: Initialize data in session_state for smooth updates ---
    if "df_data" not in st.session_state:
        st.session_state.df_data, st.session_state.last_update = (
            db_manager.load_latest_data()
        )
    if "historical_df" not in st.session_state:
        st.session_state.historical_df = db_manager.load_all_historical_data()

    # Always use data from session_state for display
    data_df = st.session_state.df_data
    last_update = st.session_state.last_update
    historical_df = st.session_state.historical_df

    # --- 2. Header ---
    st.markdown(
        f"""
    <div class="centered-header" style="background-color: #343a40; padding: 20px 10px; border-radius: 15px; margin-bottom: 1rem; box-shadow: 0 4px 12px 0 rgba(0,0,0,0.1);">
        <h1 style="color: #ffffff; margin: 0; font-size: 2.5rem;">{prepare_arabic_text("🏦 حاسبة أذون الخزانة")}</h1>
        <p style="color: #aab8c2; margin: 10px 0 0 0; font-size: 1.1rem;">{prepare_arabic_text("تطبيق تفاعلي لحساب وتحليل عوائد أذون الخزانة المصرية")}</p>
        <div style="margin-top: 20px; font-size: 1rem; color: #999; text-align: center;">
            {prepare_arabic_text("صُمم وبُرمج بواسطة")} 
            <span style="font-weight: bold; color: #00bfff;">{C.AUTHOR_NAME}</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # --- 3. Top Row: Key Metrics & Update Section ---
    top_col1, top_col2 = st.columns([2, 1])

    with top_col1:
        with st.container(border=True):
            st.subheader(prepare_arabic_text("📊 أحدث العوائد المعتمدة"), anchor=False)
            st.markdown(
                "<hr style='margin-top: -10px; margin-bottom: 15px; border-color: #495057;'>",
                unsafe_allow_html=True,
            )

            if not data_df.empty and "البيانات الأولية" not in last_update:
                day_names_en_ar = {
                    "Sunday": "الأحد",
                    "Monday": "الاثنين",
                    "Tuesday": "الثلاثاء",
                    "Wednesday": "الأربعاء",
                    "Thursday": "الخميس",
                    "Friday": "الجمعة",
                    "Saturday": "السبت",
                }
                try:
                    unique_dates = sorted(
                        data_df[C.SESSION_DATE_COLUMN_NAME].unique(),
                        key=lambda d: datetime.strptime(d, "%d/%m/%Y"),
                    )
                except (ValueError, TypeError):
                    unique_dates = data_df[C.SESSION_DATE_COLUMN_NAME].unique()

                for session_date_str in unique_dates:
                    try:
                        session_date_dt = datetime.strptime(
                            session_date_str, "%d/%m/%Y"
                        )
                        day_en = session_date_dt.strftime("%A")
                        day_ar = day_names_en_ar.get(day_en, day_en)
                        purchase_info = ""
                        if day_ar == "الأحد":
                            purchase_info = prepare_arabic_text(
                                "(يتم شراؤه يوم الخميس السابق)"
                            )
                        elif day_ar == "الاثنين":
                            purchase_info = prepare_arabic_text(
                                "(يتم شراؤه يوم الأحد السابق)"
                            )

                        st.markdown(
                            f"""<div style='text-align:center;'><h5 style='color:#ffc107; margin-bottom: -2px;'>{prepare_arabic_text(f'عطاءات يوم {day_ar} - {session_date_str}')}</h5><p style='color:#adb5bd; font-size: 0.9rem; margin-top: 0px;'>{purchase_info}</p></div>""",
                            unsafe_allow_html=True,
                        )

                        tenors_for_this_date = data_df[
                            data_df[C.SESSION_DATE_COLUMN_NAME] == session_date_str
                        ].sort_values(by=C.TENOR_COLUMN_NAME)
                        cols = st.columns(len(tenors_for_this_date) or 1)
                        for i, (_, tenor_data) in enumerate(
                            tenors_for_this_date.iterrows()
                        ):
                            with cols[i]:
                                rate = tenor_data[C.YIELD_COLUMN_NAME]
                                tenor = tenor_data[C.TENOR_COLUMN_NAME]
                                st.markdown(
                                    f"""<div style="text-align: center; background-color: #495057; padding: 8px 5px; border-radius: 10px; height: 100%;"><p style="font-size: 0.8rem; color: #adb5bd; margin: 0; white-space: nowrap;">{prepare_arabic_text(f"أجل {tenor} يوم")}</p><p style="font-size: 1.4rem; color: #ffffff; font-weight: 600; margin: 5px 0 0 0;">{rate:.3f}%</p></div>""",
                                    unsafe_allow_html=True,
                                )

                        if session_date_str != unique_dates[-1]:
                            st.markdown(
                                "<hr style='border-color: #495057; margin: 10px 0 15px 0;'>",
                                unsafe_allow_html=True,
                            )
                    except (ValueError, TypeError):
                        continue
            else:
                st.info(
                    prepare_arabic_text("في انتظار ورود البيانات من البنك المركزي...")
                )

    with top_col2:
        with st.container(border=True):
            st.subheader(prepare_arabic_text("📡 حالة البيانات"), anchor=False)
            st.write(
                f"{prepare_arabic_text('**آخر تحديث مسجل:**')} {prepare_arabic_text(last_update)}"
            )

            if st.button(
                prepare_arabic_text("🔄 تحديث البيانات من البنك المركزي"),
                use_container_width=True,
                type="primary",
            ):
                with st.spinner(
                    prepare_arabic_text(
                        "جاري جلب أحدث البيانات... قد يستغرق الأمر دقيقة."
                    )
                ):
                    try:
                        fetch_data_from_cbe(db_manager)
                        # --- IMPROVEMENT: Update session_state directly instead of st.rerun() ---
                        st.session_state.df_data, st.session_state.last_update = (
                            db_manager.load_latest_data()
                        )
                        st.session_state.historical_df = (
                            db_manager.load_all_historical_data()
                        )
                        st.toast(
                            prepare_arabic_text("تم تحديث البيانات بنجاح!"), icon="✅"
                        )
                        # By not calling st.rerun(), Streamlit will do a smoother update.
                    except Exception as e:
                        st.error(
                            prepare_arabic_text(
                                f"⚠️ حدث خطأ أثناء محاولة تحديث البيانات: {e}"
                            ),
                            icon="⚠️",
                        )

            if "البيانات الأولية" in last_update:
                st.warning(
                    prepare_arabic_text("قاعدة البيانات فارغة. قم بتحديث البيانات."),
                    icon="⏳",
                )
            else:
                try:
                    last_update_dt = datetime.strptime(
                        last_update.replace(prepare_arabic_text("بتاريخ "), ""),
                        "%d-%m-%Y",
                    )
                    if (
                        datetime.now(pytz.timezone("Africa/Cairo")).date()
                        - last_update_dt.date()
                    ).days > 0:
                        st.info(
                            "ℹ️ الأسعار المعروضة هي لآخر عطاء منشور رسميًا، وتُستخدم كمرجع استرشادي."
                        )
                    else:
                        st.success(
                            prepare_arabic_text("البيانات المعروضة محدثة لليوم."),
                            icon="✅",
                        )
                except (ValueError, TypeError):
                    pass

            st.link_button(
                prepare_arabic_text("🔗 فتح موقع البنك"),
                C.CBE_DATA_URL,
                use_container_width=True,
            )

    # --- Primary Calculator Section ---
    st.divider()
    st.header(prepare_arabic_text("🧮 حاسبة العائد الأساسية"))
    col_form_main, col_results_main = st.columns(2, gap="large")

    with col_form_main:
        with st.container(border=True):
            st.subheader(prepare_arabic_text("1. أدخل بيانات الاستثمار"), anchor=False)
            investment_amount_main = st.number_input(
                prepare_arabic_text("المبلغ المستهدف في نهاية المدة (القيمة الإسمية)"),
                min_value=25000.0,
                value=25000.0,
                step=25000.0,
            )
            options = (
                sorted(data_df[C.TENOR_COLUMN_NAME].unique())
                if not data_df.empty
                else [91, 182, 273, 364]
            )

            def get_yield_for_tenor(tenor):
                if not data_df.empty:
                    yield_row = data_df[data_df[C.TENOR_COLUMN_NAME] == tenor]
                    if not yield_row.empty:
                        return yield_row[C.YIELD_COLUMN_NAME].iloc[0]
                return None

            formatted_options = []
            for tenor in options:
                yield_val = get_yield_for_tenor(tenor)
                if yield_val is not None:
                    formatted_options.append(
                        f"{tenor} {prepare_arabic_text('يوم')} - ({yield_val:.3f}%)"
                    )
                else:
                    formatted_options.append(f"{tenor} {prepare_arabic_text('يوم')}")

            selected_option = st.selectbox(
                prepare_arabic_text("اختر مدة الاستحقاق"),
                formatted_options,
                key="main_tenor_formatted",
            )

            selected_tenor_main = (
                int(selected_option.split(" ")[0]) if selected_option else None
            )

            tax_rate_main = st.number_input(
                prepare_arabic_text("نسبة الضريبة على الأرباح (%)"),
                0.0,
                100.0,
                C.DEFAULT_TAX_RATE_PERCENT,
                step=0.5,
                format="%.1f",
            )
            calculate_button_main = st.button(
                prepare_arabic_text("احسب العائد الآن"),
                use_container_width=True,
                type="primary",
            )

    results_placeholder_main = col_results_main.empty()
    if calculate_button_main and selected_tenor_main is not None:
        try:
            if data_df.empty:
                with results_placeholder_main.container(border=True):
                    st.error(
                        prepare_arabic_text(
                            "لا توجد بيانات للعائد. يرجى تحديث البيانات أولاً."
                        )
                    )
            else:
                yield_rate = get_yield_for_tenor(selected_tenor_main)
                if yield_rate is not None:
                    results = calculate_primary_yield(
                        investment_amount_main,
                        yield_rate,
                        selected_tenor_main,
                        tax_rate_main,
                    )

                    with results_placeholder_main.container(border=True):
                        st.subheader(
                            prepare_arabic_text(
                                f"✨ ملخص استثمارك لأجل {selected_tenor_main} يوم"
                            ),
                            anchor=False,
                        )
                        st.markdown(
                            f"""<div style="text-align: center; margin-bottom: 20px;"><p style="font-size: 1.1rem; color: #adb5bd; margin-bottom: 0px;">{prepare_arabic_text("النسبة الفعلية للربح (عن الفترة)")}</p><p style="font-size: 2.8rem; color: #ffffff; font-weight: 700; line-height: 1.2;">{results['real_profit_percentage']:.3f}%</p></div>""",
                            unsafe_allow_html=True,
                        )

                        st.markdown(
                            f"""<div style="text-align: center; background-color: #495057; padding: 10px; border-radius: 10px; margin-bottom: 15px;"><p style="font-size: 1rem; color: #adb5bd; margin-bottom: 0px;">{prepare_arabic_text("💰 صافي الربح المقدم")} </p><p style="font-size: 1.9rem; color: #28a745; font-weight: 600; line-height: 1.2;">{results['net_return']:,.2f} {prepare_arabic_text("جنيه")}</p></div>""",
                            unsafe_allow_html=True,
                        )

                        final_balance = results["total_payout"] + results["net_return"]
                        st.markdown(
                            f"""<div style="text-align: center; background-color: #212529; padding: 10px; border-radius: 10px; "><p style="font-size: 1rem; color: #adb5bd; margin-bottom: 0px;">{prepare_arabic_text("🏦 الرصيد النهائي المتوقع (في حال عدم سحب الربح)")}</p><p style="font-size: 1.9rem; color: #8ab4f8; font-weight: 600; line-height: 1.2;">{final_balance:,.2f} {prepare_arabic_text("جنيه")}</p></div>""",
                            unsafe_allow_html=True,
                        )

                        with st.expander(
                            prepare_arabic_text("عرض تفاصيل الحساب الكاملة"),
                            expanded=False,
                        ):
                            st.markdown(
                                f"""<div style="padding: 10px; border-radius: 10px; background-color: #212529;">
                                <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 5px; border-bottom: 1px solid #495057;"><span style="font-size: 1.1rem;">{prepare_arabic_text("سعر الشراء الفعلي")}</span><span style="font-size: 1.2rem; font-weight: 600;">{results['purchase_price']:,.2f} {prepare_arabic_text("جنيه")}</span></div>
                                <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 5px; border-bottom: 1px solid #495057;"><span style="font-size: 1.1rem;">{prepare_arabic_text("العائد الإجمالي (قبل الضريبة)")}</span><span style="font-size: 1.2rem; font-weight: 600; color: #8ab4f8;">{results['gross_return']:,.2f} {prepare_arabic_text("جنيه")}</span></div>
                                <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 5px;"><span style="font-size: 1.1rem;">{prepare_arabic_text(f"قيمة الضريبة المستحقة ({tax_rate_main}%)")}</span><span style="font-size: 1.2rem; font-weight: 600; color: #dc3545;">{results['tax_amount']:,.2f} {prepare_arabic_text("جنيه")}</span></div>
                                </div>""",
                                unsafe_allow_html=True,
                            )

                        st.markdown(
                            "<div style='margin-top: 15px;'></div>",
                            unsafe_allow_html=True,
                        )

                        st.info(
                            prepare_arabic_text(
                                """
                                **💡 آلية صرف العوائد والضريبة:**
                                - **العائد الإجمالي (قبل الضريبة)** يُضاف إلى حسابك مقدمًا في يوم الشراء.
                                - في نهاية المدة، تسترد **القيمة الإسمية الكاملة**.
                                - **قيمة الضريبة** يتم خصمها من حسابك في تاريخ الاستحقاق. **لذا، يجب التأكد من وجود هذا المبلغ في حسابك لتجنب أي مشاكل.**
                                """
                            ),
                            icon="💡",
                        )

                else:
                    with results_placeholder_main.container(border=True):
                        st.error(
                            prepare_arabic_text("لم يتم العثور على عائد للأجل المحدد.")
                        )
        except Exception as e:
            with results_placeholder_main.container(border=True):
                st.error(
                    prepare_arabic_text(f"حدث خطأ غير متوقع أثناء الحساب: {e}"),
                    icon="🚨",
                )
    else:
        with results_placeholder_main.container(border=True):
            st.info(
                prepare_arabic_text(
                    "✨ ملخص استثمارك سيظهر هنا بتصميم أنيق بعد الضغط على زر الحساب."
                )
            )

    # --- Secondary Market Sale Calculator ---
    st.divider()
    st.header(prepare_arabic_text("⚖️ حاسبة البيع في السوق الثانوي"))
    col_secondary_form, col_secondary_results = st.columns(2, gap="large")

    with col_secondary_form:
        with st.container(border=True):
            st.subheader(
                prepare_arabic_text("1. أدخل بيانات الإذن الأصلي"), anchor=False
            )
            face_value_secondary = st.number_input(
                prepare_arabic_text("القيمة الإسمية للإذن"),
                min_value=25000.0,
                value=25000.0,
                step=25000.0,
                key="secondary_face_value",
            )
            original_yield_secondary = st.number_input(
                prepare_arabic_text("عائد الشراء الأصلي (%)"),
                min_value=1.0,
                value=29.0,
                step=0.1,
                key="secondary_original_yield",
                format="%.3f",
            )
            original_tenor_secondary = st.selectbox(
                prepare_arabic_text("أجل الإذن الأصلي (بالأيام)"),
                options,
                key="secondary_tenor",
            )
            tax_rate_secondary = st.number_input(
                prepare_arabic_text("نسبة الضريبة على الأرباح (%)"),
                0.0,
                100.0,
                C.DEFAULT_TAX_RATE_PERCENT,
                step=0.5,
                format="%.1f",
                key="secondary_tax",
            )
            st.subheader(prepare_arabic_text("2. أدخل تفاصيل البيع"), anchor=False)
            max_holding_days = (
                int(original_tenor_secondary) - 1 if original_tenor_secondary > 1 else 1
            )
            early_sale_days_secondary = st.number_input(
                prepare_arabic_text("أيام الاحتفاظ الفعلية (قبل البيع)"),
                min_value=1,
                value=min(60, max_holding_days),
                max_value=max_holding_days,
                step=1,
            )
            secondary_market_yield = st.number_input(
                prepare_arabic_text("العائد السائد في السوق للمشتري (%)"),
                min_value=1.0,
                value=30.0,
                step=0.1,
                format="%.3f",
            )
            calc_secondary_sale_button = st.button(
                prepare_arabic_text("حلل سعر البيع الثانوي"),
                use_container_width=True,
                type="primary",
                key="secondary_calc",
            )

    secondary_results_placeholder = col_secondary_results.empty()
    if calc_secondary_sale_button:
        try:
            results = analyze_secondary_sale(
                face_value_secondary,
                original_yield_secondary,
                original_tenor_secondary,
                early_sale_days_secondary,
                secondary_market_yield,
                tax_rate_secondary,
            )
            with secondary_results_placeholder.container(border=True):
                st.subheader(
                    prepare_arabic_text("✨ تحليل سعر البيع الثانوي"), anchor=False
                )
                if results.get("error"):
                    st.error(prepare_arabic_text(results["error"]))
                else:
                    if results["net_profit"] >= 0:
                        st.success(
                            f"البيع الآن يعتبر مربحًا. ستحقق ربحًا صافيًا قدره {results['net_profit']:,.2f} جنيه.",
                            icon="✅",
                        )
                    else:
                        st.warning(
                            f"البيع الآن سيحقق خسارة. ستبلغ خسارتك الصافية {abs(results['net_profit']):,.2f} جنيه.",
                            icon="⚠️",
                        )
                    st.markdown("---")
                    profit_color = (
                        "#28a745" if results["net_profit"] >= 0 else "#dc3545"
                    )
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(
                            f"""<div style="text-align: center; background-color: #495057; padding: 10px; border-radius: 10px; height: 100%;"><p style="font-size: 1rem; color: #adb5bd; margin-bottom: 0px;">{prepare_arabic_text("🏷️ سعر البيع الفعلي")}</p><p style="font-size: 1.9rem; color: #8ab4f8; font-weight: 600; line-height: 1.2;">{results['sale_price']:,.2f} {prepare_arabic_text("جنيه")}</p></div>""",
                            unsafe_allow_html=True,
                        )
                    with col2:
                        st.markdown(
                            f"""<div style="text-align: center; background-color: #495057; padding: 10px; border-radius: 10px; height: 100%;"><p style="font-size: 1rem; color: #adb5bd; margin-bottom: 0px;">{prepare_arabic_text("💰 صافي الربح / الخسارة")}</p><p style="font-size: 1.9rem; color: {profit_color}; font-weight: 600; line-height: 1.2;">{results['net_profit']:,.2f} {prepare_arabic_text("جنيه")}</p><p style="font-size: 1rem; color: {profit_color}; margin-top: -5px;">({results['period_yield']:.2f}% {prepare_arabic_text("عن فترة الاحتفاظ")})</p></div>""",
                            unsafe_allow_html=True,
                        )

                    st.markdown(
                        "<div style='margin-top: 15px;'></div>", unsafe_allow_html=True
                    )
                    with st.expander(prepare_arabic_text("عرض تفاصيل الحساب")):
                        st.markdown(
                            f"""<div style="padding: 10px; border-radius: 10px; background-color: #212529;"><div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 5px; border-bottom: 1px solid #495057;"><span style="font-size: 1.1rem;">{prepare_arabic_text("سعر الشراء الأصلي")}</span><span style="font-size: 1.2rem; font-weight: 600;">{results['original_purchase_price']:,.2f} {prepare_arabic_text("جنيه")}</span></div><div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 5px; border-bottom: 1px solid #495057;"><span style="font-size: 1.1rem;">{prepare_arabic_text("إجمالي الربح (قبل الضريبة)")}</span><span style="font-size: 1.2rem; font-weight: 600; color: {'#28a745' if results['gross_profit'] >= 0 else '#dc3545'};">{results['gross_profit']:,.2f} {prepare_arabic_text("جنيه")}</span></div><div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 5px;"><span style="font-size: 1.1rem;">{prepare_arabic_text(f"قيمة الضريبة ({tax_rate_secondary}%)")}</span><span style="font-size: 1.2rem; font-weight: 600; color: #dc3545;">-{results['tax_amount']:,.2f} {prepare_arabic_text("جنيه")}</span></div></div>""",
                            unsafe_allow_html=True,
                        )
                        if results["gross_profit"] <= 0:
                            st.info(
                                prepare_arabic_text(
                                    "لا توجد ضريبة على الخسائر الرأسمالية."
                                ),
                                icon="ℹ️",
                            )
        except Exception as e:
            with secondary_results_placeholder.container(border=True):
                st.error(
                    prepare_arabic_text(f"حدث خطأ غير متوقع أثناء الحساب: {e}"),
                    icon="🚨",
                )
    else:
        with secondary_results_placeholder.container(border=True):
            st.info(
                prepare_arabic_text("✨ أدخل بيانات البيع في النموذج لتحليل قرارك.")
            )

    # --- Historical Data Chart Section ---
    st.divider()
    st.header(prepare_arabic_text("📈 تطور العائد تاريخيًا"))

    if not historical_df.empty:
        available_tenors = sorted(historical_df[C.TENOR_COLUMN_NAME].unique())
        selected_tenors = st.multiselect(
            label=prepare_arabic_text("اختر الآجال التي تريد عرضها:"),
            options=available_tenors,
            default=available_tenors,
            label_visibility="collapsed",
        )

        if selected_tenors:
            chart_df = historical_df[
                historical_df[C.TENOR_COLUMN_NAME].isin(selected_tenors)
            ]

            fig = px.line(
                chart_df,
                x=C.DATE_COLUMN_NAME,
                y=C.YIELD_COLUMN_NAME,
                color=C.TENOR_COLUMN_NAME,
                markers=True,
                labels={
                    C.DATE_COLUMN_NAME: prepare_arabic_text("تاريخ التحديث"),
                    C.YIELD_COLUMN_NAME: prepare_arabic_text("نسبة العائد (%)"),
                    C.TENOR_COLUMN_NAME: prepare_arabic_text("الأجل (يوم)"),
                },
                title=prepare_arabic_text(
                    "التغير في متوسط العائد المرجح لأذون الخزانة"
                ),
            )
            fig.update_layout(
                legend_title_text=prepare_arabic_text("الأجل"),
                title_x=0.5,
                template="plotly_dark",
                xaxis=dict(tickformat="%d-%m-%Y"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(
                prepare_arabic_text(
                    "يرجى اختيار أجل واحد على الأقل لعرض الرسم البياني."
                )
            )

    else:
        st.info(
            prepare_arabic_text(
                "لا توجد بيانات تاريخية كافية لعرض الرسم البياني. قم بتحديث البيانات عدة مرات على مدار أيام مختلفة."
            )
        )

    # --- Help Section ---
    st.divider()
    with st.expander(prepare_arabic_text("💡 شرح ومساعدة (أسئلة شائعة)")):
        st.markdown(
            prepare_arabic_text(
                """
        #### **ما الفرق بين "العائد" و "الفائدة"؟**
        - **الفائدة (Interest):** تُحسب على أصل المبلغ وتُضاف إليه دورياً (مثل شهادات الادخار).
        - **العائد (Yield):** في أذون الخزانة، أنت تشتري الإذن بسعر **أقل** من قيمته الإسمية، وربحك هو الفارق الذي ستحصل عليه في نهاية المدة.
        ---
        #### **كيف تعمل حاسبة العائد الأساسية؟**
        1.  **حساب سعر الشراء:** `سعر الشراء = القيمة الإسمية ÷ (1 + (العائد ÷ 100) × (مدة الإذن ÷ 365))`
        2.  **حساب إجمالي الربح:** `إجمالي الربح = القيمة الإسمية - سعر الشراء`
        3.  **حساب الضريبة:** `إجمالي الربح × (نسبة الضريبة ÷ 100)`
        4.  **حساب صافي الربح:** `إجمالي الربح - قيمة الضريبة`
        ---
        #### **كيف تعمل حاسبة البيع في السوق الثانوي؟**
        هذه الحاسبة تجيب على سؤال: "كم سيكون ربحي أو خسارتي إذا بعت الإذن اليوم قبل تاريخ استحقاقه؟". سعر البيع هنا لا يعتمد على سعر شرائك، بل على سعر الفائدة **الحالي** في السوق.
        1.  **حساب سعر شرائك الأصلي:** بنفس طريقة الحاسبة الأساسية.
        2.  **حساب سعر البيع اليوم:** `الأيام المتبقية = الأجل الأصلي - أيام الاحتفاظ`، `سعر البيع = القيمة الإسمية ÷ (1 + (العائد السائد اليوم ÷ 100) × (الأيام المتبقية ÷ 365))`
        3.  **النتيجة النهائية:** `الربح أو الخسارة = سعر البيع - سعر الشراء الأصلي`. يتم حساب الضريبة على هذا الربح إذا كان موجباً.
        """
            )
        )
        st.markdown("---")
        st.subheader(prepare_arabic_text("تقدير رسوم أمين الحفظ"))
        st.markdown(
            prepare_arabic_text(
                """
        تحتفظ البنوك بأذون الخزانة الخاصة بك مقابل رسوم خدمة دورية. تُحسب هذه الرسوم كنسبة مئوية **سنوية** من **القيمة الإسمية** الإجمالية لأذونك، ولكنها تُخصم من حسابك بشكل **ربع سنوي** (كل 3 أشهر).
        
        تختلف هذه النسبة من بنك لآخر (عادة ما تكون حوالي 0.1% سنوياً). أدخل بياناتك أدناه لتقدير قيمة الخصم الربع سنوي المتوقع.
        """
            )
        )

        fee_col1, fee_col2 = st.columns(2)
        with fee_col1:
            total_face_value = st.number_input(
                prepare_arabic_text("إجمالي القيمة الإسمية لكل أذونك"),
                min_value=25000.0,
                value=100000.0,
                step=25000.0,
                key="fee_calc_total",
            )
        with fee_col2:
            fee_percentage = st.number_input(
                prepare_arabic_text("نسبة رسوم الحفظ السنوية (%)"),
                min_value=0.0,
                value=0.10,
                step=0.01,
                format="%.2f",
                key="fee_calc_perc",
            )

        annual_fee = total_face_value * (fee_percentage / 100.0)
        quarterly_deduction = annual_fee / 4

        st.markdown(
            f"""
            <div style='text-align: center; background-color: #212529; padding: 10px; border-radius: 10px; margin-top:10px;'>
                <p style="font-size: 1rem; color: #adb5bd; margin-bottom: 0px;">{prepare_arabic_text("الخصم الربع سنوي التقريبي")}</p>
                <p style="font-size: 1.5rem; color: #ffc107; font-weight: 600; line-height: 1.2;">{quarterly_deduction:,.2f} {prepare_arabic_text("جنيه")}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            prepare_arabic_text(
                "\n\n***إخلاء مسؤولية:*** *هذا التطبيق هو أداة استرشادية فقط. للحصول على أرقام نهائية ودقيقة، يرجى الرجوع إلى البنك أو المؤسسة المالية التي تتعامل معها.*"
            )
        )


if __name__ == "__main__":
    main()
