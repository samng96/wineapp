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
    Search Google Images specifically for Vivino wine label images
    Uses site:vivino.com to restrict results to Vivino only
    Focuses on labels by adding 'label' to the search query
    """
    try:
        # Search specifically on Vivino for wine labels
        search_query = quote(f'site:vivino.com {query} wine label')
        url = f"https://www.google.com/search?q={search_query}&tbm=isch&safe=active"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        html = response.text
        
        # Method 1: Look for "ou":"URL" pattern (Google's embedded image data)
        matches = re.findall(r'"ou":"(https?://[^"]+)"', html)
        vivino_urls = []
        
        for match in matches[:30]:  # Check first 30 matches
            match_lower = match.lower()
            if ('google' not in match_lower and 'gstatic' not in match_lower and 
                'doubleclick' not in match_lower):
                if 'vivino.com' in match_lower:
                    if any(ext in match_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']) or 'image' in match_lower or 'label' in match_lower:
                        vivino_urls.append(match)
        
        if vivino_urls:
            return vivino_urls[0]
        
        # Method 2: Look for Vivino CDN URLs
        vivino_cdn_pattern = r'https?://[^\s"<>\)]*images\.vivino\.com[^\s"<>\)]+'
        matches = re.findall(vivino_cdn_pattern, html, re.IGNORECASE)
        if matches:
            for match in matches:
                if any(ext in match.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']) or 'label' in match.lower():
                    return match
            return matches[0]
        
        return None
    except Exception as e:
        return None


def get_wine_label_url(wine_name, producer, vintage):
    """Get a wine label image URL from Vivino via Google Images search"""
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
    {"name": "Caymus Cabernet Sauvignon", "vintage": 2019, "producer": "Caymus Vineyards", "varietals": ["Cabernet Sauvignon"], "region": "Napa Valley", "country": "United States"},
    {"name": "Opus One", "vintage": 2018, "producer": "Opus One Winery", "varietals": ["Cabernet Sauvignon", "Cabernet Franc", "Merlot"], "region": "Napa Valley", "country": "United States"},
    {"name": "Screaming Eagle Cabernet Sauvignon", "vintage": 2017, "producer": "Screaming Eagle", "varietals": ["Cabernet Sauvignon"], "region": "Napa Valley", "country": "United States"},
    {"name": "Domaine de la Romanée-Conti", "vintage": 2018, "producer": "DRC", "varietals": ["Pinot Noir"], "region": "Burgundy", "country": "France"},
    {"name": "Château Margaux", "vintage": 2015, "producer": "Château Margaux", "varietals": ["Cabernet Sauvignon", "Merlot"], "region": "Bordeaux", "country": "France"},
    {"name": "Château Lafite Rothschild", "vintage": 2016, "producer": "Château Lafite Rothschild", "varietals": ["Cabernet Sauvignon", "Merlot"], "region": "Bordeaux", "country": "France"},
    {"name": "Penfolds Grange", "vintage": 2017, "producer": "Penfolds", "varietals": ["Shiraz"], "region": "South Australia", "country": "Australia"},
    {"name": "Sassicaia", "vintage": 2018, "producer": "Tenuta San Guido", "varietals": ["Cabernet Sauvignon", "Cabernet Franc"], "region": "Tuscany", "country": "Italy"},
    {"name": "Tignanello", "vintage": 2019, "producer": "Antinori", "varietals": ["Sangiovese", "Cabernet Sauvignon"], "region": "Tuscany", "country": "Italy"},
    {"name": "Vega Sicilia Unico", "vintage": 2012, "producer": "Vega Sicilia", "varietals": ["Tempranillo", "Cabernet Sauvignon"], "region": "Ribera del Duero", "country": "Spain"},
    {"name": "Silver Oak Cabernet Sauvignon", "vintage": 2018, "producer": "Silver Oak", "varietals": ["Cabernet Sauvignon"], "region": "Napa Valley", "country": "United States"},
    {"name": "Jordan Cabernet Sauvignon", "vintage": 2017, "producer": "Jordan Vineyard", "varietals": ["Cabernet Sauvignon"], "region": "Sonoma County", "country": "United States"},
    {"name": "Stag's Leap Wine Cellars Cask 23", "vintage": 2016, "producer": "Stag's Leap Wine Cellars", "varietals": ["Cabernet Sauvignon"], "region": "Napa Valley", "country": "United States"},
    {"name": "Ridge Monte Bello", "vintage": 2018, "producer": "Ridge Vineyards", "varietals": ["Cabernet Sauvignon"], "region": "Santa Cruz Mountains", "country": "United States"},
    {"name": "Shafer Hillside Select", "vintage": 2017, "producer": "Shafer Vineyards", "varietals": ["Cabernet Sauvignon"], "region": "Napa Valley", "country": "United States"},
    {"name": "Château Pétrus", "vintage": 2015, "producer": "Château Pétrus", "varietals": ["Merlot"], "region": "Pomerol", "country": "France"},
    {"name": "Château Cheval Blanc", "vintage": 2016, "producer": "Château Cheval Blanc", "varietals": ["Cabernet Franc", "Merlot"], "region": "Saint-Émilion", "country": "France"},
    {"name": "Dom Pérignon", "vintage": 2012, "producer": "Moët & Chandon", "varietals": ["Chardonnay", "Pinot Noir"], "region": "Champagne", "country": "France"},
    {"name": "Cristal", "vintage": 2013, "producer": "Louis Roederer", "varietals": ["Chardonnay", "Pinot Noir"], "region": "Champagne", "country": "France"},
    {"name": "Krug Grande Cuvée", "vintage": 2014, "producer": "Krug", "varietals": ["Chardonnay", "Pinot Noir", "Pinot Meunier"], "region": "Champagne", "country": "France"},
    {"name": "Burgundy Pinot Noir", "vintage": 2018, "producer": "Domaine de la Romanée-Conti", "varietals": ["Pinot Noir"], "region": "Burgundy", "country": "France"},
    {"name": "Barolo", "vintage": 2016, "producer": "Giacomo Conterno", "varietals": ["Nebbiolo"], "region": "Piedmont", "country": "Italy"},
    {"name": "Brunello di Montalcino", "vintage": 2015, "producer": "Biondi-Santi", "varietals": ["Sangiovese"], "region": "Tuscany", "country": "Italy"},
    {"name": "Amarone della Valpolicella", "vintage": 2017, "producer": "Allegrini", "varietals": ["Corvina", "Rondinella"], "region": "Veneto", "country": "Italy"},
    {"name": "Chianti Classico", "vintage": 2018, "producer": "Castello di Brolio", "varietals": ["Sangiovese"], "region": "Tuscany", "country": "Italy"},
    {"name": "Rioja Reserva", "vintage": 2015, "producer": "Marqués de Riscal", "varietals": ["Tempranillo"], "region": "Rioja", "country": "Spain"},
    {"name": "Priorat", "vintage": 2017, "producer": "Clos Mogador", "varietals": ["Garnacha", "Carignan"], "region": "Catalonia", "country": "Spain"},
    {"name": "Ribera del Duero", "vintage": 2016, "producer": "Pesquera", "varietals": ["Tempranillo"], "region": "Ribera del Duero", "country": "Spain"},
    {"name": "Malbec Reserva", "vintage": 2018, "producer": "Catena Zapata", "varietals": ["Malbec"], "region": "Mendoza", "country": "Argentina"},
    {"name": "Carmenère", "vintage": 2017, "producer": "Concha y Toro", "varietals": ["Carmenère"], "region": "Colchagua Valley", "country": "Chile"},
    {"name": "Pinot Noir", "vintage": 2019, "producer": "Domaine Drouhin", "varietals": ["Pinot Noir"], "region": "Willamette Valley", "country": "United States"},
    {"name": "Zinfandel", "vintage": 2018, "producer": "Ridge Vineyards", "varietals": ["Zinfandel"], "region": "Sonoma County", "country": "United States"},
    {"name": "Syrah", "vintage": 2017, "producer": "Sine Qua Non", "varietals": ["Syrah"], "region": "Central Coast", "country": "United States"},
    {"name": "Merlot", "vintage": 2018, "producer": "Duckhorn Vineyards", "varietals": ["Merlot"], "region": "Napa Valley", "country": "United States"},
    {"name": "Cabernet Franc", "vintage": 2017, "producer": "Lang & Reed", "varietals": ["Cabernet Franc"], "region": "Napa Valley", "country": "United States"},
    {"name": "Grenache", "vintage": 2019, "producer": "Tablas Creek", "varietals": ["Grenache"], "region": "Paso Robles", "country": "United States"},
    {"name": "Mourvèdre", "vintage": 2018, "producer": "Tablas Creek", "varietals": ["Mourvèdre"], "region": "Paso Robles", "country": "United States"},
    {"name": "Petite Sirah", "vintage": 2017, "producer": "Ridge Vineyards", "varietals": ["Petite Sirah"], "region": "Sonoma County", "country": "United States"},
    {"name": "Sangiovese", "vintage": 2018, "producer": "Castello di Amorosa", "varietals": ["Sangiovese"], "region": "Napa Valley", "country": "United States"},
    {"name": "Tempranillo", "vintage": 2019, "producer": "Tablas Creek", "varietals": ["Tempranillo"], "region": "Paso Robles", "country": "United States"},
]

WHITE_WINES = [
    {"name": "Domaine Leflaive Montrachet", "vintage": 2018, "producer": "Domaine Leflaive", "varietals": ["Chardonnay"], "region": "Burgundy", "country": "France"},
    {"name": "Kistler Chardonnay", "vintage": 2019, "producer": "Kistler Vineyards", "varietals": ["Chardonnay"], "region": "Sonoma County", "country": "United States"},
    {"name": "Rombauer Chardonnay", "vintage": 2018, "producer": "Rombauer Vineyards", "varietals": ["Chardonnay"], "region": "Napa Valley", "country": "United States"},
    {"name": "Cloudy Bay Sauvignon Blanc", "vintage": 2020, "producer": "Cloudy Bay", "varietals": ["Sauvignon Blanc"], "region": "Marlborough", "country": "New Zealand"},
    {"name": "Sancerre", "vintage": 2019, "producer": "Domaine Vacheron", "varietals": ["Sauvignon Blanc"], "region": "Loire Valley", "country": "France"},
    {"name": "Riesling", "vintage": 2018, "producer": "Dr. Loosen", "varietals": ["Riesling"], "region": "Mosel", "country": "Germany"},
    {"name": "Gewürztraminer", "vintage": 2019, "producer": "Trimbach", "varietals": ["Gewürztraminer"], "region": "Alsace", "country": "France"},
    {"name": "Pinot Grigio", "vintage": 2020, "producer": "Santa Margherita", "varietals": ["Pinot Grigio"], "region": "Veneto", "country": "Italy"},
    {"name": "Viognier", "vintage": 2018, "producer": "Condrieu", "varietals": ["Viognier"], "region": "Rhône Valley", "country": "France"},
    {"name": "Albariño", "vintage": 2019, "producer": "Bodegas Martín Códax", "varietals": ["Albariño"], "region": "Rías Baixas", "country": "Spain"},
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

    print(f"Fetching Vivino label images for {total_wines} wines...")
    print("This may take a while due to rate limiting...\n")

    # Create 40 red wine references
    for i, wine_data in enumerate(RED_WINES, 1):
        print(f"[{i}/{len(RED_WINES)}] Fetching label for: {wine_data['name']} {wine_data['vintage']}")
        label_url = get_wine_label_url(wine_data["name"], wine_data["producer"], wine_data["vintage"])
        if label_url:
            print(f"  ✓ Found: {label_url[:60]}...")
        else:
            print(f"  ✗ No image found - using None")

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
        print(f"[{i}/{len(WHITE_WINES)}] Fetching label for: {wine_data['name']} {wine_data['vintage']}")
        label_url = get_wine_label_url(wine_data["name"], wine_data["producer"], wine_data["vintage"])
        if label_url:
            print(f"  ✓ Found: {label_url[:60]}...")
        else:
            print(f"  ✗ No image found - using None")

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
