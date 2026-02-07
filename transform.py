from typing import Any, Dict, List
import re

# No external imports needed for this module


def _normalize_availability(raw_availability: Any) -> str:
    """Normalize availability to one of: 'in_stock', 'out_of_stock', 'unknown'."""
    if isinstance(raw_availability, bool):
        return "in_stock" if raw_availability else "out_of_stock"
    if raw_availability is None:
        return "unknown"
    text = str(raw_availability).strip().lower()
    mapping = {
        "in_stock": "in_stock",
        "instock": "in_stock",
        "in stock": "in_stock",
        "available": "in_stock",
        "out_of_stock": "out_of_stock",
        "out-of-stock": "out_of_stock",
        "outofstock": "out_of_stock",
        "sold_out": "out_of_stock",
        "sold-out": "out_of_stock",
        "sold out": "out_of_stock",
        "unavailable": "out_of_stock",
        "coming_soon": "unknown",
        "coming-soon": "unknown",
        "preorder": "unknown",
        "pre-order": "unknown",
    }
    return mapping.get(text, "unknown")


def to_supabase_row(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Map a generic scraped product to your Supabase products schema.

    Expected minimal input keys (from API/HTML):
    - source: str (e.g., 'manual', 'api', 'awin')
    - external_id: str (stable per merchant) - will be used as the 'id' field
    - merchant_name: str
    - merchant_id: str|int (optional)
    - title: str
    - description: str (optional)
    - brand: str (optional)
    - price: float|str (optional)
    - currency: str (e.g., 'GBP')
    - image_url: str
    - product_url: str
    - affiliate_url: str (optional)

    All other columns are left null unless provided.
    """

    row: Dict[str, Any] = {}

    # Use external_id as the primary key 'id'
    external_id = raw.get("external_id") or raw.get("product_id")
    row["id"] = str(external_id) if external_id else str(raw.get("product_url", "unknown"))
    row["source"] = raw.get("source") or "scraper"
    row["title"] = raw.get("title") or "Unknown title"
    row["description"] = raw.get("description")
    row["brand"] = raw.get("brand") or "Bershka"
    row["price"] = raw.get("price")
    row["currency"] = raw.get("currency") or "EUR"
    
    def _fix_image_url(url: str) -> str:
        if not url or not isinstance(url, str):
            return url
        u = url.strip()
        if u.startswith('/'):
            u = f"https://static.bershka.net{u}"
        elif u.startswith('//'):
            u = f"https:{u}"
        return u

    # Collect all image URLs: main image (the one we embed) + additional
    all_urls_raw = raw.get("all_image_urls")
    if isinstance(all_urls_raw, list):
        # Flatten nested lists from JMESPath e.g. xmedia[*].xmediaItems[*]...
        def _flatten_urls(x: Any, out: List[str]) -> None:
            if isinstance(x, str) and x.strip() and not x.strip().startswith("data:"):
                out.append(x.strip())
            elif isinstance(x, list):
                for item in x:
                    _flatten_urls(item, out)
        all_urls: List[str] = []
        _flatten_urls(all_urls_raw, all_urls)
        # Deduplicate preserving order
        seen_url: set = set()
        unique_urls = [u for u in all_urls if u and u not in seen_url and not seen_url.add(u)]
    else:
        unique_urls = []

    image_url = raw.get("image_url")
    if not image_url and unique_urls:
        image_url = unique_urls[0]
    if image_url:
        image_url = _fix_image_url(str(image_url))
    row["image_url"] = image_url

    # additional_images: all other image URLs, formatted as "url1 , url2 , url3"
    main_url = row["image_url"]
    if unique_urls:
        others = [u for u in unique_urls if u != main_url]
        others = [_fix_image_url(u) for u in others if u]
        row["additional_images"] = " , ".join(others) if others else None
    else:
        row["additional_images"] = None
    
    # Product URL should be unique - use the one generated in cli.py or construct from ID
    product_url = raw.get("product_url")
    if not product_url and external_id:
        # Generate a unique product URL if not provided
        title = raw.get("title", "product")
        slug = re.sub(r'[^a-z0-9]+', title.lower(), '-').strip('-')
        product_url = f"https://www.bershka.com/us/{slug}-c0p{external_id}.html"
    row["product_url"] = product_url
    row["affiliate_url"] = raw.get("affiliate_url")
    row["sale"] = raw.get("sale")

    # Set second_hand to FALSE for all current brands (they are not second-hand marketplaces)
    row["second_hand"] = False

    # Use gender from category config (set in cli.py)
    # This ensures women's products get "WOMAN" and men's products get "MAN"
    raw_gender = raw.get("gender")
    if raw_gender:
        gender_str = str(raw_gender).strip().upper()
        # If already correctly set to MAN or WOMAN, use it
        if gender_str == "MAN" or gender_str == "WOMAN":
            row["gender"] = gender_str
        # Otherwise normalize
        elif any(word in gender_str for word in ["MEN", "MAN", "MALE", "GUY", "BOY"]):
            row["gender"] = "MAN"
        elif any(word in gender_str for word in ["WOMEN", "WOMAN", "FEMALE", "LADY", "GIRL"]):
            row["gender"] = "WOMAN"
        else:
            row["gender"] = gender_str  # Keep original if doesn't match
    else:
        # No gender provided - leave as None
        row["gender"] = None

    # Category: actual product category (e.g. sweaters & hoodies, footwear, t-shirts)
    # Normalize from config name (e.g. women_sweatshirts_hoodies) to readable form
    raw_cat = raw.get("category")
    if isinstance(raw_cat, str) and raw_cat.strip():
        row["category"] = raw_cat.strip().replace("_", " ").title()
    else:
        row["category"] = raw_cat

    # Normalize sizes: accept str, list[str], or nested lists → text (comma-separated)
    size_val = raw.get("size") or raw.get("sizes")
    try:
        if isinstance(size_val, list):
            flat_sizes: List[str] = []
            for s in size_val:
                if isinstance(s, list):
                    for t in s:
                        if isinstance(t, str) and t.strip():
                            flat_sizes.append(t.strip())
                elif isinstance(s, str) and s.strip():
                    flat_sizes.append(s.strip())
            row["size"] = ", ".join(dict.fromkeys(flat_sizes)) if flat_sizes else None
        elif isinstance(size_val, str):
            row["size"] = size_val.strip() or None
    except Exception:
        pass

    # Normalize price (store as text for DB). Convert from minor units if needed.
    try:
        price_val = row.get("price")
        if price_val is not None:
            num_val = None
            if isinstance(price_val, (int, float)):
                if isinstance(price_val, int) and price_val >= 1000:
                    num_val = price_val / 100.0
                else:
                    num_val = float(price_val)
            elif isinstance(price_val, str):
                s = price_val.strip()
                s_clean = re.sub(r"[^0-9.,]", "", s)
                if s_clean.count(",") == 1 and s_clean.count(".") == 0:
                    s_clean = s_clean.replace(",", ".")
                if s_clean.count(".") > 1:
                    parts = s_clean.split(".")
                    s_clean = "".join(parts[:-1]) + "." + parts[-1]
                if s_clean:
                    num_val = float(s_clean)
                    if num_val >= 1000 and abs(num_val - int(num_val)) < 1e-9:
                        num_val = num_val / 100.0
            if num_val is not None:
                row["price"] = str(num_val) if num_val == int(num_val) else str(num_val)
    except Exception:
        pass

    # Build metadata json: include base info, plus site/source-specific _meta and useful raw fields
    try:
        # Start with a minimal base so metadata is never empty
        meta: Dict[str, Any] = {}
        for k in ("source", "id"):
            v = row.get(k)
            if v not in (None, ""):
                meta[k] = v
        if isinstance(raw.get("_meta"), dict):
            meta.update(raw["_meta"])  # type: ignore[arg-type]
        # include helpful raw context when present
        for k in ("_raw_item", "_raw_html_len"):
            if raw.get(k) is not None:
                meta[k] = raw.get(k)
        # attach original price/currency fields pre-normalization when available
        if raw.get("price") is not None and "original_price" not in meta:
            meta["original_price"] = raw.get("price")
        if raw.get("currency") is not None and "original_currency" not in meta:
            meta["original_currency"] = raw.get("currency")
        row["metadata"] = meta
    except Exception:
        pass

    return row
