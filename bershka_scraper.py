#!/usr/bin/env python3
"""
Bershka Fashion Scraper
Scrapes all products from Bershka, generates embeddings, and stores in Supabase.
"""

import asyncio
import io
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional, Any, Tuple
from urllib.parse import urljoin

import aiohttp
import requests
import torch
from PIL import Image
from supabase import create_client, Client
from transformers import AutoProcessor, AutoModel
from tqdm.asyncio import tqdm
import psycopg2
from psycopg2.extras import execute_values

from config import (
    SUPABASE_URL, SUPABASE_KEY, BERSHKA_BASE_URL, BERSHKA_APP_ID,
    BERSHKA_LANGUAGE_ID, BERSHKA_LOCALE, BATCH_SIZE, MAX_WORKERS,
    EMBEDDING_MODEL, CATEGORY_IDS, GENDER_MAPPING, CATEGORY_CLASSIFICATION,
    PRODUCT_LIMIT, CATEGORY_URLS
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bershka_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BershkaScraper:
    """Main scraper class for Bershka products."""

    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.session: Optional[aiohttp.ClientSession] = None
        self.processor = None
        self.model = None
        self.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

        # Initialize the embedding model
        self._init_embedding_model()

    def load_categories_from_file(self, filepath: str = "bershka_categories.txt") -> Dict[str, str]:
        """Load category IDs from a text file and look up their URLs from config.

        File format:
        category_id (one per line)
        Lines starting with # are comments and ignored.

        Returns:
            Dict mapping category_id to URL (looked up from CATEGORY_URLS in config)
        """
        categories = {}

        if not os.path.exists(filepath):
            logger.warning(f"Category file {filepath} not found, using empty categories")
            return categories

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue

                    category_id = line.strip()
                    if not category_id:
                        continue

                    # Look up the URL for this category ID from config
                    if category_id in CATEGORY_URLS:
                        url = CATEGORY_URLS[category_id]
                        categories[category_id] = url
                        logger.debug(f"Loaded category {category_id}: {url}")
                    else:
                        logger.warning(f"Category ID {category_id} not found in CATEGORY_URLS config")

            logger.info(f"Loaded {len(categories)} categories from {filepath}")
            return categories

        except Exception as e:
            logger.error(f"Error loading categories from {filepath}: {e}")
            return {}

    async def fetch_products_from_url(self, category_url: str) -> List[Dict[str, Any]]:
        """Fetch full product data directly from a category URL."""
        try:
            async with self.session.get(category_url) as response:
                if response.status == 200:
                    data = await response.json()
                    products = data.get('products', [])
                    logger.info(f"Fetched {len(products)} products from category URL")
                    return products
                else:
                    logger.warning(f"Failed to fetch products from {category_url}: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching products from {category_url}: {e}")
            return []

    def _init_embedding_model(self):
        """Initialize the SigLIP model for image embeddings."""
        try:
            logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
            self.processor = AutoProcessor.from_pretrained(EMBEDDING_MODEL)
            self.model = AutoModel.from_pretrained(EMBEDDING_MODEL)
            self.model.eval()
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-GB,en;q=0.9',
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
        self.executor.shutdown(wait=True)

    def build_api_url(self, category_id: int, product_ids: List[int] = None, page: int = None) -> str:
        """Build the Bershka API URL for a category and optionally product IDs."""
        url = (
            f"{BERSHKA_BASE_URL}/productsArray?"
            f"categoryId={category_id}&"
            f"appId={BERSHKA_APP_ID}&"
            f"languageId={BERSHKA_LANGUAGE_ID}&"
            f"locale={BERSHKA_LOCALE}"
        )

        if product_ids:
            product_ids_str = '%2C'.join(map(str, product_ids))
            url += f"&productIds={product_ids_str}"

        if page is not None:
            url += f"&page={page}"

        return url

    async def fetch_products_batch(self, category_id: int, product_ids: List[int] = None, page: int = None) -> Dict[str, Any]:
        """Fetch a batch of products from the Bershka API."""
        url = self.build_api_url(category_id, product_ids, page)

        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    products = data.get('products', [])
                    logger.info(f"API returned {len(products)} products for category {category_id} (page {page or 0})")
                    return data
                else:
                    logger.warning(f"API request failed: {response.status} - {url}")
                    return {"products": []}
        except Exception as e:
            logger.error(f"Error fetching products: {e} - {url}")
            return {"products": []}

    def extract_product_info(self, product: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract product information from the API response."""
        products_data = []

        # Handle bundle products (products with multiple colors/variants)
        if product.get('bundleProductSummaries'):
            for variant in product['bundleProductSummaries']:
                if variant.get('detail'):
                    colors = variant['detail'].get('colors', [])
                    if not colors:
                        continue

                    for color in colors:
                        try:
                            product_data = self._extract_single_product(product, variant, color)
                            if product_data:
                                products_data.append(product_data)
                        except Exception as e:
                            logger.error(f"Error extracting product: {e}")
                            continue
        else:
            # Handle single products
            if product.get('detail', {}).get('colors'):
                for color in product['detail']['colors']:
                    product_data = self._extract_single_product(product, product, color)
                    if product_data:
                        products_data.append(product_data)

        logger.debug(f"Extracted {len(products_data)} products from {product.get('id')}")
        return products_data

    def _extract_single_product(self, bundle_product: Dict, variant: Dict, color: Dict) -> Optional[Dict[str, Any]]:
        """Extract information for a single product variant."""
        try:
            # Get the best image URL from the variant's xmedia
            image_url = self._get_best_image_url(variant)

            if not image_url:
                return None

            # Extract basic information
            product_id = f"{color['reference']}-{color['id']}"
            title = bundle_product.get('nameEn', bundle_product.get('name', ''))
            description = variant.get('detail', {}).get('longDescription', '')

            # Extract category information
            category = self._extract_category(bundle_product)

            # Extract gender
            gender = GENDER_MAPPING.get(variant.get('sectionNameEN', ''), 'unisex')

            # Extract pricing (use the first available size's price)
            price = None
            currency = 'EUR'  # Bershka uses EUR
            if color.get('sizes') and len(color['sizes']) > 0:
                first_size = color['sizes'][0]
                price_str = first_size.get('price', '')
                if price_str:
                    try:
                        # Convert cents to decimal (e.g., 9990 -> 99.90)
                        price_cents = int(price_str)
                        price = float(price_cents) / 100
                    except (ValueError, TypeError):
                        logger.warning(f"Could not parse price: {price_str}")
                        price = None

            # Extract size information
            sizes = [size['name'] for size in color.get('sizes', []) if size.get('isBuyable')]

            # Build product URL
            product_url = f"https://www.bershka.com/en/{variant.get('productUrl', '')}.html"

            # Create comprehensive metadata
            metadata = {
                'reference': color.get('reference', ''),
                'display_reference': color.get('displayReference', ''),
                'color_name': color.get('name', ''),
                'color_id': color['id'],
                'sizes': sizes,
                'availability_date': variant.get('availabilityDate', ''),
                'family_info': variant.get('detail', {}).get('familyInfo', {}),
                'subfamily_info': variant.get('detail', {}).get('subfamilyInfo', {}),
                'certified_materials': color.get('certifiedMaterials', {}),
                'composition': color.get('composition', []),
                'composition_by_zone': color.get('compositionByZone', []),
                'care_instructions': color.get('care', []),
                'sustainability': color.get('sustainability', {}),
                'traceability': color.get('traceability', {}),
                'country_of_origin': color.get('country', ''),
                'weight': first_size.get('weight', '') if color.get('sizes') and len(color['sizes']) > 0 else '',
                'bundle_colors': bundle_product.get('bundleColors', []),
                'related_categories': bundle_product.get('relatedCategories', []),
                'tags': bundle_product.get('tags', []),
                'attributes': bundle_product.get('attributes', []),
            }

            return {
                'id': product_id,
                'source': 'scraper',
                'product_url': product_url,
                'affiliate_url': None,
                'image_url': image_url,
                'brand': 'Bershka',
                'title': title,
                'description': description,
                'category': self._classify_category(bundle_product),
                'gender': gender,
                'price': price,
                'currency': currency,
                'metadata': json.dumps(metadata),
                'size': ', '.join(sizes) if sizes else None,
                'second_hand': False,
                'created_at': None,  # Will be set by database default
                'embedding': None,  # Will be added later
            }

        except Exception as e:
            logger.error(f"Error extracting product info: {e}")
            return None

    def _get_best_image_url(self, variant: Dict) -> Optional[str]:
        """Get the best quality image URL from variant data, only using images with originalName 's1'."""
        try:
            variant_detail = variant.get('detail', {})
            if not variant_detail:
                return None

            xmedia = variant_detail.get('xmedia', [])
            if not xmedia:
                return None

            # Look for product images with originalName 's1'
            for xmedia_item in xmedia:
                for item in xmedia_item.get('xmediaItems', []):
                    # Check if this item has originalName 's1'
                    if item.get('originalName') == 's1':
                        medias = item.get('medias', [])
                        if medias:
                            # Get the first media URL (usually highest quality)
                            media = medias[0]
                            url = media.get('url', '')
                            if url.startswith('//'):
                                url = 'https:' + url
                            elif url.startswith('/'):
                                url = 'https://static.bershka.net' + url
                            return url

            return None

        except Exception as e:
            logger.error(f"Error extracting image URL: {e}")
            return None

    def _extract_category(self, product: Dict) -> str:
        """Extract category information from product data."""
        try:
            categories = []
            for cat in product.get('relatedCategories', []):
                if cat.get('name'):
                    categories.append(cat['name'])

            return ', '.join(categories) if categories else 'Unknown'

        except Exception as e:
            logger.error(f"Error extracting category: {e}")
            return 'Unknown'

    def _classify_category(self, product: Dict) -> Optional[str]:
        """Classify category as accessory, footwear, or None for clothing."""
        try:
            # Find the category key from our configuration
            for gender_key, categories in CATEGORY_IDS.items():
                for category_key, category_id in categories.items():
                    # Check if this product belongs to a classified category
                    if CATEGORY_CLASSIFICATION.get(category_key):
                        # Check if the product's related categories contain this category
                        for related_cat in product.get('relatedCategories', []):
                            if related_cat.get('id') == category_id:
                                return CATEGORY_CLASSIFICATION[category_key]

            # If not found in classified categories, return None (clothing)
            return None

        except Exception as e:
            logger.error(f"Error classifying category: {e}")
            return None

    async def generate_embedding(self, image_url: str) -> Optional[List[float]]:
        """Generate 768-dim embedding for an image URL."""
        try:
            # Download image
            async with self.session.get(image_url) as response:
                if response.status != 200:
                    return None

                image_data = await response.read()

            # Process image in thread pool
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                self.executor,
                self._process_image_embedding,
                image_data
            )

            return embedding

        except Exception as e:
            logger.error(f"Error generating embedding for {image_url}: {e}")
            return None

    def _process_image_embedding(self, image_data: bytes) -> Optional[List[float]]:
        """Process image and generate embedding (runs in thread pool)."""
        try:
            # Open image
            image = Image.open(io.BytesIO(image_data)).convert('RGB')

            # Process with SigLIP - need both image and text inputs
            inputs = self.processor(
                images=image,
                text=[""],  # Empty text input
                return_tensors="pt",
                padding=True
            )

            with torch.no_grad():
                outputs = self.model(**inputs)

            # Get the image embeddings (768-dim)
            if hasattr(outputs, 'image_embeds'):
                embedding = outputs.image_embeds.squeeze().tolist()
            else:
                # Fallback: try pooler_output or last_hidden_state
                if hasattr(outputs, 'pooler_output'):
                    embedding = outputs.pooler_output.squeeze().tolist()
                elif hasattr(outputs, 'last_hidden_state'):
                    embedding = outputs.last_hidden_state.mean(dim=1).squeeze().tolist()
                else:
                    logger.error("No suitable embedding output found")
                    return None

            # Ensure it's a list of floats
            if isinstance(embedding, float):
                return [embedding]
            elif isinstance(embedding, list):
                return embedding
            else:
                # Convert numpy array or tensor to list
                return embedding.tolist()

        except Exception as e:
            logger.error(f"Error processing image embedding: {e}")
            return None

    async def scrape_category(self, category_name: str, category_id: str, category_url: str = None) -> List[Dict[str, Any]]:
        """Scrape all products from a specific category using the category URL."""
        logger.info(f"Starting to scrape category: {category_name} (ID: {category_id})")

        if not category_url:
            logger.warning(f"No category URL provided for {category_name}")
            return []

        # Fetch products directly from the category URL
        products_data = await self.fetch_products_from_url(category_url)

        all_products = []
        for product in products_data:
            product_data = self.extract_product_info(product)
            all_products.extend(product_data)

            # Respect product limit during extraction
            if PRODUCT_LIMIT > 0 and len(all_products) >= PRODUCT_LIMIT:
                break

        logger.info(f"Found {len(all_products)} products in category {category_name}")
        return all_products

    async def process_products_batch(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a batch of products: generate embeddings and prepare for database."""
        processed_products = []

        for product in products:
            # Generate embedding
            if product['image_url']:
                embedding = await self.generate_embedding(product['image_url'])
                if embedding:
                    product['embedding'] = embedding
                    processed_products.append(product)

        return processed_products

    async def save_to_supabase(self, products: List[Dict[str, Any]]) -> int:
        """Save products to Supabase database."""
        try:
            # Convert embeddings to proper format for Supabase vector
            for product in products:
                if product.get('embedding'):
                    product['embedding'] = f"[{', '.join(map(str, product['embedding']))}]"

            # Insert in batches
            batch_size = 100
            inserted_count = 0

            for i in range(0, len(products), batch_size):
                batch = products[i:i + batch_size]

                result = self.supabase.table('products').upsert(
                    batch,
                    on_conflict='source,product_url'
                ).execute()

                inserted_count += len(result.data) if result.data else 0

            logger.info(f"Inserted/updated {inserted_count} products in database")
            return inserted_count

        except Exception as e:
            logger.error(f"Error saving to Supabase: {e}")
            return 0

    async def run_full_scrape(self):
        """Run the complete scraping pipeline."""
        logger.info("Starting full Bershka scrape")

        start_time = time.time()
        total_products = 0

        # Load categories from text file
        categories = self.load_categories_from_file()

        if not categories:
            logger.error("No categories loaded from file, aborting scrape")
            return {'error': 'No categories loaded'}

        # Scrape all categories
        all_products = []
        seen_product_urls = set()  # Track unique product URLs to avoid duplicates

        # Scrape all categories from the file
        for category_id, category_url in categories.items():
            # Create a friendly name for the category
            category_name = f"category_{category_id}"

            products = await self.scrape_category(category_name, category_id, category_url)

            # Filter out duplicates
            for product in products:
                product_url = product.get('product_url')
                if product_url and product_url not in seen_product_urls:
                    all_products.append(product)
                    seen_product_urls.add(product_url)

            # Check product limit for testing
            if PRODUCT_LIMIT > 0 and len(all_products) >= PRODUCT_LIMIT:
                all_products = all_products[:PRODUCT_LIMIT]
                logger.info(f"Reached product limit of {PRODUCT_LIMIT}, stopping scraping")
                break

        logger.info(f"Total products collected: {len(all_products)}")

        # Process products in batches (generate embeddings)
        logger.info("Generating embeddings...")

        processed_products = []
        for i in range(0, len(all_products), BATCH_SIZE):
            batch = all_products[i:i + BATCH_SIZE]
            processed_batch = await self.process_products_batch(batch)
            processed_products.extend(processed_batch)

            # Progress update
            logger.info(f"Processed {len(processed_products)}/{len(all_products)} products")

        # Save to database
        logger.info("Saving to database...")
        saved_count = await self.save_to_supabase(processed_products)

        end_time = time.time()
        duration = end_time - start_time

        logger.info(
            f"Scrape completed! "
            f"Total products: {len(all_products)}, "
            f"Processed with embeddings: {len(processed_products)}, "
            f"Saved to DB: {saved_count}, "
            f"Duration: {duration:.2f} seconds"
        )

        return {
            'total_collected': len(all_products),
            'processed': len(processed_products),
            'saved': saved_count,
            'duration': duration
        }


async def main():
    """Main entry point."""
    try:
        async with BershkaScraper() as scraper:
            results = await scraper.run_full_scrape()
            print(f"Scrape completed successfully: {results}")

    except KeyboardInterrupt:
        logger.info("Scrape interrupted by user")
    except Exception as e:
        logger.error(f"Scrape failed: {e}")
        raise


if __name__ == "__main__":
    # Run the scraper
    asyncio.run(main())
