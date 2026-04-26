# KAP API Discovery — Inspect Findings (26 Nisan 2026)

## Durum
Faz 2.1 başlangıç. KAP'tan BIST finansallarını çekme yöntemi araştırıldı.

## Özet
**KAP modern Next.js 13+ App Router (RSC) uygulaması.**
Public REST API yok, inline JSON pattern eski (Nuxt/Pages Router) ile uyumsuz.

## Probe Sonuçları

| Endpoint | Status | Size | Notlar |
|---|---|---|---|
| HOME | 200 | 165 KB | Erişilebilir |
| COMPANY_LIST_PAGE | 200 | 924 KB | SPA bundle |
| COMPANY_LIST_API | 404 | - | API yok |
| TUPRS_PAGE | 200 | 70 KB | Erişilebilir, Next.js |
| TUPRS_DISCLOSURES | 404 | - | URL yanlış |
| DISCLOSURE_API | TIMEOUT | - | API yok |
| DISCLOSURE_LIST | 404 | - | URL yanlış |
| FINANCIAL_REPORTS | 404 | - | URL yanlış |

## Tespit Edilen Teknoloji
KAP = **Next.js 13+ App Router** (kanıtlar):
- /_next/static/chunks/ standart Next.js static path
- main-app-*.js App Router-specific
- data-precedence="next" Next.js stylesheet attribute
- CSS production build hash'leri

## Aradığımız Pattern'ler (Hiçbiri Çalışmadı)
- ✗ window.__NUXT__ (Nuxt-specific)
- ✗ window.__INITIAL_STATE__ (Vue/Redux pattern)
- ✗ <script id="__NEXT_DATA__"> (Pages Router'da var, App Router'da YOK)

## Next.js App Router'da Data Inline
- RSC payload: `<script>self.__next_f.push([...])</script>` (stream'ed JSON)
- Server-rendered DOM (HTML body'sinde text)
- Reverse engineer kompleks ve kırılgan

## Stratejik Karar (Pragmatic)
**KAP scraping ZORLA — alternatif data source kullan.**

Seçilen alternatif: **isyatirim.com.tr**
- Türkiye broker, mali tabloları JSON-ish veriyor
- Aynı XBRL data (KAP'la ortak kaynak — SPK zorunlu raporlar)
- HTTP-based, scraping kararlı
- Damodaran fetcher pattern re-use edilebilir

## KAP İleride Kullanılır
- Disclosure listing (yıllık rapor URL'leri)
- KAP-spesifik bildirimler (insider trading, vb.)
- Faz 7 (Giriş/Çıkış sinyalleri) için kritik

## Yarın (27 Nisan) Plan
**Faz 2.1.1b — isyatirim API Discovery**
1. isyatirim.com.tr'i probe et (TUPRS finansal sayfası)
2. AJAX/XHR endpoint'leri bul (DevTools veya manual probe)
3. JSON response yapısı analiz
4. Pilot scraper yaz (TUPRS bilanço + gelir tablosu + nakit akışı)
