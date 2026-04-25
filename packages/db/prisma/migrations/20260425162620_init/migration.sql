-- CreateEnum
CREATE TYPE "UserTier" AS ENUM ('FREE', 'PAID', 'ADMIN');

-- CreateEnum
CREATE TYPE "LifecycleStage" AS ENUM ('YOUNG', 'HIGH_GROWTH', 'MATURE_GROWTH', 'MATURE_STABLE', 'DECLINE', 'DISTRESS');

-- CreateEnum
CREATE TYPE "RiskProfile" AS ENUM ('CONSERVATIVE', 'BALANCED', 'AGGRESSIVE');

-- CreateEnum
CREATE TYPE "Sleeve" AS ENUM ('CORE', 'FAST_GROWTH', 'HIGH_REWARD');

-- CreateEnum
CREATE TYPE "PeriodType" AS ENUM ('ANNUAL', 'QUARTERLY');

-- CreateEnum
CREATE TYPE "DataSource" AS ENUM ('KAP_XBRL', 'FASTWEB', 'FINTABLES', 'MANUAL');

-- CreateEnum
CREATE TYPE "ValuationModel" AS ENUM ('INDUSTRIAL_FCFF', 'BANKING_EXCESS_RETURN', 'HOLDING_SOTP', 'DISTRESSED', 'CYCLICAL', 'COMMODITY_REGRESSION', 'YOUNG_FIRM');

-- CreateEnum
CREATE TYPE "AlertSeverity" AS ENUM ('INFO', 'WARNING', 'CRITICAL');

-- CreateEnum
CREATE TYPE "AlertType" AS ENUM ('LIFECYCLE_TRANSITION', 'REBALANCE', 'EARNINGS', 'VALIDATION_FAIL');

-- CreateEnum
CREATE TYPE "ErrorLevel" AS ENUM ('CRITICAL', 'WARNING', 'INFO');

-- CreateEnum
CREATE TYPE "DetectorStatus" AS ENUM ('OK', 'SUSPECT', 'FLAGGED');

-- CreateEnum
CREATE TYPE "ArticleCategory" AS ENUM ('BASICS', 'DAMODARAN_METHOD', 'BIST_APPLICATIONS', 'VALIDATION_CASES');

