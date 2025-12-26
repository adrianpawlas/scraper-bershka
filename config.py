import os
from typing import Dict, List, Any
try:
    from dotenv import load_dotenv
    import yaml
except ImportError:
    # Fallback if packages not available
    def load_dotenv():
        pass
    yaml = None


def load_env():
    """Load environment variables from .env file."""
    load_dotenv()


def get_supabase_env() -> Dict[str, str]:
    """Get Supabase environment variables."""
    return {
        "url": os.getenv("SUPABASE_URL", ""),
        "key": os.getenv("SUPABASE_KEY", "")
    }


def get_default_headers() -> Dict[str, str]:
    """Get default HTTP headers."""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-GB,en;q=0.9',
    }


def load_sites_config(config_file: str = "sites.yaml") -> List[Dict[str, Any]]:
    """Load sites configuration from YAML file."""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            # If it's a dict with a sites key, return the sites list
            if isinstance(config, dict) and 'sites' in config:
                return config['sites']
            # If it's already a list, return it
            elif isinstance(config, list):
                return config
            # If it's a dict but not with sites key, wrap it in a list
            else:
                return [config]
    except FileNotFoundError:
        print(f"Config file {config_file} not found, using default Bershka config")
        return [{
            "brand": "Bershka",
            "merchant": "Bershka",
            "source": "scraper",
            "country": "us",
            "debug": True,
            "respect_robots": False,            "api": {
                "endpoints": [],
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
                    "Accept-Language": "en-GB,en;q=0.9,en-US;q=0.8,en;q=0.7"
                },
                "debug": True,
                "prewarm": [
                    "https://www.bershka.com/us/",
                    "https://www.bershka.com/us/men.html",
                    "https://www.bershka.com/us/women.html"
                ]
            }
        }]


# Bershka Configuration
BERSHKA_BASE_URL = "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549"
BERSHKA_APP_ID = 1
BERSHKA_LANGUAGE_ID = -15
BERSHKA_LOCALE = "en_GB"

# Legacy Bershka Configuration (for backward compatibility)
BERSHKA_BASE_URL = "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549"
BERSHKA_APP_ID = 1
BERSHKA_LANGUAGE_ID = -15
BERSHKA_LOCALE = "en_GB"

# Common Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

BATCH_SIZE = 10
MAX_WORKERS = 4
EMBEDDING_MODEL = "google/siglip-base-patch16-384"
PRODUCT_LIMIT = 0  # 0 = no limit

# Category mappings for Bershka - all categories from URLs
CATEGORY_IDS = {
    'men': {
        'all_mens': {'category_id': '1010834564'},  # All men's products
    },
    'women': {
        'jackets_coats': {'category_id': '1010193212'},  # Women's jackets and trench coats
        'coats': {'category_id': '1010240019'},  # Women's coats
        'jeans': {'category_id': '1010276029'},  # Women's jeans
        'pants': {'category_id': '1010193216'},  # Women's pants
        'dresses_jumpsuits': {'category_id': '1010193213'},  # Women's dresses & jumpsuits
        'sweaters_cardigans': {'category_id': '1010193223'},  # Women's sweaters & cardigans
        'sweatshirts_hoodies': {'category_id': '1010193222'},  # Women's sweatshirts & hoodies
        'tops_bodysuits': {'category_id': '1010193220'},  # Women's tops & bodysuits
        'tshirts': {'category_id': '1010193217'},  # Women's t-shirts
        'shirts_blouses': {'category_id': '1010193221'},  # Women's shirts & blouses
        'skirts': {'category_id': '1010280023'},  # Women's skirts
        'shorts_jorts': {'category_id': '1010194517'},  # Women's shorts & jorts
        'matching_sets': {'category_id': '1010429555'},  # Women's matching sets
        'shoes': {'category_id': '1010193192'},  # Women's shoes
        'bags_coinpurses': {'category_id': '1010193138'},  # Women's bags & coinpurses
        'accessories': {'category_id': '1010193134'},  # Women's accessories
        'bsk_teen': {'category_id': '1010833579'},  # Women's bsk teen
    }
}

GENDER_MAPPING = {
    'MAN': 'men',
    'WOMAN': 'women',
    '': 'unisex'
}

CATEGORY_CLASSIFICATION = {
    # Add category classifications as needed
}