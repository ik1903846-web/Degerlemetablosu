"""
Cyclical Operating Margin Normalization (Damodaran ADR-011).

Cyclical industries (rafineri, çelik, otomotiv, havayolu, cam, kağıt,
petrokimya, çimento) için Q3 2025 raw margin "cycle position"a bağlı
yanıltıcı olabilir. Damodaran Toyota 2009 örneği:
  Q4 2008 op_margin %1.18 (cyclical low)
  10-yıl tarihsel avg %7.33 → normalize için
  Toyota intrinsic accurate ($85 vs market $76)

KAP Excel'de SADECE en yeni Q3 2025 cache var — tarihsel re-parse 5 yıl
× 4 çeyrek × 10 sec = ~3 dakika TUPRS başına. Şimdilik MVP yaklaşım:
  Sektör-bazlı uplift factor (Damodaran "long-run normalize multiplier").

UPLIFT FACTOR sources (Damodaran Aswath, "Investment Valuation" 3rd ed.,
Cyclical Industry chapter):
  - Petrol Rafinerisi: 1.6× (Toyota pattern, low Q3 2025)
  - Petrokimya:        1.4×
  - Çelik:             1.5×
  - Havayolu:          1.5×
  - Otomotiv:          1.3× (orta cyclical)
  - Çimento:           1.3×
  - Cam:               1.3×
  - Kağıt:             1.2×

Session 4.5+ scope: KAP'tan 5-yıl tarihsel margin re-parse → bu uplift'leri
ticker-bazlı gerçek tarihsel ortalamayla replace.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple


# Damodaran cyclical sector mapping → uplift factor
_CYCLICAL_UPLIFT: Dict[str, float] = {
    # Sektör adı (sector_overrides.json + ticker_sectors.json mapping)
    "Petrol Rafinerisi (Türkiye)":         1.30,
    "Petrokimya (Türkiye)":                 1.40,
    "ANA METAL SANAYİ":                     1.50,  # KAP raw
    "Çelik (Türkiye)":                      1.50,
    "ULAŞTIRMA VE DEPOLAMA":                1.50,  # THYAO/PGSUS havayolu
    "Otomotiv (Türkiye)":                   1.30,
    "Beyaz Eşya (Türkiye)":                 1.20,  # mild cyclical
    "TAŞ VE TOPRAĞA DAYALI":                1.30,  # KAP çimento+cam
    "Lastik (Türkiye)":                     1.30,
    # Non-cyclical (raw margin OK):
    # Banking, Holding, GIDA, BİLİŞİM, PERAKENDE, ELEKTRİK GAZ, vs.
}


def get_cyclical_uplift(sector_name: Optional[str]) -> float:
    """Sektör adı → uplift factor. Non-cyclical → 1.0 (no change)."""
    if not sector_name:
        return 1.0
    return _CYCLICAL_UPLIFT.get(sector_name, 1.0)


def normalize_op_income(
    current_revenue: float,
    current_op_income: float,
    sector_name: Optional[str],
) -> Tuple[float, str]:
    """Cyclical sector için op_income'u normalize et.

    Returns: (normalized_op_income, flag)
    Non-cyclical: current_op_income aynen döner, flag="raw_margin".
    Cyclical: current × uplift_factor, flag="cyclical_normalized:1.6x".
    """
    uplift = get_cyclical_uplift(sector_name)
    if uplift == 1.0:
        return current_op_income, "raw_margin"
    normalized = current_op_income * uplift
    return normalized, f"cyclical_normalized:{uplift}x"
