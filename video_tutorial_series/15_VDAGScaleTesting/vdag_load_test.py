import asyncio
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import aiohttp
import pytz
import signal
import sys
import itertools
import yaml
import os
import uuid


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

class FixedRPSClient:
    def __init__(
        self,
        infer_endpoint: str,
        log_endpoint: str,
        rps: int,
        questions: List[str],
        tz_name: str = "Asia/Kolkata",
        session_prefix: str = "session_",
        request_timeout: int = 30,
        concurrent_limit: int = 1000,
        cfg: Dict[str, Any] = {}
        ):
        self.cfg = cfg
        self.infer_endpoint = infer_endpoint
        self.log_endpoint = log_endpoint
        self.rps = max(1, int(rps))
        self.questions = questions if questions else ["Explain Python asyncio with examples."]
        self.questions_cycle = itertools.cycle(self.questions)
        self.request_timeout = request_timeout
        self.test_id = str(uuid.uuid4())
        self._stopping = asyncio.Event()
        self._sem = asyncio.Semaphore(concurrent_limit)
        self._session: Optional[aiohttp.ClientSession] = None
        self.tz = pytz.timezone(tz_name)
        # Incrementing counters
        self.global_seq_no = 0          # overall sequential seq_no [attached_file:2]
        self.session_prefix = session_prefix
        self.next_session_counter = 1   # produces session_1, session_2, ... [attached_file:2]

        self.dummyunique = self.test_id[:4]

        ist_formatter = ISTFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            tz=self.tz
        )

        log_config = self.cfg.get('logging', {})
        
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

    async def start(self):
        connector = aiohttp.TCPConnector(limit=0)
        self._session = aiohttp.ClientSession(connector=connector)

    async def stop(self):
        self._stopping.set()
        if self._session:
            await self._session.close()

    def _new_session_id(self) -> str:
        sid = f"{self.session_prefix}{self.dummyunique}_{self.next_session_counter}"
        self.next_session_counter += 1
        return sid

    def _now_tz(self) -> datetime:
        return datetime.now(self.tz)

    def _new_dma_log(self, session_id: str, seq_no: int) -> Dict[str, Any]:
        now = time.time()
        now_dt = self._now_tz()
        return {
            "block_id": "dummy",
            "user_id": "dummy",
            "session_id": session_id,
            "seq_no": seq_no,
            "type": "success",
            "response_time": 0.0,
            "raw": "{}",
            "test_id": self.test_id,
            "starttime": now,
            "endtime": now,
            "starttimeObj": now_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "endtimeObj": now_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        }

    async def _post_dma(self, payload: Dict[str, Any]):
        if not self.log_endpoint:
            return
        try:
            self.logger.info(f"[DEBUG] Posting DMA log: {payload}")
            async with self._session.post(
                self.log_endpoint,
                json=payload,
                headers={"accept": "application/json", "Content-Type": "application/json"},
                timeout=5,
            ) as _:
                pass
                self.logger.info(f"[DEBUG] Posting DMA log Success")
        except Exception as e:
            self.logger.error(f"[DEBUG] Posting DMA log Exception: {e}")

    async def _fire_one(self, session_id: str, prompt: str):
        retries = self.cfg.get("inference", {}).get("vdag_param_retries",3)
        body = {
            "timeout": self.cfg.get("inference", {}).get("vdag_param_timeout",1200),
            "retries": retries,
            "session_id": session_id,
            "seq_no": 1,
            "data": {
                "mode": "chat",
                "generation_config": {
                    "temperature": 0.7,
                    "repetition_penalty": 1.0,
                    "min_p": 0.01,
                    "top_k": -1,
                    "top_p": 0.95,
                    "max_tokens": 256,
                    "max_history": 1
                },
                "message": prompt
            },
            "graph": {},
            "selection_query": {}
        }

        async with self._sem:
            # Monotonic global seq_no; if you want per-session sequence, reset when session changes [attached_file:2]
            #self.global_seq_no += 1
            seq_no = self.global_seq_no
            body["seq_no"] = seq_no
            

            dma = self._new_dma_log(session_id, seq_no)
            self.logger.info(f"[DEBUG] Sending request: session_id={session_id}, seq_no={seq_no}, prompt={prompt[:50]}...time: {dma['starttimeObj']}")
            
            t0 = time.monotonic()
            try:
                async with self._session.post(
                    self.infer_endpoint, json=body, timeout=self.request_timeout
                ) as resp:
                    
                    response_data = await resp.json()
                    rt = time.monotonic() - t0
                    dma["type"] = "success" if resp.status == 200 else "failure"
                    dma["response_time"] = rt
                    self.logger.info(f"[DEBUG] ✓ Received request: session_id={session_id}, seq_no={seq_no}, ...resp.status: {resp.status}, rt={rt:.3f}s")
                    dma["endtime"] = time.time()
                    dma["endtimeObj"] = self._now_tz().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                    asyncio.create_task(self._post_dma(dma))
            except Exception as e:
                self.logger.error(f"[ERROR] ✗ Exception for request: session_id={session_id}, seq_no={seq_no}, error: {e}")
                rt = time.monotonic() - t0
                dma["type"] = "failure"
                dma["response_time"] = rt
                dma["endtime"] = time.time()
                dma["endtimeObj"] = self._now_tz().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                asyncio.create_task(self._post_dma(dma))
            self.logger.info(f"[DEBUG] ✓ Received request: session_id={session_id}, seq_no={seq_no}, prompt={prompt[:50]}...time: {dma['endtimeObj']}, rt={dma['response_time']:.3f}s, type={dma['type']}")

    # async def run(self, duration_seconds: Optional[int] = None):
    #     if self._session is None:
    #         await self.start()

    #     start_wall = time.time()
    #     try:
    #         while not self._stopping.is_set():
    #             tick = time.monotonic()

    #             # Emit rps tasks; each gets a fresh incrementing session_id [attached_file:2]
    #             for _ in range(self.rps):
    #                 if self._stopping.is_set():
    #                     break
    #                 sid = self._new_session_id()
    #                 prompt = next(self.questions_cycle)
    #                 asyncio.create_task(self._fire_one(sid, prompt))

    #             if self._stopping.is_set():
    #                 break
    #             self.logger.info(f"[INFO] TestID: {self.test_id}")
    #             elapsed = time.monotonic() - tick
    #             await asyncio.sleep(max(0.0, 1.0 - elapsed))

    #             if duration_seconds is not None and (time.time() - start_wall) >= duration_seconds:
    #                 break
    #     except asyncio.CancelledError:
    #         pass

    async def _rps_meter(self):
        # Align to the next wall-second
        start = time.time()
        first_sleep = 1.0 - (start - int(start))
        await asyncio.sleep(first_sleep if first_sleep > 0 else 1.0)

        last_total = self.global_seq_no  # increment this counter at issue time
        while not self._stopping.is_set():
            t0 = time.time()
            await asyncio.sleep(1.0)
            total = self.global_seq_no
            window = total - last_total
            last_total = total
            self.logger.info(f"[RPS] target={self.rps} window_issued={window} issued_total={total} test-id={self.test_id}")

    async def run(self, duration_seconds: Optional[int] = None):
        """
        Precise RPS using deadline-driven pacing:
        - Inter-arrival dt = 1/rps
        - Schedule each request at t0 + n*dt
        - Fire-and-forget the actual HTTP task
        """
        if self._session is None:
            await self.start()

        if self.rps <= 0:
            raise ValueError("rps must be > 0")

        asyncio.create_task(self._rps_meter())

        dt = 1.0 / float(self.rps)
        start_wall = time.time()
        base = time.perf_counter()  # high-resolution monotonic clock
        n = 0
        self.global_seq_no = 0  # used by meter

        # Simple counters for debugging
        issued = 0
        last_report = base

        try:
            while not self._stopping.is_set():
                # Duration stop
                if duration_seconds is not None and (time.time() - start_wall) >= duration_seconds:
                    break

                deadline = base + n * dt
                now = time.perf_counter()
                delay = deadline - now
                if delay > 0:
                    # Sleep precisely to the deadline
                    await asyncio.sleep(delay)
                # If delay <= 0, we're late; skip sleeping and catch up by issuing now

                if self._stopping.is_set():
                    break

                # Issue exactly one request per tick
                sid = self._new_session_id()
                prompt = next(self.questions_cycle)
                asyncio.create_task(self._fire_one(sid, prompt))
                issued += 1
                self.global_seq_no += 1
                n += 1

                # Lightweight periodic report every ~1s without blocking pacing
                # now2 = time.perf_counter()
                # if now2 - last_report >= 1.0:
                #     self.logger.info(f"[RPS] target={self.rps} issued_total={issued} test-id={self.test_id}")  # keep minimal cost
                #     last_report = now2
        except asyncio.CancelledError:
            pass

