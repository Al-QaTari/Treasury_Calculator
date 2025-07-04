import sys
import os
import pytest

# هذا الكود يضيف المجلد الرئيسي للمشروع إلى مسار بايثون للعثور على ملف app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ⬇️ !! تأكد من أن هذه الأسماء تطابق الأسماء في ملفاتك
# من المفترض أن تكون الدالة الأولى في ملف calculations.py والثانية في app.py
from calculations import calculate_primary_yield 
from app import calculate_certificate_profit

# --- اختبارات أذون الخزانة ---

def test_treasury_bill_standard_case():
    """
    🧪 يختبر حسابات أذون الخزانة بحالة قياسية.
    """
    amount = 100000
    rate = 25.0
    duration = 364
    tax_rate = 20.0 # ⬇️ المتغير الجديد الذي تمت إضافته

    # ⬇️ تم تمرير المتغير الرابع هنا
    actual_results = calculate_primary_yield(amount, rate, duration, tax_rate)

    # النتائج المتوقعة
    expected_gross_profit = 24931.51
    expected_tax_amount = expected_gross_profit * (tax_rate / 100)
    expected_net_profit = expected_gross_profit - expected_tax_amount

    # التحقق من صحة النتائج
    assert actual_results["gross_return"] == pytest.approx(expected_gross_profit, abs=0.01)
    assert actual_results["tax_amount"] == pytest.approx(expected_tax_amount, abs=0.01)
    assert actual_results["net_return"] == pytest.approx(expected_net_profit, abs=0.01)


# --- اختبارات الشهادات البنكية ---

def test_certificate_standard_case():
    """
    🧪 يختبر حسابات الشهادات البنكية بحالة قياسية.
    """
    amount = 50000
    rate = 18.0

    actual_results = calculate_certificate_profit(amount, rate)
    
    # النتائج المتوقعة
    expected_gross_profit = 9000.0
    expected_tax_amount = 1800.0
    expected_net_profit = 7200.0

    # التحقق من صحة النتائج
    assert actual_results["gross_profit"] == pytest.approx(expected_gross_profit, abs=0.01)
    assert actual_results["tax_amount"] == pytest.approx(expected_tax_amount, abs=0.01)
    assert actual_results["net_profit"] == pytest.approx(expected_net_profit, abs=0.01)


# --- اختبارات الحالات الخاصة ---

def test_zero_amount_input():
    """
    🧪 يختبر سلوك الدوال عند إدخال مبلغ صفر.
    """
    # ⬇️ تم تمرير المتغير الرابع هنا أيضاً
    treasury_results = calculate_primary_yield(0, 25.0, 364, 20.0)
    cert_results = calculate_certificate_profit(0, 18.0)

    # يجب أن تكون كل النتائج صفراً
    assert treasury_results["gross_return"] == 0
    assert treasury_results["net_return"] == 0
    assert cert_results["gross_profit"] == 0
    assert cert_results["net_profit"] == 0