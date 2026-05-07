# Faz 4.10 Hızlı Büyüme Proxy ROLLBACK — Research Findings

**Tarih:** 7 Mayıs 2026 (~04:50)
**Commit:** Faz 4.18 (04ad40e) → Faz 4.10 ROLLBACK (3 atomic chain)
**Hedef:** Lifecycle classifier 6-stage Hızlı Büyüme dolurma → FALSIFIED
**Sonuç:** ROLLBACK — anchor 16/18 BEAT restored, Lesson #19 REFRAMED

---

## TL;DR

★ Premise audit: classifier ZATEN 6-stage Damodaran-aligned (HIGH_GROWTH 0 ticker)
★ Minimal fix proxy rule denendi: MATURE_GROWTH + rev_CAGR>25% + g>65 + comp>60
★ BIST 63 universe sadece 1 qualifier (CWENE)
★ CWENE %12 single-ticker concentration → diversification kaybı
★ Backtest: Konservatif -1.09pp, Dengeli -5.53pp, Agresif **-9.84pp ÇÖKÜŞ**
★ 16/18 BEAT → ~6/18 (10/18 KAYIP)
★ ROLLBACK — anchor restored EXACT Faz 4.18 baseline
★ Lesson #19 REFRAMED: universe constraint sleeve target

---

## Hipotez (FALSIFIED)

> "sleeve_assignment.py revenue-CAGR proxy rule MATURE_GROWTH high-grown
>  ticker'ları Hızlı Büyüme'ye route edecek, sleeve %15-35 dolacak.
>  Lifecycle classifier dokunmuyor → anchor-safe.
>  Tahmini: 5-10 ticker Hızlı Büyüme dolar, profile differentiation güçlenir."

**ACTUAL EVIDENCE:**

### Universe Probe
BIST 63 ticker MATURE_GROWTH high-CAGR candidates (rev_cagr > 25%):
| Ticker | rev_cagr | composite | upside | Eligibility |
|--------|---------:|----------:|-------:|-------------|
| KONTR  | 69.0%    | 52.5      | -128.9%| FAIL (composite < 60, SKIP via Rule 1b) |
| CWENE  | 58.3%    | 76.7      | +44.2% | **PROXY OK** ✓ |
| INFO   | 29.5%    | 82.2      |+2561.8%| FAIL (deep_value Rule 3 precedence) |
| OYAKC  | 29.2%    | 77.5      | +281.5%| FAIL (deep_value Rule 3 precedence) |

**Net qualified: 1 ticker (CWENE).**

### Concentration Risk
| Profile | Hızlı target | CWENE weight | Cash overflow |
|---------|------------:|-------------:|---------------|
| Konservatif | 15% | **12.0%** | 0.0% |
| Dengeli     | 25% | **12.0%** | 0.0% |
| Agresif     | 35% | **12.0%** | **4.0%** |

CWENE %12 single position — anti-diversification (Damodaran prensip ihlali).

### Backtest Regression
| Profile | Faz 4.18 anchor | Faz 4.10 proxy | Δ | vs XU100 |
|---------|----------------:|---------------:|---:|---------:|
| Konservatif zero | +19.11% | +18.02% | -1.09pp | +4.48 ✓ |
| Konservatif real | +18.53% | +17.44% | -1.09pp | +3.90 ✓ |
| Dengeli zero | +16.34% | +10.81% | **-5.53pp** | -2.73 ✗ |
| Dengeli real | +15.77% | +10.27% | **-5.50pp** | -3.27 ✗ |
| Agresif zero | +14.36% |  +4.52% | **-9.84pp** | -9.02 ✗ |
| Agresif real | +13.80% |  +4.00% | **-9.80pp** | -9.54 ✗ |

**BEAT 16/18 → ~6/18** (Konservatif sadece korunur, D/A çöktü).

---

## Rollback (Anchor Restored)

### Implementation
- `apps/api/portfolio/sleeve_assignment.py` Rule 6.5 early_growth_proxy REMOVED
- Lifecycle classifier dokunulmadı (anchor-safe değişimdi zaten)
- Rollback note eklendi (gelecek iterasyon için context)

