"""Script to populate DynamoDB with sample data"""
import random
import time
import requests
import re
from urllib.parse import quote
from server.utils import generate_id, get_current_timestamp
from server.models import Shelf, Cellar, WineReference, WineInstance
from server.data.storage_serializers import serialize_cellar, serialize_wine_reference, serialize_wine_instance
from server.dynamo.storage import (
    put_cellar as dynamodb_put_cellar,
    put_wine_reference as dynamodb_put_wine_reference,
    save_wine_instances as dynamodb_save_wine_instances
)


def search_vivino_images_scrape(query):
    """
    Search WineSearcher for wine label images
    Uses WineSearcher to find wine label images
    """
    try:
        # Search WineSearcher for wine
        # WineSearcher search URL format: /find/{query}
        search_query = quote(query.lower().replace(' ', '-'))
        url = f"https://www.wine-searcher.com/find/{search_query}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Referer': 'https://www.wine-searcher.com/'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        html = response.text
        
        # Method 1: Look for img tags with src or data-src containing image URLs
        # WineSearcher typically uses img tags with wine images
        img_patterns = [
            r'<img[^>]+(?:src|data-src)=["\'](https?://[^"\']+\.(?:jpg|jpeg|png|gif|webp))["\']',
            r'background-image:\s*url\(["\']?(https?://[^"\'()]+\.(?:jpg|jpeg|png|gif|webp))["\']?\)',
        ]
        
        for pattern in img_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                # Filter out WineSearcher's own assets and prefer wine label images
                for match in matches[:20]:
                    match_lower = match.lower()
                    # Skip WineSearcher assets, logos, icons
                    if ('wine-searcher.com' not in match_lower and 
                        'logo' not in match_lower and
                        'icon' not in match_lower and
                        'button' not in match_lower):
                        # Prefer images with 'label', 'bottle', 'wine' in URL
                        if any(keyword in match_lower for keyword in ['label', 'bottle', 'wine']):
                            return match
                # If no keyword match, return first valid image
                for match in matches[:10]:
                    match_lower = match.lower()
                    if ('wine-searcher.com' not in match_lower and 
                        'logo' not in match_lower and
                        'icon' not in match_lower):
                        return match
        
        # Method 2: Look for JSON data with image URLs
        json_pattern = r'"(?:imageUrl|image_url|imgUrl|img_url|labelImage|label_image|wineImage)":\s*["\'](https?://[^"\']+\.(?:jpg|jpeg|png|gif|webp))["\']'
        matches = re.findall(json_pattern, html, re.IGNORECASE)
        if matches:
            for match in matches[:5]:
                match_lower = match.lower()
                if 'wine-searcher.com' not in match_lower:
                    return match
        
        return None
    except Exception as e:
        return None


def get_wine_label_url(wine_name, producer, vintage):
    """Get a wine label image URL from WineSearcher"""
    # Build search query from wine information
    query_parts = []
    if wine_name:
        query_parts.append(wine_name)
    if producer:
        query_parts.append(producer)
    if vintage:
        query_parts.append(str(vintage))
    
    query = ' '.join(query_parts)
    
    # Search for Vivino label image
    image_url = search_vivino_images_scrape(query)
    
    if image_url:
        return image_url
    
    # Fallback: if no Vivino image found, return None or a placeholder
    # The caller should handle None appropriately
    return None


