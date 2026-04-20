#!/bin/bash
# 1. Download the latest k6 archive (AMD64)
wget https://github.com/grafana/k6/releases/download/v0.50.0/k6-v0.50.0-linux-amd64.tar.gz

# 2. Extract it
tar -xvzf k6-v0.50.0-linux-amd64.tar.gz

# 3. Move it to your path so you can run 'k6' from anywhere
sudo mv k6-v0.50.0-linux-amd64/k6 /usr/local/bin/

# 4. Verify it works
k6 version