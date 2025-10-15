import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import pytz

try:
    from google.cloud import firestore
    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False
    logging.warning("Google Cloud Firestore not available. Install with: pip install google-cloud-firestore")

try:
    from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Float, DateTime, Boolean, Text
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.dialects.postgresql import UUID
    import uuid
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logging.warning("SQLAlchemy not available. Install with: pip install sqlalchemy psycopg2-binary")

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class DatabaseLogger:
    """Handles logging test results to various databases"""
    
    def __init__(self, config: Dict[str, Any], timezone_str: str = 'Asia/Kolkata'):
        self.config = config
        self.enabled = config.get('enabled', False)
        self.db_type = config.get('type', 'firestore')
        self.ist_tz = pytz.timezone(timezone_str)
        self.engine = None
        self.Session = None
        self.metadata = None
        self.tables = {}
        
        if self.enabled:
            self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database connection based on configuration"""
        if self.db_type == 'timescaledb' and SQLALCHEMY_AVAILABLE:
            self._initialize_timescaledb()
        elif self.db_type == 'firestore' and FIRESTORE_AVAILABLE:
            self._initialize_firestore()
    
    def _initialize_timescaledb(self):
        """Initialize TimescaleDB connection"""
        try:
            tsdb_config = self.config.get('timescaledb', {})
            
            # Get connection parameters from environment variables first, then config
            host = os.getenv('TIMESCALEDB_HOST') or tsdb_config.get('host', 'localhost')
            port = os.getenv('TIMESCALEDB_PORT') or tsdb_config.get('port', 5432)
            username = os.getenv('TIMESCALEDB_USERNAME') or tsdb_config.get('username', 'tsdbuser')
            database = os.getenv('TIMESCALEDB_DATABASE') or tsdb_config.get('database', 'transactions')
            password = os.getenv('TIMESCALEDB_PASSWORD') or tsdb_config.get('password', '')
            
            if not password:
                logging.error("TimescaleDB password not found in environment or config")
                self.enabled = False
                return
            
            # Build connection string
            connection_string = (
                f"postgresql://{username}:{password}@{host}:{port}/{database}"
            )
            
            # Create engine with connection pooling
            self.engine = create_engine(
                connection_string,
                pool_size=tsdb_config.get('connection_pool_size', 5),
                max_overflow=tsdb_config.get('max_overflow', 10),
                echo=False  # Set to True for SQL debugging
            )
            
            # Create session factory
            self.Session = sessionmaker(bind=self.engine)
            
            # Initialize metadata and tables
            self.metadata = MetaData()
            self._create_tables(tsdb_config)
            
            logging.info("TimescaleDB connection initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize TimescaleDB: {e}")
            self.enabled = False
    
    def _initialize_firestore(self):
        """Initialize Firestore connection"""
        try:
            firestore_config = self.config.get('firestore', {})
            if firestore_config.get('credentials_path'):
                # Initialize with service account
                self.db = firestore.Client.from_service_account_json(
                    firestore_config['credentials_path'],
                    project=firestore_config.get('project_id')
                )
            else:
                # Use default credentials
                self.db = firestore.Client(project=firestore_config.get('project_id'))
            
            self.collection_name = firestore_config.get('collection_name', 'load_test_logs')
            logging.info("Firestore database initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize Firestore: {e}")
            self.enabled = False
    
    def _create_tables(self, tsdb_config: Dict[str, Any]):
        """Create TimescaleDB tables for load testing data"""
        schema = tsdb_config.get('schema', 'load_testing')
        table_prefix = tsdb_config.get('table_prefix', 'lt_')
        
        # Create schema if it doesn't exist
        with self.engine.connect() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
            conn.commit()
        
        # Statistics table for crowd stats (what goes to stats log files)
        self.tables['stats'] = Table(
            f'{table_prefix}stats',
            self.metadata,
            Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
            Column('timestamp', DateTime(timezone=True), nullable=False, index=True),
            Column('test_id', String(100), nullable=True, index=True),
            Column('stats_type', String(20), nullable=False),  # 'PERIODIC' or 'FINAL'
            Column('total_users', Integer),
            Column('active_users', Integer),
            Column('target_users', Integer),  # Added missing target_users
            Column('total_requests', Integer),
            Column('expected_requests_so_far', Integer),
            Column('actually_sent', Integer),
            Column('successful_requests', Integer),
            Column('failed_requests', Integer),
            Column('requests_per_second', Float),
            Column('requests_per_minute', Float),  # Added missing requests_per_minute
            Column('success_rate', Float),
            Column('interval_requests', Integer),
            Column('expected_requests_in_interval', Integer),
            Column('actually_sent_in_interval', Integer),
            Column('interval_successful', Integer),
            Column('interval_failed', Integer),
            Column('interval_requests_per_second', Float),
            Column('interval_requests_per_minute', Float),  # Added missing interval_requests_per_minute
            Column('interval_success_rate', Float),
            Column('raw_stats', Text),  # JSON dump of full stats
            schema=schema
        )
        
        # Individual request logs table
        self.tables['requests'] = Table(
            f'{table_prefix}requests',
            self.metadata,
            Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
            Column('timestamp', DateTime(timezone=True), nullable=False, index=True),
            Column('test_id', String(100), nullable=True, index=True),
            Column('user_id', String(100), nullable=True, index=True),
            Column('session_id', String(100), nullable=True),
            Column('block_name', String(100), nullable=True),
            Column('request_type', String(10), nullable=True),  # 'HTTP' or 'GRPC'
            Column('success', Boolean, nullable=False),
            Column('response_time', Float),
            Column('error_message', Text),
            Column('request_data', Text),  # JSON dump of request
            Column('response_data', Text),  # JSON dump of response
            schema=schema
        )

        # Streamlit history table
        self.tables['streamlit_history'] = Table(
            f'{table_prefix}streamlit_history',
            self.metadata,
            Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
            Column('timestamp', DateTime(timezone=True), nullable=False, index=True),
            Column('block_name', String(100), nullable=False),
            Column('instance_id', String(100), nullable=True),
            Column('executor_data', Text),
            Column('instance_data', Text),
            schema=schema
        )
        # Create all tables
        self.metadata.create_all(self.engine)
        
        # Apply schema migrations for existing tables
        self._apply_schema_migrations(schema, table_prefix)
        
        # Create hypertables for time-series optimization
        with self.engine.connect() as conn:
            try:
                # Convert to hypertable for better time-series performance
                conn.execute(text(f"SELECT create_hypertable('{schema}.{table_prefix}stats', 'timestamp', if_not_exists => TRUE)"))
                conn.execute(text(f"SELECT create_hypertable('{schema}.{table_prefix}requests', 'timestamp', if_not_exists => TRUE)"))
                conn.execute(text(f"SELECT create_hypertable('{schema}.{table_prefix}streamlit_history', 'timestamp', if_not_exists => TRUE)"))
                conn.commit()
                logging.info("TimescaleDB hypertables created successfully")
            except Exception as e:
                # Hypertables might already exist or TimescaleDB extension not installed
                logging.warning(f"Could not create hypertables (this is OK if they already exist): {e}")
                conn.rollback()
    
    def _apply_schema_migrations(self, schema: str, table_prefix: str):
        """Apply schema migrations to add missing columns to existing tables"""
        try:
            with self.engine.connect() as conn:
                # Check if the new columns exist and add them if they don't
                stats_table = f"{schema}.{table_prefix}stats"
                
                # List of new columns to add
                new_columns = [
                    ("target_users", "INTEGER"),
                    ("requests_per_minute", "FLOAT"),
                    ("expected_requests_so_far", "INTEGER"),
                    ("actually_sent", "INTEGER"),
                    ("expected_requests_in_interval", "INTEGER"),
                    ("actually_sent_in_interval", "INTEGER"),
                    ("interval_requests_per_minute", "FLOAT")
                ]
                
                for column_name, column_type in new_columns:
                    try:
                        # Check if column exists
                        result = conn.execute(text(f"""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_schema = '{schema}' 
                            AND table_name = '{table_prefix}stats' 
                            AND column_name = '{column_name}'
                        """)).fetchone()
                        
                        if not result:
                            # Column doesn't exist, add it
                            conn.execute(text(f"ALTER TABLE {stats_table} ADD COLUMN {column_name} {column_type}"))
                            logging.info(f"Added column {column_name} to {stats_table}")
                        else:
                            logging.debug(f"Column {column_name} already exists in {stats_table}")
                            
                    except Exception as e:
                        logging.warning(f"Could not add column {column_name} to {stats_table}: {e}")
                
                conn.commit()
                logging.info("Schema migrations applied successfully")
                
        except Exception as e:
            logging.error(f"Failed to apply schema migrations: {e}")
            if 'conn' in locals():
                conn.rollback()
    
    def log_request(self, log_data: Dict[str, Any]) -> Optional[str]:
        """Log a request/response to the database"""
        if not self.enabled:
            return None
        
        try:
            # Convert timestamp to IST
            if 'timestamp' in log_data:
                if isinstance(log_data['timestamp'], datetime):
                    log_data['timestamp_ist'] = log_data['timestamp'].astimezone(self.ist_tz)
                else:
                    log_data['timestamp_ist'] = datetime.now(self.ist_tz)
            else:
                log_data['timestamp_ist'] = datetime.now(self.ist_tz)
            
            if self.db_type == 'timescaledb':
                return self._log_request_timescaledb(log_data)
            elif self.db_type == 'firestore':
                doc_ref = self.db.collection(self.collection_name).add(log_data)
                return doc_ref[1].id
            
        except Exception as e:
            logging.error(f"Failed to log to database: {e}")
            return None
    
    def _log_request_timescaledb(self, log_data: Dict[str, Any]) -> Optional[str]:
        """Log request data to TimescaleDB"""
        try:
            session = self.Session()
            
            # Generate UUID for this log entry
            log_id = uuid.uuid4()
            
            # Insert into requests table
            insert_stmt = self.tables['requests'].insert().values(
                id=log_id,
                timestamp=log_data.get('timestamp_ist', datetime.now(self.ist_tz)),
                test_id=log_data.get('test_id'),
                user_id=log_data.get('user_id'),
                session_id=log_data.get('session_id'),
                block_name=log_data.get('block_name'),
                request_type=log_data.get('request_type'),
                success=log_data.get('success', False),
                response_time=log_data.get('response_time'),
                error_message=log_data.get('error_message'),
                request_data=json.dumps(log_data.get('request_data', {}), cls=DateTimeEncoder),
                response_data=json.dumps(log_data.get('response_data', {}), cls=DateTimeEncoder)
            )
            
            session.execute(insert_stmt)
            session.commit()
            session.close()
            
            return str(log_id)
            
        except SQLAlchemyError as e:
            logging.error(f"Failed to log request to TimescaleDB: {e}")
            if 'session' in locals():
                session.rollback()
                session.close()
            return None
    
    def log_statistics(self, stats_data: Dict[str, Any], stats_type: str = 'PERIODIC', test_id: str = None) -> Optional[str]:
        """Log crowd statistics to the database (main method for stats logging)"""
        if not self.enabled:
            return None
        
        try:
            if self.db_type == 'timescaledb':
                return self._log_statistics_timescaledb(stats_data, stats_type, test_id)
            elif self.db_type == 'firestore':
                # Add stats type and test_id to the data
                log_data = {
                    **stats_data,
                    'stats_type': stats_type,
                    'test_id': test_id,
                    'timestamp_ist': datetime.now(self.ist_tz)
                }
                doc_ref = self.db.collection(f"{self.collection_name}_stats").add(log_data)
                return doc_ref[1].id
                
        except Exception as e:
            logging.error(f"Failed to log statistics to database: {e}")
            return None
    
    def _log_statistics_timescaledb(self, stats_data: Dict[str, Any], stats_type: str, test_id: str) -> Optional[str]:
        """Log statistics data to TimescaleDB stats table"""
        try:
            session = self.Session()
            
            # Generate UUID for this stats entry
            stats_id = uuid.uuid4()
            
            # Extract statistics values safely with correct field mapping
            cumulative_stats = stats_data.get('cumulative_stats', {})
            interval_stats = stats_data.get('interval_stats', {})
            
            # Extract user statistics
            user_stats = cumulative_stats.get('users', {})
            total_users = user_stats.get('total', 0)
            active_users = user_stats.get('active', 0)
            target_users = user_stats.get('target', 0)  # Added missing target field
            
            # Extract request statistics
            request_stats = cumulative_stats.get('requests', {})
            total_requests = request_stats.get('total', 0)
            expected_requests_so_far = cumulative_stats.get('expected_requests_so_far', None)
            actually_sent = cumulative_stats.get('actually_sent', None)
            requests_per_second = request_stats.get('per_second', 0.0)
            requests_per_minute = request_stats.get('per_minute', 0.0)  # Added missing per_minute field

            # Fallbacks: if top-level expected/actually not present, try aggregating from block statistics
            if expected_requests_so_far is None:
                try:
                    blk_stats = cumulative_stats.get('block_statistics', {}) or {}
                    s = 0
                    found = False
                    for b, bd in blk_stats.items():
                        v = bd.get('expected_requests_so_far')
                        if v is not None:
                            s += int(v)
                            found = True
                    if found:
                        expected_requests_so_far = s
                except Exception:
                    expected_requests_so_far = None

            if actually_sent is None:
                # Prefer top-level if present; else sum per-block actually_sent or fallback to total_requests
                try:
                    blk_stats = cumulative_stats.get('block_statistics', {}) or {}
                    s = 0
                    found = False
                    for b, bd in blk_stats.items():
                        v = bd.get('actually_sent') or bd.get('total_requests')
                        if v is not None:
                            s += int(v)
                            found = True
                    if found:
                        actually_sent = s
                    else:
                        actually_sent = total_requests
                except Exception:
                    actually_sent = total_requests
            
            # For success/failure breakdown, assume all requests are successful if no breakdown available
            # (We don't have this data in the current stats structure)
            successful_requests = total_requests  # Assume all successful for now
            failed_requests = 0
            success_rate = 100.0 if total_requests > 0 else 0.0
            
            # Extract interval statistics
            interval_request_stats = interval_stats.get('requests', {})
            interval_requests = interval_request_stats.get('total_in_interval', 0)
            expected_requests_in_interval = interval_stats.get('expected_requests_in_interval', None)
            actually_sent_in_interval = interval_stats.get('actually_sent_in_interval', None)
            interval_requests_per_second = interval_request_stats.get('per_second', 0.0)
            interval_requests_per_minute = interval_request_stats.get('per_minute', 0.0)  # Added missing per_minute field

            # Fallbacks for interval values: aggregate from per-block if top-level missing
            if expected_requests_in_interval is None:
                try:
                    blk_stats = interval_stats.get('block_statistics', {}) or {}
                    s = 0
                    found = False
                    for b, bd in blk_stats.items():
                        v = bd.get('expected_requests_in_interval')
                        if v is not None:
                            s += int(v)
                            found = True
                    if found:
                        expected_requests_in_interval = s
                except Exception:
                    expected_requests_in_interval = None

            if actually_sent_in_interval is None:
                try:
                    blk_stats = interval_stats.get('block_statistics', {}) or {}
                    s = 0
                    found = False
                    for b, bd in blk_stats.items():
                        v = bd.get('actually_sent_in_interval') or bd.get('requests_in_interval')
                        if v is not None:
                            s += int(v)
                            found = True
                    if found:
                        actually_sent_in_interval = s
                    else:
                        actually_sent_in_interval = interval_requests
                except Exception:
                    actually_sent_in_interval = interval_requests
            
            # For interval success/failure, assume all successful if no breakdown available
            interval_successful = interval_requests
            interval_failed = 0
            interval_success_rate = 100.0 if interval_requests > 0 else 0.0
            
            # Insert into stats table
            insert_stmt = self.tables['stats'].insert().values(
                id=stats_id,
                timestamp=datetime.now(self.ist_tz),
                test_id=test_id,
                stats_type=stats_type,
                total_users=total_users,
                active_users=active_users,
                target_users=target_users,  # Added missing field
                total_requests=total_requests,
                expected_requests_so_far=expected_requests_so_far,
                actually_sent=actually_sent,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                requests_per_second=requests_per_second,
                requests_per_minute=requests_per_minute,  # Added missing field
                success_rate=success_rate,
                interval_requests=interval_requests,
                expected_requests_in_interval=expected_requests_in_interval,
                actually_sent_in_interval=actually_sent_in_interval,
                interval_successful=interval_successful,
                interval_failed=interval_failed,
                interval_requests_per_second=interval_requests_per_second,
                interval_requests_per_minute=interval_requests_per_minute,  # Added missing field
                interval_success_rate=interval_success_rate,
                raw_stats=json.dumps(stats_data, cls=DateTimeEncoder)  # Store full stats as JSON for complex queries
            )
            
            session.execute(insert_stmt)
            session.commit()
            session.close()
            
            return str(stats_id)
            
        except SQLAlchemyError as e:
            logging.error(f"Failed to log statistics to TimescaleDB: {e}")
            if 'session' in locals():
                session.rollback()
                session.close()
            return None
    
    def log_batch(self, log_entries: list) -> bool:
        """Log multiple entries in a batch"""
        if not self.enabled or not log_entries:
            return False
        
        try:
            if self.db_type == 'timescaledb':
                return self._log_batch_timescaledb(log_entries)
            elif self.db_type == 'firestore':
                batch = self.db.batch()
                for entry in log_entries:
                    if 'timestamp' in entry:
                        if isinstance(entry['timestamp'], datetime):
                            entry['timestamp_ist'] = entry['timestamp'].astimezone(self.ist_tz)
                        else:
                            entry['timestamp_ist'] = datetime.now(self.ist_tz)
                    else:
                        entry['timestamp_ist'] = datetime.now(self.ist_tz)
                    
                    doc_ref = self.db.collection(self.collection_name).document()
                    batch.set(doc_ref, entry)
                
                batch.commit()
                return True
                
        except Exception as e:
            logging.error(f"Failed to log batch to database: {e}")
            return False
        
        return False
    
    def _log_batch_timescaledb(self, log_entries: list) -> bool:
        """Log multiple entries to TimescaleDB in a batch"""
        try:
            session = self.Session()
            
            batch_data = []
            for entry in log_entries:
                # Convert timestamp to IST
                if 'timestamp' in entry:
                    if isinstance(entry['timestamp'], datetime):
                        entry['timestamp_ist'] = entry['timestamp'].astimezone(self.ist_tz)
                    else:
                        entry['timestamp_ist'] = datetime.now(self.ist_tz)
                else:
                    entry['timestamp_ist'] = datetime.now(self.ist_tz)
                
                batch_data.append({
                    'id': uuid.uuid4(),
                    'timestamp': entry['timestamp_ist'],
                    'test_id': entry.get('test_id'),
                    'user_id': entry.get('user_id'),
                    'session_id': entry.get('session_id'),
                    'block_name': entry.get('block_name'),
                    'request_type': entry.get('request_type'),
                    'success': entry.get('success', False),
                    'response_time': entry.get('response_time'),
                    'error_message': entry.get('error_message'),
                    'request_data': json.dumps(entry.get('request_data', {}), cls=DateTimeEncoder),
                    'response_data': json.dumps(entry.get('response_data', {}), cls=DateTimeEncoder)
                })
            
            # Bulk insert
            session.execute(self.tables['requests'].insert(), batch_data)
            session.commit()
            session.close()
            
            return True
            
        except SQLAlchemyError as e:
            logging.error(f"Failed to log batch to TimescaleDB: {e}")
            if 'session' in locals():
                session.rollback()
                session.close()
            return False
    
    def get_test_statistics(self, test_id: str) -> Dict[str, Any]:
        """Get aggregated statistics for a test run"""
        if not self.enabled:
            return {}
        
        try:
            if self.db_type == 'timescaledb':
                return self._get_test_statistics_timescaledb(test_id)
            elif self.db_type == 'firestore':
                docs = self.db.collection(self.collection_name)\
                         .where('test_id', '==', test_id)\
                         .stream()
                
                total_requests = 0
                total_response_time = 0
                success_count = 0
                error_count = 0
                
                for doc in docs:
                    data = doc.to_dict()
                    total_requests += 1
                    if data.get('success', False):
                        success_count += 1
                        total_response_time += data.get('response_time', 0)
                    else:
                        error_count += 1
                
                avg_response_time = total_response_time / success_count if success_count > 0 else 0
                success_rate = (success_count / total_requests * 100) if total_requests > 0 else 0
                
                return {
                    'total_requests': total_requests,
                    'success_count': success_count,
                    'error_count': error_count,
                    'success_rate': success_rate,
                    'avg_response_time': avg_response_time
                }
                
        except Exception as e:
            logging.error(f"Failed to get test statistics: {e}")
            return {}
        
        return {}
    
    def _get_test_statistics_timescaledb(self, test_id: str) -> Dict[str, Any]:
        """Get aggregated statistics from TimescaleDB"""
        try:
            session = self.Session()
            
            # Query for request statistics
            result = session.execute(text("""
                SELECT 
                    COUNT(*) as total_requests,
                    COUNT(*) FILTER (WHERE success = true) as success_count,
                    COUNT(*) FILTER (WHERE success = false) as error_count,
                    AVG(response_time) FILTER (WHERE success = true) as avg_response_time,
                    MIN(response_time) FILTER (WHERE success = true) as min_response_time,
                    MAX(response_time) FILTER (WHERE success = true) as max_response_time
                FROM load_testing.lt_requests 
                WHERE test_id = :test_id
            """), {'test_id': test_id}).fetchone()
            
            session.close()
            
            if result:
                total_requests = result[0] or 0
                success_count = result[1] or 0
                error_count = result[2] or 0
                success_rate = (success_count / total_requests * 100) if total_requests > 0 else 0
                
                return {
                    'total_requests': total_requests,
                    'success_count': success_count,
                    'error_count': error_count,
                    'success_rate': success_rate,
                    'avg_response_time': result[3] or 0.0,
                    'min_response_time': result[4] or 0.0,
                    'max_response_time': result[5] or 0.0
                }
            
            return {}
            
        except SQLAlchemyError as e:
            logging.error(f"Failed to get test statistics from TimescaleDB: {e}")
            if 'session' in locals():
                session.close()
            return {}
    
    def close(self):
        """Close database connections"""
        try:
            if self.db_type == 'timescaledb' and self.engine:
                self.engine.dispose()
                logging.info("TimescaleDB connection closed")
        except Exception as e:
            logging.error(f"Error closing database connection: {e}")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.close()

    def log_streamlit_history(self, log_entry: Dict[str, Any]) -> Optional[str]:
        """Log a streamlit history entry to the database (lt_streamlit_history table)"""
        if not self.enabled:
            return None
        try:
            if self.db_type == 'timescaledb':
                session = self.Session()
                entry_id = uuid.uuid4()
                timestamp = log_entry.get('timestamp', datetime.now(self.ist_tz))
                block_name = log_entry.get('block_name')
                instance_id = log_entry.get('instance_id')
                executor_data = json.dumps(log_entry.get('executor_data', {}), cls=DateTimeEncoder) if 'executor_data' in log_entry else None
                instance_data = json.dumps(log_entry.get('instance_data', {}), cls=DateTimeEncoder) if 'instance_data' in log_entry else None
                insert_stmt = self.tables['streamlit_history'].insert().values(
                    id=entry_id,
                    timestamp=timestamp,
                    block_name=block_name,
                    instance_id=instance_id,
                    executor_data=executor_data,
                    instance_data=instance_data
                )
                session.execute(insert_stmt)
                session.commit()
                session.close()
                return str(entry_id)
            elif self.db_type == 'firestore':
                doc_ref = self.db.collection(f"{self.collection_name}_streamlit_history").add(log_entry)
                return doc_ref[1].id
        except Exception as e:
            logging.error(f"Failed to log streamlit history to database: {e}")
            return None