# Sample wine data
RED_WINES = [
    {"name": "Caymus Cabernet Sauvignon", "vintage": 2019, "producer": "Caymus Vineyards", "varietals": ["Cabernet Sauvignon"], "region": "Napa Valley", "country": "United States", "label_image_url": "https://www.vivino.com/en/caymus-vineyards-cabernet-sauvignon/w/66284"},
    {"name": "Opus One", "vintage": 2018, "producer": "Opus One Winery", "varietals": ["Cabernet Sauvignon", "Cabernet Franc", "Merlot"], "region": "Napa Valley", "country": "United States", "label_image_url": "https://www.vivino.com/US/en/francis-ford-coppola-winery-eleanor-red-wine/w/1283092?year=2018"},
    {"name": "Screaming Eagle Cabernet Sauvignon", "vintage": 2017, "producer": "Screaming Eagle", "varietals": ["Cabernet Sauvignon"], "region": "Napa Valley", "country": "United States", "label_image_url": "https://www.vivino.com/US/en/moutai-cabernet-sauvignon-wine-of-china/w/1468807?year=2017"},
    {"name": "Domaine de la Romanée-Conti", "vintage": 2018, "producer": "DRC", "varietals": ["Pinot Noir"], "region": "Burgundy", "country": "France", "label_image_url": "https://www.vivino.com/US/en/domaine-de-la-cadette-l-ermitage-bourgogne/w/1197039?year=2018"},
    {"name": "Château Margaux", "vintage": 2015, "producer": "Château Margaux", "varietals": ["Cabernet Sauvignon", "Merlot"], "region": "Bordeaux", "country": "France", "label_image_url": "https://www.vivino.com/US/en/rene-renon-chateau-charmant-margaux-margaux-red-wine/w/1762595?year=1984"},
    {"name": "Château Lafite Rothschild", "vintage": 2016, "producer": "Château Lafite Rothschild", "varietals": ["Cabernet Sauvignon", "Merlot"], "region": "Bordeaux", "country": "France", "label_image_url": "https://www.vivino.com/chateau-lafite-rothschild-carruades-de-lafite-pauillac/w/23793"},
    {"name": "Penfolds Grange", "vintage": 2017, "producer": "Penfolds", "varietals": ["Shiraz"], "region": "South Australia", "country": "Australia", "label_image_url": "https://www.vivino.com/penfolds-grange/w/1136930?year=1999"},
    {"name": "Sassicaia", "vintage": 2018, "producer": "Tenuta San Guido", "varietals": ["Cabernet Sauvignon", "Cabernet Franc"], "region": "Tuscany", "country": "Italy", "label_image_url": "https://www.vivino.com/US/es/tenuta-san-guido-sassicaia/w/5078?year=2019"},
    {"name": "Tignanello", "vintage": 2019, "producer": "Antinori", "varietals": ["Sangiovese", "Cabernet Sauvignon"], "region": "Tuscany", "country": "Italy", "label_image_url": "https://www.vivino.com/antinori-tuscany-tignanello/w/1652?year=2016"},
    {"name": "Vega Sicilia Unico", "vintage": 2012, "producer": "Vega Sicilia", "varietals": ["Tempranillo", "Cabernet Sauvignon"], "region": "Ribera del Duero", "country": "Spain", "label_image_url": "https://www.vivino.com/US/en/vega-del-cega-vega-del-cega-valdepenas-blanco/w/1259759?year=2019"},
    {"name": "Silver Oak Cabernet Sauvignon", "vintage": 2018, "producer": "Silver Oak", "varietals": ["Cabernet Sauvignon"], "region": "Napa Valley", "country": "United States", "label_image_url": "https://www.vivino.com/silver-oak-cabernet-sauvignon-bonny-s-vineyard/w/3190858"},
    {"name": "Jordan Cabernet Sauvignon", "vintage": 2017, "producer": "Jordan Vineyard", "varietals": ["Cabernet Sauvignon"], "region": "Sonoma County", "country": "United States", "label_image_url": "https://www.vivino.com/US/en/edna-valley-vineyard-cabernet-sauvignon/w/1614113?year=2017"},
    {"name": "Stag's Leap Wine Cellars Cask 23", "vintage": 2016, "producer": "Stag's Leap Wine Cellars", "varietals": ["Cabernet Sauvignon"], "region": "Napa Valley", "country": "United States", "label_image_url": "https://www.vivino.com/US/en/stag-s-leap-wine-cellars-hands-of-time-red/w/1394956"},
    {"name": "Ridge Monte Bello", "vintage": 2018, "producer": "Ridge Vineyards", "varietals": ["Cabernet Sauvignon"], "region": "Santa Cruz Mountains", "country": "United States", "label_image_url": "https://www.vivino.com/US/en/ridge-vineyards-monte-bello-chardonnay/w/1219214?year=2018"},
    {"name": "Shafer Hillside Select", "vintage": 2017, "producer": "Shafer Vineyards", "varietals": ["Cabernet Sauvignon"], "region": "Napa Valley", "country": "United States", "label_image_url": "https://www.vivino.com/en/shafer-hillside-select-cabernet-sauvignon/w/5274"},
    {"name": "Château Pétrus", "vintage": 2015, "producer": "Château Pétrus", "varietals": ["Merlot"], "region": "Pomerol", "country": "France", "label_image_url": "https://www.vivino.com/en/le-chatelet-black-label/w/2643865"},
    {"name": "Château Cheval Blanc", "vintage": 2016, "producer": "Château Cheval Blanc", "varietals": ["Cabernet Franc", "Merlot"], "region": "Saint-Émilion", "country": "France", "label_image_url": "https://www.vivino.com/chateau-cheval-blanc-le-petit-cheval-bordeaux-blanc-bordeaux/w/5313010"},
    {"name": "Dom Pérignon", "vintage": 2012, "producer": "Moët & Chandon", "varietals": ["Chardonnay", "Pinot Noir"], "region": "Champagne", "country": "France", "label_image_url": "https://www.vivino.com/AU/en/chandon-australia-brut-vintage-methode-traditionnelle/w/1146478"},
    {"name": "Cristal", "vintage": 2013, "producer": "Louis Roederer", "varietals": ["Chardonnay", "Pinot Noir"], "region": "Champagne", "country": "France", "label_image_url": "https://www.vivino.com/US/en/louis-roederer-cristal-rose-brut-champagne-millesime/w/74306?year=2013"},
    {"name": "Krug Grande Cuvée", "vintage": 2014, "producer": "Krug", "varietals": ["Chardonnay", "Pinot Noir", "Pinot Meunier"], "region": "Champagne", "country": "France", "label_image_url": "https://www.vivino.com/en/krug-grande-cuvee/w/7122486"},
    {"name": "Burgundy Pinot Noir", "vintage": 2018, "producer": "Domaine de la Romanée-Conti", "varietals": ["Pinot Noir"], "region": "Burgundy", "country": "France", "label_image_url": "https://www.vivino.com/US/en/domaine-de-la-denante-bourgogne-pinot-noir/w/6790938?year=2020"},
    {"name": "Barolo", "vintage": 2016, "producer": "Giacomo Conterno", "varietals": ["Nebbiolo"], "region": "Piedmont", "country": "Italy", "label_image_url": "https://www.vivino.com/US/en/giacomo-conterno-barolo-cerretta/w/3127311?year=2015"},
    {"name": "Brunello di Montalcino", "vintage": 2015, "producer": "Biondi-Santi", "varietals": ["Sangiovese"], "region": "Tuscany", "country": "Italy", "label_image_url": "https://www.vivino.com/en/biondi-santi-brunello-di-montalcino/w/1558589"},
    {"name": "Amarone della Valpolicella", "vintage": 2017, "producer": "Allegrini", "varietals": ["Corvina", "Rondinella"], "region": "Veneto", "country": "Italy", "label_image_url": "https://www.vivino.com/US/en/allegrini-veneto-amarone-della-valpolicella-classico/w/8195?year=2007"},
    {"name": "Chianti Classico", "vintage": 2018, "producer": "Castello di Brolio", "varietals": ["Sangiovese"], "region": "Tuscany", "country": "Italy", "label_image_url": "https://www.vivino.com/ricasoli-castello-di-brolio-vin-santo-del-chianti-classico/w/1565715"},
    {"name": "Rioja Reserva", "vintage": 2015, "producer": "Marqués de Riscal", "varietals": ["Tempranillo"], "region": "Rioja", "country": "Spain", "label_image_url": "https://www.vivino.com/CA/en/marques-de-riscal-rioja-reserva/w/1163903?year=2019"},
    {"name": "Priorat", "vintage": 2017, "producer": "Clos Mogador", "varietals": ["Garnacha", "Carignan"], "region": "Catalonia", "country": "Spain", "label_image_url": "https://www.vivino.com/clos-mogador-manyetes/w/1188549"},
    {"name": "Ribera del Duero", "vintage": 2016, "producer": "Pesquera", "varietals": ["Tempranillo"], "region": "Ribera del Duero", "country": "Spain", "label_image_url": "https://www.vivino.com/toplists/wine_style_awards_2016_spanish-ribera-del-duero-red"},
    {"name": "Malbec Reserva", "vintage": 2018, "producer": "Catena Zapata", "varietals": ["Malbec"], "region": "Mendoza", "country": "Argentina", "label_image_url": "https://www.vivino.com/US/en/catena-zapata-nicasia-vineyard-altamira-malbec/w/68744?year=2003"},
    {"name": "Carmenère", "vintage": 2017, "producer": "Concha y Toro", "varietals": ["Carmenère"], "region": "Colchagua Valley", "country": "Chile", "label_image_url": "https://www.vivino.com/US/en/concha-y-toro-chardonnay/w/1725986?year=2019"},
    {"name": "Pinot Noir", "vintage": 2019, "producer": "Domaine Drouhin", "varietals": ["Pinot Noir"], "region": "Willamette Valley", "country": "United States", "label_image_url": "https://www.vivino.com/US/en/joseph-drouhin-bourgogne-pinot-noir/w/1191260?year=2019"},
    {"name": "Zinfandel", "vintage": 2018, "producer": "Ridge Vineyards", "varietals": ["Zinfandel"], "region": "Sonoma County", "country": "United States", "label_image_url": "https://www.vivino.com/US/es/ridge-vineyards-bedrock-zinfandel/w/11746394"},
    {"name": "Syrah", "vintage": 2017, "producer": "Sine Qua Non", "varietals": ["Syrah"], "region": "Central Coast", "country": "United States", "label_image_url": "https://www.vivino.com/US/en/sine-qua-non-eleven-confessions-syrah/w/11591411"},
    {"name": "Merlot", "vintage": 2018, "producer": "Duckhorn Vineyards", "varietals": ["Merlot"], "region": "Napa Valley", "country": "United States", "label_image_url": "https://www.vivino.com/duckhorn-three-palms-vineyard-merlot/w/1128389?year=2018"},
    {"name": "Cabernet Franc", "vintage": 2017, "producer": "Lang & Reed", "varietals": ["Cabernet Franc"], "region": "Napa Valley", "country": "United States", "label_image_url": "https://www.vivino.com/US/en/lang-and-reed-wine-company-premiere-napa-valley-cabernet-franc/w/10892899"},
    {"name": "Grenache", "vintage": 2019, "producer": "Tablas Creek", "varietals": ["Grenache"], "region": "Paso Robles", "country": "United States", "label_image_url": "https://www.vivino.com/US/en/tablas-creek-vineyard-grenache/w/2565412?year=2020"},
    {"name": "Mourvèdre", "vintage": 2018, "producer": "Tablas Creek", "varietals": ["Mourvèdre"], "region": "Paso Robles", "country": "United States", "label_image_url": "https://www.vivino.com/tablas-creek-vineyard-patelin-de-tablas-rose/w/2457883"},
    {"name": "Petite Sirah", "vintage": 2017, "producer": "Ridge Vineyards", "varietals": ["Petite Sirah"], "region": "Sonoma County", "country": "United States"},
    {"name": "Sangiovese", "vintage": 2018, "producer": "Castello di Amorosa", "varietals": ["Sangiovese"], "region": "Napa Valley", "country": "United States", "label_image_url": "https://www.vivino.com/en/castello-di-amorosa-sangiovese/w/1714586"},
    {"name": "Tempranillo", "vintage": 2019, "producer": "Tablas Creek", "varietals": ["Tempranillo"], "region": "Paso Robles", "country": "United States", "label_image_url": "https://www.vivino.com/US/en/abacela-fiesta-tempranillo/w/2874736?year=2019"},
]

