import json
import yaml
import asyncio
import asyncpg
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Literal, Optional
from contextlib import asynccontextmanager
from datetime import datetime

# --- 1. Load Configuration ---
def load_config(config_path='config.yaml'):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)['database']

db_config = load_config()

# --- 2. Batching Setup ---
BATCH_SIZE = db_config.get('batch_size', 100)
FLUSH_INTERVAL = db_config.get('flush_interval', 5.0)
log_queue = asyncio.Queue()

async def process_batches(pool):
    insert_query = """
    INSERT INTO log_entries (
        starttimeObj, endtimeObj, block_id, session_id, seq_no, type,
        response_time, raw, test_id, user_id, starttime, endtime
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12);
    """
    batch = []
    
    async def flush():
        if not batch: return
        try:
            await pool.executemany(insert_query, batch)
        except Exception as e:
            print(f"Batch insertion error: {e}")
        finally:
            batch.clear()
            
    try:
        while True:
            if not batch:
                item = await log_queue.get()
                batch.append(item)
                log_queue.task_done()
            
            deadline = asyncio.get_event_loop().time() + FLUSH_INTERVAL
            
            while len(batch) < BATCH_SIZE:
                time_left = deadline - asyncio.get_event_loop().time()
                if time_left <= 0:
                    break
                try:
                    item = await asyncio.wait_for(log_queue.get(), timeout=time_left)
                    batch.append(item)
                    log_queue.task_done()
                except asyncio.TimeoutError:
                    break
            
            await flush()
            
    except asyncio.CancelledError:
        while not log_queue.empty():
            batch.append(log_queue.get_nowait())
            log_queue.task_done()
        await flush()

# --- 3. Database Connection Management (Lifespan) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create the pool once on startup
    # max_size=100 is usually enough for 300req/s if queries are fast
    app.state.pool = await asyncpg.create_pool(
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['name'],
        host=db_config['host'],
        port=db_config['port'],
        min_size=db_config.get('pool_min_size', 5),
        max_size=db_config.get('pool_max_size', 20)
    )
    
    # Run setup logic
    await setup_database(app.state.pool)
    
    # Start batch processing task
    app.state.batch_task = asyncio.create_task(process_batches(app.state.pool))
    
    yield
    # Close the pool on shutdown
    app.state.batch_task.cancel()
    try:
        await app.state.batch_task
    except asyncio.CancelledError:
        pass
        
    await app.state.pool.close()

# --- 3. Database Setup Function ---
async def setup_database(pool):
    async with pool.acquire() as conn:
        # asyncpg uses 'execute' for simple queries
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS log_entries (
                starttimeObj TIMESTAMPTZ NOT NULL,
                endtimeObj TIMESTAMPTZ,
                block_id TEXT,
                session_id TEXT,
                seq_no INTEGER,
                type TEXT,
                response_time DOUBLE PRECISION,
                raw JSONB,
                test_id TEXT,
                user_id TEXT,
                starttime DOUBLE PRECISION,
                endtime DOUBLE PRECISION
            );
        """)
        # TimescaleDB hypertable setup
        try:
            await conn.execute("SELECT create_hypertable('log_entries', 'starttimeobj', if_not_exists => TRUE);")
        except Exception as e:
            print(f"Hypertable info: {e}")
        print("✅ Database ready with asyncpg pool.")

# --- 4. FastAPI Application ---
app = FastAPI(title="High-Performance Logging API", lifespan=lifespan)

class LogEntry(BaseModel):
    block_id: str
    session_id: str
    seq_no: int
    type: Literal["success", "failure"]
    response_time: float
    raw: str  # Note: asyncpg can handle dict/JSON directly, but we'll stick to your schema
    test_id: str
    user_id: str
    starttime: float
    endtime: float
    starttimeObj: str
    endtimeObj: str

# --- 5. API Endpoint ---
@app.post("/create_entry", status_code=status.HTTP_201_CREATED)
async def create_log_entry(entry: LogEntry):
    # 1. Convert ISO strings to Python datetime objects
    try:
        # Handling the 'Z' (UTC) suffix common in ISO strings
        start_obj = datetime.fromisoformat(entry.starttimeObj.replace('Z', '+00:00'))
        end_obj = datetime.fromisoformat(entry.endtimeObj.replace('Z', '+00:00'))
    except Exception as e:
        print(f"Timestamp conversion error: {e}")
        raise HTTPException(status_code=400, detail="Invalid timestamp format")

    item_tuple = (
        start_obj, end_obj, entry.block_id, entry.session_id, entry.seq_no,
        entry.type, entry.response_time, entry.raw, entry.test_id,
        entry.user_id, entry.starttime, entry.endtime
    )
    
    # Push to queue and return immediately
    log_queue.put_nowait(item_tuple)
    
    return {"message": "Log entry queued"}
