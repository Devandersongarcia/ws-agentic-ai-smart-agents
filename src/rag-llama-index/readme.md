# RAG Preprocessing Pipeline with LlamaIndex

End-to-end RAG preprocessing pipeline for restaurant data using LlamaIndex with multi-collection Astra DB architecture. This pipeline handles document ingestion through vector database storage without any querying functionality.

## Features

- **Multi-Collection Architecture**: 4 specialized collections for different data types
- **Document Ingestion**: Support for PDF, JSON, CSV, and DOCX files  
- **Smart Preprocessing**: Text cleaning, normalization, and standardization
- **Semantic Chunking**: Intelligent splitting with content-aware chunking
- **Rich Metadata**: Automatic extraction of restaurant, cuisine, dietary info, and prices
- **Vector Database Storage**: Direct storage to Astra DB collections
- **Quality Assurance**: Built-in validation and document quality testing
- **Observability**: Optional Langfuse integration for tracing

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
```

3. Set up Astra DB:
- Create an Astra DB account
- Create a new database and get your token
- Update `.env` with your credentials
- The system will create 4 collections automatically:
  - `menus` (PDF menu content)
  - `restaurants` (JSON restaurant info)
  - `coupons` (CSV discounts/offers)
  - `allergens` (DOCX allergy information)

## Multi-Collection Architecture

### Data Sources & Collections
```
storage/
├── pdf/          → menus collection
├── json/         → restaurants collection  
├── csv/          → coupons collection
└── doc/          → allergens collection
```

### Collection Specializations
- **menus**: Menu items, dishes, prices (semantic food optimization)
- **restaurants**: Restaurant details, hours, contact info (structured optimization)
- **coupons**: Discounts, promotions, offers (promotional optimization)
- **allergens**: Critical allergy information (safety-critical optimization)

## Step-by-Step Execution Guide

### Step 1: Environment Setup

```bash
python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
```

### Step 2: Verify Data Sources

Ensure your data is properly organized in the storage directory:

```
storage/
├── pdf/          
├── json/         
├── csv/          
└── doc/          
```

### Step 3: Run Multi-Collection Preprocessing Pipeline (Recommended)

```bash
cd src/rag-llama-index
python preprocessor.py multi
```

**What happens:**
1. 📥 **Document Ingestion**: Loads all files from storage/
2. 🔄 **Document Transformation**: Cleans text and extracts metadata
3. ✂️ **Chunking**: Creates semantic chunks optimized for storage
4. 💾 **Multi-Collection Indexing**: Creates 4 specialized collections in Astra DB

### Step 4: Run Single-Collection Preprocessing Pipeline (Alternative)

```bash
python preprocessor.py single
```

**What happens:**
1. 📥 **Document Ingestion**: Loads all files from storage/
2. 🔄 **Document Transformation**: Cleans text and extracts metadata
3. ✂️ **Chunking**: Creates semantic chunks
4. 💾 **Single Collection Indexing**: Stores everything in one collection

### Step 5: Monitor Results

Pipeline results are automatically saved to `output/` directory:

```
output/
├── preprocessing_results_20250810_143022.json    
└── preprocessing_traces_20250810_143022.json     
```

## Pipeline Steps

1. **Document Ingestion**: Loads files from `storage/` directory
2. **Preprocessing**: Cleans text, normalizes sections, standardizes currency
3. **Chunking**: Splits into semantic chunks (1 dish or section per chunk)
4. **Metadata Generation**: Adds restaurant, cuisine, dietary labels, prices
5. **Embedding**: Converts text to vectors using text-embedding-3-small
6. **Indexing**: Stores in Astra vector database collections

## Output

Pipeline results are saved to `output/` directory:
- `preprocessing_results_*.json`: Execution statistics and collection information
- `preprocessing_traces_*.json`: Detailed execution traces (if enabled)

## Directory Structure

```
src/rag-llama-index/
├── config.py           
├── ingestion.py        
├── transformer.py      
├── chunking.py         
├── indexer.py          
├── quality.py          
├── preprocessor.py     
├── requirements.txt    
└── .env.example        
```

## Multi-Collection Benefits

### 🎯 **Specialized Storage**
- Menu documents optimized for food similarity vectors
- Restaurant documents optimized for location/metadata vectors
- Coupon documents optimized for promotional content vectors
- Allergen documents optimized for safety-critical vectors

### 🔒 **Safety-Critical Separation**
- Allergen data isolated in dedicated collection
- Specialized metadata enrichment for safety information
- Clear separation of concerns for different data types

### ⚡ **Performance**
- Targeted indexing strategies per data type
- Reduced vector space per collection for better performance
- Collection-specific optimization strategies during preprocessing

### 🔧 **Maintenance**
- Independent preprocessing per data source
- Specialized transformation pipelines per collection
- Different metadata schemas per collection type

## Quality Metrics

The preprocessing pipeline tracks:
- Document ingestion statistics by type and source
- Transformation success rates and metadata completeness
- Chunk quality metrics (size, distribution, semantic coherence)
- Indexing success rates per collection
- Processing performance and execution times

## Configuration

Key configuration options in `config.py`:
- Astra DB connection settings
- OpenAI API configuration
- Embedding model settings (text-embedding-3-small, 1536 dimensions)
- Chunk size and overlap parameters
- Collection names and mappings
- Langfuse tracing configuration