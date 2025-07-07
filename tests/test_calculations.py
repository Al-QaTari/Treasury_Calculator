# tests/test_calculations.py
import sys
import os
import pytest

# يضيف المجلد الرئيسي للمشروع إلى مسار بايثون للعثور على الوحدات البرمجية
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from calculations import calculate_primary_yield, analyze_secondary_sale
import constants as C

# --- اختبارات حاسبة العائد الأساسية (بطريقة أكثر دقة) ---

def test_primary_yield_logic_is_self_consistent():
    """
    🧪 يختبر أن منطق حاسبة العائد الأساسي سليم ومترابط.
    This test verifies that the function's internal logic is consistent.
    """
    face_value = 100000.0
    yield_rate = 25.0
    tenor = 364
    tax_rate = 20.0

    results = calculate_primary_yield(face_value, yield_rate, tenor, tax_rate)

    # 1. هل سعر الشراء + الربح الإجمالي = القيمة الإسمية؟
    assert results["purchase_price"] + results["gross_return"] == pytest.approx(face_value)

    # 2. هل الربح الصافي = الربح الإجمالي - الضريبة؟
    assert results["gross_return"] - results["tax_amount"] == pytest.approx(results["net_return"])

    # 3. هل الضريبة المحسوبة صحيحة؟
    assert results["tax_amount"] == pytest.approx(results["gross_return"] * (tax_rate / 100.0))

    # 4. هل المبلغ المستلم في النهاية هو القيمة الإسمية؟
    assert results["total_payout"] == pytest.approx(face_value)


def test_primary_yield_zero_amount():
    """
    🧪 يختبر سلوك حاسبة العائد الأساسية عند إدخال مبلغ صفر.
    """
    results = calculate_primary_yield(0, 25.0, 364, 20.0)
    assert results["net_return"] == 0
    assert results["gross_return"] == 0
    assert results["purchase_price"] == 0


# --- اختبارات حاسبة البيع الثانوي (بطريقة أكثر دقة) ---

def test_secondary_sale_logic_with_profit():
    """
    🧪 يختبر منطق البيع الثانوي في حالة تحقيق ربح.
    """
    results = analyze_secondary_sale(
        face_value=100000,
        original_yield=25.0,
        original_tenor=364,
        holding_days=90,
        secondary_yield=23.0,
        tax_rate=20.0,
    )

    assert results["error"] is None
    # 1. هل سعر الشراء + الربح الإجمالي = سعر البيع؟
    assert results["original_purchase_price"] + results["gross_profit"] == pytest.approx(results["sale_price"])
    # 2. هل الربح الصافي = الربح الإجمالي - الضريبة؟
    assert results["gross_profit"] - results["tax_amount"] == pytest.approx(results["net_profit"])
    # 3. هل الضريبة أكبر من صفر في حالة الربح؟
    assert results["tax_amount"] > 0


def test_secondary_sale_logic_with_loss():
    """
    🧪 يختبر منطق البيع الثانوي في حالة تحقيق خسارة.
    """
    results = analyze_secondary_sale(
        face_value=100000,
        original_yield=25.0,
        original_tenor=364,
        holding_days=90,
        secondary_yield=35.0, # عائد مرتفع يؤدي لخسارة
        tax_rate=20.0,
    )
    
    assert results["error"] is None
    # 1. هل سعر الشراء + الربح الإجمالي (الذي سيكون سالبًا) = سعر البيع؟
    assert results["original_purchase_price"] + results["gross_profit"] == pytest.approx(results["sale_price"])
    # 2. هل الربح الصافي يساوي الربح الإجمالي (لأن الضريبة صفر)؟
    assert results["gross_profit"] == pytest.approx(results["net_profit"])
    # 3. هل الضريبة تساوي صفر في حالة الخسارة؟
    assert results["tax_amount"] == 0


def test_secondary_sale_invalid_days():
    """
    🧪 يختبر الحالة التي تكون فيها أيام الاحتفاظ غير صالحة.
    """
    results = analyze_secondary_sale(100000, 25.0, 91, 91, 28.0, 20.0)
    assert results["error"] is not None
