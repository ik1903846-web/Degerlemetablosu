// =============================================================================
// REELDEĞER — Prisma 7 Config
// Prisma 6'da datasource.url schema.prisma'daydı; Prisma 7'de buraya taşındı.
// env() helper type-safe DATABASE_URL erişimi sağlar (eksikse hata).
// Path'ler bu dosyanın bulunduğu yere göre RESOLVE edilir.
// =============================================================================

import dotenv from "dotenv";
import { defineConfig, env } from "prisma/config";
import path from "node:path";
import { fileURLToPath } from "node:url";

// ESM __dirname equivalent
const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Repo root'taki .env'i yükle
// packages/db -> abiminprojev2 (2 levels up to repo root)
dotenv.config({ path: path.resolve(__dirname, "../../.env") });

type Env = {
  DATABASE_URL: string;
};

export default defineConfig({
  schema: "prisma/schema.prisma",
  migrations: {
    path: "prisma/migrations",
    seed: "tsx prisma/seed.ts",
  },
  datasource: {
    url: env<Env>("DATABASE_URL"),
  },
});