WHITE_WINES = [
    {"name": "Domaine Leflaive Montrachet", "vintage": 2018, "producer": "Domaine Leflaive", "varietals": ["Chardonnay"], "region": "Burgundy", "country": "France", "label_image_url": "https://www.vivino.com/en/domaine-leflaive-leflaive-associes-puligny-montrachet/w/7540902"},
    {"name": "Kistler Chardonnay", "vintage": 2019, "producer": "Kistler Vineyards", "varietals": ["Chardonnay"], "region": "Sonoma County", "country": "United States", "label_image_url": "https://www.vivino.com/US/en/pellegrini-vineyards-estate-grown-stainless-steel-chardonnay/w/14109?year=2019"},
    {"name": "Rombauer Chardonnay", "vintage": 2018, "producer": "Rombauer Vineyards", "varietals": ["Chardonnay"], "region": "Napa Valley", "country": "United States", "label_image_url": "https://www.vivino.com/US/en/mascota-vineyards-mendoza-opi-chardonnay/w/2085675?year=2018"},
    {"name": "Cloudy Bay Sauvignon Blanc", "vintage": 2020, "producer": "Cloudy Bay", "varietals": ["Sauvignon Blanc"], "region": "Marlborough", "country": "New Zealand", "label_image_url": "https://www.vivino.com/US/en/cloudy-bay-sauvignon-blanc/w/18978?year=2020"},
    {"name": "Sancerre", "vintage": 2019, "producer": "Domaine Vacheron", "varietals": ["Sauvignon Blanc"], "region": "Loire Valley", "country": "France", "label_image_url": "https://www.vivino.com/US/en/le-garenne-sancerre-blanc/w/9659773?year=2019"},
    {"name": "Riesling", "vintage": 2018, "producer": "Dr. Loosen", "varietals": ["Riesling"], "region": "Mosel", "country": "Germany", "label_image_url": "https://www.vivino.com/US/en/dr-loosen-riesling-villa-loosen/w/1568115?year=2018"},
    {"name": "Gewürztraminer", "vintage": 2019, "producer": "Trimbach", "varietals": ["Gewürztraminer"], "region": "Alsace", "country": "France", "label_image_url": "https://www.vivino.com/US/en/trimbach-alsace-muscat-alsace-reserve/w/63704?year=2019"},
    {"name": "Pinot Grigio", "vintage": 2020, "producer": "Santa Margherita", "varietals": ["Pinot Grigio"], "region": "Veneto", "country": "Italy", "label_image_url": "https://www.vivino.com/US/en/santa-margherita-laudato-pinot-grigio/w/7971213?year=2018"},
    {"name": "Viognier", "vintage": 2018, "producer": "Condrieu", "varietals": ["Viognier"], "region": "Rhône Valley", "country": "France", "label_image_url": "https://www.vivino.com/US/en/le-paradou-viognier/w/16489?year=2018"},
    {"name": "Albariño", "vintage": 2019, "producer": "Bodegas Martín Códax", "varietals": ["Albariño"], "region": "Rías Baixas", "country": "Spain", "label_image_url": "https://www.vivino.com/US/en/bodegas-martin-codax-rias-baixas-albarino-el-jardin-de-ana/w/1285971?year=2019"},
]


