#!/bin/bash
# Run the Streamlit response time visualization app
export TIMESCALEDB_HOST=${TIMESCALEDB_HOST:-x.x.x.x}
export TIMESCALEDB_PASSWORD=${TIMESCALEDB_PASSWORD:-abcxyz}

streamlit run streamlit_visualize_response_time.py
