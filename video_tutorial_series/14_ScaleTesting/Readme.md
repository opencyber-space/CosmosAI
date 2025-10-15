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
3. Adjust usage patterns and crowd patterns according to your needs

## Running Tests

```bash
# Run with default config
python crowd.py

# Run with custom config
python crowd.py custom_config.yaml

# Run unit tests
pytest test_load_testing.py -v
```

## Key Features

- **Configurable Load Patterns**: Simulate real user behavior with hourly activity patterns
- **Multiple Blocks Support**: Test multiple LLM endpoints simultaneously  
- **Session Management**: Each user maintains multiple chat sessions
- **Database Logging**: Optional logging to GCP Firestore
- **Health Monitoring**: Automatic user restart on failures
- **Timezone Support**: All timestamps converted to IST
- **Comprehensive Testing**: Full pytest suite included

## Customization

All parameters are configurable via `config.yaml`:
- Block URLs and generation configs
- User behavior patterns
- Crowd size patterns  
- Database settings
- Test duration and intervals