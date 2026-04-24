# REELDEĞER

BIST Damodaran-tabanlı değerleme ve portföy sistemi (v2.2).

## Durum

**Faz 1.1** — Monorepo iskelet kurulumu (devam ediyor).

## Stack

- **Monorepo:** pnpm workspaces + Turborepo
- **Frontend:** Next.js 14 + TailwindCSS + shadcn/ui _(henüz eklenmedi)_
- **Backend:** FastAPI + Pydantic + Prisma _(henüz eklenmedi)_
- **DB:** PostgreSQL + Redis _(henüz eklenmedi)_

## Yapı

```
reeldeger/
├── apps/              # Next.js web, FastAPI api, Streamlit admin
├── packages/          # valuation-engine, data-pipeline, vb.
├── package.json       # Root workspace
├── pnpm-workspace.yaml
└── turbo.json
```

## Gereksinimler

- Node.js >= 20
- pnpm >= 10
- Python 3.11+ (ileride)
- Docker (ileride)

## Başlangıç

```bash
pnpm install
```

## Faz 1 Gate Kriterleri

Üç doğrulama vakası geçmeli (±%5):

1. Heineken €59.65 (Industrial FCFF)
2. ABN Amro €30.87 (Banking Excess Return)
3. Tube Industries ₹61.57 (EM lambda — ADR-006c düzeltilmiş formül)

Detay için `docs/` dizini (henüz eklenmedi).
