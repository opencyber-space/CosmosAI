#!/bin/bash
PORT=${1:-5000}

# Install dependencies
pip install -r requirements.txt

# Run Gunicorn
# -w 4: 4 worker processes
# -k gevent: Use gevent for async handling (CRITICAL for high RPS)
# --worker-connections 1000: Max simultaneous connections per worker
gunicorn -w 4 -k gevent --worker-connections 1000 --access-logfile - -b 0.0.0.0:${PORT} app:app