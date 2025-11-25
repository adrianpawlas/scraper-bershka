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
            "respect_robots": False,
            "api": {
                "endpoints": [
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=201096327%2C191849698%2C201304218%2C204544074%2C201927866%2C205222885%2C204203891%2C204203890%2C203971838%2C203677704%2C202812583%2C202680979%2C202411683%2C202238171%2C201967673%2C201129538%2C201096326%2C201096315%2C200711323%2C200672117&appId=1&languageId=-15&locale=en_GB", #all men's products
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193212&productIds=189276819%2C189277126%2C189975385%2C190668687%2C196958508%2C189836534%2C189276745%2C190668686%2C205025006%2C196700066%2C196700067%2C191585747%2C205025003%2C189907075%2C198810474%2C198810475%2C198409429%2C191849717%2C192346450%2C190110934%2C189276930&appId=1&languageId=-15&locale=en_GB", #women's jackets and trench coats
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010240019&productIds=191107022%2C189277173%2C204042832%2C189277172%2C202798264%2C189277171%2C189276786%2C202798279%2C189276784%2C189276782%2C189276785%2C190966805%2C195184008%2C191567193%2C191567194%2C197287397%2C194635099%2C194635098%2C189836544%2C189836543&appId=1&languageId=-15&locale=en_GB", #women's coats
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010276029&productIds=204234905%2C208227334%2C193750495%2C189277029%2C196951967%2C196951966%2C205025032%2C196951986%2C197299074%2C199061494%2C196951985%2C193056302%2C193056303%2C194635118%2C194635119%2C201653849%2C201198143%2C200346175%2C189276952%2C189276955%2C189276951%2C189276953&appId=1&languageId=-15&locale=en_GB", #women's jeans
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193216&productIds=205676865%2C208227340%2C199767297%2C192537537%2C193885271%2C205025004%2C191983814%2C191983813%2C207206287%2C202459054%2C199125540%2C199125541%2C199219990%2C189277143%2C204042838%2C198311888%2C202459056%2C206551553%2C206551552%2C206551554&appId=1&languageId=-15&locale=en_GB", #women's pants
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193213&productIds=206098478%2C206098470%2C196958028%2C192659228%2C198888253%2C203622818%2C202098272%2C197716827%2C202266882%2C206143318%2C198282748%2C201082411%2C192519460%2C196958149%2C195554265%2C200227971%2C200227970%2C199942359%2C199942358%2C197573693&appId=1&languageId=-15&locale=en_GB", #women's dresses & jumpsuits
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193223&productIds=191867628%2C199756257%2C199756258%2C198552052%2C191567204%2C191567205%2C191567203%2C194030446%2C191983812%2C195859485%2C197831038%2C195183995%2C194030447%2C191567223%2C191567222%2C189486676%2C194669571%2C195318230%2C194669576%2C199767272%2C199767273&appId=1&languageId=-15&locale=en_GB", #women's sweaters & cardigans
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193222&productIds=205470743%2C205462797%2C203392689%2C198552031%2C203210422%2C196513967%2C198552032%2C201304217%2C197381853%2C203302139%2C195682638%2C197716820%2C201493027%2C202818372%2C204054385%2C207374437%2C197716804%2C197716803%2C195682631%2C194788954&appId=1&languageId=-15&locale=en_GB", #women's sweatshirts & hoodies
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193220&productIds=206098469%2C202757041%2C206805014%2C197322949%2C201818674%2C203622821%2C204245233%2C191722643%2C195710380%2C197716835%2C196830011%2C196830012%2C205462803%2C202238185%2C198034868%2C206080228%2C199767245%2C196951706%2C199105562%2C196958310&appId=1&languageId=-15&locale=en_GB", #women's tops & bodysuits
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193217&productIds=204937263%2C205470746%2C208227341%2C205462810%2C205470747%2C205470745%2C204937265%2C204937264%2C206098469%2C202757041%2C197716818%2C202935353%2C198552047%2C201081924%2C193182119%2C196958146%2C196958145%2C196958143%2C196958144%2C198000442&appId=1&languageId=-15&locale=en_GB", #women's t-shirts
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193221&productIds=196946568%2C196946571%2C200309568%2C196946569%2C202798275%2C207206781%2C196946565%2C203597898%2C205566793%2C197299019%2C202680970%2C198911575%2C205120768%2C201870276%2C201870275%2C198341844%2C191102668%2C190927201%2C190927202%2C202797833%2C198409452&appId=1&languageId=-15&locale=en_GB", #women's shirts & blouses
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010280023&productIds=206551558%2C200458825%2C199372104%2C196951956%2C196951957%2C199809311%2C202680968%2C206080599%2C189277213%2C202669583%2C202669584%2C198656632%2C190964400%2C189836530%2C189276845%2C203793125%2C203793126%2C201239536%2C206080959%2C201239537&appId=1&languageId=-15&locale=en_GB", #women's skirts
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010194517&productIds=200227992%2C206080960%2C202535406%2C202459045%2C202459046%2C198373427%2C198409414%2C197622276%2C197298422%2C196958003%2C196958005%2C196958004%2C198373428%2C206080226%2C203277883%2C196957965%2C196957967%2C196957969%2C196957970%2C196957966&appId=1&languageId=-15&locale=en_GB", #women's shorts & jorts
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010429555&productIds=207373921%2C201665294%2C201653849%2C201855278%2C193750494%2C205025167%2C199767297%2C207206655%2C206805014%2C206551558%2C202798233%2C201818674%2C201621442%2C204043355%2C199121623%2C197806420%2C204042764%2C202411681%2C202680968%2C204726627%2C201172232%2C200832242&appId=1&languageId=-15&locale=en_GB", #women's matching sets
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193192&productIds=201855340%2C191239082%2C204042854%2C196958599%2C204067106%2C208227402%2C204067108%2C208227864%2C189486678%2C189836532%2C196958596%2C195184034%2C201854840%2C202797916%2C192519465%2C196958543%2C194976853%2C192519451%2C200309632%2C190782790%2C191261414&appId=1&languageId=-15&locale=en_GB", #women's shoes
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193138&productIds=204634216%2C197298903%2C196951975%2C196951911%2C189276935%2C200766649%2C203302140%2C200863240%2C196951910%2C189276755%2C197309091%2C196951819%2C196951822%2C196951820%2C196014192%2C205025484%2C201129527%2C201129528%2C189276808%2C196957981%2C196958027&appId=1&languageId=-15&locale=en_GB", #women's bags & coinpurses
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193134&productIds=204634216%2C200396071%2C200863240%2C196951911%2C197298903%2C196951975%2C196951910%2C189276755%2C197309091%2C196958261%2C189276935%2C203793126%2C203793127%2C202459049%2C207374434%2C207373971%2C202459050%2C196958217%2C196957980%2C196957979&appId=1&languageId=-15&locale=en_GB", #women's accessories
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