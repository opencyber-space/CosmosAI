import asyncio
import aiohttp
import grpc
import logging
import uuid
import time, json
import random
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pytz
from dataclasses import dataclass
from db_logger import DatabaseLogger
import os

import grpc_utils.service_pb2 as service_pb2
import grpc_utils.service_pb2_grpc as service_pb2_grpc

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

@dataclass
class Session:
    """Represents a generate session with an LLM block"""
    session_id: str
    block_id: str
    block_url: str
    generation_config: Dict[str, Any]
    created_at: datetime
    request_count: int = 0
    failed_requests: int = 0
    time_total: float = 0.0  # Total time spent on requests


class User:
    """Represents a single user performing load testing"""
    
    # Shared logger for all users
    _shared_logger = None
    _shared_logger_initialized = False
    _shared_aiohttp_session = None
    _shared_aiohttp_session_limit = 300  # Will be set from config


    def __init__(self, user_id: str, config: Dict[str, Any], blocks: Dict[str, Any], 
                 db_logger: Optional[DatabaseLogger] = None, test_id: str = None, global_config: Dict[str, Any] = None):
        self.user_id = user_id
        self.config = config
        self.blocks = blocks
        self.inference_server_url = config.get('inferenceServerURL', '')
        self.db_logger = db_logger
        self.global_config = global_config or {}
        self.test_id = test_id or str(uuid.uuid4())
        # Get timezone from config, default to Asia/Kolkata
        timezone_str = self.global_config.get('logging', {}).get('timezone', 'Asia/Kolkata')
        self.ist_tz = pytz.timezone(timezone_str)

        # Setup shared logger for all users (non-blocking with queue handler)
        if not User._shared_logger_initialized:
            import queue
            from logging.handlers import QueueHandler, QueueListener
            log_config = self.global_config.get('logging', {})
            logger = logging.getLogger("UserShared")
            logger.setLevel(getattr(logging, log_config.get('level', 'INFO')))
            formatter = ISTFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                tz=self.ist_tz
            )
            # File handler (shared log file)
            if not os.path.exists("logs"):
                os.makedirs("logs")
            log_file_path = log_config.get('log_file', 'logs/UserShared.log')
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setFormatter(formatter)
            # Use a queue for non-blocking logging
            log_queue = queue.Queue(-1)
            queue_handler = QueueHandler(log_queue)
            logger.addHandler(queue_handler)
            # Console handler
            handlers = [file_handler]
            if log_config.get('console_output', True):
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(formatter)
                handlers.append(console_handler)
            listener = QueueListener(log_queue, *handlers, respect_handler_level=True)
            listener.daemon = True
            listener.start()
            logger.propagate = False
            User._shared_logger = logger
            User._shared_logger_initialized = True
        # Always set self.logger for every User instance
        self.logger = User._shared_logger

        # --- Load questions from file and prepare per-block assignment ---
        self.questions_file = self.global_config.get('questions_file', 'questions.jsonl')
        self.questions_per_block = {block_id: [] for block_id in self.blocks}
        self._read_questions_file()
        # Shared aiohttp session (class-level, one per process)
        if User._shared_aiohttp_session is None:
            # Calculate optimal session limit from config
            try:
                users_per_hour = int(self.global_config.get('crowd_config', {}).get('users_per_hour', 100))
                requests_per_hour_per_session = int(self.global_config.get('user_config', {}).get('requests_per_hour_per_session', 60))
                sessions_per_block = int(self.global_config.get('user_config', {}).get('sessions_per_block', 2))
                blocks_count = len(self.global_config.get('blocks', {}))
                session_limit = users_per_hour * requests_per_hour_per_session * sessions_per_block * max(1, blocks_count)
                session_limit = min(session_limit, 65536)  # Cap to avoid too many open connections
            except Exception as e:
                session_limit = 1000  # fallback
            User._shared_aiohttp_session_limit = session_limit
            
            connector = aiohttp.TCPConnector(limit=User._shared_aiohttp_session_limit)
            User._shared_aiohttp_session = aiohttp.ClientSession(connector=connector)
        self.aiohttp_session = User._shared_aiohttp_session
        
        # Configuration
        self.sessions_per_block = config.get('sessions_per_block', 2)
        self.requests_per_hour_per_session = config.get('requests_per_hour_per_session', 50)
        
        # Load user-specific usage patterns from CSV or fallback to config (now logger is available)
        self.usage_patterns = self._load_user_usage_patterns(config.get('usage_patterns', {}))
        self.usage_pattern_red_time = time.time()

        self.request_timeout = config.get('request_timeout', 30)
        self.retry_attempts = config.get('retry_attempts', 3)
        
        # State
        self.sessions: List[Session] = []
        self.is_active = False
        self.tasks: List[asyncio.Task] = []
        
        # Initialize sessions (now logger is available)
        self._create_sessions()

        # Load questions from file
        # with open(self.global_config.get('questions_file', 'questions.jsonl'), 'r') as f:
        #     self.all_questions = [json.loads(line) for line in f]
        # self.questions_per_block = {block_id: [q for q in self.all_questions if block_id not in q['used_blocks']] for block_id in self.blocks}
    
    def _read_questions_file(self, block_id_to_fill="") -> List[Dict[str, Any]]:
        """Read questions from the questions file"""
        all_questions = []
        if os.path.exists(self.questions_file):
            with open(self.questions_file, 'r') as f:
                for line in f:
                    try:
                        q = json.loads(line)
                        all_questions.append(q)
                    except Exception:
                        continue
            # For each block, filter questions not yet used for that block
            for block_id in self.blocks:
                if block_id_to_fill == "":
                    self.questions_per_block[block_id] = [q for q in all_questions if block_id not in q.get('used_blocks', [])]
                    random.shuffle(self.questions_per_block[block_id])
                elif block_id == block_id_to_fill:
                    self.questions_per_block[block_id] = [q for q in all_questions if block_id not in q.get('used_blocks', [])]
                    # Shuffle questions for randomness
                    random.shuffle(self.questions_per_block[block_id])
        else:
            self.logger.warning(f"Questions file {self.questions_file} not found. No questions loaded.")


    def _load_user_usage_patterns(self, fallback_patterns: Dict[int, float]) -> Dict[int, float]:
        """Load user-specific usage patterns from CSV file or use fallback"""
        csv_file = self.global_config.get('user_config', {}).get('csv_file', 'user_behavior_patterns.csv')
        if not os.path.exists(csv_file):
            self.logger.info(f"CSV file {csv_file} not found, using fallback patterns from config")
            return fallback_patterns
        try:
            user_index = int(self.user_id.split('_')[1])
            with open(csv_file, 'r', newline='') as file:
                reader = csv.reader(file)
                header = next(reader, None)  # Skip header row
                for row in reader:
                    if len(row) >= 25 and int(row[0]) == user_index:
                        patterns = {hour: float(row[hour + 1]) for hour in range(24)}
                        self.logger.info(f"Loaded usage patterns for user {self.user_id} (index {user_index}) from CSV")
                        return patterns
                self.logger.warning(f"User index {user_index} not found in CSV, using fallback patterns")
                return fallback_patterns
        except (ValueError, IndexError, IOError) as e:
            self.logger.error(f"Error loading usage patterns from CSV: {e}")
            self.logger.info("Falling back to config patterns")
            return fallback_patterns
    
    def _create_sessions(self):
        """Create sessions for each block"""
        block_count = 0
        for block_id, block_config in self.blocks.items():
            for i in range(self.sessions_per_block):
                session = Session(
                    session_id=f"{self.user_id}-{block_id}-{(block_count*self.sessions_per_block)+i}",
                    block_id=block_id,
                    block_url=self.global_config.get('inferenceServerURL', ''),  #block_config.get('url', ''),
                    generation_config=block_config.get('generation_config', {}),
                    created_at=datetime.now(self.ist_tz)
                )
                self.sessions.append(session)
            block_count += 1
    
    def _get_current_hour_multiplier(self) -> float:
        """Get the current hour's activity multiplier"""
        current_hour = datetime.now(self.ist_tz).hour
        # if (time.time()-self.usage_pattern_red_time) > 300:
        #     #reread the usage pattern 
        #     self.usage_patterns = self._load_user_usage_patterns(self.config.get('usage_patterns', {}))
        #     self.usage_pattern_red_time = time.time()
        return self.usage_patterns.get(current_hour, 1.0)
    
    def _calculate_requests_per_session(self) -> int:
        """Calculate requests per session based on current time"""
        base_requests = self.requests_per_hour_per_session
        multiplier = self._get_current_hour_multiplier()
        return max(1, int(base_requests * multiplier))
    
    async def _make_http_request(self, session: Session, message: str) -> Dict[str, Any]:
        """Make HTTP request to LLM block (using shared ClientSession)"""
        final_message = message
        if "qwen" in session.block_id.lower():
            final_message = message + " /no_think"
        generation_config = {
            "max_new_tokens": 512,
            "do_sample": False,
            "top_k": 50,
            "top_p": 0.95,
            "temperature": 1.0
        }
        generation_config = self.global_config.get("blocks", {}).get(session.block_id, {}).get("generation_config", generation_config)
        print(generation_config)
        seq_no = session.request_count + 1
        if "gemma" in session.block_id.lower():
            payload = {
                "model": session.block_id,
                "session_id": session.session_id,
                "seq_no": seq_no,
                "data": {
                    "mode": "generate",
                    "generation_config": generation_config,
                    "messages": [{"content": [
                        {"type": "text", "text": "Analyze the following image and generate your objective scene report.?"},
                        {"type": "image_url",
                         "image_url": {"url": "https://akm-img-a-in.tosshub.com/indiatoday/images/story/202311/chain-snatching-caught-on-camera-in-bengaluru-293151697-16x9_0.jpg"}}]}],
                    "session_id": session.session_id,
                    "system_message": "Analyze the following text and generate your objective scene report."
                },
                "graph": {},
                "files": {},
                "selection_query": {}
            }
        else:
            payload = {
                "model": session.block_id,
                "session_id": session.session_id,
                "seq_no": seq_no,
                "data": {
                    "mode": "generate",
                    "generation_config": generation_config,
                    "prompt": final_message,
                    "system_message": "You are a helpful assistant."
                },
                "graph": {},
                "files": {},
                "selection_query": {},
                "timeout": self.request_timeout
            }
        #payload["data"]["generation_config"].update(session.generation_config)
        # Simple timing approach: measure just before request to just after response
        _req_start = time.monotonic()
        start_time_perf = time.perf_counter()

        dataDumpToDMA = {
            "block_id":  session.block_id,
            "session_id": session.session_id,
            "seq_no": seq_no,
            "type": "success",
            "response_time": 0.0,
            "raw": "{}",
            "test_id": self.test_id,
            "user_id": self.user_id,
            "starttime": time.time(),
            "endtime": time.time(),
            "starttimeObj": datetime.now(self.ist_tz),
            "endtimeObj": datetime.now(self.ist_tz)
        }

        try:
            self.logger.info(f"Sending HTTP request to {session.block_url} with session_id: {session.session_id} for sequence number: {payload['seq_no']}")
            # Use shared aiohttp session
            async with self.aiohttp_session.post(session.block_url, json=payload, timeout=self.request_timeout) as response:
                response_data = await response.json()
                end_time_perf = time.perf_counter()
                duration = end_time_perf - start_time_perf
                _resp_time = time.monotonic() - _req_start
                self.logger.info(f"✓ Received HTTP response for session_id: {session.session_id} and sequence number: {payload['seq_no']} with response time: {_resp_time:.2f}s")
                self.logger.info(f"duration: {duration}")
                self.logger.info(f"_resp_time: {_resp_time}")
                dataDumpToDMA["type"] = "success" if response.status == 200 else "failure"
                dataDumpToDMA["response_time"] = _resp_time
                dataDumpToDMA["raw"] = "{}" #json.dumps(response_data)
                dataDumpToDMA["endtime"] = time.time()
                # Convert datetime to ISO string with microseconds and 'Z' for UTC-like format
                dataDumpToDMA["endtimeObj"] = datetime.now(self.ist_tz).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                # Fix: convert datetime objects to ISO string before sending to DMA endpoint
                for k in ["starttimeObj", "endtimeObj"]:
                    if isinstance(dataDumpToDMA.get(k), datetime):
                        dataDumpToDMA[k] = dataDumpToDMA[k].strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                try:
                    # Send dataDumpToDMA to external endpoint, ignore timeout errors
                    logEndPoint = self.global_config.get("database", {}).get("dma_logging_end_point", "")
                    self.logger.info(f"logEndPoint: {logEndPoint}")
                    self.logger.info(f"dataDumpToDMA: {dataDumpToDMA}")
                    if logEndPoint:
                        async with self.aiohttp_session.post(
                            logEndPoint,
                            json=dataDumpToDMA,
                            headers={"accept": "application/json", "Content-Type": "application/json"},
                            timeout=3
                        ) as dma_resp:
                            pass  # Ignore response
                            dma_response_data = await dma_resp.json()
                            self.logger.info(f"DMA dma_response_data: {dma_response_data}")
                except asyncio.TimeoutError as e:
                    self.logger.info(f"DMA logging timeout: {e}")  # Ignore timeout errors for this request
                except Exception as e:
                    self.logger.info(f"DMA logging failed: {e}")
                return {
                    "success": response.status == 200,
                    "response_time": _resp_time,
                    "status_code": response.status,
                    "response_data": response_data,
                    "error": None
                }
        except Exception as e:
            import traceback
            error_type = type(e).__name__
            tb_str = traceback.format_exc()
            # On error, try to get elapsed if available
            _resp_time = time.monotonic() - _req_start
            self.logger.error(f"HTTP request failed: [{error_type}] {e}\nTraceback:\n{tb_str}")
            self.logger.info(f"✗ HTTP request failed for session_id: {session.session_id} after {_resp_time:.2f}s")
            dataDumpToDMA["type"] = "failure"
            dataDumpToDMA["response_time"] = _resp_time
            dataDumpToDMA["raw"] = "{}"
            dataDumpToDMA["endtime"] = time.time()
            # Convert datetime to ISO string with microseconds and 'Z' for UTC-like format
            dataDumpToDMA["endtimeObj"] = datetime.now(self.ist_tz).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            # Fix: convert datetime objects to ISO string before sending to DMA endpoint
            for k in ["starttimeObj", "endtimeObj"]:
                if isinstance(dataDumpToDMA.get(k), datetime):
                    dataDumpToDMA[k] = dataDumpToDMA[k].strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            
            try:
                # Send dataDumpToDMA to external endpoint, ignore timeout errors
                logEndPoint = self.global_config.get("database", {}).get("dma_logging_end_point", "")
                self.logger.info(f"logEndPoint: {logEndPoint}")
                self.logger.info(f"dataDumpToDMA: {dataDumpToDMA}")
                if logEndPoint:
                    async with self.aiohttp_session.post(
                        logEndPoint,
                        json=dataDumpToDMA,
                        headers={"accept": "application/json", "Content-Type": "application/json"},
                        timeout=3
                    ) as dma_resp:
                        pass  # Ignore response
                        dma_response_data = await dma_resp.json()
                        self.logger.info(f"DMA dma_response_data: {dma_response_data}")
            except asyncio.TimeoutError as e:
                self.logger.info(f"DMA logging timeout: {e}")
            except Exception as e:
                self.logger.info(f"DMA logging failed: {e}")
            
            return {
                "success": False,
                "response_time": _resp_time,
                "status_code": None,
                "response_data": None,
                "error": f"{error_type}: {e}"
            }
    
    async def _make_grpc_request(self, session: Session, message: str) -> Dict[str, Any]:
        """Make gRPC request to LLM block using proper async gRPC patterns"""
        channel = None
        try:
            # Validate gRPC URL
            grpc_url = self.global_config.get('grpcServiceURL', '')
            if not grpc_url:
                self.logger.error(f"✗ gRPC URL not configured for session_id: {session.session_id}")
                raise ValueError("gRPC URL not configured")
            
            self.logger.debug(f"Creating gRPC channel to: {grpc_url}")
            
            # Create async gRPC channel
            channel = grpc.aio.insecure_channel(grpc_url)
            stub = service_pb2_grpc.BlockInferenceServiceStub(channel)
            
            # Example file metadata and binary data
            file_info = service_pb2.FileInfo(
                metadata=json.dumps({"filename": "example.txt", "size": 123}),
                file_data=b"Example file content"
            )
            seq_no = session.request_count + 1

            # Create base generation config and update with session-specific config
            generation_config = {
                "max_new_tokens": 512,
                "do_sample": False,
                "top_k": 50,
                "top_p": 0.95,
                "temperature": 1.0
            }
            generation_config = self.global_config.get("blocks", {}).get(session.block_id, {}).get("generation_config", generation_config)
            
            # Fix: Use session.block_id instead of undefined block_id
            final_message = message
            if "qwen" in session.block_id.lower():
                final_message = message + " /no_think"

            # Create the BlockInferencePacket request
            data = None
            if "gemma" in session.block_id.lower():
                data = json.dumps({
                            "mode": "generate",
                            "generation_config": generation_config,
                            "messages": [{"content": [
                                        {"type": "text", "text": "Analyze the following image and generate your objective scene report.?"},
                                        {"type": "image_url",
                                    "image_url": {"url": "https://akm-img-a-in.tosshub.com/indiatoday/images/story/202311/chain-snatching-caught-on-camera-in-bengaluru-293151697-16x9_0.jpg"}}] }],
                            "session_id": session.session_id,
                            "system_message": "Analyze the following text and generate your objective scene report."
                        })
            else:
                data = json.dumps({
                    "mode": "generate",
                    "system_message": "You are a helpful assistant.",
                    "prompt": final_message,
                    "generation_config": generation_config,
                    "session_id": session.session_id
                }) 
            request = service_pb2.BlockInferencePacket(
                block_id=session.block_id,
                session_id=session.session_id,
                seq_no=seq_no,
                frame_ptr=b"",  # Empty bytes for now
                data=data, 
                query_parameters="",
                ts=time.time(),
                files=[file_info],  # Attach the file
                output_ptr=b''
            )
            
            # Make the async gRPC call with timeout; measure with monotonic clock
            _req_start = time.monotonic()
            self.logger.info(f"Sending gRPC request to {grpc_url} with session_id: {session.session_id} for sequence number: {seq_no}")
            self.logger.debug(f"gRPC request payload size: {len(request.data)} bytes, block_id: {session.block_id}")
            try:
                response = await asyncio.wait_for(
                    stub.infer(request), 
                    timeout=self.request_timeout
                )
                response_time = time.monotonic() - _req_start
                self.logger.info(f"✓ Received gRPC response for session_id: {session.session_id} and sequence number: {seq_no} with response time: {response_time:.2f}s")
            except asyncio.TimeoutError:
                response_time = time.monotonic() - _req_start
                self.logger.error(f"✗ gRPC request timed out after {self.request_timeout}s for session_id: {session.session_id}")
                raise
            except grpc.aio.AioRpcError as grpc_error:
                response_time = time.monotonic() - _req_start
                self.logger.error(f"✗ gRPC call failed immediately: {grpc_error.code()} - {grpc_error.details()}")
                raise

            # Parse JSON response data
            self.logger.debug(f"Raw gRPC response data type: {type(response.data)}, length: {len(response.data) if response.data else 'None'}")
            try:
                if not response.data:
                    self.logger.warning(f"Empty response data received for session_id: {session.session_id}")
                    response_data = {}
                else:
                    response_data = json.loads(response.data)
                    self.logger.debug(f"Successfully parsed gRPC response for session_id: {session.session_id}")
                    #self.logger.info(f"Parsed Response: {response_data}")
            except json.JSONDecodeError as json_error:
                self.logger.error(f"Response data is not a valid JSON string for session_id: {session.session_id}. Raw data: {response.data[:200]}...")
                raise ValueError(f"Invalid JSON response: {str(json_error)}")

            return {
                "success": True,
                "response_time": response_time,
                "status_code": 200,
                "response_data": response_data,
                "error": None
            }
            
        except ValueError as ve:
            self.logger.error(f"✗ gRPC Configuration Error for session_id {session.session_id}: {str(ve)}")
            return {
                "success": False,
                "response_time": 0,
                "response_data": None,
                "status_code": None,
                "error": f"Configuration Error: {str(ve)}"
            }
        except grpc.aio.AioRpcError as e:  # Fixed: Use AioRpcError for async gRPC
            self.logger.error(f"✗ gRPC RPC Error for session_id {session.session_id}: {e.code()} - {e.details()}")
            return {
                "success": False,
                "response_time": 0,
                "response_data": None,
                "status_code": None,
                "error": f"gRPC Error: {e.code()} - {e.details()}"
            }
        except asyncio.TimeoutError:
            self.logger.error(f"✗ gRPC Timeout Error for session_id {session.session_id}: Request timed out after {self.request_timeout}s")
            return {
                "success": False,
                "response_time": 0,
                "response_data": None,
                "status_code": None,
                "error": f"gRPC Timeout: Request timed out after {self.request_timeout}s"
            }
        except Exception as e:
            self.logger.error(f"✗ gRPC Exception for session_id {session.session_id}: {type(e).__name__}: {str(e)}")
            return {
                "success": False,
                "response_time": 0,
                "response_data": None,
                "status_code": None,
                "error": f"{type(e).__name__}: {str(e)}"
            }
        finally:
            # Properly close the channel
            if channel:
                await channel.close()
    
    async def _send_request_with_retry(self, session: Session, message: str, 
                                     request_type: str = "http") -> Dict[str, Any]:
        """Send request with retry logic"""
        for attempt in range(self.retry_attempts):
            try:
                if request_type.lower() == "http":
                    result = await self._make_http_request(session, message)
                else:
                    result = await self._make_grpc_request(session, message)
                # result = {"success":True}
                # await asyncio.sleep(2)  # Simulate network delay for realistic timing

                if result["success"]:
                    return result
                else:
                    session.failed_requests += 1
                
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
            except Exception as e:
                self.logger.error(f"Request attempt {attempt + 1} failed: {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(2 ** attempt)
        
        return {
            "success": False,
            "response_time": 0,
            "status_code": None,
            "response_data": None,
            "error": "Max retries exceeded"
        }
    
    async def _log_request(self, session: Session, request_data: Dict[str, Any], 
                          response_data: Dict[str, Any]):
        """Log request/response data"""
        if not self.db_logger or not self.global_config.get('database', {}).get('enableRequestResponse', False):
            return
        if self.db_logger:
            log_entry = {
                "test_id": self.test_id,
                "user_id": self.user_id,
                "session_id": session.session_id,
                "block_id": session.block_id,
                "block_url": session.block_url,
                "timestamp": datetime.now(self.ist_tz),
                "request_data": request_data,
                "response_data": response_data,
                "success": response_data.get("success", False),
                "response_time": response_data.get("response_time", 0),
                "error": response_data.get("error")
            }
            await asyncio.create_task(
                asyncio.to_thread(self.db_logger.log_request, log_entry)
            )
    
    async def _session_worker(self, session: Session):
        """Worker for a single session - sends requests based on usage patterns"""
        # Initialize timing - add small random offset to prevent all sessions starting simultaneously
        import random
        start_time = time.time() + random.uniform(0, 1.0)  # Random start within 1 second
        request_number = 0
        last_calculated_hour = -1
        current_interval = None
        
        # Wait for the initial start time
        initial_sleep = start_time - time.time()
        if initial_sleep > 0:
            await asyncio.sleep(initial_sleep)
        
        while self.is_active:
            try:
                # Only recalculate interval when hour changes to avoid precision issues
                current_hour = datetime.now(self.ist_tz).hour
                if current_hour != last_calculated_hour:
                    requests_this_hour = self._calculate_requests_per_session()
                    self.logger.info(f"Hour {current_hour}: requests_this_hour={requests_this_hour}, multiplier={self._get_current_hour_multiplier()}, base={self.requests_per_hour_per_session}")
                    if requests_this_hour > 0:
                        current_interval = 3600.0 / requests_this_hour  # Use float for precision
                        self.logger.info(f"Session {session.session_id}: Hour {current_hour}, {requests_this_hour} req/hr, {current_interval:.3f}s interval")
                    else:
                        current_interval = None
                    last_calculated_hour = current_hour
                
                if current_interval is not None:
                    # Calculate exact time for this request (no drift accumulation)
                    # scheduled_time = start_time + (request_number * current_interval)
                    # current_time = time.time()
                    self.logger.debug(f"Session {session.session_id} sleeping for {current_interval:.3f}s until next request")
                    await asyncio.sleep(current_interval)
                    
                    # Wait until scheduled time
                    # if current_time < scheduled_time:
                    #     sleep_time = scheduled_time - current_time
                    #     if sleep_time > 0.001:  # Only log if significant
                    #         self.logger.debug(f"Session {session.session_id} sleeping for {sleep_time:.3f}s until next request")
                    #     await asyncio.sleep(sleep_time)
                    # elif current_time > scheduled_time + 1:  # More than 1 second late
                    #     self.logger.warning(f"Session {session.session_id} is {current_time - scheduled_time:.3f}s behind schedule")

                    # --- Select a unique question for this block/session ---
                    message = None
                    block_id = session.block_id
                    if self.questions_per_block.get(block_id):
                        try:
                            question_entry = self.questions_per_block[block_id].pop(0)
                            message = question_entry['question']
                        except Exception as e:
                            self.logger.error(f"Error retrieving question for block {block_id}: {e}")
                            self.logger.warning(f"Reloading questions for block {block_id} due to error")
                            self._read_questions_file(block_id_to_fill=block_id)
                        # Mark as used for this block
                        # if 'used_blocks' not in question_entry:
                        #     question_entry['used_blocks'] = []
                        # question_entry['used_blocks'].append(block_id)
                        # Optionally, update the file (append-only for now)
                        # (For full atomic update, rewrite file, but here we skip for performance)
                    else:
                        message = "Can you provide python flask web development examples?"
                        self.logger.warning(f"No more unique questions available for block {block_id} in session {session.session_id}")

                    # --- Interactive config update via keyboard ---
                    # import sys
                    # import threading
                    # def get_input_with_timeout(prompt, timeout):
                    #     result = {"value": None}
                    #     def input_thread():
                    #         try:
                    #             result["value"] = input(prompt)
                    #         except Exception:
                    #             result["value"] = None
                    #     t = threading.Thread(target=input_thread)
                    #     t.daemon = True
                    #     t.start()
                    #     t.join(timeout)
                    #     return result["value"]
                    # # Only allow in main thread (avoid issues in async workers)
                    # if threading.current_thread() is threading.main_thread():
                    #     user_input = await asyncio.to_thread(get_input_with_timeout, "Press 'k' to update config, or Enter to continue: ", 3)
                    #     if user_input == "k":
                    #         var_name = await asyncio.to_thread(get_input_with_timeout, "Enter variable name to update: ", 15)
                    #         if var_name and hasattr(self, var_name):
                    #             new_value = await asyncio.to_thread(get_input_with_timeout, f"Enter new value for {var_name}: ", 15)
                    #             if new_value is not None:
                    #                 # Try to convert to int/float/bool if possible
                    #                 try:
                    #                     if new_value.lower() in ("true", "false"):
                    #                         value = new_value.lower() == "true"
                    #                     else:
                    #                         value = new_value
                    #                 except Exception:
                    #                     try:
                    #                         value = float(new_value)
                    #                     except Exception:
                    #                         value = new_value
                    #                 setattr(self, var_name, value)
                    #                 self.logger.info(f"Updated self.{var_name} to {value}")
                    #             else:
                    #                 self.logger.warning("No value entered, skipping update.")
                    #         else:
                    #             self.logger.warning(f"Variable '{var_name}' not found in self.")
                    #     else:
                    #         self.logger.debug("No config update requested, continuing.")
                    # else:
                    #     self.logger.debug("Config update only allowed in main thread, skipping.")
                    self.logger.info(f"Session {session.session_id} createing _handle_single_request #{session.request_count + 1}")
                    asyncio.create_task(self._handle_single_request(session, message))
                    self.logger.info(f"Session {session.session_id} done with  _handle_single_request #{session.request_count + 1}")
                    
                    # Increment request counter for next scheduling
                    #request_number += 1
                    
                else:
                    # No requests this hour, check again in 30 seconds
                    self.logger.info(f"Session {session.session_id} no requests scheduled this hour, sleeping for 30s as current_interval is None")
                    await asyncio.sleep(30)
                    # Reset timing when activity resumes
                    start_time = time.time()
                    request_number = 0
                    last_calculated_hour = -1
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in session worker {session.session_id}: {e}")
                await asyncio.sleep(10)  # Wait before retrying
                # Reset timing after error
                start_time = time.time()
                request_number = 0
                last_calculated_hour = -1
    
    async def _handle_single_request(self, session: Session, message: str):
        """Handle a single request independently of timing"""
        try:
            # Send request
            request_data = {"prompt": message, "timestamp": datetime.now(self.ist_tz)}
            request_type = self.blocks[session.block_id].get('requestType', 'HTTP')
            request_type = 'http' if request_type == 'HTTP' else 'grpc'
            response_data = await self._send_request_with_retry(session, message, request_type=request_type)
            
            # Update session state
            session.request_count += 1

            if not response_data.get("success"):
                #session.failed_requests += 1
                #this is handled now in _send_request_with_retry
                pass
            else:
                session.time_total = session.time_total + response_data.get("response_time", 0)
            
            # Log the request
            await self._log_request(session, request_data, response_data)
            
        except Exception as e:
            self.logger.error(f"Error handling request for session {session.session_id}: {e}")
    
    async def start(self):
        """Start the user's activity"""
        if self.is_active:
            return
        
        self.is_active = True
        self.logger.info(f"User {self.user_id} starting with {len(self.sessions)} sessions")
        
        # Start a task for each session
        for session in self.sessions:
            task = asyncio.create_task(self._session_worker(session))
            self.tasks.append(task)
    
    async def stop(self):
        """Stop the user's activity"""
        if not self.is_active:
            return
        
        self.is_active = False
        self.logger.info(f"User {self.user_id} stopping")
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.tasks.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get user statistics"""
        total_requests = sum(session.request_count for session in self.sessions)
        active_sessions = len([s for s in self.sessions if s.request_count > 0])
        
        return {
            "user_id": self.user_id,
            "total_sessions": len(self.sessions),
            "active_sessions": active_sessions,
            "total_requests": total_requests,
            "is_active": self.is_active,
            "sessions": [
                {
                    "session_id": s.session_id,
                    "block_id": s.block_id,
                    "request_count": s.request_count,
                    "created_at": s.created_at.isoformat()
                }
                for s in self.sessions
            ]
        }