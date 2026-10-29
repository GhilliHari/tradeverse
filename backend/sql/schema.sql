-- BigQuery Schema DDL for Tradeverse 12-Year Market Analytics
-- Dataset: tradeverse-fe8ef.tradeverse_analytics

CREATE SCHEMA IF NOT EXISTS `tradeverse-fe8ef.tradeverse_analytics`
OPTIONS(location="asia-east1");

-- Table: 12-Year Combined Market History
CREATE TABLE IF NOT EXISTS `tradeverse-fe8ef.tradeverse_analytics.market_history_12y` (
    timestamp TIMESTAMP,
    symbol STRING,
    open FLOAT64,
    high FLOAT64,
    low FLOAT64,
    close FLOAT64,
    volume INT64,
    rsi FLOAT64,
    atr FLOAT64,
    pcr FLOAT64,
    regime STRING,
    split_type STRING -- 'TRAIN_10Y' or 'TEST_2Y'
);

-- Table: 10-Year Training Subset
CREATE OR REPLACE VIEW `tradeverse-fe8ef.tradeverse_analytics.v_train_10y` AS
SELECT * 
FROM `tradeverse-fe8ef.tradeverse_analytics.market_history_12y`
WHERE split_type = 'TRAIN_10Y';

-- Table: 2-Year Out-of-Sample Testing Subset
CREATE OR REPLACE VIEW `tradeverse-fe8ef.tradeverse_analytics.v_test_2y` AS
SELECT * 
FROM `tradeverse-fe8ef.tradeverse_analytics.market_history_12y`
WHERE split_type = 'TEST_2Y';
