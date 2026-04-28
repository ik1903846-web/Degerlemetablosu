# Faz 4.8 Tactical Regime Overlay — Research Findings (28 Nis 2026)

**Tarih:** 28 Nisan 2026 öğle (~12:50)
**Commit:** Faz 4.7 (6b7d7f7) → Faz 4.8 (3 atomic chain)
**Hedef:** Damodaran ADR-042 spec — 4-regime cash escalation + Max DD protection

---

## TL;DR

★ Hipotez ATLENIR ⚠ — Tactical overlay BIST 2021-2026 period için ETKİSİZ
★ USD alpha kayıp -3.3-3.5pp/yr (tüm 6 backtest) — büyük cost
★ Max DD AYNI veya hafif DAHA KÖTÜ (USD +0.29pp Dengeli realistic)
★ Sharpe küçük iyileşme (+0.04 TL basis, vol düşüşü etkisi)
★ Damodaran Lesson #11 — "value over timing" prensibi CONFIRMED
★ Implementation güvenli (regime='normal' default → tactical OFF, eski davranış)

---

## Hipotez vs Gerçek

**Hipotez:** "Panic regime'de cash %25 → Max DD %30-50 azaltır.
Trade-off: panic alpha kayıp + drawdown protection."

**Gerçek (Dengeli realistic USD basis):**

| Metric        | Static    | Tactical  | Δ        |
|---------------|----------:|----------:|---------:|
| USD Ann       | +10.25%   |  +6.87%   | -3.38pp ⚠ |
| TL Ann        | +55.32%   | +50.55%   | -4.77pp  |
| TL Sharpe     | 1.39      | 1.43      | +0.04    |
| TL Max DD     | -9.93%    | -9.93%    |  0.00    |
| USD Max DD    | -25.60%   | -25.89%   | +0.29pp ⚠ |

**Hipotez DOĞRULANMADI:** Max DD korumadı, alpha büyük kayıp.

---

## REGIME_OVERLAY Implementation (Yine de Yapıldı)

**Mantık:** Implementation infrastructure mature, ancak default OFF.
Faz 4.9+ farklı tactical yaklaşımları (sector rotation, momentum) için test edilebilir.

### Eklenen Constant (`portfolio/portfolio_construction.py`)

```python
REGIME_OVERLAY = {
    "normal": {
        "sleeve_multiplier": 1.00,
        "cash_min_pct": 2.0, "cash_max_pct": 15.0,
    },
    "moderate_stress": {
        "sleeve_multiplier": 0.95,
        "cash_min_pct": 5.0, "cash_max_pct": 15.0,
    },
    "significant_stress": {
        "sleeve_multiplier": 0.85,
        "cash_min_pct": 10.0, "cash_max_pct": 20.0,
    },
    "panic": {
        "sleeve_multiplier": 0.75,
        "cash_min_pct": 15.0, "cash_max_pct": 25.0,
    },
}
```

### `build_portfolio()` Extension

```python
def build_portfolio(assignments, risk_profile, total_capital_tl,
                     regime: str = "normal"):
    overlay = get_regime_overlay(regime)
    target_alloc_pct = {
        k: v * 100.0 * overlay["sleeve_multiplier"]
        for k, v in target_alloc.items()
    }
    # cash min/max → regime overlay'den
```

### `simulation.run_backtest()` Extension

```python
def run_backtest(snapshot, prices, quarter_ends, cost_model,
                  regime_overlay=None, regime_calendar=None):
    if regime_overlay and regime_calendar:
        regime = regime_for_qe.get(q_start, "normal")
        mult = regime_overlay[regime]["sleeve_multiplier"]
        target_w = {t: w × mult for t, w in base_target_w.items()}
```

---

## Backtest Detay (Tüm 6 Run)

### USD-Basis Comparison

| Profile          | Static USD | Tactical USD | Δ alpha   | Static DD | Tact DD   | Δ DD     |
|------------------|-----------:|-------------:|----------:|----------:|----------:|---------:|
| Konservatif zero |  +11.07%   |  +7.60%      | -3.47pp   | -25.11%   | -25.51%   | +0.40pp  |
| Konservatif real |  +10.54%   |  +7.09%      | -3.46pp   | -25.80%   | -26.20%   | +0.40pp  |
| Dengeli zero     |  +10.78%   |  +7.39%      | -3.40pp   | -24.91%   | -25.20%   | +0.29pp  |
| Dengeli real     |  +10.25%   |  +6.87%      | -3.38pp   | -25.60%   | -25.89%   | +0.29pp  |
| Agresif zero     |  +10.40%   |  +7.07%      | -3.33pp   | -24.93%   | -25.12%   | +0.19pp  |
| Agresif real     |   +9.87%   |  +6.56%      | -3.31pp   | -25.63%   | -25.81%   | +0.18pp  |

**Tüm profillerde:** Alpha kayıp -3.3 to -3.5pp/yr, Max DD +0.18 to +0.40pp DAHA KÖTÜ.

### Triple Benchmark USD-Basis (Aynı, comparison için)

- XU100: +13.54%/yr USD, Max DD -24.91%
- XU030: +14.74%/yr USD, Max DD -22.72%
- SPY:    +8.55%/yr USD, Max DD -24.80%

Tactical Dengeli realistic USD +6.87%/yr → SPY beat KAYBOLDU (-1.68pp).

