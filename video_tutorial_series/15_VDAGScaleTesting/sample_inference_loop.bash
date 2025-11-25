#!/bin/bash
# Repeated inference script: loop 100 times, send 4 requests per iteration
# Increments only currentSession after each request. currentSequence remains constant.

set -euo pipefail

# --- Configuration ---
session_start=${SESSION_START:-50}
sequence_start=${SEQUENCE_START:-48}
iterations=${ITERATIONS:-100}
sleep_between_requests=${SLEEP_SEC:-1}

currentSession=$session_start
currentSequence=$sequence_start

MESSAGES=(
  "write a one lines about photosynthesis"
  "write a one lines about color theory"
  "write a one lines about army"
  "write a one lines about sports"
)

ENDPOINT=${ENDPOINT:-"http://CLUSTER2MASTER:32527/v1/infer"}

# helper to pretty print JSON if jq is available
pretty_pipe() {
  if command -v jq >/dev/null 2>&1; then
    jq .
  else
    cat
  fi
}

echo "Starting: iterations=${iterations}, starting session=${currentSession}, seq=${currentSequence}"

for i in $(seq 1 "$iterations"); do
  echo "=== Iteration $i / $iterations ==="
  for msg in "${MESSAGES[@]}"; do
    # Build and send request (variables expand inside heredoc)
    curl -s -X POST "$ENDPOINT" \
      -H "Content-Type: application/json" \
      -d "$(cat <<EOF
{
  "timeout": 1200,
  "retries": 3,
  "session_id": "session${currentSession}",
  "seq_no": ${currentSequence},
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
    "message": "${msg}"
  },
  "graph": {},
  "selection_query": {}
}
EOF
)" | pretty_pipe &

    echo "Sent session=${currentSession} seq=${currentSequence} message='${msg}'"

    # increment only currentSession as requested
    currentSession=$((currentSession + 1))

    sleep "$sleep_between_requests"
  done
done

echo "All iterations done."
