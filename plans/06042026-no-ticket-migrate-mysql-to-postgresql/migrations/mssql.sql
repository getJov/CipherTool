-- CipherTool database migration scaffold for Microsoft SQL Server.
-- This project is targeting Supabase PostgreSQL; this file exists because the
-- planning convention requires database-change plans to include MSSQL,
-- PostgreSQL, and Knex migration artifacts.

-- Schema description:
-- Table: users
-- Columns:
--   id              integer primary key, generated automatically
--   username        variable-length text, required
--   password        variable-length text, required password hash
--   login_attempts  integer, default 0
--   blocked         boolean-like flag, default false
-- Constraints:
--   primary key on id
-- Relationships:
--   none

-- TODO: fill during execution only if MSSQL support becomes required.
