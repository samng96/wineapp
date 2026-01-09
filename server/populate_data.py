"""Script to populate the server with sample data"""
import json
import os
import random
from server.utils import (
    DATA_DIR, CELLARS_FILE, WINE_REFERENCES_FILE, WINE_INSTANCES_FILE,
    generate_id, get_current_timestamp, init_data_files
)
from server.models import Shelf, Cellar, WineReference, WineInstance, register_wine_reference
from server.storage import serialize_cellar, serialize_wine_reference, serialize_wine_instance

# Sample wine data (40 red wines, 10 white wines)
RED_WINES = [
    {"name": "Caymus Cabernet Sauvignon", "vintage": 2019, "producer": "Caymus Vineyards", "region": "Napa Valley", "country": "USA", "varietals": ["Cabernet Sauvignon"]},
    {"name": "Opus One", "vintage": 2018, "producer": "Opus One Winery", "region": "Napa Valley", "country": "USA", "varietals": ["Cabernet Sauvignon", "Merlot", "Cabernet Franc"]},
    {"name": "Screaming Eagle Cabernet Sauvignon", "vintage": 2017, "producer": "Screaming Eagle", "region": "Napa Valley", "country": "USA", "varietals": ["Cabernet Sauvignon"]},
    {"name": "Domaine de la Romanée-Conti", "vintage": 2018, "producer": "DRC", "region": "Burgundy", "country": "France", "varietals": ["Pinot Noir"]},
    {"name": "Château Margaux", "vintage": 2015, "producer": "Château Margaux", "region": "Bordeaux", "country": "France", "varietals": ["Cabernet Sauvignon", "Merlot", "Cabernet Franc", "Petit Verdot"]},
    {"name": "Château Lafite Rothschild", "vintage": 2016, "producer": "Château Lafite Rothschild", "region": "Bordeaux", "country": "France", "varietals": ["Cabernet Sauvignon", "Merlot", "Cabernet Franc", "Petit Verdot"]},
    {"name": "Penfolds Grange", "vintage": 2017, "producer": "Penfolds", "region": "Barossa Valley", "country": "Australia", "varietals": ["Shiraz"]},
    {"name": "Sassicaia", "vintage": 2018, "producer": "Tenuta San Guido", "region": "Tuscany", "country": "Italy", "varietals": ["Cabernet Sauvignon", "Cabernet Franc"]},
    {"name": "Tignanello", "vintage": 2019, "producer": "Antinori", "region": "Tuscany", "country": "Italy", "varietals": ["Sangiovese", "Cabernet Sauvignon", "Cabernet Franc"]},
    {"name": "Vega Sicilia Unico", "vintage": 2012, "producer": "Vega Sicilia", "region": "Ribera del Duero", "country": "Spain", "varietals": ["Tempranillo", "Cabernet Sauvignon"]},
    {"name": "Silver Oak Cabernet Sauvignon", "vintage": 2018, "producer": "Silver Oak", "region": "Napa Valley", "country": "USA", "varietals": ["Cabernet Sauvignon"]},
    {"name": "Jordan Cabernet Sauvignon", "vintage": 2017, "producer": "Jordan Vineyard", "region": "Sonoma County", "country": "USA", "varietals": ["Cabernet Sauvignon", "Merlot", "Petit Verdot", "Malbec"]},
    {"name": "Stag's Leap Wine Cellars Cask 23", "vintage": 2016, "producer": "Stag's Leap Wine Cellars", "region": "Napa Valley", "country": "USA", "varietals": ["Cabernet Sauvignon"]},
    {"name": "Ridge Monte Bello", "vintage": 2018, "producer": "Ridge Vineyards", "region": "Santa Cruz Mountains", "country": "USA", "varietals": ["Cabernet Sauvignon", "Merlot", "Cabernet Franc", "Petit Verdot"]},
    {"name": "Shafer Hillside Select", "vintage": 2017, "producer": "Shafer Vineyards", "region": "Napa Valley", "country": "USA", "varietals": ["Cabernet Sauvignon"]},
    {"name": "Château Pétrus", "vintage": 2015, "producer": "Château Pétrus", "region": "Pomerol", "country": "France", "varietals": ["Merlot", "Cabernet Franc"]},
    {"name": "Château Cheval Blanc", "vintage": 2016, "producer": "Château Cheval Blanc", "region": "Saint-Émilion", "country": "France", "varietals": ["Cabernet Franc", "Merlot"]},
    {"name": "Dom Pérignon", "vintage": 2012, "producer": "Moët & Chandon", "region": "Champagne", "country": "France", "varietals": ["Chardonnay", "Pinot Noir"]},
    {"name": "Cristal", "vintage": 2013, "producer": "Louis Roederer", "region": "Champagne", "country": "France", "varietals": ["Chardonnay", "Pinot Noir"]},
    {"name": "Krug Grande Cuvée", "vintage": 2014, "producer": "Krug", "region": "Champagne", "country": "France", "varietals": ["Chardonnay", "Pinot Noir", "Pinot Meunier"]},
    {"name": "Burgundy Pinot Noir", "vintage": 2018, "producer": "Domaine de la Romanée-Conti", "region": "Burgundy", "country": "France", "varietals": ["Pinot Noir"]},
    {"name": "Barolo", "vintage": 2016, "producer": "Giacomo Conterno", "region": "Piedmont", "country": "Italy", "varietals": ["Nebbiolo"]},
    {"name": "Brunello di Montalcino", "vintage": 2015, "producer": "Biondi-Santi", "region": "Tuscany", "country": "Italy", "varietals": ["Sangiovese"]},
    {"name": "Amarone della Valpolicella", "vintage": 2017, "producer": "Allegrini", "region": "Veneto", "country": "Italy", "varietals": ["Corvina", "Rondinella", "Molinara"]},
    {"name": "Chianti Classico", "vintage": 2018, "producer": "Castello di Brolio", "region": "Tuscany", "country": "Italy", "varietals": ["Sangiovese"]},
    {"name": "Rioja Reserva", "vintage": 2015, "producer": "Marqués de Riscal", "region": "Rioja", "country": "Spain", "varietals": ["Tempranillo", "Garnacha", "Graciano"]},
    {"name": "Priorat", "vintage": 2017, "producer": "Clos Mogador", "region": "Priorat", "country": "Spain", "varietals": ["Garnacha", "Cariñena", "Syrah", "Cabernet Sauvignon"]},
    {"name": "Ribera del Duero", "vintage": 2016, "producer": "Pesquera", "region": "Ribera del Duero", "country": "Spain", "varietals": ["Tempranillo"]},
    {"name": "Malbec Reserva", "vintage": 2018, "producer": "Catena Zapata", "region": "Mendoza", "country": "Argentina", "varietals": ["Malbec"]},
    {"name": "Carmenère", "vintage": 2017, "producer": "Concha y Toro", "region": "Colchagua Valley", "country": "Chile", "varietals": ["Carmenère"]},
    {"name": "Pinot Noir", "vintage": 2019, "producer": "Domaine Drouhin", "region": "Willamette Valley", "country": "USA", "varietals": ["Pinot Noir"]},
    {"name": "Zinfandel", "vintage": 2018, "producer": "Ridge Vineyards", "region": "Sonoma County", "country": "USA", "varietals": ["Zinfandel"]},
    {"name": "Syrah", "vintage": 2017, "producer": "Sine Qua Non", "region": "Santa Barbara County", "country": "USA", "varietals": ["Syrah"]},
    {"name": "Merlot", "vintage": 2018, "producer": "Duckhorn Vineyards", "region": "Napa Valley", "country": "USA", "varietals": ["Merlot"]},
    {"name": "Cabernet Franc", "vintage": 2017, "producer": "Lang & Reed", "region": "Napa Valley", "country": "USA", "varietals": ["Cabernet Franc"]},
    {"name": "Grenache", "vintage": 2019, "producer": "Tablas Creek", "region": "Paso Robles", "country": "USA", "varietals": ["Grenache"]},
    {"name": "Mourvèdre", "vintage": 2018, "producer": "Tablas Creek", "region": "Paso Robles", "country": "USA", "varietals": ["Mourvèdre"]},
    {"name": "Petite Sirah", "vintage": 2017, "producer": "Ridge Vineyards", "region": "Sonoma County", "country": "USA", "varietals": ["Petite Sirah"]},
    {"name": "Sangiovese", "vintage": 2018, "producer": "Castello di Amorosa", "region": "Napa Valley", "country": "USA", "varietals": ["Sangiovese"]},
    {"name": "Tempranillo", "vintage": 2019, "producer": "Tablas Creek", "region": "Paso Robles", "country": "USA", "varietals": ["Tempranillo"]},
]