def create_cellars():
    """Create sample cellars"""
    timestamp = get_current_timestamp()
    
    # Main Wine Cellar - 6 shelves, mix of single and double
    main_cellar_shelves = [
        Shelf(positions=8, is_double=True),
        Shelf(positions=8, is_double=True),
        Shelf(positions=8, is_double=True),
        Shelf(positions=8, is_double=True),
        Shelf(positions=8, is_double=False),
        Shelf(positions=8, is_double=False),
    ]
    main_cellar = Cellar(
        id=generate_id(),
        name="Main Wine Cellar",
        shelves=main_cellar_shelves,
        temperature=55.0,
        version=1,
        created_at=timestamp,
        updated_at=timestamp
    )
    
    # Secondary Cellar - 7 shelves, mix of single and double
    secondary_cellar_shelves = [
        Shelf(positions=6, is_double=True),
        Shelf(positions=6, is_double=True),
        Shelf(positions=6, is_double=False),
        Shelf(positions=6, is_double=False),
        Shelf(positions=6, is_double=False),
        Shelf(positions=6, is_double=False),
        Shelf(positions=6, is_double=False),
    ]
    secondary_cellar = Cellar(
        id=generate_id(),
        name="Secondary Cellar",
        shelves=secondary_cellar_shelves,
        temperature=58.0,
        version=1,
        created_at=timestamp,
        updated_at=timestamp
    )
    
    return [main_cellar, secondary_cellar]


