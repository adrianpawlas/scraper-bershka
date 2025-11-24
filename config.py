import os
from typing import Dict, List, Any
from dotenv import load_dotenv
import yaml


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
            "respect_robots": False,
            "api": {
                "endpoints": [
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564",
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193212",
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010240019",
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010276029",
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193216",
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193213",
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193223",
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193222",
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193220",
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193217",
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193221",
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010280023",
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010194517",
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010429555",
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010361506",
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193192",
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193138",
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193134",
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
    except Exception as e:
        print(f"Error loading config: {e}")
        return []


def get_site_configs(all_sites: List[Dict[str, Any]], filter_brands: str) -> List[Dict[str, Any]]:
    """Filter sites based on brand names."""
    if filter_brands.lower() == "all":
        return all_sites

    brand_list = [b.strip() for b in filter_brands.split(",")]
    return [site for site in all_sites if site.get("brand", "").lower() in [b.lower() for b in brand_list]]