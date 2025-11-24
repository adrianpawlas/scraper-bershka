import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
import re

try:
    from .config import load_env, get_supabase_env
    from .http_client import PoliteSession
    from .db import SupabaseREST
    from .api_ingestor import ingest_api
    from .transform import to_supabase_row
    from .embeddings import get_image_embedding
except ImportError:
    # Fallback for direct execution
    from config import load_env, get_supabase_env
    from http_client import PoliteSession
    from db import SupabaseREST
    from api_ingestor import ingest_api
    from transform import to_supabase_row
    from embeddings import get_image_embedding


def discover_product_ids(session: PoliteSession, category_ids_url: str, category_id: str, headers: Dict[str, str], debug: bool = False) -> Optional[List[int]]:
    """Discover all product IDs for a category using the category endpoint.
    Returns None if the endpoint is blocked/fails, so caller can use fallback.
    """
    url = category_ids_url.format(category_id=category_id)
    
    if debug:
        print(f"  Attempting to discover products from: {url[:80]}...")
    
    try:
        resp = session.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        
        product_ids = data.get("productIds", [])
        if product_ids:
            print(f"  SUCCESS: Found {len(product_ids)} product IDs from category API")
            return product_ids
        return None
    except Exception as e:
        if debug:
            print(f"  Category API blocked/failed: {str(e)[:50]}")
        return None