def create_wine_references():
    """Create wine references from the sample data"""
    references = []
    timestamp = get_current_timestamp()

    all_wines = RED_WINES + WHITE_WINES
    total_wines = len(all_wines)

    print(f"Processing {total_wines} wines...")
    print("Using hardcoded label_image_url if available, otherwise attempting to fetch...\n")

    # Create 40 red wine references
    for i, wine_data in enumerate(RED_WINES, 1):
        print(f"[{i}/{len(RED_WINES)}] Processing: {wine_data['name']} {wine_data['vintage']}")
        # Use hardcoded label_image_url if available, otherwise try to fetch
        label_url = wine_data.get("label_image_url")
        if not label_url:
            label_url = get_wine_label_url(wine_data["name"], wine_data["producer"], wine_data["vintage"])
            if label_url:
                print(f"  ✓ Found: {label_url[:60]}...")
            else:
                print(f"  ✗ No image found - using None")
        else:
            print(f"  ✓ Using hardcoded URL: {label_url[:60]}...")

        reference = WineReference(
            id=generate_id(),
            name=wine_data["name"],
            type="Red",
            vintage=wine_data["vintage"],
            producer=wine_data["producer"],
            varietals=wine_data["varietals"],
            region=wine_data["region"],
            country=wine_data["country"],
            rating=4,  # Default rating
            tasting_notes=f"Excellent {wine_data['name']} from {wine_data['region']}",
            label_image_url=label_url,  # Can be None if not found
            version=1,
            created_at=timestamp,
            updated_at=timestamp
        )
        references.append(reference)
        
        # Rate limiting - be respectful (increased delay to avoid 429 errors)
        time.sleep(1.0)
    
    # Create 10 white wine references
    for i, wine_data in enumerate(WHITE_WINES, 1):
        print(f"[{i}/{len(WHITE_WINES)}] Processing: {wine_data['name']} {wine_data['vintage']}")
        # Use hardcoded label_image_url if available, otherwise try to fetch
        label_url = wine_data.get("label_image_url")
        if not label_url:
            label_url = get_wine_label_url(wine_data["name"], wine_data["producer"], wine_data["vintage"])
            if label_url:
                print(f"  ✓ Found: {label_url[:60]}...")
            else:
                print(f"  ✗ No image found - using None")
        else:
            print(f"  ✓ Using hardcoded URL: {label_url[:60]}...")

        reference = WineReference(
            id=generate_id(),
            name=wine_data["name"],
            type="White",
            vintage=wine_data["vintage"],
            producer=wine_data["producer"],
            varietals=wine_data["varietals"],
            region=wine_data["region"],
            country=wine_data["country"],
            rating=4,  # Default rating
            tasting_notes=f"Excellent {wine_data['name']} from {wine_data['region']}",
            label_image_url=label_url,  # Can be None if not found
            version=1,
            created_at=timestamp,
            updated_at=timestamp
        )
        references.append(reference)
        
        # Rate limiting - be respectful (increased delay to avoid 429 errors)
        time.sleep(1.0)
    
    return references


