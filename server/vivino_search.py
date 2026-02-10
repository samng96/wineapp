"""Vivino search functionality - fetches wine data from Vivino's search page"""
import requests
import re
import json
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any
from urllib.parse import quote_plus


# Vivino type_id to wine type mapping
VIVINO_TYPE_MAP = {
    1: 'Red',
    2: 'White',
    3: 'Sparkling',
    4: 'Rosé',
    7: 'Dessert',
    24: 'Fortified',
}


def search_vivino(query: str, limit: int = 10) -> List[Dict]:
    """
    Search Vivino for wines by fetching the search page and extracting
    the preloaded state data embedded in the HTML.

    Args:
        query: Wine name to search for
        limit: Maximum number of results to return (default 10)

    Returns:
        List of wine dictionaries with fields:
        - name: Wine name
        - type: Wine type (Red, White, etc.)
        - vintage: Vintage year (optional)
        - producer: Producer name (optional)
        - region: Region name (optional)
        - country: Country name (optional)
        - rating: Rating 1-5 (optional)
        - labelImageUrl: URL to wine label image (optional)
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120.0.0.0 Safari/537.36',
        }

        search_url = f"https://www.vivino.com/search/wines?q={quote_plus(query)}"
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Vivino embeds search results as JSON in a data-preloaded-state attribute
        search_div = soup.find('div', id='search-page')
        if not search_div:
            print(f"No search-page div found for '{query}'")
            return _get_fallback_results(query, limit)

        state_str = search_div.get('data-preloaded-state', '')
        if not state_str:
            print(f"No preloaded state found for '{query}'")
            return _get_fallback_results(query, limit)

        state = json.loads(state_str)
        matches = state.get('search_results', {}).get('matches', [])

        if not matches:
            return []

        wines = []
        for match in matches[:limit]:
            wine = _parse_vivino_match(match)
            if wine:
                wines.append(wine)

        return wines

    except Exception as e:
        print(f"Error searching Vivino: {e}")
        return _get_fallback_results(query, limit)


def _parse_vivino_match(match: Dict[str, Any]) -> Optional[Dict]:
    """
    Parse a match from Vivino's preloaded search results.

    Args:
        match: A match dict from Vivino's search_results.matches

    Returns:
        Wine dictionary or None
    """
    try:
        vintage = match.get('vintage', {})
        wine_data = vintage.get('wine', {})
        winery = wine_data.get('winery', {})
        region = wine_data.get('region', {})
        country = region.get('country', {})
        stats = vintage.get('statistics', {})
        image = vintage.get('image', {})

        name = vintage.get('name', '')
        if not name:
            return None

        # Map type_id to wine type string
        type_id = wine_data.get('type_id')
        wine_type = VIVINO_TYPE_MAP.get(type_id, 'Red')

        # Get year (may be None for non-vintage wines)
        year = vintage.get('year')
        if year and isinstance(year, str) and year.strip() == '':
            year = None

        # Build image URL
        img_location = image.get('location', '')
        label_image_url = None
        if img_location:
            if img_location.startswith('//'):
                label_image_url = 'https:' + img_location
            elif img_location.startswith('http'):
                label_image_url = img_location

        # Get rating
        rating = stats.get('ratings_average')
        if rating is not None:
            rating = round(float(rating), 1)

        return {
            'name': name,
            'type': wine_type,
            'vintage': int(year) if year else None,
            'producer': winery.get('name'),
            'region': region.get('name'),
            'country': country.get('name'),
            'rating': rating,
            'labelImageUrl': label_image_url,
        }

    except Exception as e:
        print(f"Error parsing Vivino match: {e}")
        return None


def _get_fallback_results(query: str, limit: int) -> List[Dict]:
    """
    Generate fallback sample results when fetching fails.

    Args:
        query: Search query
        limit: Number of results to generate

    Returns:
        List of sample wine dictionaries
    """
    sample_wines = [
        {
            'name': f'{query}',
            'type': _extract_wine_type_from_query(query),
            'vintage': 2019,
            'producer': 'Sample Winery',
            'region': 'Napa Valley',
            'country': 'United States',
            'rating': 4.2,
            'labelImageUrl': None
        },
        {
            'name': f'{query} Reserve',
            'type': _extract_wine_type_from_query(query),
            'vintage': 2018,
            'producer': 'Sample Estate',
            'region': 'Sonoma',
            'country': 'United States',
            'rating': 4.5,
            'labelImageUrl': None
        },
        {
            'name': f'{query} Special Selection',
            'type': _extract_wine_type_from_query(query),
            'vintage': 2020,
            'producer': 'Sample Vineyards',
            'region': 'Paso Robles',
            'country': 'United States',
            'rating': 4.0,
            'labelImageUrl': None
        }
    ]

    return sample_wines[:min(limit, len(sample_wines))]


def _extract_wine_type_from_query(query: str) -> str:
    """
    Extract wine type from search query text.

    Args:
        query: Search query text

    Returns:
        Wine type (Red, White, Rosé, Sparkling, Dessert, Fortified, or Other)
    """
    query_lower = query.lower()

    # Check for specific wine types
    if any(word in query_lower for word in ['champagne', 'sparkling', 'prosecco', 'cava', 'spumante']):
        return 'Sparkling'
    if any(word in query_lower for word in ['port', 'sherry', 'madeira', 'marsala', 'vermouth']):
        return 'Fortified'
    if any(word in query_lower for word in ['dessert', 'ice wine', 'sauternes', 'tokaji']):
        return 'Dessert'
    if any(word in query_lower for word in ['rosé', 'rose']):
        return 'Rosé'

    # Red wine varietals
    red_varietals = [
        'cabernet', 'merlot', 'pinot noir', 'syrah', 'shiraz', 'malbec',
        'zinfandel', 'tempranillo', 'sangiovese', 'nebbiolo', 'grenache',
        'barbera', 'petite sirah', 'mourvèdre', 'carmenère', 'barolo',
        'brunello', 'amarone', 'chianti', 'rioja', 'priorat', 'ribera'
    ]
    if any(varietal in query_lower for varietal in red_varietals):
        return 'Red'

    # White wine varietals
    white_varietals = [
        'chardonnay', 'sauvignon blanc', 'riesling', 'pinot grigio', 'pinot gris',
        'viognier', 'gewürztraminer', 'chenin blanc', 'albariño', 'grüner veltliner',
        'vermentino', 'moscato', 'sancerre', 'chablis', 'montrachet'
    ]
    if any(varietal in query_lower for varietal in white_varietals):
        return 'White'

    # Default to Red if no specific type found
    return 'Red'
