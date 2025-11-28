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
            "api": {                "endpoints": [
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=201096327%2C191849698%2C201304218%2C204544074%2C201927866%2C205222885%2C204203891%2C204203890%2C203971838%2C203677704%2C202812583%2C202680979%2C202411683%2C202238171%2C201967673%2C201129538%2C201096326%2C201096315%2C200711323%2C200672117&appId=1&languageId=-15&locale=en_GB", #all men's products", # all men's part 1
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=196141805%2C198373420%2C199767252%2C198000428%2C198034876%2C198588036%2C196141823%2C194669586%2C193776708%2C189276765%2C196946198%2C197459672%2C196141810%2C191125002%2C189975384%2C189276671%2C198187171%2C196353581%2C189276800&appId=1&languageId=-15&locale=en_GB", # all men's part 2", # all men's part 2
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=200826136%2C197475606%2C195682633%2C189276970%2C189276672%2C202747154%2C198034874%2C196946251%2C194788931%2C189276978%2C196665664%2C202411697%2C196353583%2C191983810%2C189277123%2C200524397%2C200396060%2C199767250%2C197659255&appId=1&languageId=-15&locale=en_GB", # all men's part 3", # all men's part 3
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=196661256%2C196661255%2C192659245%2C192655084%2C191989456%2C191567199%2C189276761%2C202459059%2C200024811%2C189276994%2C196016893%2C196141822%2C194981070%2C196353592%2C196946337%2C196946547%2C196946468%2C190966798%2C189276769&appId=1&languageId=-15&locale=en_GB", # all men's part 4", # all men's part 4
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=200830960%2C199767278%2C198409450%2C197246010%2C197246009%2C196946358%2C194669587%2C192820816%2C189277186%2C189277113%2C189276767%2C193207899%2C196946365%2C198373417%2C198187172%2C199608187%2C196353610%2C192494079%2C196946311%2C193940068&appId=1&languageId=-15&locale=en_GB", # all men's part 5", # all men's part 5
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=193885275%2C191567201%2C189276647%2C195531375%2C196946472%2C196946469%2C195987774%2C192004813%2C199608185%2C198187165%2C197723472%2C197622280%2C196946188%2C194788943%2C191864175%2C190782789%2C189277100%2C189277099%2C189277037&appId=1&languageId=-15&locale=en_GB", # all men's part 6", # all men's part 6
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=189277036%2C189276760%2C189277060%2C189277038%2C189276801%2C196946399%2C197378447%2C196946368%2C199767251%2C192370123%2C206171992%2C201511415%2C197585518%2C195556771%2C195184028%2C193776698%2C191849704%2C189558403%2C197659259%2C192519459&appId=1&languageId=-15&locale=en_GB", # all men's part 7", # all men's part 7
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=189276674%2C189276673%2C199767306%2C192494072%2C196946451%2C196946449%2C196946325%2C189276979%2C197246004%2C196946400%2C196946396%2C189277105%2C196353582%2C189277121%2C207265979%2C200458829%2C200319618%2C197378443%2C195311757%2C193334234&appId=1&languageId=-15&locale=en_GB", # all men's part 8", # all men's part 8
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=192659239%2C192004812%2C191989454%2C189276868%2C199125545%2C197459671%2C196946460%2C193334220%2C191567200%2C189276646%2C196946539%2C200795801%2C200672116%2C199767300%2C198552053%2C198373419%2C197716844%2C197141151%2C194949977&appId=1&languageId=-15&locale=en_GB", # all men's part 9", # all men's part 9
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=193776709%2C193564638%2C193207903%2C190782788%2C189907076%2C189277111%2C196946374%2C189277144%2C197378446%2C197175886%2C196946267%2C196946266%2C196946263%2C194337795%2C196959731%2C191261415%2C197831052%2C196946439%2C196946355%2C189411168&appId=1&languageId=-15&locale=en_GB", # all men's part 10", # all men's part 10
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=189411167%2C195987775%2C199121614%2C193757600%2C196946199%2C201239530%2C199756259%2C199121631%2C197716805%2C196946499%2C196946497%2C196946326%2C196946249%2C196946189%2C193207906%2C192494076%2C191864171%2C190788873%2C189277102&appId=1&languageId=-15&locale=en_GB", # all men's part 11", # all men's part 11
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=189277035%2C189277031%2C189276729%2C197659262%2C196513953%2C189276665%2C201096318%2C201096317%2C196946202%2C196946201%2C189277040%2C193564627%2C199573590%2C194635117%2C189276921%2C196946369%2C199008236%2C195682632%2C195311756%2C197294204&appId=1&languageId=-15&locale=en_GB", # all men's part 12", # all men's part 12
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=195307613%2C189276759%2C197287385%2C194981073%2C195834056%2C193334221%2C191567218%2C202411695%2C199767248%2C197831053%2C197294198%2C196946408%2C189277106%2C203302141%2C199125546%2C196946461%2C189836537%2C189836535%2C189276727%2C189276648&appId=1&languageId=-15&locale=en_GB", # all men's part 13", # all men's part 13
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=196870080%2C196946338%2C189276973%2C199881682%2C198282752%2C197378445%2C196946466%2C196946268%2C194949968%2C194337794%2C196946333%2C196946225%2C189276773%2C202068094%2C199767310%2C199125550%2C199125549%2C199061493%2C199022858&appId=1&languageId=-15&locale=en_GB", # all men's part 14", # all men's part 14
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=197831037%2C196946353%2C195157718%2C192494071%2C190174626%2C189277190%2C196946471%2C196946195%2C196946548%2C196946327%2C196946190%2C196946187%2C194337796%2C193207907%2C192346446%2C192346445%2C196946542%2C196946540%2C199372093%2C197632448&appId=1&languageId=-15&locale=en_GB", # all men's part 15", # all men's part 15
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=195157721%2C196946364%2C196946536%2C199121628%2C197378439%2C196946464%2C196946223%2C196946222%2C196946221%2C196946220%2C196946218%2C193885267%2C198552033%2C196946178%2C196353605%2C194337802%2C196946336%2C196946334%2C204488360&appId=1&languageId=-15&locale=en_GB", # all men's part 16", # all men's part 16
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=204488359%2C204283070%2C204074723%2C203712810%2C203392691%2C203392690%2C203017256%2C202757040%2C202459060%2C202384090%2C202238179%2C202125158%2C201665292&appId=1&languageId=-15&locale=en_GB", # all men's part 17", # all men's part 17
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=201665291%2C201592802%2C201535567%2C201264284%2C201096316%2C201020136%2C201020129%2C200832244%2C200830961%2C200830957%2C200771987%2C200766640%2C200766639%2C200706007%2C200706006%2C200706005&appId=1&languageId=-15&locale=en_GB", # all men's part 18", # all men's part 18
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=200524404%2C200458828%2C200458827%2C200396059%2C200396055%2C200346171%2C200319622%2C200319620%2C200227984%2C200227983%2C200227978%2C200227976%2C199881692%2C199850196%2C199809304%2C199809303%2C199767317%2C199767311%2C199767309%2C199767308&appId=1&languageId=-15&locale=en_GB", # all men's part 19", # all men's part 19
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=199767305%2C199767304%2C199767303%2C199767299%2C199767295%2C199767290%2C199767253%2C199756248%2C199756247%2C199756246%2C199756244%2C199717203%2C199638921%2C199608177%2C199554621%2C199375652%2C199375651%2C199173439%2C199125548%2C199121630&appId=1&languageId=-15&locale=en_GB", # all men's part 20", # all men's part 20
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=199121629%2C199121627%2C199121621%2C199121620%2C199121618%2C199121617%2C199023287%2C199023279%2C199022863%2C198824259%2C198777323%2C198777322%2C198777321%2C198747068%2C198747067%2C198747065%2C198656628%2C198656620%2C198656617%2C198588034&appId=1&languageId=-15&locale=en_GB", # all men's part 21", # all men's part 21
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=198552043%2C198552017%2C198373423%2C198347568%2C198311897%2C198187170%2C198187169%2C198187166%2C198187163%2C198187161%2C198187157%2C198187156%2C198068466%2C198068456%2C197930176%2C197831055%2C197831051%2C197723477%2C197723476%2C197723475&appId=1&languageId=-15&locale=en_GB", # all men's part 22", # all men's part 22
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=197723474%2C197723473%2C197716847%2C197716845%2C197659258%2C197659256%2C197659247%2C197622313%2C197622284%2C197573690%2C197378448%2C197378440%2C197378438%2C197378437%2C197378435%2C197378434%2C197329929%2C197329927%2C197322986%2C197316322&appId=1&languageId=-15&locale=en_GB", # all men's part 23", # all men's part 23
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=197294209%2C197294202%2C197294201%2C197294200%2C197294199%2C197287383%2C197246008%2C197175884%2C197172583%2C197172582%2C197172581%2C196959734%2C196959732%2C196958566%2C196958562%2C196958554%2C196958553%2C196958544%2C196946546%2C196946537&appId=1&languageId=-15&locale=en_GB", # all men's part 24", # all men's part 24
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=196946535%2C196946534%2C196946527%2C196946525%2C196946524%2C196946519%2C196946518%2C196946517%2C196946516%2C196946515%2C196946514%2C196946513%2C196946504%2C196946502%2C196946496%2C196946495%2C196946494%2C196946486%2C196946480%2C196946479&appId=1&languageId=-15&locale=en_GB", # all men's part 25", # all men's part 25
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=196946476%2C196946474%2C196946473%2C196946467%2C196946462%2C196946459%2C196946458%2C196946455%2C196946450%2C196946448%2C196946447%2C196946444%2C196946436%2C196946435%2C196946433%2C196946432%2C196946431%2C196946425%2C196946406%2C196946405&appId=1&languageId=-15&locale=en_GB", # all men's part 26", # all men's part 26
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=196946314%2C196946306%2C196946287%2C196946273%2C196946272%2C196946256%2C196946255%2C196946248%2C196946228%2C196946226%2C196946224%2C196946216%2C196946214%2C196946213%2C196946211%2C196946203%2C196946200%2C196946182%2C196946176%2C196946167&appId=1&languageId=-15&locale=en_GB", # all men's part 27", # all men's part 27
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=196946166%2C196946155%2C196946154%2C196946153%2C196830017%2C196700070%2C196700068%2C196700065%2C196665659%2C196513948%2C196513943%2C196353593%2C196353591%2C196353584%2C196162812%2C196162811%2C196162810%2C196141811%2C196016897%2C196016896&appId=1&languageId=-15&locale=en_GB", # all men's part 28", # all men's part 28
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=195987777%2C195987773%2C195983172%2C195862278%2C195862277%2C195862275%2C195862267%2C195834051%2C195834049%2C195682625%2C195531376%2C195531372%2C195311760%2C195311759%2C195307610%2C195184031%2C195184030%2C195184027%2C195184025%2C195157722&appId=1&languageId=-15&locale=en_GB", # all men's part 29", # all men's part 29
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=195157719%2C195157715%2C194981083%2C194981077%2C194981075%2C194949978%2C194949971%2C194949970%2C194949969%2C194788950%2C194788946%2C194788942%2C194788938%2C194788937%2C194788936%2C194788932%2C194669599%2C194669598%2C194337797%2C194337793&appId=1&languageId=-15&locale=en_GB", # all men's part 30", # all men's part 30
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=194337792%2C194337791%2C194030450%2C193885274%2C193885270%2C193885269%2C193885265%2C193776707%2C193776697%2C193776696%2C193572872%2C193334222%2C193207904%2C193207902%2C193200763%2C193200761%2C193200752%2C193200751%2C193182137%2C193182136&appId=1&languageId=-15&locale=en_GB", # all men's part 31", # all men's part 31
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=193182135%2C193182134%2C193182133%2C193182121%2C193182098%2C193182097%2C193056304%2C193056300%2C193028969%2C193028968%2C192971325%2C192971324%2C192971323%2C192659235%2C192643134%2C192643132%2C192494077%2C192487439%2C192363749%2C191867614&appId=1&languageId=-15&locale=en_GB", # all men's part 32", # all men's part 32
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=191124991%2C191124990%2C191124989%2C191124986%2C191121883%2C190966799%2C190964401%2C190962781%2C190962779%2C190807182%2C190788875%2C190788868%2C190788866%2C190782792%2C190782791%2C190425496%2C190425483%2C190425482%2C190324330%2C190174625&appId=1&languageId=-15&locale=en_GB", # all men's part 33", # all men's part 33
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=190110937%2C190110936%2C190103763%2C189901628%2C189836561%2C189558393%2C189545667%2C189411169%2C189277205%2C189277204%2C189277203%2C189277200%2C189277199%2C189277192%2C189277189%2C189277188%2C189277187%2C189277182%2C189277169%2C189277168&appId=1&languageId=-15&locale=en_GB", # all men's part 34", # all men's part 34
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=189277153%2C189277114%2C189277110%2C189277107%2C189277098%2C189277096%2C189277090%2C189277069%2C189277068%2C189277061%2C189277059%2C189277044%2C189277039%2C189277033%2C189276992%2C189276986%2C189276985%2C189276972%2C189276843%2C189276835&appId=1&languageId=-15&locale=en_GB", # all men's part 35", # all men's part 35
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=189276834%2C189276812%2C189276805%2C189276804%2C189276803%2C189276802%2C189276799%2C189276772%2C189276737%2C189276728%2C189276707%2C189276682%2C189276664%2C189276663%2C189276662%2C189276659%2C189276651%2C189276649%2C189276641%2C189276640&appId=1&languageId=-15&locale=en_GB", # all men's part 36", # all men's part 36
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010834564&productIds=189276631&appId=1&languageId=-15&locale=en_GB", # all men's part 37", # all men's part 37
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193212&productIds=189276819%2C189277126%2C189975385%2C190668687%2C196958508%2C189836534%2C189276745%2C190668686%2C205025006%2C196700066%2C196700067%2C191585747%2C205025003%2C189907075%2C198810474%2C198810475%2C198409429%2C191849717%2C192346450%2C190110934%2C189276930&appId=1&languageId=-15&locale=en_GB", #women's jackets and trench coats", #women's jackets and trench coats
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010240019&productIds=191107022%2C189277173%2C204042832%2C189277172%2C202798264%2C189277171%2C189276786%2C202798279%2C189276784%2C189276782%2C189276785%2C190966805%2C195184008%2C191567193%2C191567194%2C197287397%2C194635099%2C194635098%2C189836544%2C189836543&appId=1&languageId=-15&locale=en_GB", #women's coats", #women's coats
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010276029&productIds=204234905%2C208227334%2C193750495%2C189277029%2C196951967%2C196951966%2C205025032%2C196951986%2C197299074%2C199061494%2C196951985%2C193056302%2C193056303%2C194635118%2C194635119%2C201653849%2C201198143%2C200346175%2C189276952%2C189276955%2C189276951%2C189276953&appId=1&languageId=-15&locale=en_GB", #women's jeans", #women's jeans
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193216&productIds=205676865%2C208227340%2C199767297%2C192537537%2C193885271%2C205025004%2C191983814%2C191983813%2C207206287%2C202459054%2C199125540%2C199125541%2C199219990%2C189277143%2C204042838%2C198311888%2C202459056%2C206551553%2C206551552%2C206551554&appId=1&languageId=-15&locale=en_GB", #women's pants", #women's pants
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193213&productIds=206098478%2C206098470%2C196958028%2C192659228%2C198888253%2C203622818%2C202098272%2C197716827%2C202266882%2C206143318%2C198282748%2C201082411%2C192519460%2C196958149%2C195554265%2C200227971%2C200227970%2C199942359%2C199942358%2C197573693&appId=1&languageId=-15&locale=en_GB", #women's dresses & jumpsuits", #women's dresses & jumpsuits
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193223&productIds=191867628%2C199756257%2C199756258%2C198552052%2C191567204%2C191567205%2C191567203%2C194030446%2C191983812%2C195859485%2C197831038%2C195183995%2C194030447%2C191567223%2C191567222%2C189486676%2C194669571%2C195318230%2C194669576%2C199767272%2C199767273&appId=1&languageId=-15&locale=en_GB", #women's sweaters & cardigans", #women's sweaters & cardigans
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193222&productIds=205470743%2C205462797%2C203392689%2C198552031%2C203210422%2C196513967%2C198552032%2C201304217%2C197381853%2C203302139%2C195682638%2C197716820%2C201493027%2C202818372%2C204054385%2C207374437%2C197716804%2C197716803%2C195682631%2C194788954&appId=1&languageId=-15&locale=en_GB", #women's sweatshirts & hoodies", #women's sweatshirts & hoodies
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193220&productIds=206098469%2C202757041%2C206805014%2C197322949%2C201818674%2C203622821%2C204245233%2C191722643%2C195710380%2C197716835%2C196830011%2C196830012%2C205462803%2C202238185%2C198034868%2C206080228%2C199767245%2C196951706%2C199105562%2C196958310&appId=1&languageId=-15&locale=en_GB", #women's tops & bodysuits", #women's tops & bodysuits
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193217&productIds=204937263%2C205470746%2C208227341%2C205462810%2C205470747%2C205470745%2C204937265%2C204937264%2C197716818%2C202935353%2C198552047%2C201081924%2C193182119%2C196958146%2C196958145%2C196958143%2C196958144%2C198000442&appId=1&languageId=-15&locale=en_GB", #women's t-shirts", #women's t-shirts
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193221&productIds=196946568%2C196946571%2C200309568%2C196946569%2C202798275%2C207206781%2C196946565%2C203597898%2C205566793%2C197299019%2C202680970%2C198911575%2C205120768%2C201870276%2C201870275%2C198341844%2C191102668%2C190927201%2C190927202%2C202797833%2C198409452&appId=1&languageId=-15&locale=en_GB", #women's shirts & blouses", #women's shirts & blouses
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010280023&productIds=206551558%2C200458825%2C199372104%2C196951956%2C196951957%2C199809311%2C202680968%2C206080599%2C189277213%2C202669583%2C202669584%2C198656632%2C190964400%2C189836530%2C189276845%2C203793125%2C203793126%2C201239536%2C206080959%2C201239537&appId=1&languageId=-15&locale=en_GB", #women's skirts", #women's skirts
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010194517&productIds=200227992%2C206080960%2C202535406%2C202459045%2C202459046%2C198373427%2C198409414%2C197622276%2C197298422%2C196958003%2C196958005%2C196958004%2C198373428%2C206080226%2C203277883%2C196957965%2C196957967%2C196957969%2C196957970%2C196957966&appId=1&languageId=-15&locale=en_GB", #women's shorts & jorts", #women's shorts & jorts
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010429555&productIds=207373921%2C201665294%2C201855278%2C193750494%2C205025167%2C207206655%2C202798233%2C201621442%2C204043355%2C199121623%2C197806420%2C204042764%2C202411681%2C204726627%2C201172232%2C200832242&appId=1&languageId=-15&locale=en_GB", #women's matching sets", #women's matching sets
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193192&productIds=201855340%2C191239082%2C204042854%2C196958599%2C204067106%2C208227402%2C204067108%2C208227864%2C189486678%2C189836532%2C196958596%2C195184034%2C201854840%2C202797916%2C192519465%2C196958543%2C194976853%2C192519451%2C200309632%2C190782790%2C191261414&appId=1&languageId=-15&locale=en_GB", #women's shoes", #women's shoes
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193138&productIds=204634216%2C197298903%2C196951975%2C196951911%2C189276935%2C200766649%2C203302140%2C200863240%2C196951910%2C189276755%2C197309091%2C196951819%2C196951822%2C196951820%2C196014192%2C205025484%2C201129527%2C201129528%2C189276808%2C196957981%2C196958027&appId=1&languageId=-15&locale=en_GB", #women's bags & coinpurses", #women's bags & coinpurses
                    "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549/productsArray?categoryId=1010193134&productIds=200396071%2C196958261%2C203793127%2C202459049%2C207374434%2C207373971%2C202459050%2C196958217%2C196957980%2C196957979&appId=1&languageId=-15&locale=en_GB", #women's accessories", #women's accessories
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


# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Bershka API Configuration
BERSHKA_BASE_URL = "https://www.bershka.com/itxrest/3/catalog/store/45009578/40259549"
BERSHKA_APP_ID = "1"
BERSHKA_LANGUAGE_ID = "-15"
BERSHKA_LOCALE = "en_GB"

# Processing Configuration
BATCH_SIZE = 50
MAX_WORKERS = 10
EMBEDDING_MODEL = "google/siglip-so400m-patch14-384"
PRODUCT_LIMIT = 0  # 0 means no limit

# Category Configuration
CATEGORY_IDS = {
    'men': {
        'all': {'category_id': '1010834564'}
    },
    'women': {
        'jackets_trench': {'category_id': '1010193212'},
        'coats': {'category_id': '1010240019'},
        'jeans': {'category_id': '1010276029'},
        'pants': {'category_id': '1010193216'},
        'dresses_jumpsuits': {'category_id': '1010193213'},
        'sweaters_cardigans': {'category_id': '1010193223'},
        'sweatshirts_hoodies': {'category_id': '1010193222'},
        'tops_bodysuits': {'category_id': '1010193220'},
        'tshirts': {'category_id': '1010193217'},
        'shirts_blouses': {'category_id': '1010193221'},
        'skirts': {'category_id': '1010280023'},
        'shorts_jorts': {'category_id': '1010194517'},
        'matching_sets': {'category_id': '1010429555'},
        'swimwear': {'category_id': '1010361506'},
        'shoes': {'category_id': '1010193192'},
        'bags': {'category_id': '1010193138'},
        'accessories': {'category_id': '1010193134'}
    }
}

# Gender mapping
GENDER_MAPPING = {
    'WOMAN': 'women',
    'MAN': 'men',
    'UNISEX': 'unisex'
}

# Category classification (for accessories/footwear vs clothing)
CATEGORY_CLASSIFICATION = {
    'shoes': 'footwear',
    'bags': 'accessories',
    'accessories': 'accessories'
}

# Category URL mapping - maps category IDs to their JSON URLs
# REPLACE THESE PLACEHOLDER URLs WITH YOUR ACTUAL JSON URLs
CATEGORY_URLS = {
    # Men's categories
    '1010834564': 'https://your-domain.com/api/bershka/mens_all_products.json',

    # Women's categories
    '1010193212': 'https://your-domain.com/api/bershka/womens_jackets_products.json',
    '1010240019': 'https://your-domain.com/api/bershka/womens_coats_products.json',
    '1010276029': 'https://your-domain.com/api/bershka/womens_jeans_products.json',
    '1010193216': 'https://your-domain.com/api/bershka/womens_pants_products.json',
    '1010193213': 'https://your-domain.com/api/bershka/womens_dresses_products.json',
    '1010193223': 'https://your-domain.com/api/bershka/womens_sweaters_products.json',
    '1010193222': 'https://your-domain.com/api/bershka/womens_hoodies_products.json',
    '1010193220': 'https://your-domain.com/api/bershka/womens_tops_products.json',
    '1010193217': 'https://your-domain.com/api/bershka/womens_tshirts_products.json',
    '1010193221': 'https://your-domain.com/api/bershka/womens_blouses_products.json',
    '1010280023': 'https://your-domain.com/api/bershka/womens_skirts_products.json',
    '1010194517': 'https://your-domain.com/api/bershka/womens_shorts_products.json',
    '1010429555': 'https://your-domain.com/api/bershka/womens_sets_products.json',
    '1010361506': 'https://your-domain.com/api/bershka/womens_swimwear_products.json',
    '1010193192': 'https://your-domain.com/api/bershka/womens_shoes_products.json',
    '1010193138': 'https://your-domain.com/api/bershka/womens_bags_products.json',
    '1010193134': 'https://your-domain.com/api/bershka/womens_accessories_products.json'
}