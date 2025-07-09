# tests/test_db_manager.py
import sys
import os
import pytest
import pandas as pd
from datetime import datetime

# إضافة المجلد الرئيسي للمشروع إلى مسار بايثون
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db_manager import DatabaseManager
import constants as C

@pytest.fixture
def in_memory_db():
    """
    إعداد قاعدة بيانات وهمية في الذاكرة لكل اختبار، والتأكد من أنها نظيفة.
    This fixture creates a fresh in-memory database for each test.
    """
    # استخدام ":memory:" ينشئ قاعدة بيانات مؤقتة في الرام
    db_manager = DatabaseManager(db_filename=":memory:")
    return db_manager

def test_save_and_load_data(in_memory_db):
    """
    🧪 يختبر حفظ DataFrame في قاعدة البيانات ثم تحميل أحدث البيانات والتحقق من تطابقها.
    Tests the flow of saving data and then loading the latest set.
    """
    # 1. إعداد بيانات وهمية
    test_date = datetime.now().strftime("%Y-%m-%d")
    data = {
        C.DATE_COLUMN_NAME: [test_date, test_date],
        C.TENOR_COLUMN_NAME: [91, 182],
        C.YIELD_COLUMN_NAME: [25.5, 26.5],
        C.SESSION_DATE_COLUMN_NAME: ["01/01/2025", "01/01/2025"]
    }
    df_to_save = pd.DataFrame(data)

    # 2. عملية الحفظ
    in_memory_db.save_data(df_to_save)

    # 3. عملية التحميل
    loaded_df, status_message = in_memory_db.load_latest_data()

    # 4. التحقق من النتائج
    assert status_message is not None, "يجب أن يتم إرجاع رسالة حالة"
    assert not loaded_df.empty, "يجب ألا يكون الـ DataFrame المحمل فارغًا"
    assert len(loaded_df) == 2, "يجب أن يحتوي الـ DataFrame المحمل على صفين"
    
    # التحقق من أن قيمة العائد لأجل 182 يومًا صحيحة
    yield_182 = loaded_df[loaded_df[C.TENOR_COLUMN_NAME] == 182][C.YIELD_COLUMN_NAME].iloc[0]
    assert yield_182 == 26.5