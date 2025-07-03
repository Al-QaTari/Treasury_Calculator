import constants as C # تم التعديل هنا: إزالة النقطة

def calculate_primary_yield(investment_amount, tenor, yield_rate, tax_rate):
    """
    Calculates the net return for a primary T-bill investment.
    """
    annual_yield_decimal = yield_rate / 100.0
    gross_return = investment_amount * (annual_yield_decimal / C.DAYS_IN_YEAR) * tenor
    tax_amount = gross_return * (tax_rate / 100.0)
    net_return = gross_return - tax_amount
    total_payout = investment_amount + net_return
    return {
        "gross_return": gross_return,
        "tax_amount": tax_amount,
        "net_return": net_return,
        "total_payout": total_payout
    }

def analyze_secondary_sale(face_value, original_yield, original_tenor, holding_days, secondary_yield, tax_rate):
    """
    Analyzes the outcome of selling a T-bill on the secondary market.
    """
    # Business logic validation
    if not 1 <= holding_days < original_tenor:
        return {"error": "أيام الاحتفاظ يجب أن تكون أكبر من صفر وأقل من أجل الإذن الأصلي."}

    original_purchase_price = face_value / (1 + (original_yield / 100 * original_tenor / C.DAYS_IN_YEAR))
    remaining_days = original_tenor - holding_days

    sale_price = face_value / (1 + (secondary_yield / 100 * remaining_days / C.DAYS_IN_YEAR))
    gross_profit = sale_price - original_purchase_price
    tax_amount = max(0, gross_profit * (tax_rate / 100.0))
    net_profit = gross_profit - tax_amount
    annualized_yield = (net_profit / original_purchase_price) * (C.DAYS_IN_YEAR / holding_days) * 100 if holding_days > 0 else 0

    return {
        "error": None,
        "sale_price": sale_price,
        "gross_profit": gross_profit,
        "tax_amount": tax_amount,
        "net_profit": net_profit,
        "annualized_yield": annualized_yield,
        "original_purchase_price": original_purchase_price
    }