import os
from dotenv import load_dotenv

load_dotenv()

# Supabase Configuration
SUPABASE_URL = "https://yqawmzggcgpeyaaynrjk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlxYXdtemdnY2dwZXlhYXlucmprIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NTAxMDkyNiwiZXhwIjoyMDcwNTg2OTI2fQ.XtLpxausFriraFJeX27ZzsdQsFv3uQKXBBggoz6P4D4"

# Bershka API Configuration
BERSHKA_BASE_URL = "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549"
BERSHKA_APP_ID = 1
BERSHKA_LANGUAGE_ID = -15
BERSHKA_LOCALE = "en_GB"

# Processing Configuration
BATCH_SIZE = int(os.getenv('BATCH_SIZE', 50))
MAX_WORKERS = int(os.getenv('MAX_WORKERS', 5))
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'google/siglip-base-patch16-384')
PRODUCT_LIMIT = int(os.getenv('PRODUCT_LIMIT', 0))  # 0 = no limit, > 0 = limit for testing

# Category IDs for different sections
CATEGORY_IDS = {
    'men': {
        'all': 1010834564,  # Men's category
    },
    'women': {
        'jackets_trench': 1010193212,
        'coats': 1010240019,
        'jeans': 1010276029,
        'pants': 1010193216,
        'dresses_jumpsuit': 1010193213,
        'sweaters_cardigans': 1010193223,
        'sweatshirts_hoodies': 1010193222,
        'tops_bodysuits': 1010193220,
        'tshirts': 1010193217,
        'shirts_blouses': 1010193221,
        'skirts': 1010280023,
        'shorts_jorts': 1010194517,
        'matching_sets': 1010429555,
        'swimwear': 1010361506,
        'shoes': 1010193192,
        'bags_coin_purses': 1010193138,
        'accessories': 1010193134,
    }
}

# Gender mapping from section names
GENDER_MAPPING = {
    'MEN': 'MAN',
    'WOMEN': 'WOMAN',
    'KIDS': 'KIDS',
    'UNISEX': 'UNISEX'
}

# Category classification (accessory, footwear, or None for clothing)
CATEGORY_CLASSIFICATION = {
    'shoes': 'footwear',
    'bags_coin_purses': 'accessory',
    'accessories': 'accessory',
    # All other categories (clothing) will be None/null
}
