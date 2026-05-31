CREATE DATABASE airflow OWNER retail_user;

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS analytics.retail_sales_features (
    store_id INTEGER NOT NULL,
    department INTEGER NOT NULL,
    sale_date DATE NOT NULL,
    weekly_sales NUMERIC(14, 2) NOT NULL,
    sales_amount NUMERIC(14, 2) NOT NULL,
    store_type VARCHAR(10) NOT NULL,
    store_size INTEGER NOT NULL,
    region VARCHAR(50) NOT NULL,
    temperature NUMERIC(8, 2),
    fuel_price NUMERIC(8, 2),
    markdown_1 NUMERIC(14, 2),
    markdown_2 NUMERIC(14, 2),
    markdown_3 NUMERIC(14, 2),
    markdown_4 NUMERIC(14, 2),
    markdown_5 NUMERIC(14, 2),
    markdown_total NUMERIC(14, 2) NOT NULL,
    cpi NUMERIC(10, 2),
    unemployment NUMERIC(8, 2),
    is_holiday BOOLEAN NOT NULL,
    holiday_name VARCHAR(100) NOT NULL,
    season VARCHAR(20) NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    week_of_year INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    is_month_start BOOLEAN NOT NULL,
    is_month_end BOOLEAN NOT NULL,
    sales_lag_1_week NUMERIC(14, 2),
    sales_lag_4_weeks NUMERIC(14, 2),
    sales_rolling_4_week_avg NUMERIC(14, 2),
    sales_rolling_12_week_avg NUMERIC(14, 2),
    store_department_sales_rank NUMERIC(8, 2),
    PRIMARY KEY (store_id, department, sale_date)
);

CREATE TABLE IF NOT EXISTS analytics.store_weekly_sales (
    store_id INTEGER NOT NULL,
    sale_date DATE NOT NULL,
    weekly_sales NUMERIC(14, 2) NOT NULL,
    department_count INTEGER NOT NULL,
    is_holiday BOOLEAN NOT NULL,
    markdown_total NUMERIC(14, 2) NOT NULL,
    temperature NUMERIC(8, 2),
    fuel_price NUMERIC(8, 2),
    cpi NUMERIC(10, 2),
    unemployment NUMERIC(8, 2),
    store_type VARCHAR(10) NOT NULL,
    store_size INTEGER NOT NULL,
    region VARCHAR(50) NOT NULL,
    holiday_name VARCHAR(100) NOT NULL,
    season VARCHAR(20) NOT NULL,
    sales_amount NUMERIC(14, 2) NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    week_of_year INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    is_month_start BOOLEAN NOT NULL,
    is_month_end BOOLEAN NOT NULL,
    store_sales_lag_1_week NUMERIC(14, 2),
    store_sales_rolling_4_week_avg NUMERIC(14, 2),
    PRIMARY KEY (store_id, sale_date)
);

CREATE INDEX IF NOT EXISTS ix_retail_sales_features_sale_date
    ON analytics.retail_sales_features (sale_date);
CREATE INDEX IF NOT EXISTS ix_retail_sales_features_store_date
    ON analytics.retail_sales_features (store_id, sale_date);
CREATE INDEX IF NOT EXISTS ix_retail_sales_features_department
    ON analytics.retail_sales_features (department);
CREATE INDEX IF NOT EXISTS ix_retail_sales_features_region_date
    ON analytics.retail_sales_features (region, sale_date);
CREATE INDEX IF NOT EXISTS ix_store_weekly_sales_sale_date
    ON analytics.store_weekly_sales (sale_date);
CREATE INDEX IF NOT EXISTS ix_store_weekly_sales_store_date
    ON analytics.store_weekly_sales (store_id, sale_date);
CREATE INDEX IF NOT EXISTS ix_store_weekly_sales_region_date
    ON analytics.store_weekly_sales (region, sale_date);
