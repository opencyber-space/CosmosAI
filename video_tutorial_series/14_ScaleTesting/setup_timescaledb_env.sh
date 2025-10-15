#!/bin/bash
# TimescaleDB Environment Setup Script
# Source this file: source setup_timescaledb_env.sh

echo "Setting up TimescaleDB environment variables..."

# Set TimescaleDB connection parameters
export TIMESCALEDB_HOST="x.x.x.x"
export TIMESCALEDB_PORT="30954"
export TIMESCALEDB_USERNAME="tsdbuser"
export TIMESCALEDB_DATABASE="transactions"
export TIMESCALEDB_PASSWORD="abcxyz"

export DMA_TIMESCALEDB_HOST="x.x.x.x"
export DMA_TIMESCALEDB_PASSWORD="abcxyz"

echo "Environment variables set:"
echo "  TIMESCALEDB_HOST=$TIMESCALEDB_HOST"
echo "  TIMESCALEDB_PORT=$TIMESCALEDB_PORT"
echo "  TIMESCALEDB_USERNAME=$TIMESCALEDB_USERNAME"
echo "  TIMESCALEDB_DATABASE=$TIMESCALEDB_DATABASE"
echo "  TIMESCALEDB_PASSWORD=***"

echo "  DMA_TIMESCALEDB_HOST=$DMA_TIMESCALEDB_HOST"
echo "  DMA_TIMESCALEDB_PASSWORD=***"

echo ""
echo "You can now run your load testing with TimescaleDB integration!"
echo "Test the connection with: python test_timescaledb.py"