WHITE_WINES = [
    {"name": "Domaine Leflaive Montrachet", "vintage": 2018, "producer": "Domaine Leflaive", "region": "Burgundy", "country": "France", "varietals": ["Chardonnay"]},
    {"name": "Kistler Chardonnay", "vintage": 2019, "producer": "Kistler Vineyards", "region": "Sonoma County", "country": "USA", "varietals": ["Chardonnay"]},
    {"name": "Rombauer Chardonnay", "vintage": 2018, "producer": "Rombauer Vineyards", "region": "Napa Valley", "country": "USA", "varietals": ["Chardonnay"]},
    {"name": "Cloudy Bay Sauvignon Blanc", "vintage": 2020, "producer": "Cloudy Bay", "region": "Marlborough", "country": "New Zealand", "varietals": ["Sauvignon Blanc"]},
    {"name": "Sancerre", "vintage": 2019, "producer": "Domaine Vacheron", "region": "Loire Valley", "country": "France", "varietals": ["Sauvignon Blanc"]},
    {"name": "Riesling", "vintage": 2018, "producer": "Dr. Loosen", "region": "Mosel", "country": "Germany", "varietals": ["Riesling"]},
    {"name": "Gewürztraminer", "vintage": 2019, "producer": "Trimbach", "region": "Alsace", "country": "France", "varietals": ["Gewürztraminer"]},
    {"name": "Pinot Grigio", "vintage": 2020, "producer": "Santa Margherita", "region": "Veneto", "country": "Italy", "varietals": ["Pinot Grigio"]},
    {"name": "Viognier", "vintage": 2018, "producer": "Condrieu", "region": "Rhône Valley", "country": "France", "varietals": ["Viognier"]},
    {"name": "Albariño", "vintage": 2019, "producer": "Bodegas Martín Códax", "region": "Rías Baixas", "country": "Spain", "varietals": ["Albariño"]},
]


