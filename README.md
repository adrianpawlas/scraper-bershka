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
   python run_scraper.py
   ```

   Or run directly:
   ```bash
   python bershka_scraper.py
   ```

3. **Test the Scraper**:
   ```bash
   python test_scraper.py
   ```

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
