-- Tavonga PostgreSQL Database Initialization Script
-- This script runs when the PostgreSQL container starts for the first time

-- Create database if it doesn't exist (this is handled by docker-compose env vars)
-- But we can set some initial configurations

-- Set timezone
SET timezone = 'UTC';

-- Enable some useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for better performance (will be created after Django migrations)
-- These are commented out since Django will create them via migrations
-- Uncomment after running initial migrations if you want custom indexes

-- Performance settings for the session
SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

-- Log successful initialization
SELECT 'Tavonga PostgreSQL database initialized successfully!' as status; 