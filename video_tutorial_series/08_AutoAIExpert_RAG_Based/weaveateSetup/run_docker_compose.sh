#!/bin/bash

PWD="$(pwd)"


# Navigate to the docker directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Script is located at: $SCRIPT_DIR"

cd "$SCRIPT_DIR"
# Run docker-compose to start the services
docker compose up -d

cd ${PWD}