def create_cellars():
    """Create the two cellars with specified shelf configurations"""
    timestamp = get_current_timestamp()
    
    # Cellar 1: Uniform shelves - all same size, same isDouble
    # Let's make it 6 shelves, all double-sided with 8 positions each
    cellar1_shelves = [Shelf(positions=8, is_double=True) for _ in range(6)]
    cellar1 = Cellar(
        id=generate_id(),
        name="Main Wine Cellar",
        shelves=cellar1_shelves,
        temperature=55,
        version=1,
        created_at=timestamp,
        updated_at=timestamp
    )
    
    # Cellar 2: Mixed shelves
    # 5 shelves on top: double-sided with 5 positions each side
    # 2 shelves on bottom: single-sided with 8 positions each
    cellar2_shelves = []
    cellar2_shelves.extend([Shelf(positions=5, is_double=True) for _ in range(5)])  # Top 5
    cellar2_shelves.extend([Shelf(positions=8, is_double=False) for _ in range(2)])  # Bottom 2
    
    cellar2 = Cellar(
        id=generate_id(),
        name="Secondary Cellar",
        shelves=cellar2_shelves,
        temperature=58,
        version=1,
        created_at=timestamp,
        updated_at=timestamp
    )
    
    return [cellar1, cellar2]


def create_wine_references():
    """Create wine references from the sample data"""
    references = []
    timestamp = get_current_timestamp()
    
    # Create 40 red wine references
    for wine_data in RED_WINES:
        label_url = get_wine_label_url(wine_data["name"], wine_data["producer"], wine_data["vintage"])
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
            label_image_url=label_url,
            version=1,
            created_at=timestamp,
            updated_at=timestamp
        )
        register_wine_reference(reference)
        references.append(reference)
    
    # Create 10 white wine references
    for wine_data in WHITE_WINES:
        label_url = get_wine_label_url(wine_data["name"], wine_data["producer"], wine_data["vintage"])
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
            label_image_url=label_url,
            version=1,
            created_at=timestamp,
            updated_at=timestamp
        )
        register_wine_reference(reference)
        references.append(reference)
    
    return references


def get_wine_label_url(wine_name, producer, vintage):
    """Generate a wine label image URL using Unsplash API for wine bottle images"""
    # Use Unsplash Source API for wine bottle images
    # Format: https://source.unsplash.com/featured/?wine+bottle
    # For more specific searches, we can use the wine name
    search_terms = wine_name.lower().replace(" ", "+").replace("'", "")
    # Use a generic wine bottle image from Unsplash with search terms
    return f"https://source.unsplash.com/400x600/?wine+bottle+{search_terms}"


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
            shelf = cellar.shelves[shelf_index]
            is_front = (side == 'front') if shelf.is_double else True
            
            # Create location tuple
            location = (cellar, shelf, position, is_front)
            
            # Create instance
            instance = WineInstance(
                id=generate_id(),
                reference=reference,
                location=location,
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
        is_front = (side == 'front') if shelf.is_double else True
        
        # Create location tuple
        location = (cellar, shelf, position, is_front)
        
        # Create instance
        instance = WineInstance(
            id=generate_id(),
            reference=reference,
            location=location,
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
    # Initialize data files
    init_data_files()
    
    # Clear existing data
    from server.models import clear_wine_references_registry
    clear_wine_references_registry()
    
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
    
    # Serialize and save
    print("Saving data...")
    cellars_data = [serialize_cellar(c) for c in cellars]
    references_data = [serialize_wine_reference(r) for r in references]
    instances_data = [serialize_wine_instance(i) for i in instances]
    
    with open(CELLARS_FILE, 'w') as f:
        json.dump(cellars_data, f, indent=2)
    
    with open(WINE_REFERENCES_FILE, 'w') as f:
        json.dump(references_data, f, indent=2)
    
    with open(WINE_INSTANCES_FILE, 'w') as f:
        json.dump(instances_data, f, indent=2)
    
    print("Data population complete!")
    print(f"\nSummary:")
    print(f"  Cellars: {len(cellars)}")
    print(f"    - {cellars[0].name}: {len(cellars[0].shelves)} shelves, capacity {cellars[0].capacity}")
    print(f"    - {cellars[1].name}: {len(cellars[1].shelves)} shelves, capacity {cellars[1].capacity}")
    print(f"  Wine References: {len(references)}")
    print(f"  Wine Instances: {len(instances)}")


if __name__ == '__main__':
    main()
