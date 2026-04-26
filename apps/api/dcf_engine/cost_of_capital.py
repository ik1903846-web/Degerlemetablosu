"""
Cost of Capital hesaplamaları (Damodaran metodolojisi).

ADR References:
- ADR-005a: Cost of Equity = Rf + β × ERP
- ADR-006c: λ revenue-based country exposure
- ADR-065: Bottom-up beta (Hamada formülü)
- ADR-026: Optimal capital structure diagnostic
"""

from dataclasses import dataclass


# ============================================================================
# Cost of Equity
# ============================================================================

def cost_of_equity(
    risk_free_rate: float,
    beta_levered: float,
    equity_risk_premium: float,
) -> float:
    """
    Cost of Equity hesabı (CAPM modeli).

    Damodaran Heineken 2019 formülü:
        Cost of Equity = Rf + β × ERP

    Bu formül "revenue-weighted ERP" ile çalışır (çoklu coğrafya):
        ERP = Σ(weight_i × ERP_i)

    Args:
        risk_free_rate: Risk-free rate (decimal, örn 0.04 = %4)
        beta_levered: Levered beta (firma kaldıraçlı beta)
        equity_risk_premium: ERP (revenue-weighted veya tek ülke)

    Returns:
        Cost of Equity (decimal)

    Example:
        >>> cost_of_equity(-0.005, 1.20, 0.0683)
        0.07696
    """
    return risk_free_rate + beta_levered * equity_risk_premium


# ============================================================================
# Beta Hesaplamaları (ADR-065 Bottom-up Beta)
# ============================================================================

def unlever_beta(
    levered_beta: float,
    debt_to_equity: float,
    tax_rate: float,
) -> float:
    """
    Levered beta'yı unlever et (Hamada formülü ters).

    β_unlevered = β_levered / (1 + (1-tax) × D/E)

    Args:
        levered_beta: Levered (kaldıraçlı) beta
        debt_to_equity: D/E ratio (decimal, örn 0.67 = %67)
        tax_rate: Marginal tax rate (decimal)

    Returns:
        Unlevered beta

    Example:
        >>> unlever_beta(1.20, 0.6698, 0.25)
        0.7984...
    """
    return levered_beta / (1 + (1 - tax_rate) * debt_to_equity)


def relever_beta(
    unlevered_beta: float,
    debt_to_equity: float,
    tax_rate: float,
) -> float:
    """
    Unlevered beta'yı firma kaldıraçıyla relever et (Hamada formülü).

    β_levered = β_unlevered × (1 + (1-tax) × D/E)

    Args:
        unlevered_beta: Sektör unlevered beta (Damodaran tablodan)
        debt_to_equity: Firma D/E ratio
        tax_rate: Marginal tax rate

    Returns:
        Levered beta (firma için)

    Example:
        >>> relever_beta(0.80, 0.6698, 0.25)
        1.2018...
    """
    return unlevered_beta * (1 + (1 - tax_rate) * debt_to_equity)


# ============================================================================
# Cost of Debt
# ============================================================================

def after_tax_cost_of_debt(
    risk_free_rate: float,
    default_spread: float,
    tax_rate: float,
) -> float:
    """
    After-tax Cost of Debt hesabı.

    Pre-tax: Rd = Rf + default spread
    After-tax: Rd × (1 - tax)

    Args:
        risk_free_rate: Risk-free rate
        default_spread: Firma kredi rating'ine göre spread
        tax_rate: Marginal tax rate (vergi kalkanı için)

    Returns:
        After-tax cost of debt (decimal)

    Example (Heineken 2019):
        >>> after_tax_cost_of_debt(-0.005, 0.02, 0.25)
        0.01125
    """
    pre_tax_cost = risk_free_rate + default_spread
    return pre_tax_cost * (1 - tax_rate)


# ============================================================================
# WACC
# ============================================================================

@dataclass
class WACCResult:
    """WACC hesabı detaylı sonuç."""
    cost_of_equity: float
    cost_of_debt_after_tax: float
    equity_weight: float
    debt_weight: float
    wacc: float


def wacc(
    cost_of_equity: float,
    cost_of_debt_after_tax: float,
    equity_weight: float,
    debt_weight: float,
) -> WACCResult:
    """
    WACC = E/(E+D) × Re + D/(E+D) × Rd × (1-t)

    Args:
        cost_of_equity: Cost of Equity (decimal)
        cost_of_debt_after_tax: After-tax Cost of Debt
        equity_weight: E / (E+D)
        debt_weight: D / (E+D)

    Returns:
        WACCResult dataclass with breakdown

    Example (Heineken 2019):
        >>> result = wacc(0.0766, 0.0113, 0.599, 0.401)
        >>> result.wacc
        0.0504...
    """
    # Weights kontrol (toplam 1.0 olmalı)
    total_weight = equity_weight + debt_weight
    if abs(total_weight - 1.0) > 0.01:
        raise ValueError(
            f"Equity + Debt weights must sum to 1.0, got {total_weight}"
        )

    wacc_value = (
        equity_weight * cost_of_equity +
        debt_weight * cost_of_debt_after_tax
    )

    return WACCResult(
        cost_of_equity=cost_of_equity,
        cost_of_debt_after_tax=cost_of_debt_after_tax,
        equity_weight=equity_weight,
        debt_weight=debt_weight,
        wacc=wacc_value,
    )
