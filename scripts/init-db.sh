#!/bin/bash
set -e

# This script runs as postgres user during container initialization

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create saramedico user if it doesn't exist
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'saramedico_user') THEN
            CREATE USER saramedico_user WITH PASSWORD 'SaraMed1c0_Dev_2024!Secure';
        END IF;
    END
    \$\$;
    
    -- Create saramedico_dev database
    SELECT 'CREATE DATABASE saramedico_dev OWNER saramedico_user'
    WHERE NOT EXISTS (SELECT FROM pg_catalog.pg_database WHERE datname = 'saramedico_dev')\gexec
EOSQL

# Connect to saramedico_dev and set up extensions
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "saramedico_dev" <<-EOSQL
    -- Grant all privileges to saramedico_user
    GRANT ALL PRIVILEGES ON SCHEMA public TO saramedico_user;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO saramedico_user;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO saramedico_user;
    
    -- Enable extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";
    CREATE EXTENSION IF NOT EXISTS "vector";
EOSQL

echo "✅ Database saramedico_dev created with user saramedico_user"
