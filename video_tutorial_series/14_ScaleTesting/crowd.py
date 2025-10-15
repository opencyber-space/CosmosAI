import asyncio
import logging
import uuid
import yaml
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pytz
from user import User
from db_logger import DatabaseLogger
import csv

class ISTFormatter(logging.Formatter):
    """Custom formatter that converts UTC time to configurable timezone"""
    def __init__(self, fmt=None, datefmt=None, style='%', tz=None):
        super().__init__(fmt, datefmt, style)
        self.tz = tz or pytz.timezone('Asia/Kolkata')  # Fallback default
    
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=self.tz)
        if datefmt:
            return dt.strftime(datefmt)
        else:
            return dt.strftime('%Y-%m-%d %H:%M:%S,%f')[:-3] + ' IST'

class Crowd:
    """Manages multiple users for load testing"""
    
    def __init__(self, config_path: str):
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        self.blocks = self.config.get('blocks', {})
        self.user_config = self.config.get('user_config', {})
        self.crowd_config = self.config.get('crowd_config', {})
        self.test_config = self.config.get('test_config', {})
        # Get timezone from config, default to Asia/Kolkata
        timezone_str = self.config.get('logging', {}).get('timezone', 'Asia/Kolkata')
        self.ist_tz = pytz.timezone(timezone_str)
        self.test_id = str(uuid.uuid4())
        # Initialize database logger
        db_config = self.config.get('database', {})
        self.db_logger = DatabaseLogger(db_config, timezone_str) if db_config.get('enabled', False) else None
        # State
        self.users: Dict[str, User] = {}
        self.is_running = False
        self.management_task: Optional[asyncio.Task] = None
        self.stats_task: Optional[asyncio.Task] = None
        # Stats tracking for interval calculations
        self.stats_log_interval = self.test_config.get('stats_log_interval', 60)  # seconds
        self._last_stats_snapshot = None  # For interval calculations
        self._last_stats_time = None
        # Setup logging
        log_config = self.config.get('logging', {})
        # --- Ensure shared logger/session are initialized by creating the first User ---
        from user import User
        _ = User(
            user_id="user_0_init",
            config=self.user_config,
            blocks=self.blocks,
            db_logger=self.db_logger,
            test_id=self.test_id,
            global_config=self.config
        )
        
        # Create IST formatter
        ist_formatter = ISTFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            tz=self.ist_tz
        )
        
        # Clear any existing handlers to avoid duplicates
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        logging.basicConfig(
            level=getattr(logging, log_config.get('level', 'INFO')),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[]  # We'll add handlers manually with IST formatter
        )
        
        # Add file handler with IST formatter and immediate flushing
        file_handler = logging.FileHandler(log_config.get('log_file', 'load_test.log'))
        file_handler.setFormatter(ist_formatter)
        # Force immediate write by setting buffer size to 0 (unbuffered)
        if hasattr(file_handler.stream, 'reconfigure'):
            try:
                file_handler.stream.reconfigure(line_buffering=True)
            except TypeError:
                # Fallback: close and reopen with unbuffered mode
                file_handler.stream.close()
                file_handler.stream = open(file_handler.baseFilename, 'a', buffering=1, encoding='utf-8')
        root_logger.addHandler(file_handler)
        
        # Add console handler with IST formatter if enabled
        if log_config.get('console_output', True):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(ist_formatter)
            # Console is usually line buffered by default
            root_logger.addHandler(console_handler)
        
        # Set root logger level
        root_logger.setLevel(getattr(logging, log_config.get('level', 'INFO')))
        
        self.logger = logging.getLogger('Crowd')

        # Stats logging setup
        #self.stats_log_interval = 60  # 5 minutes in seconds
        self.setup_stats_logging()
        
        
    
    def setup_stats_logging(self):
        """Setup statistics logging infrastructure"""
        # Ensure stats directory exists
        if not os.path.exists("stats"):
            os.makedirs("stats")
        
        # Create stats logger
        self.stats_logger = logging.getLogger('CrowdStats')
        self.stats_logger.setLevel(logging.INFO)
        
        # Clear any existing handlers to avoid duplicates
        self.stats_logger.handlers.clear()
        
        # Create stats file handler with timestamp in filename
        stats_log_file = f"stats/crowd_stats_{datetime.now(self.ist_tz).strftime('%Y%m%d_%H%M%S')}.log"
        
        try:
            stats_handler = logging.FileHandler(stats_log_file, mode='w', encoding='utf-8')
            
            # Use IST formatter for stats as well
            stats_formatter = ISTFormatter('%(asctime)s - %(message)s', tz=self.ist_tz)
            stats_handler.setFormatter(stats_formatter)
            stats_handler.setLevel(logging.INFO)
            
            # Force immediate write for stats files
            if hasattr(stats_handler.stream, 'reconfigure'):
                try:
                    stats_handler.stream.reconfigure(line_buffering=True)
                except TypeError:
                    # Fallback: close and reopen with line buffering
                    stats_handler.stream.close()
                    stats_handler.stream = open(stats_handler.baseFilename, 'w', buffering=1, encoding='utf-8')
            
            self.stats_logger.addHandler(stats_handler)
            
            # Prevent propagation to root logger
            self.stats_logger.propagate = False
            
            # Test write to ensure file is working
            self.stats_logger.info("INITIALIZATION: Stats logging started")
            stats_handler.flush()
            
            self.logger.info(f"Stats logging initialized - File: {stats_log_file}")
            
            # Store file path for reference
            self.stats_log_file = stats_log_file
            
        except Exception as e:
            self.logger.error(f"Failed to setup stats logging: {e}")
            self.stats_logger = None
    
    def _get_current_hour_multiplier(self) -> float:
        """Get current hour's crowd multiplier"""
        current_hour = datetime.now(self.ist_tz).hour
        crowd_patterns = self.crowd_config.get('crowd_patterns', {})
        return crowd_patterns.get(current_hour, 1.0)
    
    def _calculate_target_users(self) -> int:
        """Calculate target number of users for current hour"""
        base_users = self.crowd_config.get('users_per_hour', 100)
        multiplier = self._get_current_hour_multiplier()
        max_users = self.crowd_config.get('max_concurrent_users', 1000)
        
        target = int(base_users * multiplier)
        # Ensure at least 1 user if multiplier > 0 (to maintain some load)
        if multiplier > 0 and target == 0:
            target = 1
        return min(target, max_users)
    
    async def _create_user(self) -> User:
        """Create a new user"""
        user_id = f"user_{len(self.users)}_{uuid.uuid4().hex[:8]}"
        user = User(
            user_id=user_id,
            config=self.user_config,
            blocks=self.blocks,
            db_logger=self.db_logger,
            test_id=self.test_id,
            global_config=self.config
        )
        return user
    
    async def _spawn_users(self, count: int):
        """Spawn new users"""
        spawn_interval = self.crowd_config.get('user_spawn_interval', 1)
        
        for i in range(count):
            if not self.is_running:
                break
            # Skip the first user if it's the special init user
            user = await self._create_user()
            if user.user_id == "user_0_init":
                continue
            self.users[user.user_id] = user
            await user.start()
            self.logger.info(f"Spawned user {user.user_id} ({len(self.users)} total users)")
            if i < count - 1:
                await asyncio.sleep(spawn_interval)
    
    async def _remove_users(self, count: int):
        """Remove excess users"""
        users_to_remove = list(self.users.keys())[:count]
        
        for user_id in users_to_remove:
            if user_id in self.users:
                user = self.users[user_id]
                await user.stop()
                del self.users[user_id]
                self.logger.info(f"Removed user {user_id} ({len(self.users)} total users)")
    
    def flush_all_loggers(self):
        """Manually flush all loggers to ensure immediate write to files"""
        # Flush main logger
        for handler in self.logger.handlers:
            if hasattr(handler, 'flush'):
                handler.flush()
        
        # Flush stats logger
        if self.stats_logger:
            for handler in self.stats_logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
        
        # Flush all user loggers
        for user in self.users.values():
            if hasattr(user, 'logger'):
                for handler in user.logger.handlers:
                    if hasattr(handler, 'flush'):
                        handler.flush()
    
    async def _manage_user_count(self):
        """Continuously manage user count based on patterns"""
        while self.is_running:
            try:
                target_users = self._calculate_target_users()
                current_users = len(self.users)
                
                self.logger.info(f"Target users: {target_users}, Current users: {current_users}")
                
                if target_users > current_users:
                    # Need to spawn more users
                    users_to_spawn = target_users - current_users
                    await self._spawn_users(users_to_spawn)
                    
                elif target_users < current_users:
                    # Need to remove some users
                    users_to_remove = current_users - target_users
                    await self._remove_users(users_to_remove)
                
                # Check user health and restart failed users
                await self._health_check()
                
                # Wait before next check (check every minute)
                await asyncio.sleep(self.crowd_config.get('manage_user_count_sleep', 60))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in user management: {e}")
                await asyncio.sleep(30)
    
    async def _health_check(self):
        """Check health of users and restart failed ones"""
        health_check_interval = self.test_config.get('health_check_interval', 60)
        
        failed_users = []
        for user_id, user in self.users.items():
            # Check if user tasks are still running
            if user.is_active and not any(not task.done() for task in user.tasks):
                failed_users.append(user_id)
        
        # Restart failed users
        for user_id in failed_users:
            self.logger.warning(f"Restarting failed user {user_id}")
            old_user = self.users[user_id]
            await old_user.stop()
            
            # Create new user with same ID
            new_user = User(
                user_id=user_id,
                config=self.user_config,
                blocks=self.blocks,
                db_logger=self.db_logger,
                test_id=self.test_id
            )
            self.users[user_id] = new_user
            await new_user.start()
    
    async def _stats_collector(self):
        """Collect and log statistics every minute"""
        self.logger.info(f"Stats collector started - will log every {self.stats_log_interval} seconds")
        
        while self.is_running:
            try:
                await asyncio.sleep(self.stats_log_interval)
                
                if self.is_running:  # Check again after sleep
                    self.logger.debug("Collecting periodic stats...")
                    stats = self.get_statistics()
                    await self._log_stats(stats)
                    self.logger.debug("Periodic stats logged successfully")
                    
                    # Force flush all loggers after stats collection
                    self.flush_all_loggers()
                    
            except asyncio.CancelledError:
                # Log final stats before stopping
                self.logger.info("Stats collector cancelled - logging final stats")
                try:
                    stats = self.get_statistics(is_final=True)
                    await self._log_stats(stats, final=True)
                    self.logger.info("Final stats logged successfully")
                    
                    # Force flush all loggers for final stats
                    self.flush_all_loggers()
                    
                    # Mark that stats have been printed to prevent duplicate in main finally block
                    self._final_stats_printed = True
                except Exception as e:
                    self.logger.error(f"Error logging final stats: {e}")
                break
            except Exception as e:
                self.logger.error(f"Error in stats collection: {e}")
                await asyncio.sleep(30)  # Wait before retrying
    
    async def _log_stats(self, stats: Dict[str, Any], final: bool = False):
        """Log statistics with unified format containing both cumulative and interval data"""
        try:
            # Add additional metadata
            log_type = 'final_stats' if final else 'periodic_stats'
            log_timestamp = datetime.now(self.ist_tz).isoformat()
            
            # Extract cumulative and interval stats for processing
            cumulative = stats.get('cumulative_stats', {})
            interval = stats.get('interval_stats')
            
            # Create unified stats format with all important information
            unified_stats = {
                "test_id": stats.get('test_id'),
                "timestamp": stats.get('timestamp'),
                "test_start_time": stats.get('test_start_time'),
                "log_type": log_type,
                "log_timestamp": log_timestamp,
                
                # Add missing fields from detailed format
                "is_running": stats.get('is_running'),
                "current_hour": cumulative.get('current_hour'),
                "current_hour_multiplier": cumulative.get('current_hour_multiplier'),
                
                "cumulative_stats": {
                    "users": {
                        "total": cumulative.get('total_users'),
                        "active": cumulative.get('active_users'),
                        "target": cumulative.get('target_users')
                    },
                    "requests": {
                        "total": cumulative.get('total_requests'),
                        "per_second": cumulative.get('requests_per_second'),
                        "per_minute": cumulative.get('requests_per_minute'),
                        "expected_requests_so_far": cumulative.get('expected_requests_so_far'),
                        "actually_sent": cumulative.get('actually_sent')
                    },
                    "test_duration_seconds": cumulative.get('test_duration_seconds'),
                    "block_statistics": cumulative.get('block_statistics', {})
                }
            }
            
            # Add interval stats if available
            if interval:
                # Include expected and actually_sent fields if present
                unified_stats["interval_stats"] = {
                    "duration_seconds": interval.get('duration_seconds'),
                    "requests": {
                        "total_in_interval": interval.get('requests_in_interval'),
                        "per_second": interval.get('requests_per_second'),
                        "per_minute": interval.get('requests_per_minute'),
                        "expected_requests_in_interval": interval.get('expected_requests_in_interval'),
                        "actually_sent_in_interval": interval.get('actually_sent_in_interval')
                    },
                    "interval_period": f"{interval.get('interval_start')} to {interval.get('interval_end')}",
                    "block_statistics": {
                        block_id: {
                            "requests_in_interval": block_data.get('requests_in_interval'),
                            "requests_per_second": block_data.get('requests_per_second'),
                            "requests_per_minute": block_data.get('requests_per_minute'),
                            "expected_requests_in_interval": block_data.get('expected_requests_in_interval'),
                            "actually_sent_in_interval": block_data.get('actually_sent_in_interval')
                        }
                        for block_id, block_data in interval.get('block_statistics', {}).items()
                    }
                }
            
            # Convert to JSON for logging
            unified_json = json.dumps(unified_stats, indent=2, default=str)
            log_prefix = "FINAL_STATS" if final else "PERIODIC_STATS"
            
            # Log to stats file if logger is available
            if self.stats_logger:
                self.stats_logger.info(f"{log_prefix}: {unified_json}")
                
                # Force flush the file handler to ensure immediate write
                for handler in self.stats_logger.handlers:
                    if hasattr(handler, 'flush'):
                        handler.flush()
                
                interval_info = f" (interval: {interval.get('duration_seconds', 0):.1f}s)" if interval else " (first log - no interval data)"
                self.logger.info(f"{'Final' if final else 'Periodic'} stats logged{interval_info}")
                
                # Also flush main logger handlers
                for handler in self.logger.handlers:
                    if hasattr(handler, 'flush'):
                        handler.flush()
            else:
                self.logger.warning("Stats logger not available - cannot log to file")
                # Fallback: log to main log file
                self.logger.info(f"{log_prefix}: {unified_json}")
            
            # Log one-liner for quick scanning
            if interval:
                one_liner = (
                    f"{'Final' if final else 'Periodic'} Stats - "
                    f"Users: {cumulative.get('active_users')}/{cumulative.get('total_users')} (target: {cumulative.get('target_users')}), "
                    f"Total Requests: {cumulative.get('total_requests')}, "
                    f"Interval: {interval.get('requests_in_interval')} req in {interval.get('duration_seconds'):.1f}s "
                    f"({interval.get('requests_per_minute'):.1f} req/min), "
                    f"Cumulative: {cumulative.get('requests_per_minute'):.1f} req/min"
                )
            else:
                one_liner = (
                    f"{'Final' if final else 'Periodic'} Stats - "
                    f"Users: {cumulative.get('active_users')}/{cumulative.get('total_users')} (target: {cumulative.get('target_users')}), "
                    f"Total Requests: {cumulative.get('total_requests')}, "
                    f"Avg Rate: {cumulative.get('requests_per_minute'):.1f} req/min"
                )
            self.logger.info(f"STATS_ONELINER: {one_liner}")
            
            # Log to database if enabled
            if self.db_logger:
                await self._log_stats_to_db(unified_stats)
            
        except Exception as e:
            self.logger.error(f"Error logging stats: {e}")
            import traceback
            self.logger.error(f"Stats logging traceback: {traceback.format_exc()}")
    
    async def _log_stats_to_db(self, stats: Dict[str, Any]):
        """Log statistics to database using the new TimescaleDB integration"""
        try:
            self.logger.debug(f"[DBLOG] Entering _log_stats_to_db. db_logger: {self.db_logger}, database config: {self.config.get('database', {})}")
            if not self.db_logger or not self.config.get('database', {}).get('enableStats', False):
                self.logger.debug("[DBLOG] Skipping DB logging: db_logger missing or enableStats is False.")
                return
            # Determine if this is a final stats or periodic stats
            stats_type = 'FINAL' if stats.get('log_type') == 'final_stats' else 'PERIODIC'
            self.logger.info(f"[DBLOG] Attempting to log {stats_type} stats to DB. Payload: {json.dumps(stats)[:500]} ...")
            # Use the new log_statistics method which handles both TimescaleDB and Firestore
            await asyncio.to_thread(
                self.db_logger.log_statistics, 
                stats, 
                stats_type, 
                self.test_id
            )
            self.logger.info(f"[DBLOG] Successfully logged {stats_type.lower()} statistics to database")
        except Exception as e:
            self.logger.error(f"[DBLOG] Error logging stats to database: {e}")
            import traceback
            self.logger.error(f"[DBLOG] Database stats logging traceback: {traceback.format_exc()}")
            self.logger.error(f"[DBLOG] Stats payload: {json.dumps(stats)}")
    
    async def start_test(self, duration_hours: Optional[float] = None):
        """Start the load test"""
        if self.is_running:
            self.logger.warning("Test is already running")
            return
        
        test_duration = duration_hours or self.test_config.get('duration_hours', 24)
        warm_up_minutes = self.test_config.get('warm_up_minutes', 5)
        cool_down_minutes = self.test_config.get('cool_down_minutes', 5)
        
        self.logger.info(f"Starting load test {self.test_id}")
        self.logger.info(f"Duration: {test_duration} hours")
        self.logger.info(f"Warm-up: {warm_up_minutes} minutes")
        self.logger.info(f"Cool-down: {cool_down_minutes} minutes")
        
        # Track test start time for rate calculations
        self._test_start_time = datetime.now(self.ist_tz)
        
        self.is_running = True
        
        # Start user management and stats collection
        self.management_task = asyncio.create_task(self._manage_user_count())
        self.stats_task = asyncio.create_task(self._stats_collector())
        
        stats_printed = False
        try:
            # Warm-up period
            if warm_up_minutes > 0:
                self.logger.info("Starting warm-up period")
                await asyncio.sleep(warm_up_minutes * 60)
                self.logger.info("Warm-up period completed")
            
            # Main test period
            self.logger.info("Starting main test period")
            await asyncio.sleep(test_duration * 3600)
            self.logger.info("Main test period completed")
            
            # Cool-down period
            if cool_down_minutes > 0:
                self.logger.info("Starting cool-down period")
                await asyncio.sleep(cool_down_minutes * 60)
                self.logger.info("Cool-down period completed")
                
        except asyncio.CancelledError:
            self.logger.info("Test was cancelled")
            stats_printed = False  # Allow final stats to be printed in finally block
        finally:
            # Only log final stats if not already logged by stats collector
            if not stats_printed and not getattr(self, '_final_stats_printed', False):
                # Get final statistics and log them
                final_stats = self.get_statistics(is_final=True)
                self.logger.info("Final test statistics:")
                await self._log_stats(final_stats, final=True)
            await self.stop_test()
    
    async def stop_test(self):
        """Stop the load test"""
        if not self.is_running:
            return
        
        self.logger.info("Stopping load test")
        self.is_running = False
        
        # Cancel management and stats tasks
        tasks_to_cancel = []
        if self.management_task:
            tasks_to_cancel.append(self.management_task)
        if self.stats_task:
            tasks_to_cancel.append(self.stats_task)
        
        for task in tasks_to_cancel:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Stop all users
        stop_tasks = []
        for user in self.users.values():
            stop_tasks.append(user.stop())
        
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)
        
        self.users.clear()
        self.logger.info("Load test stopped")
    
    def get_statistics(self, is_final: bool = False) -> Dict[str, Any]:
        """Get enhanced crowd statistics with both interval and cumulative data"""
        try:
            current_time = datetime.now(self.ist_tz)
            
            # Calculate cumulative stats
            total_users = len(self.users)
            active_users = len([u for u in self.users.values() if u.is_active])
            total_requests = sum(
                sum(session.request_count for session in user.sessions)
                for user in self.users.values()
            )
            failed_requests = sum(
                sum(session.failed_requests for session in user.sessions)
                for user in self.users.values()
            )

            total_time_for_all_requests = sum(
                sum(session.time_total for session in user.sessions)
                for user in self.users.values()
            )
            all_request_count = (total_requests+failed_requests)
            avg_time_for_all_requests = (total_time_for_all_requests / all_request_count) if all_request_count > 0 else 0
            self.logger.info(f"Total requests: {total_requests}, Failed requests: {failed_requests}, Average time: {avg_time_for_all_requests}")

            # --- Compute expected requests so far using configs and usage patterns ---
            def load_usage_patterns() -> Dict[int, float]:
                # Try CSV first (user_config.csv_file), else fallback to config usage_patterns
                csv_file = self.user_config.get('csv_file') or self.user_config.get('csv_file', 'user_behavior_patterns.csv')
                patterns = {}
                if csv_file and os.path.exists(csv_file):
                    try:
                        with open(csv_file, 'r', newline='') as cf:
                            reader = csv.reader(cf)
                            # Expect rows like: hour, multiplier
                            for row in reader:
                                if not row:
                                    continue
                                try:
                                    h = int(row[0])
                                    v = float(row[1])
                                    patterns[h] = v
                                except Exception:
                                    # Skip header or malformed rows
                                    continue
                        # Ensure we have 0-23 keys (fall back to config where missing)
                    except Exception:
                        patterns = {}

                # Merge with fallback config patterns
                cfg_patterns = self.user_config.get('usage_patterns', {}) or {}
                for h in range(24):
                    if h not in patterns:
                        patterns[h] = cfg_patterns.get(h, 1.0)
                return patterns

            usage_patterns = load_usage_patterns()

            # Helper: compute expected requests between two datetimes (inclusive start, exclusive end)
            def compute_expected_between(start_dt: datetime, end_dt: datetime) -> (float, Dict[str, float]):
                """Return (expected_total_requests, expected_per_block_dict) for the period."""
                if end_dt <= start_dt:
                    return 0.0, {b: 0.0 for b in self.blocks}

                base_users = self.crowd_config.get('users_per_hour', 100)
                crowd_patterns = self.crowd_config.get('crowd_patterns', {})
                sessions_per_block = self.user_config.get('sessions_per_block', 1)
                reqs_per_hour_per_session = self.user_config.get('requests_per_hour_per_session', 60)
                num_blocks = max(1, len(self.blocks))

                total_expected = 0.0
                block_expected = {b: 0.0 for b in self.blocks}

                # iterate hour by hour between start and end
                cur = start_dt.replace(minute=0, second=0, microsecond=0)
                while cur < end_dt:
                    hour_start = cur
                    hour_end = (cur + timedelta(hours=1))
                    seg_start = max(start_dt, hour_start)
                    seg_end = min(end_dt, hour_end)
                    seg_seconds = (seg_end - seg_start).total_seconds()
                    h = hour_start.hour

                    users_this_hour = base_users * float(crowd_patterns.get(h, 1.0))
                    usage_mult = float(usage_patterns.get(h, 1.0))

                    # expected requests per second PER BLOCK
                    per_block_per_sec = (users_this_hour * sessions_per_block * reqs_per_hour_per_session * usage_mult) / 3600.0

                    for b in self.blocks:
                        add = per_block_per_sec * seg_seconds
                        block_expected[b] += add

                    # total across all blocks
                    total_expected += per_block_per_sec * seg_seconds * num_blocks

                    cur = hour_end

                return total_expected, block_expected

            # Compute expected from test start to now
            test_start = getattr(self, '_test_start_time', current_time)
            expected_total_cumulative, expected_block_cumulative = compute_expected_between(test_start, current_time)
            
            # Get per-block cumulative statistics
            cumulative_block_stats = {}
            for block_id in self.blocks.keys():
                block_requests = sum(
                    sum(session.request_count for session in user.sessions if session.block_id == block_id)
                    for user in self.users.values()
                )
                block_sessions = sum(
                    len([s for s in user.sessions if s.block_id == block_id])
                    for user in self.users.values()
                )
                #total_time_for_block_requests = sum(s.time_total for s in user.sessions if s.block_id == block_id for user in self.users.values())
                total_time_for_block_requests = sum(
                    s.time_total
                    for user in self.users.values()
                    for s in user.sessions
                    if s.block_id == block_id
                )
                avg_time_for_all_requests = (total_time_for_block_requests / block_requests) if block_requests > 0 else 0
                cumulative_block_stats[block_id] = {
                    "total_requests": block_requests,
                    "total_sessions": block_sessions,
                    "avg_requests_per_session": round(block_requests / block_sessions, 2) if block_sessions > 0 else 0,
                    "avg_time_per_request": round(avg_time_for_all_requests, 4)
                }
            
            # Calculate cumulative request rates
            if hasattr(self, '_test_start_time'):
                test_duration = (current_time - self._test_start_time).total_seconds()
                cumulative_requests_per_second = round(total_requests / test_duration, 2) if test_duration > 0 else 0
                cumulative_requests_per_minute = round(cumulative_requests_per_second * 60, 2)
            else:
                self._test_start_time = current_time
                cumulative_requests_per_second = 0
                cumulative_requests_per_minute = 0
            
            # Calculate interval stats
            interval_stats = None
            snapshot_to_store = None  # We'll decide what to store after interval calculation
            
            if self._last_stats_snapshot and self._last_stats_time:
                # Normal interval calculation (we have a previous snapshot to compare)
                interval_duration = (current_time - self._last_stats_time).total_seconds()
                # Fix: Access the nested structure correctly
                last_total_requests = self._last_stats_snapshot.get('cumulative_stats', {}).get('total_requests', 0)
                interval_requests = total_requests - last_total_requests
                
                # Debug logging
                self.logger.debug(f"Interval calculation: current={total_requests}, last={last_total_requests}, interval={interval_requests}, duration={interval_duration:.2f}s")
                
                interval_requests_per_second = round(interval_requests / interval_duration, 2) if interval_duration > 0 else 0
                interval_requests_per_minute = round(interval_requests_per_second * 60, 2)
                
                # Calculate interval block stats
                interval_block_stats = {}
                for block_id in self.blocks.keys():
                    current_block_requests = cumulative_block_stats[block_id]['total_requests']
                    last_block_requests = self._last_stats_snapshot.get('cumulative_stats', {}).get('block_statistics', {}).get(block_id, {}).get('total_requests', 0)
                    interval_block_requests = current_block_requests - last_block_requests
                    
                    interval_block_stats[block_id] = {
                        "requests_in_interval": interval_block_requests,
                        "requests_per_second": round(interval_block_requests / interval_duration, 2) if interval_duration > 0 else 0,
                        "requests_per_minute": round((interval_block_requests / interval_duration) * 60, 2) if interval_duration > 0 else 0
                    }
                
                interval_stats = {
                    "duration_seconds": round(interval_duration, 2),
                    "requests_in_interval": interval_requests,
                    # expected and actually_sent in interval
                    "expected_requests_in_interval": 0,
                    "actually_sent_in_interval": interval_requests,
                    "requests_per_second": interval_requests_per_second,
                    "requests_per_minute": interval_requests_per_minute,
                    "block_statistics": interval_block_stats,
                    "interval_start": self._last_stats_time.isoformat(),
                    "interval_end": current_time.isoformat()
                }
            else:
                # First log - create initial interval stats using cumulative data
                # (treat all current progress as the "first interval")
                test_duration = (current_time - getattr(self, '_test_start_time', current_time)).total_seconds()
                
                # For the first log, interval = cumulative (progress from 0 to current)
                interval_requests_per_second = round(total_requests / test_duration, 2) if test_duration > 0 else 0
                interval_requests_per_minute = round(interval_requests_per_second * 60, 2)
                
                # Calculate initial interval block stats (all current requests are "interval" requests)
                interval_block_stats = {}
                for block_id in self.blocks.keys():
                    current_block_requests = cumulative_block_stats[block_id]['total_requests']
                    
                    interval_block_stats[block_id] = {
                        "requests_in_interval": current_block_requests,  # All current requests
                        "requests_per_second": round(current_block_requests / test_duration, 2) if test_duration > 0 else 0,
                        "requests_per_minute": round((current_block_requests / test_duration) * 60, 2) if test_duration > 0 else 0
                    }
                
                interval_stats = {
                    "duration_seconds": round(test_duration, 2),
                    "requests_in_interval": total_requests,  # All current requests are "interval" requests
                    "expected_requests_in_interval": 0,
                    "actually_sent_in_interval": total_requests,
                    "requests_per_second": interval_requests_per_second,
                    "requests_per_minute": interval_requests_per_minute,
                    "block_statistics": interval_block_stats,
                    "interval_start": getattr(self, '_test_start_time', current_time).isoformat(),
                    "interval_end": current_time.isoformat()
                }
                
                self.logger.debug(f"First interval calculation: total_requests={total_requests}, duration={test_duration:.2f}s")
            
            # Prepare snapshot for next interval (but don't store it yet)
            snapshot_to_store = {
                'cumulative_stats': {
                    'total_requests': total_requests,
                    'block_statistics': cumulative_block_stats
                }
            }

            # Store expected cumulative totals in snapshot so next interval can compute delta
            snapshot_to_store['cumulative_stats']['expected_total_requests'] = expected_total_cumulative
            snapshot_to_store['cumulative_stats']['expected_block_statistics'] = expected_block_cumulative
            
            # Prepare complete stats structure
            stats = {
                "test_id": self.test_id,
                "is_running": self.is_running,
                "timestamp": current_time.isoformat(),
                "test_start_time": getattr(self, '_test_start_time', current_time).isoformat(),
                
                # Cumulative stats (since test started)
                "cumulative_stats": {
                    "total_users": total_users,
                    "active_users": active_users,
                    "total_requests": total_requests,
                    # number of requests actually sent (assume session.request_count tracks sent requests)
                    "actually_sent": total_requests,
                    "expected_requests_so_far": round(expected_total_cumulative),
                    "target_users": self._calculate_target_users(),
                    "current_hour_multiplier": self._get_current_hour_multiplier(),
                    "current_hour": current_time.hour,
                    "requests_per_second": cumulative_requests_per_second,
                    "requests_per_minute": cumulative_requests_per_minute,
                    "block_statistics": cumulative_block_stats,
                    "test_duration_seconds": round((current_time - getattr(self, '_test_start_time', current_time)).total_seconds(), 2)
                }
            }
            
            # Add interval stats (now always available)
            # Fill expected per-block and expected interval totals
            # Compute expected for the interval using the same method as cumulative
            if self._last_stats_time:
                expected_interval_total, expected_interval_block = compute_expected_between(self._last_stats_time, current_time)
            else:
                expected_interval_total, expected_interval_block = compute_expected_between(getattr(self, '_test_start_time', current_time), current_time)

            interval_stats["expected_requests_in_interval"] = round(expected_interval_total)
            interval_stats["actually_sent_in_interval"] = interval_stats.get('requests_in_interval', 0)
            # Attach expected per-block numbers
            for b, val in expected_interval_block.items():
                if b in interval_stats['block_statistics']:
                    interval_stats['block_statistics'][b]['expected_requests_in_interval'] = round(val)
                    interval_stats['block_statistics'][b]['actually_sent_in_interval'] = interval_stats['block_statistics'][b].get('requests_in_interval', 0)

            # Also annotate cumulative block statistics with expected and actually_sent
            for b in stats['cumulative_stats']['block_statistics'].keys():
                stats['cumulative_stats']['block_statistics'][b]['expected_requests_so_far'] = round(expected_block_cumulative.get(b, 0))
                stats['cumulative_stats']['block_statistics'][b]['actually_sent'] = stats['cumulative_stats']['block_statistics'][b].get('total_requests', 0)

            stats["interval_stats"] = interval_stats
            
            # Add database statistics if available
            if self.db_logger:
                try:
                    db_stats = self.db_logger.get_test_statistics(self.test_id)
                    stats["database_statistics"] = db_stats
                except Exception as e:
                    self.logger.warning(f"Could not get database statistics: {e}")
            
            # Store current snapshot for next interval calculation
            # Don't update snapshot for final calls to preserve interval data
            if not is_final and self.is_running:  # Only update snapshot during active test and non-final calls
                # Store the prepared snapshot
                self._last_stats_snapshot = snapshot_to_store
                self._last_stats_time = current_time
                self.logger.debug(f"Updated snapshot: requests={total_requests}, time={current_time.strftime('%H:%M:%S')}")
            else:
                self.logger.debug(f"Skipped snapshot update: is_final={is_final}, is_running={self.is_running}")
            
            return stats
        except Exception as e:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno if tb else 'unknown'
            #print(f"[DEBUG] Error get_statistics     at line {line_number}: {e}")
            logger.error(f"Error during get_statistics at line {line_number}: {e}")

# Main execution function
async def main():
    """Main function to run the load test"""
    import sys
    
    config_path = sys.argv[1] if len(sys.argv) > 1 else 'config.yaml'
    
    crowd = Crowd(config_path)
    
    try:
        # Start the test
        await crowd.start_test()
    except KeyboardInterrupt:
        print("\nReceived interrupt signal, stopping test...")
        await crowd.stop_test()
    except Exception as e:
        logging.error(f"Test failed with error: {e}")
        await crowd.stop_test()
        raise

if __name__ == "__main__":
    asyncio.run(main())