import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
import re
import json

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


def discover_product_ids_with_playwright(category_id: str, debug: bool = False) -> List[int]:
    """Use Playwright to get product IDs by loading the actual page."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        if debug:
            print("  Playwright not available, using fallback")
        return []
    
    product_ids = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            # Navigate to category page
            url = f"https://www.bershka.com/us/men/clothes/view-all-c{category_id}.html"
            if debug:
                print(f"  Loading page: {url}")
            
            page.goto(url, wait_until='networkidle', timeout=60000)
            
            # Wait for products to load
            page.wait_for_timeout(3000)
            
            # Get all network requests that contain product IDs
            # The page makes a request to the category/product endpoint
            
            # Try to extract from page content
            content = page.content()
            
            # Look for product IDs in the page (they're in JSON data)
            matches = re.findall(r'"id"\s*:\s*(\d{9,})', content)
            product_ids = list(set(int(m) for m in matches))
            
            if debug:
                print(f"  Found {len(product_ids)} product IDs from page content")
            
            browser.close()
            
    except Exception as e:
        if debug:
            print(f"  Playwright error: {e}")
    
    return product_ids


def discover_product_ids_from_api(session: PoliteSession, category_id: str, category_api_url: Optional[str], category_ids_url_template: Optional[str], headers: Dict[str, str], debug: bool = False) -> List[int]:
    """Try to get product IDs from the category API with proper parameters."""
    
    # Build list of URLs to try: use category-specific URL first, then template
    urls_to_try = []
    
    # 1. Use category-specific API URL if provided
    if category_api_url:
        urls_to_try.append(category_api_url)
    
    # 2. Try template URL if provided
    if category_ids_url_template:
        urls_to_try.append(category_ids_url_template.format(category_id=category_id))
    
    # 3. Fallback to hardcoded templates
    urls_to_try.extend([
        f"https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/category/{category_id}/product?showProducts=false&showNoStock=false&appId=1&languageId=-15&locale=en_GB",
        f"https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/category/{category_id}/product?languageId=-1&appId=1",
    ])
    
    for url in urls_to_try:
        try:
            if debug:
                print(f"  Trying: {url[:80]}...")
            resp = session.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                product_ids = data.get("productIds", [])
                if product_ids:
                    print(f"  SUCCESS: Found {len(product_ids)} product IDs from API")
                    return product_ids
        except Exception as e:
            if debug:
                print(f"  Failed: {str(e)[:50]}")
    
    return []


def run_for_site(site: Dict, session: PoliteSession, db: SupabaseREST, supa_env: Dict[str, str], limit: int = 0) -> int:
    """Scrape products for a single site."""
    brand = site.get("brand", "Unknown")
    merchant = site.get("merchant", brand)
    source = site.get("source", "scraper")
    debug = bool(site.get("debug"))

    collected: List[Dict] = []
    seen_product_ids: Set[int] = set()

    if site.get("api"):
        api_conf = site["api"]
        headers = api_conf.get("headers", {})

        # Prewarm cookies/session
        for warm_url in api_conf.get("prewarm", []):
            try:
                session.get(warm_url, headers=headers)
            except Exception:
                pass

        products_url = api_conf.get("products_url")
        product_url_template = api_conf.get("product_url_template")
        batch_size = api_conf.get("batch_size", 50)
        
        if not products_url:
            print("Error: Missing products_url in config")
            return 0

        category_endpoints = api_conf.get("category_endpoints", [])
        total_products_found = 0
        
        for cat_conf in category_endpoints:
            category_id = cat_conf.get("id")
            category_name = cat_conf.get("name", category_id)
            category_gender = cat_conf.get("gender")
            category_type = cat_conf.get("category")
            category_api_url = cat_conf.get("category_api_url")  # Per-category API URL
            fallback_ids_str = cat_conf.get("fallback_ids", "")
            
            if not category_id:
                continue
            
            print(f"\nProcessing category: {category_name} ({category_id})")
            
            # Check if category_api_url is a productsArray URL (already contains productIds)
            use_direct_url = False
            if category_api_url and "productsArray" in category_api_url and "productIds=" in category_api_url:
                # This URL already contains productIds and returns products directly
                use_direct_url = True
                print(f"  Using direct productsArray URL (contains productIds)")
            
            if use_direct_url:
                # Use the URL directly to fetch products
                try:
                    batch_products = ingest_api(
                        session,
                        category_api_url,
                        api_conf["items_path"],
                        api_conf["field_map"],
                        {"headers": headers},
                        debug=False,
                    )
                    
                    print(f"    Got {len(batch_products)} products from direct API")
                    
                    # Extract product IDs from the fetched products for tracking
                    fetched_ids = [p.get("external_id") or p.get("product_id") or p.get("id") for p in batch_products if p.get("external_id") or p.get("product_id") or p.get("id")]
                    total_products_found += len(fetched_ids)
                    seen_product_ids.update(int(pid) for pid in fetched_ids if pid)
                    
                    # Process products directly (skip batching since we already have them)
                    for p in batch_products:
                        p["merchant"] = merchant
                        p["source"] = source
                        p["gender"] = category_gender
                        
                        if category_type:
                            p["category"] = category_type
                        
                        if site.get("country"):
                            p["country"] = site.get("country")

                        if not p.get("external_id"):
                            p["external_id"] = p.get("product_id") or p.get("id")

                        product_id = p.get("external_id") or p.get("product_id")
                        title = p.get("title", "product")
                        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
                        p["product_url"] = product_url_template.format(
                            slug=slug,
                            product_id=product_id
                        )

                        row = to_supabase_row(p)

                        image_url = row.get("image_url")
                        if not image_url or not isinstance(image_url, str):
                            continue
                        
                        if any(ext in image_url.lower() for ext in ['.mp4', '.m3u8', '.webm', 'video']):
                            if debug:
                                print(f"    [SKIP] Video file: {image_url[:50]}...")
                            continue
                        
                        if 'bershka' in image_url.lower() and 'assets/public' not in image_url:
                            continue

                        emb = get_image_embedding(image_url)
                        if emb is not None:
                            row["embedding"] = emb
                            collected.append(row)
                        
                        if limit and len(collected) >= limit:
                            print(f"\n  Reached limit of {limit} products")
                            break
                    
                    print(f"  Total collected so far: {len(collected)} products with embeddings")
                    
                    # Skip to next category (already processed this one)
                    # Check limit after processing all categories
                    continue
                    
                except Exception as e:
                    print(f"  Error fetching from direct URL: {e}")
                    # Fall through to discovery method
            
            # Step 1: Try to discover product IDs from API
            # Use category-specific URL if provided, otherwise use template
            category_ids_url_template = api_conf.get("category_ids_url")
            product_ids = discover_product_ids_from_api(session, category_id, category_api_url, category_ids_url_template, headers, debug)
            
            # Step 2: If API failed, try Playwright
            if not product_ids:
                if debug:
                    print("  API blocked, trying Playwright...")
                product_ids = discover_product_ids_with_playwright(category_id, debug)
            
            # Step 3: If still no IDs, use fallback
            if not product_ids and fallback_ids_str:
                product_ids = [int(pid.strip()) for pid in fallback_ids_str.split(",") if pid.strip()]
                print(f"  Using {len(product_ids)} fallback product IDs")
            
            if not product_ids:
                print(f"  No products found, skipping")
                continue
            
            total_products_found += len(product_ids)
            
            # Filter duplicates
            new_product_ids = [pid for pid in product_ids if pid not in seen_product_ids]
            seen_product_ids.update(product_ids)
            
            if len(new_product_ids) < len(product_ids):
                print(f"  {len(product_ids) - len(new_product_ids)} duplicates filtered, {len(new_product_ids)} new products")
            
            if not new_product_ids:
                continue
            
            # Step 4: Fetch products in batches
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
                        debug=False,
                    )
                    
                    print(f"    Got {len(batch_products)} products from API")
                    
                    for p in batch_products:
                        p["merchant"] = merchant
                        p["source"] = source
                        p["gender"] = category_gender
                        
                        if category_type:
                            p["category"] = category_type
                        
                        if site.get("country"):
                            p["country"] = site.get("country")

                        if not p.get("external_id"):
                            p["external_id"] = p.get("product_id") or p.get("id")

                        product_id = p.get("external_id") or p.get("product_id")
                        title = p.get("title", "product")
                        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
                        p["product_url"] = product_url_template.format(
                            slug=slug,
                            product_id=product_id
                        )

                        row = to_supabase_row(p)

                        image_url = row.get("image_url")
                        if not image_url or not isinstance(image_url, str):
                            continue
                        
                        if any(ext in image_url.lower() for ext in ['.mp4', '.m3u8', '.webm', 'video']):
                            if debug:
                                print(f"    [SKIP] Video file: {image_url[:50]}...")
                            continue
                        
                        if 'bershka' in image_url.lower() and 'assets/public' not in image_url:
                            continue

                        emb = get_image_embedding(image_url)
                        if emb is not None:
                            row["embedding"] = emb
                            collected.append(row)
                        
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

    if collected:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {brand}: processed {len(collected)} products with embeddings")
        if supa_env["url"] and supa_env["key"]:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {brand}: upserting to database...")
            
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
                    for row in batch:
                        try:
                            db.upsert_products([row])
                            success_count += 1
                        except Exception as e2:
                            print(f"    Failed to insert product {row.get('id')}: {str(e2)[:80]}")
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {brand}: database operations completed ({success_count} products)")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {brand}: skipping database upsert (credentials not set)")

    return len(collected)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bershka fashion scraper")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of products (for testing)")

    args = parser.parse_args()

    load_env()
    supa_env = get_supabase_env()
    db = SupabaseREST(url=supa_env["url"], key=supa_env["key"])

    from config import load_sites_config
    sites = load_sites_config("sites.yaml")

    if not sites:
        print("Error: No sites configured in sites.yaml")
        return

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