def create_wine_instances(references, cellars):
    """Create 65 wine instances (50 red, 15 white) and assign them to cellars randomly"""
    instances = []
    timestamp = get_current_timestamp()
    
    # Collect all available positions across all cellars
    available_positions = []
    for cellar in cellars:
        for shelf_index, shelf in enumerate(cellar.shelves):
            if shelf.is_double:
                for side in ['front', 'back']:
                    for pos in range(shelf.positions):
                        if cellar.is_position_available(shelf_index, side, pos):
                            available_positions.append((cellar, shelf_index, side, pos))
            else:
                for pos in range(shelf.positions):
                    if cellar.is_position_available(shelf_index, 'single', pos):
                        available_positions.append((cellar, shelf_index, 'single', pos))
    
    # Randomize the available positions
    random.shuffle(available_positions)
    
    if len(available_positions) < 65:
        raise ValueError(f"Not enough available positions ({len(available_positions)}) for 65 wine instances")
    
    # Separate red and white references
    red_references = [ref for ref in references if ref.type == 'Red']
    white_references = [ref for ref in references if ref.type == 'White']
    
    # We need 65 instances total: 50 red, 15 white
    instance_count = 0
    
    # Create 50 red wine instances
    # Some red references should have multiple instances
    red_instance_count = 0
    red_reference_index = 0
    
    while red_instance_count < 50:
        reference = red_references[red_reference_index % len(red_references)]
        
        # Determine how many instances for this reference
        # First 10 red references get 2 instances each (20 instances)
        # Remaining red references get 1 instance each
        if red_reference_index < 10:
            num_instances = 2
        else:
            num_instances = 1
        
        # Create instances for this reference
        for i in range(num_instances):
            if red_instance_count >= 50:
                break
            
            # Get a random available position
            cellar, shelf_index, side, position = available_positions[instance_count]
            
            # Create instance
            instance = WineInstance(
                id=generate_id(),
                reference=reference,
                price=round(50.0 + (instance_count * 2.5), 2),  # Varying prices
                purchase_date="2024-01-15",
                drink_by_date="2030-01-15",
                consumed=False,
                consumed_date=None,
                stored_date=timestamp,
                version=1,
                created_at=timestamp,
                updated_at=timestamp
            )
            
            # Assign to cellar position
            cellar.assign_wine_to_position(shelf_index, side, position, instance)
            
            instances.append(instance)
            instance_count += 1
            red_instance_count += 1
        
        red_reference_index += 1
    
    # Create 15 white wine instances
    # Cycle through white references to distribute them
    white_reference_index = 0
    
    for white_instance_count in range(15):
        reference = white_references[white_reference_index % len(white_references)]
        
        # Get a random available position
        cellar, shelf_index, side, position = available_positions[instance_count]
        shelf = cellar.shelves[shelf_index]
        
        # Create instance
        instance = WineInstance(
            id=generate_id(),
            reference=reference,
            price=round(30.0 + (instance_count * 2.5), 2),  # Varying prices for white wines
            purchase_date="2024-01-15",
            drink_by_date="2030-01-15",
            consumed=False,
            consumed_date=None,
            stored_date=timestamp,
            version=1,
            created_at=timestamp,
            updated_at=timestamp
        )
        
        # Assign to cellar position
        cellar.assign_wine_to_position(shelf_index, side, position, instance)
        
        instances.append(instance)
        instance_count += 1
        white_reference_index += 1
    
    return instances