---

## Neden Tactical ETKİSİZ?

### 20 Quarter Regime Mix
- 13 normal × 1.00 multiplier
-  4 moderate × 0.95
-  1 significant × 0.85
-  2 panic × 0.75

**Average multiplier:** (13 + 3.8 + 0.85 + 1.5) / 20 = **0.9575**
**Beklenen return reduction:** ~%4.25/yr (TL basis)
**Gerçek reduction:** ~%4.79/yr (TL) / ~%3.40/yr (USD)

### Ana Sebepler

1. **Drawdown Correlation:** BIST 2021-2026 panic regime drawdown'ları
   isolated değil — TL devaluation persistent, USD basis cash da TL-exposed.

2. **USD basis cash shelter YOK:** Panic regime'de cash %25'e geçtiğinde,
   bu cash hâlâ TL — USD/TRY devaluation'a maruz. Real shelter olmuyor.

3. **Sample size küçük:** Sadece 3 quarter (1 significant + 2 panic) ciddi
   escalation gerekiyor — istatistiksel olarak DD reduction sinyal yetersiz.

4. **Lag effect:** regime_for_qe[q_start] kullanılır (look-ahead bias yok).
   Yani panic'i Q-1 sonu görüp Q'da %25 cash'e geçiyoruz. Q içi market
   düşüşü tam exposure.

---

## Damodaran Lesson #11 (REELDEĞER finding)

> "Tactical regime overlay NOT EFFECTIVE for BIST 2021-2026 period:
>
>    (a) Drawdowns CORRELATED across regimes (TL devaluation persistent
>        throughout sample period)
>    (b) USD basis cash also TL-exposed (no real shelter — TL-denominated
>        cash devalues during panic regimes)
>    (c) Alpha cost (-%3-5/yr) OUTWEIGHS minimal DD protection
>    (d) Damodaran 'value over timing' principle CONFIRMED — Lesson #3
>        (cash > overpay) ≠ tactical reduce-to-cash; static cash policy
>        (Faz 4.2 strict %15 cap) preferable to dynamic regime escalation.
>
>  Implementation güvenli (default regime='normal' → tactical OFF,
>  Faz 4.7 davranışı). Tactical mode bu market regime için USE EDİLMEMELİ.
>
>  Faz 4.9+ farklı tactical yaklaşımı candidates:
>    - Sector rotation (regime-dependent sector weights)
>    - Momentum overlay (price momentum × regime filter)
>    - Volatility-adjusted exposure (instead of regime-based)
>  Bu candidates test edilmeden değer sermek YANLIŞ Damodaran disipline."

---

## Hipotez Falsification — Methodology Asset

Faz 4.7 (Lesson #10) + Faz 4.8 (Lesson #11) **iki ardışık hipotez fail**.
Bu rastlantı değil — Damodaran spec'in ADR'leri (042, 055) GENERİC, BIST'e
spesifik validation olmadan ad-hoc önermek çalışmıyor.

**Pattern:** Spec → Hipotez → Implement → Backtest → Falsify → Document.
Bu döngü *negative result* da bilimsel kazanç. Gelecek implementation
kararlarında reference olarak duruyor.

---

## 11 Damodaran Lesson Timeline (Cumulative)

| #  | Lesson                                            | Faz       |
|----|---------------------------------------------------|-----------|
| 1  | Holdings cannot be valued like industrial firms   | Faz 2.5   |
| 2  | Cyclical DCF asymmetric cap                       | Faz 2.6   |
| 3  | Cash > overpay when universe inadequate           | Faz 3     |
| 4  | Adaptive cap by lifecycle                         | Faz 2.7   |
| 5  | Banking DDM > P/B fallback                        | Faz 6     |
| 6  | Banking-specific Pentagon weights                 | Faz 6.5 e |
| 7  | MVP backtest documented bias                      | Faz 4     |
| 8  | Cash band strict %15 + redistribute               | Faz 4.2   |
| 9  | Universe size diminishing returns + DD via div    | Faz 4.5   |
| 10 | Hypothesis falsification > methodology force-fit  | Faz 4.7   |
| 11 | Tactical regime overlay NOT EFFECTIVE BIST period | Faz 4.8 ★ |

---

## Bilinen Sınırlar (Faz 4.9+ Parking)

1. Tactical default OFF — kullanıcı bilinçli aktive etmeli.
2. Sector rotation alternative test edilmedi (Faz 4.9 candidate).
3. Momentum overlay test edilmedi (Faz 4.9 candidate).
4. Drawdown correlation analizi (formal correlation matrix) yapılmadı.
5. Different bear market regime (2008-2009 BIST) test edilmedi —
   2021-2026 sample TL devaluation dominant, equity-specific drawdown az.

---

## Output Files

- `apps/api/outputs/backtest_results_TACTICAL_20260428_124845.csv`
- `apps/api/outputs/backtest_results_TACTICAL_20260428_124845.json`

---

## Sonraki

- **Faz 4.9 (önerilen):** Sector rotation veya momentum overlay alternative test
- **Faz 4.6:** BIST 100 expansion (Hızlı Büyüme dolar)
- **Faz 4.10:** Option A historical Pentagon recompute (look-ahead bias removal)
- **Faz 7+:** Distress model Black-Scholes
