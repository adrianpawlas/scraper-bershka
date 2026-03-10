"""Parse Bershka API responses."""
import json
import re
from urllib.parse import parse_qs, urlparse
from typing import Any

from config import (
    BASE_PRODUCT_URL,
    COUNTRY_TO_CURRENCY,
    IMAGE_BASE_URL,
    MEN_CATEGORY_IDS,
    PRODUCT_URL_LOCALE,
    RECORD_ID_PREFIX,
    WOMEN_CATEGORY_IDS,
)


def detect_api_type(data: dict) -> str:
    """Detect API response type: 'products' (full data) or 'grid' (product IDs)."""
    if "products" in data or "productsArray" in data:
        return "products"
    if "gridElements" in data or "productIds" in data:
        return "grid"
    raise ValueError("Unknown API response format")


def extract_product_ids_from_grid(data: dict) -> set[int]:
    """Extract all unique product IDs from grid/category API response."""
    product_ids = set()

    if "productIds" in data:
        product_ids.update(data["productIds"])

    if "sortedProductIds" in data:
        product_ids.update(data["sortedProductIds"])

    if "gridElements" in data:
        for elem in data["gridElements"]:
            # block (Massimo Dutti) or CC (Bershka)
            if "commercialComponentIds" in elem and elem.get("type") in ("block", "CC"):
                for cc in elem["commercialComponentIds"]:
                    if isinstance(cc, dict) and "ccId" in cc:
                        product_ids.add(cc["ccId"])
                    elif isinstance(cc, int):
                        product_ids.add(cc)
            if "ccIds" in elem:
                product_ids.update(elem["ccIds"])

    # From result.typeFilter and result.attributeFilter (nested structure)
    result = data.get("result", data)
    if "typeFilter" in result:
        for tf in result["typeFilter"]:
            product_ids.update(tf.get("productIds", []))
    if "attributeFilter" in result:
        for af in result["attributeFilter"]:
            if "values" in af:
                for v in af["values"]:
                    product_ids.update(v.get("productIds", []))

    return product_ids


# Only use full CDN URLs (assets/public)
ASSETS_PUBLIC_PREFIX = f"{IMAGE_BASE_URL}/assets/public/"


def get_image_urls_from_product(bundle_summary: dict) -> tuple[str | None, list[str]]:
    """
    Extract main image URL and additional image URLs from product.
    Uses full CDN URLs (e.g. static.bershka.net/assets/public/...).
    Returns (main_image_url, [additional_urls]).
    """
    main_url = None
    additional_urls = []

    detail = bundle_summary.get("detail", {})
    xmedia = detail.get("xmedia", [])

    # Collect only full assets/public URLs. Prefer -o1 (exact, not o14/o15), fallback -o3
    all_urls: list[str] = []
    o1_url: str | None = None
    o3_url: str | None = None
    for xm in xmedia:
        for item in xm.get("xmediaItems", []):
            for media in item.get("medias", []):
                url = media.get("url")
                if not url or not url.startswith(ASSETS_PUBLIC_PREFIX):
                    continue
                if url in all_urls:
                    continue
                # Exact -o1: -o1/ or -o1. (avoids -o14, -o15)
                if "-o1/" in url or "-o1." in url:
                    o1_url = url
                elif "-o3/" in url or "-o3." in url:
                    o3_url = url
                all_urls.append(url)

    if not all_urls:
        return None, []

    # Prefer -o1 for main, then -o3, then -c, then -t, then first valid
    if o1_url:
        main_url = o1_url
        additional_urls = [u for u in all_urls if u != o1_url]
    elif o3_url:
        main_url = o3_url
        additional_urls = [u for u in all_urls if u != o3_url]
    else:
        for suffix in ("-c", "-t"):
            for u in all_urls:
                if suffix in u:
                    main_url = u
                    additional_urls = [x for x in all_urls if x != u]
                    break
            if main_url:
                break
        if not main_url:
            main_url = all_urls[0]
            additional_urls = all_urls[1:]

    return main_url, additional_urls


def format_price(price_cents: str | int, currency: str) -> str:
    """Convert price from cents to formatted string: 69.95EUR or 35.90EUR."""
    try:
        cents = int(price_cents)
        amount = cents / 100
        return f"{amount:.2f}{currency}"
    except (ValueError, TypeError):
        return ""


def ensure_price_with_currency(val: str | None, default_currency: str = "EUR") -> str | None:
    """Ensure price string has currency suffix (e.g. 35.9 -> 35.90EUR)."""
    if not val or not str(val).strip():
        return None
    s = str(val).strip()
    if re.search(r"[A-Z]{3}$", s):
        return s
    try:
        num = float(s)
        return f"{num:.2f}{default_currency}"
    except (ValueError, TypeError):
        return s


