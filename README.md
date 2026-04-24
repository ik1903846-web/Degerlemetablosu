# REELDEĞER

BIST Damodaran-tabanlı değerleme ve portföy sistemi (v2.2).

## Durum

**Faz 1.1** — Monorepo iskelet kurulumu (devam ediyor).

## Stack

- **Monorepo:** pnpm workspaces + Turborepo 2.9.6
- **Frontend:** Next.js 15.5.15 + React 18.3 + TailwindCSS 4 + ESLint 9 (App Router, TS strict)
- **Backend:** FastAPI + Pydantic + Prisma _(henüz eklenmedi)_
- **DB:** PostgreSQL + Redis _(henüz eklenmedi)_

### Stack Kararları (Faz 1.1)

- **Next 15 + React 18:** Spec "Next 14" diyor ama 15.5.15 LTS daha güncel ve geriye uyumlu. React 19 + Next 15 SSG kombinasyonunda `<Html> outside pages/_document` regresyonu var (boş scaffold ile bile reproduce edildi), o yüzden React 18'e sabitlendi.
- **TailwindCSS 4:** create-next-app default'u. CSS-first config (eski `tailwind.config.ts` yerine `@theme` direktifi).
- **`cross-env` build wrapper'ı:** `apps/web/package.json`'daki build script'i `cross-env NODE_ENV=production next build`. Sebep: Claude Code Bash tool subshell'lerine `NODE_ENV=development` sızdırıyor (parent süreç envinden); bu durumda Next.js build'i `<Html>` hatası veriyor. cross-env defensive guard. Detay: `docs/ADR/ADR-105.md`.
- **Build motor:** Webpack (Next 15 default). Turbopack build'de SSG regresyonları var, dev'de hala kullanılıyor (`next dev --turbopack`).

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
