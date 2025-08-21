#!/bin/bash
#How To Run
#bash weaveateSetup/create_folders.sh

# Navigate to the docker directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Script is located at: $SCRIPT_DIR"

# Create necessary directories
mkdir -p $SCRIPT_DIR/weaviate_data