def slugify(text: str) -> str:
    """Create URL slug from product name."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text).strip("-")
    return text[:80] if text else "product"


def extract_category_id_from_url(url: str) -> int | None:
    """Extract categoryId from products API URL for gender inference."""
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        ids = params.get("categoryId", [])
        if ids:
            return int(ids[0])
    except (ValueError, IndexError, TypeError):
        pass
    return None


def get_gender_from_category_id(category_id: int | None) -> str | None:
    """Map Bershka categoryId to gender: woman, man, or None (unknown/unisex)."""
    if category_id is None:
        return None
    if category_id in WOMEN_CATEGORY_IDS:
        return "woman"
    if category_id in MEN_CATEGORY_IDS:
        return "man"
    return None


def get_gender_from_related_categories(product: dict) -> str | None:
    """Infer gender from relatedCategories IDs (fallback when URL categoryId unavailable)."""
    for cat in product.get("relatedCategories", []):
        cid = cat.get("id")
        if isinstance(cid, int):
            if cid in WOMEN_CATEGORY_IDS:
                return "woman"
            if cid in MEN_CATEGORY_IDS:
                return "man"
    return None


def get_categories_from_attributes(attributes: list[dict]) -> str:
    """Extract category from XTYPEFILTER attributes, comma-separated."""
    categories = []
    for attr in attributes or []:
        if attr.get("type") == "XTYPEFILTER" and attr.get("value"):
            cat = attr["value"].strip()
            # Skip season codes like I2025, V2026
            if cat and cat not in categories and not re.match(r"^[IV]\d{4}$", cat):
                categories.append(cat)
    # Handle compound categories like "Sweaters & Hoodies" -> "Sweaters, Hoodies"
    result = []
    for c in categories:
        if "&" in c:
            result.extend(x.strip() for x in c.split("&") if x.strip())
        else:
            result.append(c)
    return ", ".join(result) if result else ""


def get_category_from_related(product: dict, bundle_summary: dict) -> str:
    """Extract category from relatedCategories (product or bundle detail)."""
    names = []
    for source in (product, bundle_summary):
        for cat in source.get("relatedCategories", []):
            name = (cat.get("name") or "").strip()
            if name and name not in names and not re.match(r"^[IV]\d{4}$", name):
                names.append(name)
    return ", ".join(names[:5]) if names else ""  # Limit to first 5


def get_description_from_attributes(attributes: list[dict]) -> str:
    """Build description from DESCRIPTION type attributes."""
    parts = []
    for attr in attributes or []:
        if attr.get("type") == "DESCRIPTION" and attr.get("value"):
            parts.append(attr["value"])
    return " | ".join(parts) if parts else ""


def get_description(product: dict, bundle_summary: dict) -> str:
    """Build full description from detail + attributes."""
    parts = []
    detail = bundle_summary.get("detail", {})
    desc = (detail.get("description") or "").strip()
    long_desc = (detail.get("longDescription") or "").strip()
    if desc:
        parts.append(desc)
    if long_desc and long_desc != desc:
        parts.append(long_desc)
    attrs_desc = get_description_from_attributes(product.get("attributes", []))
    if attrs_desc:
        parts.append(attrs_desc)
    # Add composition summary
    for comp_group in detail.get("composition", []):
        for item in comp_group.get("composition", []) if isinstance(comp_group, dict) else []:
            pct = item.get("percentage")
            name = item.get("name") or item.get("description")
            if name and pct is not None:
                parts.append(f"{pct}% {name}")
                break
    return " | ".join(parts) if parts else ""


# Terms suggesting women's products (category/name)
_WOMAN_TERMS = frozenset(
    w.lower()
    for w in (
        "woman", "women", "ladies", "lady", "female",
        "skirt", "skirts", "dress", "dresses", "blouse", "blouses",
        "heels", "pumps", "handbag", "handbags", "bra", "bralette",
        "maternity", "mum", "girl", "girls",
    )
)


def get_gender_from_attributes(
    attributes: list[dict],
    category: str = "",
    title: str = "",
) -> str | None:
    """Extract gender from MAN/WOMAN attributes, else infer from category/title. Returns None if unknown/unisex."""
    for attr in attributes or []:
        attr_type = attr.get("type", "")
        if attr_type == "WOMAN":
            return "woman"
        if attr_type == "MAN":
            return "man"

    # Infer from category and title when no explicit attribute
    combined = f"{category} {title}".lower()
    words = set(re.findall(r"\w+", combined))
    if words & _WOMAN_TERMS:
        return "woman"
    # Only infer "man" when we have whole-word signals (avoid 'boy' in 'boyfriend')
    _MAN_TERMS = frozenset(("man", "men", "male", "boy", "boys"))
    if words & _MAN_TERMS:
        return "man"
    return None


# EUR countries - prefer for price lookup; fallback to any country
EUR_COUNTRIES = frozenset(
    c for c, curr in COUNTRY_TO_CURRENCY.items() if curr == "EUR"
)


def collect_prices_eur(
    bundle_summary: dict,
) -> tuple[str | None, str | None]:
    """
    Collect prices in EUR. API: price=current, oldPrice=original when on sale.
    Takes first available price (prefer EUR countries), treats as EUR cents.
    Returns (normal_price_eur, sale_price_eur | None).
    - normal_price: original/regular price in EUR (e.g. 69.95EUR)
    - sale_price: discounted price when on sale (oldPrice exists), else None
    """
    original_cents: int | None = None
    sale_cents: int | None = None
    found_eur = False

    colors = bundle_summary.get("detail", {}).get("colors", [])
    # First pass: try EUR countries
    for color in colors:
        for size in color.get("sizes", []):
            country = (size.get("country") or "").upper()
            if country not in EUR_COUNTRIES:
                continue

            price_str = size.get("price")
            old_price_str = size.get("oldPrice")

            try:
                price_cents = int(price_str) if price_str else None
                old_cents = int(old_price_str) if old_price_str else None

                if price_cents is not None:
                    if old_cents is not None:
                        original_cents = old_cents
                        sale_cents = price_cents
                    else:
                        original_cents = price_cents
                        sale_cents = None
                    found_eur = True
                    break
            except (ValueError, TypeError):
                pass
        if found_eur:
            break

    # Fallback: take first price from any country
    if original_cents is None:
        for color in colors:
            for size in color.get("sizes", []):
                price_str = size.get("price")
                old_price_str = size.get("oldPrice")
                try:
                    price_cents = int(price_str) if price_str else None
                    old_cents = int(old_price_str) if old_price_str else None

                    if price_cents is not None:
                        if old_cents is not None:
                            original_cents = old_cents
                            sale_cents = price_cents
                        else:
                            original_cents = price_cents
                            sale_cents = None
                        break
                except (ValueError, TypeError):
                    pass
            if original_cents is not None:
                break

    if original_cents is None:
        return None, None

    price_str = format_price(original_cents, "EUR")
    sale_str = format_price(sale_cents, "EUR") if sale_cents is not None else None
    return price_str, sale_str


def build_product_url(
    product: dict, bundle_summary: dict, product_id: int, gender: str = "man"
) -> str:
    """Build product page URL: {locale}/{slug}-l{ref}?pelement={product_id}."""
    detail = bundle_summary.get("detail", {})
    ref = detail.get("reference") or detail.get("displayReference") or ""
    ref_clean = ref.split("-")[0].replace("/", "").strip() if ref else ""
    if len(ref_clean) < 8:
        ref_clean = ref_clean.zfill(8)

    name = product.get("name") or product.get("nameEn") or "product"
    slug = slugify(name)

    base = f"{BASE_PRODUCT_URL}/{PRODUCT_URL_LOCALE}"
    if ref_clean:
        return f"{base}/{slug}-l{ref_clean}?pelement={product_id}"
    return f"{base}/{slug}?pelement={product_id}"


def parse_products_api(data: dict, category_id: int | None = None) -> list[dict]:
    """
    Parse products API response into flat product records for DB.
    One record per product (unique by product_url) - bundles share URL.
    category_id: from URL (categoryId param) for gender inference (men/women).
    """
    products_raw = data.get("productsArray", data.get("products", []))
    records = []
    seen_urls: set[str] = set()

    for product in products_raw:
        if product.get("state") != "visible":
            continue

        bundle_summaries = product.get("bundleProductSummaries", [])
        if not bundle_summaries:
            continue

        bundle = bundle_summaries[0]
        detail = bundle.get("detail", {})

        main_image, additional_images = get_image_urls_from_product(bundle)

        if not main_image:
            continue

        product_id = product.get("id")
        attributes = product.get("attributes", [])
        cat_attrs = get_categories_from_attributes(attributes)
        cat_related = get_category_from_related(product, bundle)
        category = cat_related or cat_attrs or None
        title = product.get("name") or product.get("nameEn") or ""
        gender = get_gender_from_category_id(category_id)
        if gender is None:
            gender = get_gender_from_related_categories(product)
        if gender is None:
            gender = get_gender_from_attributes(attributes, category=category or "", title=title)
        product_url = build_product_url(product, bundle, product_id, gender or "man")

        if product_url in seen_urls:
            continue
        seen_urls.add(product_url)

        description = get_description(product, bundle) or None

        price_str, sale_str = collect_prices_eur(bundle)
        price_str = ensure_price_with_currency(price_str) if price_str else None
        sale_str = ensure_price_with_currency(sale_str) if sale_str else None

        additional_images_str = " , ".join(additional_images) if additional_images else None

        metadata = json.dumps(
            {
                "product_id": product_id,
                "reference": detail.get("reference"),
                "display_reference": detail.get("displayReference"),
                "composition": detail.get("composition"),
                "care": detail.get("care"),
                "attributes": attributes[:20],
            },
            default=str,
        )

        records.append(
            {
                "id": f"{RECORD_ID_PREFIX}_{product_id}",
                "product_id": product_id,
                "product_url": product_url,
                "gender": gender,
                "image_url": main_image,
                "additional_images": additional_images_str,
                "title": product.get("name") or product.get("nameEn") or "Unknown",
                "description": description,
                "category": category,
                "price": price_str,
                "sale": sale_str,
                "metadata": metadata,
                "raw_product": product,
                "raw_bundle": bundle,
            }
        )

    return records
