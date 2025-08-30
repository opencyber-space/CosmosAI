from prometheus_client import Counter, Gauge, Histogram, start_http_server
from prometheus_client.registry import REGISTRY
import os
import threading

import redis
import time
import json

from .block_metrics import BlockHardwareMetrics
from .node import detect_node_id


class AIOSMetrics:
    def __init__(self, block_id=None):
        self.block_id = block_id or os.getenv('BLOCK_ID', 'test-block')
        self.instance_id = os.getenv('INSTANCE_ID', 'instance-001')

        # Initialize Prometheus metrics
        self.metrics = {}
        self.stop_event = threading.Event()
        self.redis_client = redis.StrictRedis(host=os.getenv(
            "METRICS_REDIS_HOST", "localhost"), port=6379, db=0
        )

        self.block_hardware_metrics = BlockHardwareMetrics()

        self.node_id = detect_node_id()

    def register_counter(self, name, documentation, labelnames=None):
        if labelnames is None:
            labelnames = []
        self.metrics[name] = Counter(
            name, documentation, labelnames=labelnames, registry=REGISTRY)

    def register_gauge(self, name, documentation, labelnames=None):
        if labelnames is None:
            labelnames = []
        self.metrics[name] = Gauge(
            name, documentation, labelnames=labelnames, registry=REGISTRY)

    def register_histogram(self, name, documentation, labelnames=None, buckets=None):
        if labelnames is None:
            labelnames = []
        if buckets is None:
            buckets = [0.1, 0.2, 0.5, 1, 2, 5, 10]
        self.metrics[name] = Histogram(
            name, documentation, labelnames=labelnames, buckets=buckets, registry=REGISTRY)

    def increment_counter(self, name, labelnames=None):
        metric = self.metrics.get(name)
        if metric and isinstance(metric, Counter):
            metric.inc()

    def set_gauge(self, name, value, labelnames=None):
        metric = self.metrics.get(name)
        if metric and isinstance(metric, Gauge):
            metric.set(value)

    def observe_histogram(self, name, value, labelnames=None):
        metric = self.metrics.get(name)
        if metric and isinstance(metric, Histogram):
            metric.observe(value)

    def _get_labelnames(self, custom_labelnames=None):
        labelnames = {
            'blockID': self.block_id,
            'instanceID': self.instance_id,
            "nodeID": self.node_id
        }
        if custom_labelnames:
            labelnames.update(custom_labelnames)
        return labelnames

    def start_http_server(self, m_port=8000):
        def _run_server():
            port = int(os.getenv("METRICS_PORT", m_port))
            start_http_server(port)

            # Wait until stop_event is set
            self.stop_event.wait()

        # start redis writer:
        self.write_to_redis()

        # Create and start the server thread
        server_thread = threading.Thread(target=_run_server)
        server_thread.start()

    def write_to_redis(self):
        def _write_metrics():
            while not self.stop_event.is_set():
                metrics_data = {
                    "blockId": self.block_id,
                    "instanceId": self.instance_id,
                    "nodeId": self.node_id,
                    "type": "app",
                    "timestamp": time.time()
                }

                for name, metric in self.metrics.items():
                    samples = metric.collect()[0].samples

                    for sample in samples:
                        if "_created" in sample.name:
                            continue  # Skip created timestamps

                        metrics_data[sample.name] = sample.value

                metrics_data['hardware'] = self.block_hardware_metrics.get_metrics()

                try:
                    json_data = json.dumps(metrics_data)
                    self.redis_client.lpush('NODE_METRICS', json_data)
                except Exception as e:
                    print(f"Error pushing metrics to Redis: {e}")

                time.sleep(30)

        write_thread = threading.Thread(target=_write_metrics)
        write_thread.start()

