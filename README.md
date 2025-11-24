# Bershka Fashion Scraper ✅ PRODUCTION READY

A comprehensive scraper for Bershka fashion products that extracts product information, generates image embeddings using Google's SigLIP model, and stores everything in a Supabase database.

## ✅ **STATUS: FULLY FUNCTIONAL**

- **✅ API Integration**: Successfully connected to Bershka's REST API
- **✅ Product Extraction**: Extracts all required fields (source, brand, embedding, product_url, image_url, title, gender, category, price, currency, second_hand, metadata, created_at)
- **✅ Image Processing**: Downloads and processes product images
- **✅ Embedding Generation**: Uses `google/siglip-base-patch16-384` for 768-dim embeddings
- **✅ Database Integration**: Stores data in Supabase with proper formatting
- **✅ Error Handling**: Comprehensive logging and graceful failure handling
- **✅ Production Ready**: Tested and working with real data

## 📊 **Latest Test Results**
- **32 products** successfully extracted from men's category
- **All required fields** properly formatted
- **Image URLs** working correctly
- **Database schema** compatible

## Features

- **Complete Product Catalog**: Scrapes all products from Bershka's men's and women's categories
- **Rich Product Data**: Extracts titles, descriptions, prices, sizes, categories, and comprehensive metadata
- **Image Embeddings**: Generates 768-dimensional embeddings using `google/siglip-base-patch16-384`
- **Supabase Integration**: Stores all data in a PostgreSQL database with vector support
- **Modular Architecture**: Inspired by production Zara scraper with separate concerns
- **JMESPath Data Extraction**: Robust JSON parsing with fallback expressions
- **Polite HTTP Client**: Respects robots.txt and implements request delays
- **YAML Configuration**: Easily configurable for different sites and APIs
- **Async Processing**: Concurrent processing for efficient scraping and embedding generation
- **Error Handling**: Comprehensive logging and graceful failure handling

## Database Schema

The scraper expects a Supabase table `products` with the following structure:

```sql
create table public.products (
  id text not null,
  source text null,
  product_url text null,
  affiliate_url text null,
  image_url text not null,
  brand text null,
  title text not null,
  description text null,
  category text null,
  gender text null,
  price double precision null,
  currency text null,
  search_tsv tsvector null,
  created_at timestamp with time zone null default now(),
  metadata text null,
  size text null,
  second_hand boolean null default false,
  embedding public.vector null,
  constraint products_pkey primary key (id),
  constraint products_source_product_url_key unique (source, product_url)
) TABLESPACE pg_default;
```

## 🚀 **Quick Start**

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Scraper**:
   ```bash
   python cli.py
   ```

   Or with options:
   ```bash
   python cli.py --limit 100  # Test with 100 products
   python cli.py --help       # See all options
   ```

3. **Test Individual Components**:
   ```bash
   python test_limited.py     # Test with 10 products
   python test_scraper.py     # Test original scraper
   ```

## 🏗️ **Architecture**

The scraper uses a modular, production-ready architecture inspired by enterprise scraping systems:

```
├── cli.py              # Command-line interface and main runner
├── api_ingestor.py     # API data extraction with JMESPath
├── transform.py        # Data transformation to Supabase schema
├── embeddings.py       # Image embedding generation (SigLIP)
├── http_client.py      # Polite HTTP client with robots.txt support
├── db.py              # Supabase database operations
├── config.py          # Configuration management
├── sites.yaml         # Site-specific configurations
└── bershka_scraper.py # Legacy single-file scraper (for reference)
```

### **Key Components:**

- **CLI Interface**: `python cli.py --limit 100` for testing
- **API Ingestor**: Uses JMESPath for robust JSON data extraction
- **Data Transform**: Maps API responses to your Supabase schema
- **Embedding Service**: Generates 768-dim SigLIP image embeddings
- **HTTP Client**: Polite requests with robots.txt compliance
- **Database Layer**: Optimized Supabase operations with deduplication

## 🤖 **GitHub Actions Automation**

The scraper includes automated daily runs via GitHub Actions:

### **Daily Schedule**
- **Runs automatically** every day at midnight UTC
- **12-hour timeout** to prevent runaway processes
- **Full scrape** by default

### **Manual Runs**
- Go to GitHub repository → Actions → "Scrape Bershka Products"
- Click "Run workflow" to trigger manually
- Choose between "full" or "test" mode

### **GitHub Setup Required**

#### **Repository Secrets** (Settings → Secrets and variables → Actions):
```
SUPABASE_URL = your_supabase_project_url
SUPABASE_KEY = your_supabase_anon_key
```

#### **Repository Variables** (Settings → Secrets and variables → Actions → Variables):
```
BATCH_SIZE = 50          # Optional, defaults to 50
MAX_WORKERS = 5          # Optional, defaults to 5
```

### **Workflow Features**
- ✅ **Automatic execution** at midnight UTC daily
- ✅ **Manual trigger** option
- ✅ **Test mode** for quick validation
- ✅ **Log upload** on failures for debugging
- ✅ **12-hour timeout** protection
- ✅ **Dependency caching** for faster runs

## Configuration

### Categories Scraped

**Men's Categories**:
- All men's products

**Women's Categories**:
- Jackets & Trench
- Coats
- Jeans
- Pants
- Dresses & Jumpsuit
- Sweaters & Cardigans
- Sweatshirts & Hoodies
- Tops & Bodysuits
- T-Shirts
- Shirts & Blouses
- Skirts
- Shorts & Jorts
- Matching Sets
- Swimwear
- Shoes
- Bags & Coin Purses
- Accessories

### Processing Configuration

- **BATCH_SIZE**: Number of products to process simultaneously (default: 50)
- **MAX_WORKERS**: Maximum concurrent workers for image processing (default: 5)
- **Embedding Model**: `google/siglip-base-patch16-384` (768-dimensional)

## API Information

The scraper uses Bershka's internal REST API:
- Base URL: `https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549`
- Returns JSON data with complete product information including images, pricing, and metadata

## Output

Each product record includes:
- **Basic Info**: ID, URL, title, description, brand
- **Categorization**: Category, gender, sizes
- **Pricing**: Price and currency
- **Media**: High-quality product images
- **Embeddings**: 768-dimensional vector representations for similarity search
- **Metadata**: JSON object with additional product details (composition, certifications, etc.)

## Logging

All operations are logged to both console and `bershka_scraper.log` with timestamps and severity levels.

## Error Handling

- Network request failures are logged and skipped
- Image processing errors are handled gracefully
- Database insertion errors are logged with details
- Partial failures don't stop the entire scraping process

## Performance Notes

- Image embeddings are generated concurrently using a thread pool
- API requests are made asynchronously
- Products are inserted in batches for efficiency
- Progress is logged regularly for monitoring

## Dependencies

- `requests/aiohttp`: HTTP client for API calls
- `supabase`: Database client
- `transformers`: Hugging Face models
- `torch`: PyTorch for model inference
- `Pillow`: Image processing
- `tqdm`: Progress bars
- `python-dotenv`: Environment variable management
