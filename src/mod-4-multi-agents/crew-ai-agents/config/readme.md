# Configuration Module

## Purpose
Centralized configuration management for the Restaurant Recommendation Multi-Agent System. Provides type-safe settings loading from environment variables with validation and default values.

## Architecture
This module uses Pydantic Settings to:
- Load configuration from `.env` files
- Validate all settings at startup
- Provide type hints for IDE support
- Ensure required settings are present
- Create necessary directories automatically

## Key Classes

- `Settings`: Main configuration class with all application settings
- `get_settings()`: Cached function to retrieve settings singleton

## Usage Example

```python
from config import get_settings

settings = get_settings()

api_key = settings.openai_api_key
model = settings.openai_model_name
supabase_url = settings.supabase_url

storage_path = settings.get_absolute_storage_path()
```

## Configuration Categories

### Core Services
- **OpenAI**: API keys, models, embedding settings
- **Supabase**: URLs, keys, collection names
- **Langfuse**: Observability configuration
- **CrewAI**: Framework settings

### Agent Configuration
- **Concierge**: Role, goals, retry settings
- **Dietary Specialist**: Safety settings, strict mode
- **Promotions Manager**: Discount thresholds

### Pipeline Settings
- **Ingestion**: Batch sizes, chunking parameters
- **Docling**: GPU usage, OCR settings

### Application Settings
- **Environment**: Development/production modes
- **Logging**: Levels and formats
- **Paths**: Storage, output, cache directories
- **Rate Limiting**: Request and token limits
- **Caching**: TTL and storage types

## Environment Variables

All settings are loaded from environment variables. See `.env.example` for complete list.

Key required variables:
- `OPENAI_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_DB_URL`
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`

## Validation

The Settings class includes validators for:
- Temperature ranges (0-2)
- Log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Path resolution (converts relative to absolute)
- Required field presence

## Testing

Run configuration tests:
```bash
pytest config/test_config.py -v
```

## Dependencies
- `pydantic>=2.7.0`
- `pydantic-settings>=2.3.0`
- `python-dotenv>=1.0.0`