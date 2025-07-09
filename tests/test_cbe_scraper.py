# tests/test_cbe_scraper.py
import sys
import os
import pytest
import pandas as pd

# إضافة المجلد الرئيسي للمشروع إلى مسار بايثون
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cbe_scraper import parse_cbe_html
import constants as C

# محتوى HTML وهمي تم نسخه من الموقع للاختبار بدون انترنت
MOCK_HTML_CONTENT = """
<html>
<body>
    <h2>النتائج</h2>
    <table>
        <thead>
            <tr><th>البيان</th><th>182</th><th>364</th></tr>
        </thead>
        <tbody>
            <tr><td>تاريخ الجلسة</td><td>06/07/2025</td><td>06/07/2025</td></tr>
        </tbody>
    </table>
    <p><strong>تفاصيل العروض المقبولة</strong></p>
    <table>
      <tbody>
        <tr><td>أقل عائد</td><td>26.111</td><td>24.999</td></tr>
        <tr><td>أعلى عائد</td><td>28.222</td><td>25.555</td></tr>
        <tr><td>متوسط العائد المرجح</td><td>27.192</td><td>25.043</td></tr>
      </tbody>
    </table>

    <h2>النتائج</h2>
    <table>
        <thead>
            <tr><th>البيان</th><th>91</th><th>273</th></tr>
        </thead>
        <tbody>
            <tr><td>تاريخ الجلسة</td><td>07/07/2025</td><td>07/07/2025</td></tr>
        </tbody>
    </table>
    <p><strong>تفاصيل العروض المقبولة</strong></p>
    <table>
      <tbody>
        <tr><td>أقل عائد</td><td>26.000</td><td>25.000</td></tr>
        <tr><td>أعلى عائد</td><td>28.000</td><td>27.000</td></tr>
        <tr><td>متوسط العائد المرجح</td><td>27.558</td><td>26.758</td></tr>
      </tbody>
    </table>
</body>
</html>
"""

def test_html_parser_with_mock_data():
    """
    🧪 يختبر دالة تحليل HTML باستخدام بيانات وهمية محفوظة.
    Tests the HTML parsing function with static mock data.
    """
    # 1. استدعاء الدالة مع المحتوى الوهمي
    parsed_df = parse_cbe_html(MOCK_HTML_CONTENT)

    # 2. التحقق من النتائج
    assert parsed_df is not None, "يجب ألا تكون النتيجة None"
    assert isinstance(parsed_df, pd.DataFrame), "يجب أن تكون النتيجة DataFrame"
    assert not parsed_df.empty, "يجب ألا يكون الـ DataFrame فارغًا"
    
    # 3. التحقق من الهيكل والأبعاد
    assert len(parsed_df) == 4, "يجب أن يتم استخلاص بيانات لـ 4 آجال"
    expected_columns = [C.TENOR_COLUMN_NAME, C.YIELD_COLUMN_NAME, C.SESSION_DATE_COLUMN_NAME, C.DATE_COLUMN_NAME]
    assert all(col in parsed_df.columns for col in expected_columns), "يجب أن يحتوي على الأعمدة المتوقعة"

    # 4. التحقق من دقة تحليل قيمة محددة
    # تحويل الآجال إلى أرقام للمقارنة الصحيحة
    parsed_df[C.TENOR_COLUMN_NAME] = pd.to_numeric(parsed_df[C.TENOR_COLUMN_NAME])
    yield_364 = parsed_df[parsed_df[C.TENOR_COLUMN_NAME] == 364][C.YIELD_COLUMN_NAME].iloc[0]
    assert yield_364 == 25.043, "يجب أن تكون قيمة العائد لأجل 364 يومًا صحيحة"
    
    yield_91 = parsed_df[parsed_df[C.TENOR_COLUMN_NAME] == 91][C.YIELD_COLUMN_NAME].iloc[0]
    assert yield_91 == 27.558, "يجب أن تكون قيمة العائد لأجل 91 يومًا صحيحة"