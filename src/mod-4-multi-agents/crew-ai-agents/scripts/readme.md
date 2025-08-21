# Scripts

## Purpose
Utility scripts for system setup, data ingestion, validation, and maintenance. These scripts provide command-line interfaces for managing the multi-agent system.

## Architecture
Scripts are designed to be run independently and follow a consistent pattern:
- Rich console output for better user experience
- Error handling and validation
- Progress tracking for long-running operations
- Clear success/failure indicators

## Available Scripts

### `validate_environment.py`
Validates that all required environment variables and dependencies are configured correctly.

```bash
python scripts/validate_environment.py
```

**Checks:**
- Python version (3.9+)
- Environment variables
- Package installations
- Data file existence
- Service connectivity

### `setup_database.py`
Initializes Supabase database with pgvector extension and creates necessary collections.

```bash
python scripts/setup_database.py
```

**Creates:**
- Vector collections for menus, restaurants, coupons, allergens
- Restaurant table for structured queries
- Necessary indexes for performance

### `ingest_data.py`
Processes all data files and stores them in Supabase with embeddings.

```bash
python scripts/ingest_data.py
```

**Processes:**
- PDF files (restaurant menus)
- JSON files (restaurant data)
- CSV files (coupons)
- DOCX files (allergen guidelines)

**Features:**
- Progress tracking
- Cost estimation
- Error reporting
- Validation after completion

### `benchmark.py` (Coming Soon)
Performance benchmarking for vector search and agent responses.

```bash
python scripts/benchmark.py
```

## Usage Workflow

The typical setup workflow:

1. **Validate Environment**
   ```bash
   python scripts/validate_environment.py
   ```
   Ensure all dependencies and credentials are configured.

2. **Setup Database**
   ```bash
   python scripts/setup_database.py
   ```
   Initialize Supabase collections and tables.

3. **Ingest Data**
   ```bash
   python scripts/ingest_data.py
   ```
   Process and store all restaurant data.

4. **Run Main Application**
   ```bash
   python main.py
   ```
   Start the multi-agent system.

## Error Handling

All scripts include comprehensive error handling:
- Clear error messages
- Suggested fixes
- Non-zero exit codes on failure
- Stack traces in debug mode

## Output Format

Scripts use Rich library for formatted output:
- ✓ Success indicators
- ✗ Error indicators
- ⚠ Warning indicators
- Progress bars for long operations
- Formatted tables for statistics
- Colored output for clarity

## Configuration

Scripts read configuration from:
- `.env` file in project root
- `config/settings.py` for defaults
- Command-line arguments (where applicable)

## Testing

Test scripts functionality:
```bash
python -c "from scripts.validate_environment import EnvironmentValidator"
python -c "from scripts.setup_database import setup_database"
python -c "from scripts.ingest_data import ingest_data"
```

## Dependencies
- `rich>=13.7.0` - Terminal formatting
- `click>=8.1.0` - CLI interface (future)
- All dependencies from main application