import sys
import os
import pytest

# يضيف المجلد الرئيسي للمشروع إلى مسار بايثون للعثور على الوحدات البرمجية
# This adds the project's root directory to Python's path to find the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# --- استيراد الدوال المحدثة من ملف calculations ---
# تم حذف استيراد الدالة القديمة وإضافة الدالة الجديدة
from calculations import calculate_primary_yield, analyze_secondary_sale

# --- اختبارات حاسبة العائد الأساسية ---

def test_calculate_primary_yield_standard_case():
    """
    🧪 يختبر حساب العائد الأساسي لأذون الخزانة في حالة قياسية.
    تم تحديث القيم المتوقعة بناءً على طريقة الحساب الجديدة والصحيحة.
    """
    face_value = 100000.0
    yield_rate = 25.0
    tenor = 364
    tax_rate = 20.0

    actual_results = calculate_primary_yield(face_value, yield_rate, tenor, tax_rate)

    # النتائج المتوقعة بناءً على الحساب الصحيح (كأداة خصم)
    expected_purchase_price = 80040.04
    expected_gross_return = 19959.96
    expected_tax_amount = 3991.99
    expected_net_return = 15967.97
    expected_real_profit_percentage = 19.95

    assert actual_results["purchase_price"] == pytest.approx(expected_purchase_price, abs=0.01)
    assert actual_results["gross_return"] == pytest.approx(expected_gross_return, abs=0.01)
    assert actual_results["tax_amount"] == pytest.approx(expected_tax_amount, abs=0.01)
    assert actual_results["net_return"] == pytest.approx(expected_net_return, abs=0.01)
    assert actual_results["real_profit_percentage"] == pytest.approx(expected_real_profit_percentage, abs=0.01)


def test_calculate_primary_yield_zero_amount():
    """
    🧪 يختبر سلوك حاسبة العائد الأساسية عند إدخال مبلغ صفر.
    """
    results = calculate_primary_yield(0, 25.0, 364, 20.0)
    assert results["net_return"] == 0
    assert results["gross_return"] == 0
    assert results["purchase_price"] == 0


# --- اختبارات جديدة لحاسبة البيع في السوق الثانوي ---

def test_analyze_secondary_sale_with_profit():
    """
    🧪 [فحص جديد] يختبر حاسبة البيع الثانوي في حالة تحقيق ربح.
    """
    results = analyze_secondary_sale(
        face_value=100000,
        original_yield=25.0,
        original_tenor=364,
        holding_days=90,
        secondary_yield=23.0,  # العائد في السوق قل، لذا من المتوقع تحقيق ربح
        tax_rate=20.0,
    )

    assert results["error"] is None
    assert results["sale_price"] == pytest.approx(85361.30, abs=0.01)
    assert results["net_profit"] == pytest.approx(4257.01, abs=0.01)
    assert results["tax_amount"] == pytest.approx(1064.25, abs=0.01)


def test_analyze_secondary_sale_with_loss():
    """
    🧪 [فحص جديد] يختبر حاسبة البيع الثانوي في حالة تحقيق خسارة.
    """
    results = analyze_secondary_sale(
        face_value=100000,
        original_yield=25.0,
        original_tenor=364,
        holding_days=90,
        secondary_yield=28.0,  # العائد في السوق زاد، لذا من المتوقع تحقيق خسارة
        tax_rate=20.0,
    )
    
    assert results["error"] is None
    assert results["sale_price"] == pytest.approx(83136.92, abs=0.01)
    assert results["net_profit"] == pytest.approx(3096.88, abs=0.01)
    # يجب أن تكون الضريبة صفراً في حالة الخسارة
    assert results["tax_amount"] == 0


def test_analyze_secondary_sale_invalid_days():
    """
    🧪 [فحص جديد] يختبر الحالة التي تكون فيها أيام الاحتفاظ غير صالحة.
    """
    results_too_many_days = analyze_secondary_sale(100000, 25.0, 91, 91, 28.0, 20.0)
    results_zero_days = analyze_secondary_sale(100000, 25.0, 91, 0, 28.0, 20.0)

    assert results_too_many_days["error"] is not None
    assert results_zero_days["error"] is not None
