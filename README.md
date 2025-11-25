# Bershka Fashion Scraper

A comprehensive scraper for Bershka fashion products that extracts product information, generates image embeddings using Google's SigLIP model, and stores everything in a Supabase database.

## Features

- **Complete Product Catalog**: Scrapes all products from Bershka's men's and women's categories (thousands of products)
- **Two-Step API Approach**: First fetches ALL product IDs, then batch-fetches product details
- **Image Embeddings**: Generates 768-dimensional embeddings using `google/siglip-base-patch16-384`
- **Supabase Integration**: Stores all data in PostgreSQL with vector support
- **Local File Support**: Can load product IDs from local JSON files when API is blocked
- **Modular Architecture**: Clean separation of concerns with YAML configuration

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Set Environment Variables
Create a `.env` file:
```
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

### 3. Capture Category Data (Required)
Since Bershka's API blocks direct requests, you need to capture category JSON files from your browser.
See `CAPTURE_INSTRUCTIONS.md` for detailed steps.

Save files to `category_data/` folder:
- `category_data/1010834564.json` (men's all)
- `category_data/1010193212.json` (women's jackets)
- etc.

### 4. Run the Scraper
```bash
python -m cli              # Full scrape
python -m cli --limit 10   # Test with 10 products
```

## How It Works

### Two-Step Approach
1. **Step 1**: Load ALL product IDs from category endpoint (e.g., 888 for men's category)
   - Source: Local JSON files in `category_data/` or API
   
2. **Step 2**: Fetch product details in batches of 50
   - Uses `productsArray` endpoint with product IDs

### Data Flow
```
category_data/*.json → Product IDs → Batch API calls → Transform → Embeddings → Supabase
```

## Categories Scraped

| Category | ID | Gender |
|----------|-----|--------|
| Men's All | 1010834564 | MAN |
| Jackets & Trench | 1010193212 | WOMAN |
| Coats | 1010240019 | WOMAN |
| Jeans | 1010276029 | WOMAN |
| Pants | 1010193216 | WOMAN |
| Dresses & Jumpsuit | 1010193213 | WOMAN |
| Sweaters & Cardigans | 1010193223 | WOMAN |
| Sweatshirts & Hoodies | 1010193222 | WOMAN |
| Tops & Bodysuits | 1010193220 | WOMAN |
| T-Shirts | 1010193217 | WOMAN |
| Shirts & Blouses | 1010193221 | WOMAN |
| Skirts | 1010280023 | WOMAN |
| Shorts & Jorts | 1010194517 | WOMAN |
| Matching Sets | 1010429555 | WOMAN |
| Swimwear | 1010361506 | WOMAN |
| Shoes | 1010193192 | WOMAN |
| Bags | 1010193138 | WOMAN |
| Accessories | 1010193134 | WOMAN |

## Project Structure

```
├── cli.py              # Main entry point
├── api_ingestor.py     # API data extraction with JMESPath
├── transform.py        # Data transformation to Supabase schema
├── embeddings.py       # Image embedding generation (SigLIP)
├── http_client.py      # HTTP client with session management
├── db.py               # Supabase database operations
├── config.py           # Configuration management
├── sites.yaml          # Site-specific configurations
├── category_data/      # Local JSON files with product IDs (not in git)
└── CAPTURE_INSTRUCTIONS.md  # How to capture category data
```

## GitHub Actions

The scraper includes a manual GitHub Actions workflow:

### Setup Required
Add these secrets to your repository (Settings → Secrets → Actions):
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon key

### Running
1. Go to Actions → "Scrape Bershka Products"
2. Click "Run workflow"
3. Choose "full" or "test" mode

**Note**: The workflow is manual-only since API URLs change frequently.

## Database Schema

```sql
create table public.products (
  id text not null,
  source text null,
  product_url text null,
  image_url text not null,
  brand text null,
  title text not null,
  description text null,
  category text null,
  gender text null,
  price double precision null,
  currency text null,
  created_at timestamp with time zone null default now(),
  metadata text null,
  second_hand boolean null default false,
  embedding public.vector null,
  constraint products_pkey primary key (id),
  constraint products_source_product_url_key unique (source, product_url)
);
```

## Output Fields

Each product record includes:
- **id**: Unique product identifier
- **source**: "scraper"
- **brand**: "Bershka"
- **product_url**: Full product URL
- **image_url**: Product image URL
- **title**: Product name
- **gender**: "MAN" or "WOMAN"
- **category**: "footwear", "accessory", or null (for clothing)
- **price**: Price value (e.g., 45.9)
- **currency**: "EUR"
- **second_hand**: false
- **embedding**: 768-dimensional vector
- **created_at**: Timestamp

## Troubleshooting

### API Returns 403
The API blocks direct requests. Capture category JSON files from your browser using the instructions in `CAPTURE_INSTRUCTIONS.md`.

### Missing Products
Make sure all category JSON files are in `category_data/` folder. Check `CAPTURE_INSTRUCTIONS.md` for the full list of URLs.

### Embedding Errors
Some products have video URLs instead of images. These are automatically skipped.
