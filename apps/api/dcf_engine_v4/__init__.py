"""
KAP-Only DCF Engine v4 (Faz 11 v4.0 — Session 4B).

Mevcut apps/api/dcf_engine/ DOKUNULMAZ (Session 6 atomic cutover).
Bu paket KAP-only data ile çalışan minimal Damodaran DCF.

Modüller:
  lifecycle_classifier  — 6-stage classification
  cost_of_capital       — Rf + β × ERP + λ × CRP, synthetic Kd, WACC
  fcff_engine           — 2-stage FCFF + Gordon Growth terminal

Banking/Holding/Insurance parking (Session 4.5+):
  GARAN/AKBNK   → "method_not_implemented" (Excess Return / DDM)
  KCHOL/SAHOL   → "method_not_implemented" (SOTP 3-level)
  ANSGR/AKGRT   → "method_not_implemented" (Insurance template)
"""
