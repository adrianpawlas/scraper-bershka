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
except ImportError:
    # Fallback for direct execution
    from config import load_env, get_supabase_env
    from http_client import PoliteSession
    from db import SupabaseREST
    from api_ingestor import ingest_api
    from transform import to_supabase_row
    from embeddings import get_image_embedding


def run_for_site(site: Dict, session: PoliteSession, db: SupabaseREST, limit: int = 0) -> int:
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

        products = []
        for ep in api_conf.get("endpoints", []):
            try:
                batch = ingest_api(
                    session,
                    ep,
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
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {brand}: processed {len(collected)} products, upserting to database...")
        db.upsert_products(collected)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {brand}: database operations completed")

    return len(collected)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bershka fashion scraper")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of products (for testing)")

    args = parser.parse_args()

    load_env()
    supa_env = get_supabase_env()
    db = SupabaseREST(url=supa_env["url"], key=supa_env["key"])

    # Load Bershka site configuration
    sites = [{
        "brand": "Bershka",
        "merchant": "Bershka",
        "source": "scraper",
        "country": "us",
        "debug": True,
        "respect_robots": False,
        "api": {
            "endpoints": [
                "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564",  # men's all products
                "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193212",  # women's jackets & trench
                "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010240019",  # women's coats
                "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010276029",  # women's jeans
                "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193216",  # women's pants
                "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193213",  # women's dresses & jumpsuit
                "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193223",  # women's sweaters & cardigans
                "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193222",  # women's sweatshirts & hoodies
                "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193220",  # women's tops & bodysuits
                "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193217",  # women's tshirts
                "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193221",  # women's shirts & blouses
                "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010280023",  # women's skirts
                "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010194517",  # women's shorts & jorts
                "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010429555",  # women's matching sets
                "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010361506",  # women's swimwear
                "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193192",  # women's shoes
                "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193138",  # women's bags & coin purses
                "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193134",  # women's accessories
            ],
            "items_path": "products",
            "field_map": {
                "external_id": "id",
                "product_id": "id",
                "title": ["nameEn", "name"],
                "description": ["bundleProductSummaries[0].detail.longDescription", "bundleProductSummaries[0].detail.description"],
                "gender": "bundleProductSummaries[0].sectionNameEN",
                "price": "bundleProductSummaries[0].detail.colors[0].sizes[0].price",
                "currency": "'EUR'",
                "image_url": "bundleProductSummaries[0].detail.colors[0].image.url",
                "product_url": "bundleProductSummaries[0].productUrl",
                "brand": "'Bershka'",
                "sizes": "bundleProductSummaries[0].detail.colors[0].sizes[].name"
            },
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-GB,en;q=0.9"
            },
            "debug": True,
            "prewarm": [
                "https://www.bershka.com/us/",
                "https://www.bershka.com/us/men.html",
                "https://www.bershka.com/us/women.html"
            ]
        }
    }]

    # Setup session
    session = PoliteSession(default_headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-GB,en;q=0.9',
    }, respect_robots=False)

    total = 0
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Processing Bershka...")

    start_time = datetime.now()
    site_count = run_for_site(sites[0], session, db, limit=args.limit)
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Bershka: imported {site_count} products ({duration:.1f}s)")
    total += site_count

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Total: imported {total} products")


if __name__ == "__main__":
    main()
