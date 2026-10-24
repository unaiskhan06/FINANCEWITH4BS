-- ══════════════════════════════════════════════════════════
-- Finance With 4B's — Database Schema (MySQL)
-- Database layer for manually-entered metal rates.
-- Loaded automatically by backend/app.py -> init_db().
-- ══════════════════════════════════════════════════════════

CREATE DATABASE IF NOT EXISTS `finance_rates`;

USE `finance_rates`;

CREATE TABLE IF NOT EXISTS metal_rates (
    id INT PRIMARY KEY,
    gold_24k DECIMAL(12,2) NULL,
    gold_22k DECIMAL(12,2) NULL,
    gold_18k DECIMAL(12,2) NULL,
    silver_per_gram DECIMAL(12,2) NULL,
    platinum_per_gram DECIMAL(12,2) NULL,
    gold_24k_change DECIMAL(12,2) NULL,
    gold_22k_change DECIMAL(12,2) NULL,
    gold_18k_change DECIMAL(12,2) NULL,
    silver_change DECIMAL(12,2) NULL,
    platinum_change DECIMAL(12,2) NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
