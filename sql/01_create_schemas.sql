-- Run this FIRST. Creates the 3-layer warehouse schema inside your existing
-- local Postgres database (e.g. a database called hospital_dw).
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;
