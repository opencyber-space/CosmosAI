# LLM Load Testing Framework

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

1. Update `config.yaml` with your block URLs and configurations
2. run the setting up of environment as per your needs: 
   ```bash
   bash setup_timescaledb_env.sh
   ```

## Running Tests

```bash
# Run with default config
python vdag_load_test.py
```

## Key Features
- **Create Virtual DAGs**: Define workflows with multiple LLM blocks 
- **Session Management**: Each request is treated as a new session
- **Database Logging**: Metrics logging to TimescaleDB
- **Timezone Support**: All timestamps converted to IST
- **Streamlit based Dashboard**: Real-time monitoring of load tests

## Customization

All parameters are configurable via `config.yaml`:
- Test duration and intervals