def main():
    """Main function to populate all data"""
    print("Creating cellars...")
    cellars = create_cellars()
    print(f"Created {len(cellars)} cellars")
    
    print("Creating wine references...")
    references = create_wine_references()
    print(f"Created {len(references)} wine references ({sum(1 for r in references if r.type == 'Red')} red, {sum(1 for r in references if r.type == 'White')} white)")
    
    print("Creating wine instances...")
    instances = create_wine_instances(references, cellars)
    red_count = sum(1 for inst in instances if inst.reference.type == 'Red')
    white_count = sum(1 for inst in instances if inst.reference.type == 'White')
    print(f"Created {len(instances)} wine instances ({red_count} red, {white_count} white)")
    
    # Serialize and save to DynamoDB
    print("Saving data to DynamoDB...")
    cellars_data = [serialize_cellar(c) for c in cellars]
    references_data = [serialize_wine_reference(r) for r in references]
    instances_data = [serialize_wine_instance(i) for i in instances]
    
    # Save cellars
    for cellar_data in cellars_data:
        dynamodb_put_cellar(cellar_data)
    
    # Save wine references
    for reference_data in references_data:
        dynamodb_put_wine_reference(reference_data)
    
    # Save wine instances (uses batch writer)
    dynamodb_save_wine_instances(instances_data)
    
    print("Data population complete!")
    print(f"\nSummary:")
    print(f"  Cellars: {len(cellars)}")
    print(f"    - {cellars[0].name}: {len(cellars[0].shelves)} shelves, capacity {cellars[0].capacity}")
    print(f"    - {cellars[1].name}: {len(cellars[1].shelves)} shelves, capacity {cellars[1].capacity}")
    print(f"  Wine References: {len(references)}")
    print(f"  Wine Instances: {len(instances)}")


if __name__ == '__main__':
    main()