### Verification (race-free pipeline)
```
Konservatif zero: +1068.95% | +67.80%/yr | USD +19.11%/yr (Sharpe 0.28)
Dengeli zero:     +945.16%  | +63.89%/yr | USD +16.34%/yr
Agresif zero:     +863.45%  | +61.11%/yr | USD +14.36%/yr
```
EXACT MATCH Faz 4.18 baseline ★ → BIT-IDENTICAL anchor restored.

Sleeve breakdown:
- core 11 / hizli 0 / yuksek 17 / skip 32 (3 profile aynı)
- TUPRS 187.10 INTACT (46+ commit anchor)

---

## Lesson #19 REFRAMED

**ESKİ tez (Faz 4.10 plan):**
"Sleeve allocation classifier rule revize ile dolar."

**YENİ tez (Faz 4.10 ROLLBACK evidence):**
"Sleeve allocation REFLECTS universe opportunity set, NOT classifier rule.
BIST 63 universe HIGH_GROWTH 0 + MATURE_GROWTH high-CAGR proxy 1 qualifier
(CWENE only, deep_value precedence sonrası) → Hızlı sleeve target %15-35
UNREALISTIC. Single-ticker proxy concentration trap."

**Generalization:**
Universe constraint methodology limit. Eğer universe'de yeterli ticker yoksa
sleeve target açığı tek ticker'a yüklenir = anti-diversification (Damodaran
prensibi ihlali). 

**Future paths (parking):**
- (a) Universe expansion (BIST 100 → BIST Tüm 500+) → 5-10 HIGH_GROWTH candidate
- (b) Sleeve target realistic (Hızlı %5-10 max BIST 63 için)
- (c) HIGH_GROWTH classifier rule loosening + young_firm_dcf orchestrator
- (d) Per-position cap Hızlı sleeve (%2-5) + cash overflow tolerance

**Anchor-safe pragmatic:** Hızlı sleeve %0 documented, profile spectrum
Core/Yüksek dengesi ile sağlanır.

---

## 5. Ardışık Rollback Pattern (METHODOLOGY ASSET)

| Faz   | Hipotez                                  | Result               |
|-------|------------------------------------------|----------------------|
| 4.7   | AEFES/AKSA cap extreme > %50             | FAIL → ROLLBACK doğru |
| 4.8   | Tactical regime → DD %30-50 ↓            | FAIL → ROLLBACK doğru |
| 4.13  | Filter strict → Yüksek drag azalır       | FAIL → ROLLBACK doğru |
| 7.1   | Distress integration neutral (race-fix)  | FAIL → ROLLBACK doğru |
| 4.10  | Hızlı proxy rule sleeve dolur            | **FAIL → ROLLBACK doğru** ★ |

**Damodaran rigor through revision ULTIMATE:**
"Hypothesis falsification > methodology force fit (Lesson #10)
+ Universe constraint awareness (Lesson #19 REFRAMED)
+ Race-free tool integrity (Lesson #18 AUTOMATION)
= Methodology evaluation 5-katman discipline."

---

## 19 Damodaran Lesson Timeline

| #  | Faz             | Title                                          | Status              |
|----|-----------------|------------------------------------------------|---------------------|
| 1-15 (önceki, validated)                                                         |
| 16 | 4.17            | Profile Differentiation                        | Production          |
| 17 | 7→7.1→7.2→7.3   | Distress as Call Option (BS + Modified BS)     | MODULE-ONLY ★       |
| 18 | 7.1→7.2→7.3→4.18| Race Condition Methodology Tool Integrity      | AUTOMATION COMPLETE ★|
| 19 | 4.10 ROLLBACK   | Universe Constraint Sleeve Target              | NEGATIVE FINDING ★  |

---

## Sonraki

- **Faz 5.2:** Frontend extension (regime cal, watchlist, distress dashboard)
- **Faz 8.x:** Distress longer horizon backtest (40Q+, separate sleeve)
- **Faz 4.20+:** Universe expansion (BIST Tüm 500+) — Hızlı Büyüme dolma path
- **Faz 7.4+:** HIGH_GROWTH classifier rule loosening + young_firm_dcf orchestrator
