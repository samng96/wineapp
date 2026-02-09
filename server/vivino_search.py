"""Vivino search functionality - scrapes Vivino website to find wines"""
import requests
import re
from bs4 import BeautifulSoup
from typing import List, Dict
from urllib.parse import quote, urljoin


def search_vivino(query: str, limit: int = 10) -> List[Dict]:
    """
    Search Vivino for wines matching the query by scraping Google search results

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
        # Use Google to search for Vivino wines
        # This is more reliable than trying to scrape Vivino directly (which uses heavy JS)
        search_query = quote(f'site:vivino.com/wines {query}')
        url = f"https://www.google.com/search?q={search_query}&num={limit * 2}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        wines = []

        # Find all Google search result links
        search_results = soup.find_all('a', href=True)

        for link in search_results:
            if len(wines) >= limit:
                break

            href = link.get('href', '')

            # Look for Vivino wine URLs in the format: /url?q=https://www.vivino.com/wines/...
            if '/url?q=https://www.vivino.com/wines/' in href:
                # Extract the actual Vivino URL
                vivino_url = href.split('/url?q=')[1].split('&')[0]

                # Extract wine information from the URL and link text
                wine_name = link.get_text(strip=True)

                # Skip if the name is empty or just navigation text
                if not wine_name or len(wine_name) < 3 or wine_name in ['Images', 'Videos', 'News', 'Shopping', 'Maps']:
                    continue

                # Try to extract vintage from the wine name
                vintage = None
                vintage_match = re.search(r'\b(19|20)\d{2}\b', wine_name)
                if vintage_match:
                    vintage = int(vintage_match.group())
                    # Remove vintage from name
                    wine_name = re.sub(r'\s*\b(19|20)\d{2}\b\s*', ' ', wine_name).strip()

                # Clean up the wine name (remove Vivino branding, etc.)
                wine_name = re.sub(r'\s*[-|]\s*Vivino.*$', '', wine_name, flags=re.IGNORECASE)
                wine_name = wine_name.strip()

                # Skip if we filtered out too much
                if not wine_name or len(wine_name) < 2:
                    continue

                # Try to extract producer (usually before a dash or pipe)
                producer = None
                producer_match = re.search(r'^(.+?)\s+[-–—]\s+', wine_name)
                if producer_match:
                    producer = producer_match.group(1).strip()

                # Determine wine type from the query and wine name
                wine_type = _extract_wine_type_from_query(f"{query} {wine_name}")

                wine = {
                    'name': wine_name,
                    'type': wine_type,
                    'vintage': vintage,
                    'producer': producer,
                    'region': None,
                    'country': None,
                    'rating': None,
                    'labelImageUrl': None,
                }

                # Try to fetch additional details from the Vivino page
                try:
                    wine_details = _fetch_wine_details(vivino_url)
                    if wine_details:
                        wine.update(wine_details)
                except Exception as e:
                    print(f"Error fetching wine details from {vivino_url}: {e}")

                wines.append(wine)

        # If we didn't get enough results from Google, fall back to sample data
        if len(wines) == 0:
            print(f"No wines found via Google search for '{query}', using fallback")
            wines = _get_fallback_results(query, limit)

        return wines[:limit]

    except Exception as e:
        print(f"Error searching Vivino via Google: {e}")
        # Fall back to sample data
        return _get_fallback_results(query, limit)


def _fetch_wine_details(vivino_url: str) -> Dict:
    """
    Fetch additional wine details from a Vivino wine page

    Args:
        vivino_url: URL to the Vivino wine page

    Returns:
        Dictionary with wine details (producer, region, country, rating, labelImageUrl)
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }

        response = requests.get(vivino_url, headers=headers, timeout=5)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        details = {}

        # Try to extract wine details from meta tags (most reliable)
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            details['labelImageUrl'] = og_image['content']

        # Try to find wine region/country
        region_elem = soup.find(text=re.compile(r'Region|Country', re.IGNORECASE))
        if region_elem:
            parent = region_elem.find_parent()
            if parent:
                region_text = parent.get_text(strip=True)
                # Extract country and region
                if ',' in region_text:
                    parts = region_text.split(',')
                    details['region'] = parts[0].strip()
                    if len(parts) > 1:
                        details['country'] = parts[-1].strip()
                else:
                    details['country'] = region_text

        # Try to find rating
        rating_elem = soup.find('div', class_=re.compile(r'rating|average'))
        if not rating_elem:
            rating_elem = soup.find(text=re.compile(r'\d+\.\d+'))
        if rating_elem:
            rating_text = rating_elem.get_text(strip=True) if hasattr(rating_elem, 'get_text') else str(rating_elem)
            rating_match = re.search(r'(\d+\.?\d*)', rating_text)
            if rating_match:
                rating = float(rating_match.group(1))
                # Vivino uses 1-5 scale
                if rating <= 5:
                    details['rating'] = round(rating, 1)

        return details

    except Exception as e:
        print(f"Error fetching details from {vivino_url}: {e}")
        return {}


def _get_fallback_results(query: str, limit: int) -> List[Dict]:
    """
    Generate fallback sample results when scraping fails

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
    Extract wine type from search query text

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