-- CreateTable
CREATE TABLE "User" (
    "id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "name" TEXT,
    "emailVerified" TIMESTAMPTZ(6),
    "image" TEXT,
    "locale" TEXT NOT NULL DEFAULT 'tr',
    "tier" "UserTier" NOT NULL DEFAULT 'FREE',
    "stripeCustomerId" TEXT,
    "subscriptionId" TEXT,
    "dcfUsageWeekly" INTEGER NOT NULL DEFAULT 0,
    "dcfUsageResetAt" TIMESTAMPTZ(6),
    "createdAt" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Account" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "provider" TEXT NOT NULL,
    "providerAccountId" TEXT NOT NULL,
    "refresh_token" TEXT,
    "access_token" TEXT,
    "expires_at" INTEGER,
    "token_type" TEXT,
    "scope" TEXT,
    "id_token" TEXT,
    "session_state" TEXT,

    CONSTRAINT "Account_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Session" (
    "id" TEXT NOT NULL,
    "sessionToken" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "expires" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "Session_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "VerificationToken" (
    "identifier" TEXT NOT NULL,
    "token" TEXT NOT NULL,
    "expires" TIMESTAMPTZ(6) NOT NULL
);

-- CreateTable
CREATE TABLE "Company" (
    "id" TEXT NOT NULL,
    "ticker" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "sector" TEXT,
    "industry" TEXT,
    "listedAt" TIMESTAMPTZ(6),
    "delistedAt" TIMESTAMPTZ(6),
    "delistingReason" TEXT,
    "lifecycleStage" "LifecycleStage",
    "lastClassifiedAt" TIMESTAMPTZ(6),
    "lastTradedPriceUsd" DECIMAL(14,4),
    "lastTradedPriceTry" DECIMAL(14,4),
    "lastTradedAt" TIMESTAMPTZ(6),
    "createdAt" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "Company_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "CompanyFinancial" (
    "id" TEXT NOT NULL,
    "companyId" TEXT NOT NULL,
    "period" TEXT NOT NULL,
    "periodType" "PeriodType" NOT NULL,
    "reportedAt" TIMESTAMPTZ(6),
    "currency" TEXT NOT NULL DEFAULT 'USD',
    "revenueUsd" DECIMAL(18,2),
    "operatingIncome" DECIMAL(18,2),
    "netIncome" DECIMAL(18,2),
    "capex" DECIMAL(18,2),
    "rdExpense" DECIMAL(18,2),
    "debt" DECIMAL(18,2),
    "cash" DECIMAL(18,2),
    "shares" BIGINT,
    "roic" DECIMAL(10,6),
    "roe" DECIMAL(10,6),
    "ebitMargin" DECIMAL(10,6),
    "source" "DataSource" NOT NULL,
    "sourceVersion" TEXT,
    "createdAt" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "CompanyFinancial_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "WatchlistItem" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "companyId" TEXT NOT NULL,
    "addedAt" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "notes" TEXT,

    CONSTRAINT "WatchlistItem_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Valuation" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "companyId" TEXT NOT NULL,
    "modelType" "ValuationModel" NOT NULL,
    "inputs" JSONB NOT NULL,
    "rfUsd" DECIMAL(10,6) NOT NULL,
    "matureErp" DECIMAL(10,6) NOT NULL,
    "turkeyCrp" DECIMAL(10,6) NOT NULL,
    "lambda" DECIMAL(10,6) NOT NULL,
    "beta" DECIMAL(10,6) NOT NULL,
    "wacc" DECIMAL(10,6) NOT NULL,
    "currency" TEXT NOT NULL DEFAULT 'USD',
    "intrinsicValue" DECIMAL(18,4) NOT NULL,
    "confidenceBand70Lower" DECIMAL(18,4),
    "confidenceBand70Upper" DECIMAL(18,4),
    "confidenceBand95Lower" DECIMAL(18,4),
    "confidenceBand95Upper" DECIMAL(18,4),
    "marketPrice" DECIMAL(18,4),
    "marginOfSafety" DECIMAL(10,6),
    "runawayStatus" "DetectorStatus",
    "meltdownStatus" "DetectorStatus",
    "narrativeConfirmScore" DECIMAL(10,6),
    "complexityScore" INTEGER,
    "gitCommitHash" TEXT,
    "dataVintage" TEXT,
    "previousValuationId" TEXT,
    "createdAt" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Valuation_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Portfolio" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "riskProfile" "RiskProfile" NOT NULL DEFAULT 'BALANCED',
    "totalValueUsd" DECIMAL(18,2),
    "totalValueTry" DECIMAL(18,2),
    "cashPct" DECIMAL(7,4) NOT NULL DEFAULT 0.05,
    "createdAt" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "Portfolio_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Position" (
    "id" TEXT NOT NULL,
    "portfolioId" TEXT NOT NULL,
    "companyId" TEXT NOT NULL,
    "sleeve" "Sleeve" NOT NULL,
    "entryPrice" DECIMAL(14,4) NOT NULL,
    "entryDate" TIMESTAMPTZ(6) NOT NULL,
    "currentSize" DECIMAL(7,4) NOT NULL,
    "exitPrice" DECIMAL(14,4),
    "exitDate" TIMESTAMPTZ(6),
    "exitReason" TEXT,
    "createdAt" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "Position_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Rebalance" (
    "id" TEXT NOT NULL,
    "portfolioId" TEXT NOT NULL,
    "trigger" TEXT NOT NULL,
    "actions" JSONB NOT NULL,
    "executedAt" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Rebalance_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Alert" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "companyId" TEXT,
    "type" "AlertType" NOT NULL,
    "severity" "AlertSeverity" NOT NULL,
    "title" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "acknowledged" BOOLEAN NOT NULL DEFAULT false,
    "acknowledgedAt" TIMESTAMPTZ(6),
    "createdAt" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Alert_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "AuditLog" (
    "id" TEXT NOT NULL,
    "userId" TEXT,
    "action" TEXT NOT NULL,
    "entityType" TEXT,
    "entityId" TEXT,
    "metadata" JSONB,
    "ipAddress" TEXT,
    "userAgent" TEXT,
    "createdAt" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "AuditLog_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ErrorLog" (
    "id" TEXT NOT NULL,
    "level" "ErrorLevel" NOT NULL,
    "source" TEXT NOT NULL,
    "message" TEXT NOT NULL,
    "stackTrace" TEXT,
    "context" JSONB,
    "resolved" BOOLEAN NOT NULL DEFAULT false,
    "resolvedAt" TIMESTAMPTZ(6),
    "createdAt" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ErrorLog_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "DamodaranParameter" (
    "id" TEXT NOT NULL,
    "parameter" TEXT NOT NULL,
    "value" DECIMAL(20,10) NOT NULL,
    "source" TEXT NOT NULL,
    "vintage" TEXT NOT NULL,
    "checksum" TEXT NOT NULL,
    "effectiveFrom" TIMESTAMPTZ(6) NOT NULL,
    "effectiveTo" TIMESTAMPTZ(6),
    "createdAt" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "DamodaranParameter_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ValidationCase" (
    "id" SERIAL NOT NULL,
    "number" INTEGER NOT NULL,
    "name" TEXT NOT NULL,
    "model" "ValuationModel" NOT NULL,
    "expectedValue" DECIMAL(18,4) NOT NULL,
    "expectedCurrency" TEXT NOT NULL DEFAULT 'USD',
    "tolerance" DECIMAL(7,4) NOT NULL,
    "requiredSpreadsheets" TEXT[],
    "criticalForPhase1" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ValidationCase_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ValidationRun" (
    "id" TEXT NOT NULL,
    "caseId" INTEGER NOT NULL,
    "userId" TEXT,
    "actualValue" DECIMAL(18,4) NOT NULL,
    "passed" BOOLEAN NOT NULL,
    "errorPercent" DECIMAL(10,6),
    "gitCommitHash" TEXT NOT NULL,
    "runAt" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ValidationRun_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Article" (
    "id" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "localeKey" TEXT NOT NULL,
    "titles" JSONB NOT NULL,
    "bodies" JSONB NOT NULL,
    "category" "ArticleCategory" NOT NULL,
    "readTime" INTEGER,
    "order" INTEGER NOT NULL DEFAULT 0,
    "publishedAt" TIMESTAMPTZ(6),
    "createdAt" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "Article_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "User_email_key" ON "User"("email");

-- CreateIndex
CREATE UNIQUE INDEX "User_stripeCustomerId_key" ON "User"("stripeCustomerId");

-- CreateIndex
CREATE UNIQUE INDEX "User_subscriptionId_key" ON "User"("subscriptionId");

-- CreateIndex
CREATE INDEX "User_tier_idx" ON "User"("tier");

-- CreateIndex
CREATE INDEX "Account_userId_idx" ON "Account"("userId");

-- CreateIndex
CREATE UNIQUE INDEX "Account_provider_providerAccountId_key" ON "Account"("provider", "providerAccountId");

-- CreateIndex
CREATE UNIQUE INDEX "Session_sessionToken_key" ON "Session"("sessionToken");

-- CreateIndex
CREATE INDEX "Session_userId_idx" ON "Session"("userId");

-- CreateIndex
CREATE UNIQUE INDEX "VerificationToken_token_key" ON "VerificationToken"("token");

-- CreateIndex
CREATE UNIQUE INDEX "VerificationToken_identifier_token_key" ON "VerificationToken"("identifier", "token");

-- CreateIndex
CREATE UNIQUE INDEX "Company_ticker_key" ON "Company"("ticker");

-- CreateIndex
CREATE INDEX "Company_sector_idx" ON "Company"("sector");

-- CreateIndex
CREATE INDEX "Company_lifecycleStage_idx" ON "Company"("lifecycleStage");

-- CreateIndex
CREATE INDEX "Company_delistedAt_idx" ON "Company"("delistedAt");

-- CreateIndex
CREATE INDEX "CompanyFinancial_companyId_period_idx" ON "CompanyFinancial"("companyId", "period");

-- CreateIndex
CREATE INDEX "CompanyFinancial_companyId_periodType_idx" ON "CompanyFinancial"("companyId", "periodType");

-- CreateIndex
CREATE UNIQUE INDEX "CompanyFinancial_companyId_period_source_key" ON "CompanyFinancial"("companyId", "period", "source");

-- CreateIndex
CREATE INDEX "WatchlistItem_userId_idx" ON "WatchlistItem"("userId");

-- CreateIndex
CREATE UNIQUE INDEX "WatchlistItem_userId_companyId_key" ON "WatchlistItem"("userId", "companyId");

-- CreateIndex
CREATE INDEX "Valuation_userId_createdAt_idx" ON "Valuation"("userId", "createdAt");

-- CreateIndex
CREATE INDEX "Valuation_companyId_createdAt_idx" ON "Valuation"("companyId", "createdAt");

-- CreateIndex
CREATE INDEX "Valuation_modelType_idx" ON "Valuation"("modelType");

-- CreateIndex
CREATE INDEX "Valuation_gitCommitHash_idx" ON "Valuation"("gitCommitHash");

-- CreateIndex
CREATE INDEX "Portfolio_userId_idx" ON "Portfolio"("userId");

-- CreateIndex
CREATE INDEX "Position_portfolioId_idx" ON "Position"("portfolioId");

-- CreateIndex
CREATE INDEX "Position_companyId_idx" ON "Position"("companyId");

-- CreateIndex
CREATE INDEX "Position_sleeve_idx" ON "Position"("sleeve");

-- CreateIndex
CREATE INDEX "Position_exitDate_idx" ON "Position"("exitDate");

-- CreateIndex
CREATE INDEX "Rebalance_portfolioId_executedAt_idx" ON "Rebalance"("portfolioId", "executedAt");

-- CreateIndex
CREATE INDEX "Alert_userId_acknowledged_idx" ON "Alert"("userId", "acknowledged");

-- CreateIndex
CREATE INDEX "Alert_userId_createdAt_idx" ON "Alert"("userId", "createdAt");

-- CreateIndex
CREATE INDEX "AuditLog_userId_createdAt_idx" ON "AuditLog"("userId", "createdAt");

-- CreateIndex
CREATE INDEX "AuditLog_createdAt_idx" ON "AuditLog"("createdAt");

-- CreateIndex
CREATE INDEX "AuditLog_entityType_entityId_idx" ON "AuditLog"("entityType", "entityId");

-- CreateIndex
CREATE INDEX "ErrorLog_level_resolved_idx" ON "ErrorLog"("level", "resolved");

-- CreateIndex
CREATE INDEX "ErrorLog_createdAt_idx" ON "ErrorLog"("createdAt");

-- CreateIndex
CREATE INDEX "ErrorLog_source_idx" ON "ErrorLog"("source");

-- CreateIndex
CREATE INDEX "DamodaranParameter_parameter_effectiveFrom_idx" ON "DamodaranParameter"("parameter", "effectiveFrom");

-- CreateIndex
CREATE INDEX "DamodaranParameter_source_vintage_idx" ON "DamodaranParameter"("source", "vintage");

-- CreateIndex
CREATE UNIQUE INDEX "DamodaranParameter_parameter_vintage_key" ON "DamodaranParameter"("parameter", "vintage");

-- CreateIndex
CREATE UNIQUE INDEX "ValidationCase_number_key" ON "ValidationCase"("number");

-- CreateIndex
CREATE INDEX "ValidationCase_criticalForPhase1_idx" ON "ValidationCase"("criticalForPhase1");

-- CreateIndex
CREATE INDEX "ValidationRun_caseId_runAt_idx" ON "ValidationRun"("caseId", "runAt");

-- CreateIndex
CREATE INDEX "ValidationRun_gitCommitHash_idx" ON "ValidationRun"("gitCommitHash");

-- CreateIndex
CREATE INDEX "ValidationRun_passed_idx" ON "ValidationRun"("passed");

-- CreateIndex
CREATE UNIQUE INDEX "Article_slug_key" ON "Article"("slug");

-- CreateIndex
CREATE INDEX "Article_category_order_idx" ON "Article"("category", "order");

-- CreateIndex
CREATE INDEX "Article_publishedAt_idx" ON "Article"("publishedAt");

-- AddForeignKey
ALTER TABLE "Account" ADD CONSTRAINT "Account_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Session" ADD CONSTRAINT "Session_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CompanyFinancial" ADD CONSTRAINT "CompanyFinancial_companyId_fkey" FOREIGN KEY ("companyId") REFERENCES "Company"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "WatchlistItem" ADD CONSTRAINT "WatchlistItem_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "WatchlistItem" ADD CONSTRAINT "WatchlistItem_companyId_fkey" FOREIGN KEY ("companyId") REFERENCES "Company"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Valuation" ADD CONSTRAINT "Valuation_previousValuationId_fkey" FOREIGN KEY ("previousValuationId") REFERENCES "Valuation"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Valuation" ADD CONSTRAINT "Valuation_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Valuation" ADD CONSTRAINT "Valuation_companyId_fkey" FOREIGN KEY ("companyId") REFERENCES "Company"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Portfolio" ADD CONSTRAINT "Portfolio_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Position" ADD CONSTRAINT "Position_portfolioId_fkey" FOREIGN KEY ("portfolioId") REFERENCES "Portfolio"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Position" ADD CONSTRAINT "Position_companyId_fkey" FOREIGN KEY ("companyId") REFERENCES "Company"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Rebalance" ADD CONSTRAINT "Rebalance_portfolioId_fkey" FOREIGN KEY ("portfolioId") REFERENCES "Portfolio"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Alert" ADD CONSTRAINT "Alert_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Alert" ADD CONSTRAINT "Alert_companyId_fkey" FOREIGN KEY ("companyId") REFERENCES "Company"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AuditLog" ADD CONSTRAINT "AuditLog_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ValidationRun" ADD CONSTRAINT "ValidationRun_caseId_fkey" FOREIGN KEY ("caseId") REFERENCES "ValidationCase"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ValidationRun" ADD CONSTRAINT "ValidationRun_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;