def load_questions(path: str) -> List[str]:
    qs: List[str] = []
    if path.endswith(".jsonl"):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    q = obj.get("question") or obj.get("prompt") or obj.get("text")
                    if q:
                        qs.append(str(q))
                except Exception:
                    qs.append(line)
    else:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    qs.append(line)
    if not qs:
        qs = ["Explain Python asyncio with examples."]
    return qs

def load_config_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def compute_duration_seconds(cfg: Dict[str, Any]) -> Optional[int]:
    load_cfg = cfg.get("load", {})
    dur_s = load_cfg.get("duration_seconds")
    dur_h = load_cfg.get("duration_hours")
    if dur_s is not None:
        return int(dur_s)
    if dur_h is not None:
        return int(float(dur_h) * 3600)
    return None

async def amain():
    cfg_path = os.environ.get("CONFIG_YAML", "config.yaml")
    cfg = load_config_yaml(cfg_path)

    infer_endpoint = cfg.get("inference", {}).get("endpoint", "")
    request_timeout = int(cfg.get("inference", {}).get("request_timeout", 30))

    log_endpoint = cfg.get("logging", {}).get("dma_endpoint", "")
    tz_name = cfg.get("logging", {}).get("timezone", "Asia/Kolkata")

    rps = int(cfg.get("load", {}).get("rps", 5))
    duration_seconds = compute_duration_seconds(cfg)

    questions_file = cfg.get("dataset", {}).get("questions_file", "questions.jsonl")
    questions = load_questions(questions_file)

    concurrent_limit = int(cfg.get("runner", {}).get("concurrent_limit", 1000))
    test_id = cfg.get("runner", {}).get("test_id")
    session_prefix = cfg.get("runner", {}).get("session_prefix", "session_")

    client = FixedRPSClient(
        infer_endpoint=infer_endpoint,
        log_endpoint=log_endpoint,
        rps=rps,
        questions=questions,
        tz_name=tz_name,
        session_prefix=session_prefix,
        request_timeout=request_timeout,
        concurrent_limit=concurrent_limit,
        cfg=cfg,
    )

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _handle_stop():
        # signal handler runs in the loop’s thread
        try:
            client._stopping.set()  # let client.run() break its while loop
        except Exception:
            pass
        stop_event.set()            # release the main waiter

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_stop)
        except NotImplementedError:
            pass

    await client.start()
    run_task = asyncio.create_task(client.run(duration_seconds=duration_seconds))
    if duration_seconds is None:
        await stop_event.wait()
    try:
        await run_task
    finally:
        await client.stop()

def main():
    asyncio.run(amain())

if __name__ == "__main__":
    main()