def run_for_site(site: Dict, session: PoliteSession, db: SupabaseREST, supa_env: Dict[str, str], limit: int = 0) -> int:
    """Scrape products for a single site."""
    brand = site.get("brand", "Unknown")
    merchant = site.get("merchant", brand)
    source = site.get("source", "scraper")
    debug = bool(site.get("debug"))

    collected: List[Dict] = []
    seen_product_ids = set()  # Track seen product IDs to avoid duplicates

    if site.get("api"):
        api_conf = site["api"]

        headers = api_conf.get("headers", {})

        # Prewarm cookies/session
        for warm_url in api_conf.get("prewarm", []):
            try:
                session.get(warm_url, headers=headers)
            except Exception:
                pass

        # Get URL templates
        category_ids_url = api_conf.get("category_ids_url")
        products_url = api_conf.get("products_url")
        product_url_template = api_conf.get("product_url_template")
        batch_size = api_conf.get("batch_size", 50)
        
        if not products_url:
            print("Error: Missing products_url in config")
            return 0

        # Process each category
        category_endpoints = api_conf.get("category_endpoints", [])
        total_products_found = 0
        using_fallback = False
        
        for cat_conf in category_endpoints:
            category_id = cat_conf.get("id")
            category_name = cat_conf.get("name", category_id)
            category_gender = cat_conf.get("gender")
            category_type = cat_conf.get("category")  # footwear, accessory, or None
            fallback_ids_str = cat_conf.get("fallback_ids", "")
            
            if not category_id:
                continue
            
            print(f"\nProcessing category: {category_name} ({category_id})")
            
            # Step 1: Try to discover all product IDs from category API
            product_ids = None
            if category_ids_url:
                product_ids = discover_product_ids(session, category_ids_url, category_id, headers, debug)
            
            # Step 2: If category API failed, use fallback IDs
            if not product_ids:
                if fallback_ids_str:
                    product_ids = [int(pid.strip()) for pid in fallback_ids_str.split(",") if pid.strip()]
                    print(f"  Using {len(product_ids)} fallback product IDs")
                    using_fallback = True
                else:
                    print(f"  No products found and no fallback IDs, skipping")
                    continue
            
            if not product_ids:
                continue
            
            total_products_found += len(product_ids)
            
            # Filter out already seen product IDs
            new_product_ids = [pid for pid in product_ids if pid not in seen_product_ids]
            seen_product_ids.update(product_ids)
            
            if len(new_product_ids) < len(product_ids):
                print(f"  {len(product_ids) - len(new_product_ids)} duplicates filtered, {len(new_product_ids)} new products")
            
            if not new_product_ids:
                continue
            
            # Step 3: Fetch products in batches
            for i in range(0, len(new_product_ids), batch_size):
                batch_ids = new_product_ids[i:i + batch_size]
                batch_ids_str = ",".join(str(pid) for pid in batch_ids)
                
                batch_url = products_url.format(
                    category_id=category_id,
                    product_ids=batch_ids_str
                )
                
                print(f"  Batch {i//batch_size + 1}: fetching {len(batch_ids)} products...")
                
                try:
                    batch_products = ingest_api(
                        session,
                        batch_url,
                        api_conf["items_path"],
                        api_conf["field_map"],
                        {"headers": headers},
                        debug=False,  # Reduce noise
                    )
                    
                    print(f"    Got {len(batch_products)} products from API")
                    
                    # Process each product
                    for p in batch_products:
                        p["merchant"] = merchant
                        p["source"] = source
                        p["gender"] = category_gender
                        
                        # Set category based on config
                        if category_type:
                            p["category"] = category_type
                        
                        # Add country if specified
                        if site.get("country"):
                            p["country"] = site.get("country")

                        # Ensure external_id exists
                        if not p.get("external_id"):
                            p["external_id"] = p.get("product_id") or p.get("id")

                        # Generate product URL
                        product_id = p.get("external_id") or p.get("product_id")
                        title = p.get("title", "product")
                        # Create URL-friendly slug
                        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
                        p["product_url"] = product_url_template.format(
                            slug=slug,
                            product_id=product_id
                        )

                        row = to_supabase_row(p)

                        # Skip if no valid image URL
                        image_url = row.get("image_url")
                        if not image_url or not isinstance(image_url, str):
                            if debug:
                                print(f"    [SKIP] No image URL for product {product_id}")
                            continue
                        
                        # Skip video files and invalid URLs
                        if any(ext in image_url.lower() for ext in ['.mp4', '.m3u8', '.webm', 'video']):
                            if debug:
                                print(f"    [SKIP] Video file: {image_url[:50]}...")
                            continue
                        
                        # Skip URLs that don't look like valid Bershka images
                        if 'bershka' in image_url.lower() and 'assets/public' not in image_url:
                            if debug:
                                print(f"    [SKIP] Invalid Bershka URL: {image_url[:50]}...")
                            continue

                        # Generate image embedding
                        emb = get_image_embedding(image_url)
                        if emb is not None:
                            row["embedding"] = emb
                            collected.append(row)
                        else:
                            if debug:
                                print(f"    [SKIP] Failed to generate embedding for {product_id}")

                        # Check limit
                        if limit and len(collected) >= limit:
                            print(f"\n  Reached limit of {limit} products")
                            break
                    
                    if limit and len(collected) >= limit:
                        break
                        
                except Exception as e:
                    print(f"  Error fetching batch: {e}")
                    continue
            
            if limit and len(collected) >= limit:
                break
            
            print(f"  Total collected so far: {len(collected)} products with embeddings")
        
        print(f"\n{'='*50}")
        print(f"Total products discovered across all categories: {total_products_found}")
        print(f"Unique products after deduplication: {len(seen_product_ids)}")
        if using_fallback:
            print(f"NOTE: Using fallback product IDs (category API was blocked)")
            print(f"      Full product discovery will work from GitHub Actions")

    if collected:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {brand}: processed {len(collected)} products with embeddings")
        if supa_env["url"] and supa_env["key"]:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {brand}: upserting to database...")
            
            # Upsert in batches to avoid issues
            upsert_batch_size = 50
            success_count = 0
            for i in range(0, len(collected), upsert_batch_size):
                batch = collected[i:i + upsert_batch_size]
                try:
                    db.upsert_products(batch)
                    success_count += len(batch)
                    print(f"  Upserted batch {i//upsert_batch_size + 1}: {len(batch)} products (total: {success_count})")
                except Exception as e:
                    print(f"  Error upserting batch: {e}")
                    # Try individual inserts for failed batch
                    for row in batch:
                        try:
                            db.upsert_products([row])
                            success_count += 1
                        except Exception as e2:
                            print(f"    Failed to insert product {row.get('id')}: {str(e2)[:80]}")
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {brand}: database operations completed ({success_count} products)")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {brand}: skipping database upsert (credentials not set)")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {brand}: to enable database operations, set SUPABASE_URL and SUPABASE_KEY environment variables")

    return len(collected)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bershka fashion scraper")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of products (for testing)")

    args = parser.parse_args()

    load_env()
    supa_env = get_supabase_env()
    db = SupabaseREST(url=supa_env["url"], key=supa_env["key"])

    # Load site configuration from sites.yaml
    from config import load_sites_config
    sites = load_sites_config("sites.yaml")

    if not sites:
        print("Error: No sites configured in sites.yaml")
        return

    # Setup session
    session = PoliteSession(default_headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-GB,en;q=0.9',
    }, respect_robots=False)

    total = 0
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting Bershka scraper...")

    start_time = datetime.now()
    site_count = run_for_site(sites[0], session, db, supa_env, limit=args.limit)
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Bershka: imported {site_count} products ({duration:.1f}s)")
    total += site_count

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Total: imported {total} products")


if __name__ == "__main__":
    main()
