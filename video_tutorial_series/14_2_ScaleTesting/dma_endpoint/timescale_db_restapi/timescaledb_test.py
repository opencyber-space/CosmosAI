import psycopg2
import sys

# Replace with the actual IP and NodePort from your setup.
HOST = "CLUSTER_2_MASTER_NODE"
PORT = "30008"  # The nodePort you defined in the YAML file
DB_NAME = "timescaledb"
USER = "TIMESCALEDB_USER"
PASSWORD = "TIMESCALEDB_PASSOWRD"

try:
    # Connect to the TimescaleDB instance
    conn = psycopg2.connect(
        host=HOST,
        port=PORT,
        database=DB_NAME,
        user=USER,
        password=PASSWORD
    )
    
    # Create a cursor object
    cur = conn.cursor()

    print("✅ Successfully connected to TimescaleDB.")

    # --- Test push operation: Create a table and insert data ---
    
    # Create a simple table if it doesn't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            time TIMESTAMPTZ NOT NULL,
            device_id TEXT,
            temperature DOUBLE PRECISION
        );
    """)
    conn.commit()
    print("🚀 Table 'metrics' checked/created successfully.")

    # Insert a sample row
    cur.execute("""
        INSERT INTO metrics (time, device_id, temperature)
        VALUES (NOW(), 'sensor_01', 25.5);
    """)
    conn.commit()
    print("🚀 Successfully pushed a test row.")

except psycopg2.OperationalError as e:
    print("❌ Failed to connect or operate with TimescaleDB.")
    print(f"Error: {e}")
    sys.exit(1)

finally:
    # Close the cursor and connection
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close()
    print("Connection closed.")
