import argparse
from datetime import datetime
from typing import Dict, List

try:
    from .config import load_env, get_supabase_env
    from .http_client import PoliteSession
    from .db import SupabaseREST
    from .api_ingestor import ingest_api
    from .transform import to_supabase_row
    from .embeddings import get_image_embedding
    from .html_scraper import discover_product_ids_for_categories
except ImportError:
    # Fallback for direct execution
    from config import load_env, get_supabase_env
    from http_client import PoliteSession
    from db import SupabaseREST
    from api_ingestor import ingest_api
    from transform import to_supabase_row
    from embeddings import get_image_embedding
    from html_scraper import discover_product_ids_for_categories


def run_for_site(site: Dict, session: PoliteSession, db: SupabaseREST, supa_env: Dict[str, str], limit: int = 0) -> int:
    """Scrape products for a single site."""
    brand = site.get("brand", "Unknown")
    merchant = site.get("merchant", brand)
    source = site.get("source", "scraper")
    debug = bool(site.get("debug"))

    collected: List[Dict] = []

    if site.get("api"):
        api_conf = site["api"]

        request_kwargs = {}
        if "headers" in api_conf:
            request_kwargs["headers"] = api_conf["headers"]

        # Prewarm cookies/session
        for warm_url in api_conf.get("prewarm", []):
            try:
                session.get(warm_url, headers=request_kwargs.get("headers"))
            except Exception:
                pass

        # First, discover product IDs from category pages
        category_urls = []
        for ep in api_conf.get("endpoints", []):
            # Convert API endpoints to HTML category URLs
            if 'categoryId=' in ep:
                category_id = ep.split('categoryId=')[1].split('&')[0]
                # Create HTML category URL
                html_url = f"https://www.bershka.com/us/category/{category_id}.html"
                category_urls.append(html_url)

        print(f"Discovering product IDs from {len(category_urls)} category pages...")
        category_product_ids = discover_product_ids_for_categories(session, category_urls, request_kwargs.get("headers"))

        # Now use the discovered product IDs to call the API
        products = []
        for ep in api_conf.get("endpoints", []):
            try:
                if 'categoryId=' in ep:
                    category_id = ep.split('categoryId=')[1].split('&')[0]
                    product_ids = category_product_ids.get(category_id, [])

                    if not product_ids:
                        print(f"No product IDs found for category {category_id}, skipping")
                        continue

                    # Split product IDs into batches (API might have limits)
                    batch_size = 50
                    for i in range(0, len(product_ids), batch_size):
                        batch_ids = product_ids[i:i + batch_size]
                        batch_url = f"{ep.split('&')[0]}&productIds={','.join(batch_ids)}"

                        if debug:
                            print(f"Debug: Processing batch {i//batch_size + 1} for category {category_id}: {len(batch_ids)} products")
                            print(f"Debug: URL: {batch_url[:150]}...")

                        batch = ingest_api(
                            session,
                            batch_url,
                            api_conf["items_path"],
                            api_conf["field_map"],
                            request_kwargs,
                            debug,
                        )
                        if batch:
                            products.extend(batch)
                            if limit and len(products) >= limit:
                                products = products[:limit]
                                break

                    if limit and len(products) >= limit:
                        break

            except Exception as e:
                if debug:
                    print(f"Error processing endpoint {ep}: {e}")
                continue

        for p in products:
            p.setdefault("merchant", merchant)
            p.setdefault("source", source)

            # Add country if specified
            if site.get("country"):
                p["country"] = site.get("country")

            # Ensure external_id exists
            if not p.get("external_id"):
                p["external_id"] = p.get("product_id") or p.get("id")

            row = to_supabase_row(p)

            # Generate image embedding
            emb = get_image_embedding(row.get("image_url"))
            if emb is not None:
                row["embedding"] = emb

            collected.append(row)

    if collected:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {brand}: processed {len(collected)} products")
        if supa_env["url"] and supa_env["key"]:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {brand}: upserting to database...")
            db.upsert_products(collected)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {brand}: database operations completed")
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

    # Setup session
    session = PoliteSession(default_headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-GB,en;q=0.9',
    }, respect_robots=False)

    total = 0
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Processing Bershka...")

    start_time = datetime.now()
    site_count = run_for_site(sites[0], session, db, supa_env, limit=args.limit)
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Bershka: imported {site_count} products ({duration:.1f}s)")
    total += site_count

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Total: imported {total} products")


if __name__ == "__main__":
    main()
