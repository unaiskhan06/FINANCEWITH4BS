-- ══════════════════════════════════════════════════════════
-- Finance With 4B's — Database Schema (PostgreSQL)
-- Used when DATABASE_URL is set (e.g. Render PostgreSQL).
-- Loaded automatically by backend/app.py -> init_db().
--
-- Note: the managed database itself already exists on the host,
-- so there is no CREATE DATABASE / USE statement here.
-- PostgreSQL has no "ON UPDATE CURRENT_TIMESTAMP", so updated_at
-- is set explicitly by save_rates() on every write.
-- ══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS metal_rates (
    id INTEGER PRIMARY KEY,
    gold_24k NUMERIC(12,2),
    gold_22k NUMERIC(12,2),
    gold_18k NUMERIC(12,2),
    silver_per_gram NUMERIC(12,2),
    platinum_per_gram NUMERIC(12,2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
