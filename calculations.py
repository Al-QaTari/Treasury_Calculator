# calculations.py
from typing import Dict, Any, Optional

import constants as C

def calculate_primary_yield(face_value: float, yield_rate: float, tenor: int, tax_rate: float) -> Dict[str, float]:
    """
    Calculates returns for a primary T-bill investment based on its discount nature.
    The 'yield_rate' is the annualized yield, used to find the purchase price.

    Args:
        face_value (float): The nominal value of the T-bill at maturity.
        yield_rate (float): The annualized accepted yield rate (e.g., 27.5).
        tenor (int): The term of the T-bill in days.
        tax_rate (float): The tax rate on profits (e.g., 20.0).

    Returns:
        A dictionary with detailed calculation results.
    """
    if face_value <= 0 or yield_rate <= 0 or tenor <= 0:
        return {key: 0.0 for key in [
            "purchase_price", "gross_return", "tax_amount", "net_return",
            "total_payout", "real_profit_percentage"
        ]}

    # This calculation reflects the discount instrument nature of T-bills
    purchase_price = face_value / (1 + (yield_rate / 100.0 * tenor / C.DAYS_IN_YEAR))
    
    gross_return = face_value - purchase_price
    tax_amount = gross_return * (tax_rate / 100.0)
    net_return = gross_return - tax_amount

    # Real profit percentage is the net return over the actual amount paid
    real_profit_percentage = (net_return / purchase_price) * 100 if purchase_price > 0 else 0

    return {
        "purchase_price": purchase_price,
        "gross_return": gross_return,
        "tax_amount": tax_amount,
        "net_return": net_return,
        "total_payout": face_value,  # At maturity, you receive the face value
        "real_profit_percentage": real_profit_percentage,
    }


def analyze_secondary_sale(face_value: float, original_yield: float, original_tenor: int, 
                           holding_days: int, secondary_yield: float, tax_rate: float) -> Dict[str, Any]:
    """
    Analyzes the outcome of selling a T-bill on the secondary market.

    Args:
        face_value (float): The T-bill's nominal value.
        original_yield (float): The yield rate at the time of original purchase.
        original_tenor (int): The original term of the T-bill in days.
        holding_days (int): How many days the T-bill was held before selling.
        secondary_yield (float): The prevailing market yield for the remaining period.
        tax_rate (float): The tax rate on profits.

    Returns:
        A dictionary with the analysis results or an error message.
    """
    if not 1 <= holding_days < original_tenor:
        return {"error": "أيام الاحتفاظ يجب أن تكون أكبر من صفر وأقل من أجل الإذن الأصلي."}

    # Price you paid initially
    original_purchase_price = face_value / (1 + (original_yield / 100.0 * original_tenor / C.DAYS_IN_YEAR))
    
    # Price you sell at today
    remaining_days = original_tenor - holding_days
    sale_price = face_value / (1 + (secondary_yield / 100.0 * remaining_days / C.DAYS_IN_YEAR))
    
    gross_profit = sale_price - original_purchase_price
    tax_amount = max(0, gross_profit * (tax_rate / 100.0)) # Tax is only on positive profit
    net_profit = gross_profit - tax_amount

    # Actual yield for the period you held the T-bill
    period_yield = (net_profit / original_purchase_price) * 100 if original_purchase_price > 0 else 0

    return {
        "error": None,
        "original_purchase_price": original_purchase_price,
        "sale_price": sale_price,
        "gross_profit": gross_profit,
        "tax_amount": tax_amount,
        "net_profit": net_profit,
        "period_yield": period_yield,
    }
