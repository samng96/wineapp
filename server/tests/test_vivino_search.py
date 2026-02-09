"""Tests for Vivino search functionality"""
import pytest
from server.vivino_search import search_vivino, _extract_wine_type_from_query


class TestVivinoSearch:
    """Test the search_vivino function"""

    def test_search_returns_results(self):
        """Test that search returns a list of wine results"""
        results = search_vivino('Cabernet Sauvignon')

        assert isinstance(results, list)
        assert len(results) > 0

    def test_search_respects_limit(self):
        """Test that search respects the limit parameter"""
        results = search_vivino('Merlot', limit=2)

        assert len(results) <= 2

    def test_search_result_structure(self):
        """Test that each search result has the expected structure"""
        results = search_vivino('Pinot Noir', limit=1)

        assert len(results) > 0

        wine = results[0]

        # Required fields
        assert 'name' in wine
        assert 'type' in wine

        # Optional fields
        assert 'vintage' in wine or wine.get('vintage') is None
        assert 'producer' in wine or wine.get('producer') is None
        assert 'region' in wine or wine.get('region') is None
        assert 'country' in wine or wine.get('country') is None
        assert 'rating' in wine or wine.get('rating') is None
        assert 'labelImageUrl' in wine or wine.get('labelImageUrl') is None

    def test_search_includes_query_in_results(self):
        """Test that search results include the query term"""
        query = 'Chardonnay'
        results = search_vivino(query, limit=1)

        assert len(results) > 0
        # At least one result should contain the query term
        assert any(query.lower() in wine['name'].lower() for wine in results)

    def test_search_with_empty_query(self):
        """Test search with empty query returns results"""
        results = search_vivino('')

        # Even with empty query, should return some results (or empty list)
        assert isinstance(results, list)

    def test_search_with_special_characters(self):
        """Test search with special characters in query"""
        results = search_vivino('Château Lafite')

        assert isinstance(results, list)

    def test_search_default_limit(self):
        """Test that search uses default limit when not specified"""
        results = search_vivino('Cabernet')

        # Default limit is 10, should not exceed that
        assert len(results) <= 10


class TestExtractWineType:
    """Test the _extract_wine_type_from_query function"""

    def test_red_wine_varietals(self):
        """Test that red wine varietals are correctly identified"""
        red_varietals = [
            'Cabernet Sauvignon',
            'Merlot',
            'Pinot Noir',
            'Syrah',
            'Shiraz',
            'Malbec',
            'Zinfandel',
            'Tempranillo',
            'Sangiovese',
            'Nebbiolo',
            'Grenache',
            'Barbera',
            'Petite Sirah',
            'Mourvèdre',
            'Carmenère',
            'Barolo',
            'Brunello',
            'Amarone',
            'Chianti',
            'Rioja',
        ]

        for varietal in red_varietals:
            wine_type = _extract_wine_type_from_query(varietal)
            assert wine_type == 'Red', f"Expected {varietal} to be classified as Red, got {wine_type}"

    def test_white_wine_varietals(self):
        """Test that white wine varietals are correctly identified"""
        white_varietals = [
            'Chardonnay',
            'Sauvignon Blanc',
            'Riesling',
            'Pinot Grigio',
            'Pinot Gris',
            'Viognier',
            'Gewürztraminer',
            'Chenin Blanc',
            'Albariño',
            'Grüner Veltliner',
            'Vermentino',
            'Moscato',
            'Sancerre',
            'Chablis',
        ]

        for varietal in white_varietals:
            wine_type = _extract_wine_type_from_query(varietal)
            assert wine_type == 'White', f"Expected {varietal} to be classified as White, got {wine_type}"

    def test_sparkling_wine(self):
        """Test that sparkling wines are correctly identified"""
        sparkling_wines = [
            'Champagne',
            'Prosecco',
            'Cava',
            'Sparkling Wine',
            'Spumante',
        ]

        for wine in sparkling_wines:
            wine_type = _extract_wine_type_from_query(wine)
            assert wine_type == 'Sparkling', f"Expected {wine} to be classified as Sparkling, got {wine_type}"

    def test_rose_wine(self):
        """Test that rosé wines are correctly identified"""
        rose_wines = [
            'Rosé',
            'Rose Wine',
            'Provence Rosé',
        ]

        for wine in rose_wines:
            wine_type = _extract_wine_type_from_query(wine)
            assert wine_type == 'Rosé', f"Expected {wine} to be classified as Rosé, got {wine_type}"

    def test_fortified_wine(self):
        """Test that fortified wines are correctly identified"""
        fortified_wines = [
            'Port',
            'Sherry',
            'Madeira',
            'Marsala',
            'Vermouth',
        ]

        for wine in fortified_wines:
            wine_type = _extract_wine_type_from_query(wine)
            assert wine_type == 'Fortified', f"Expected {wine} to be classified as Fortified, got {wine_type}"

    def test_dessert_wine(self):
        """Test that dessert wines are correctly identified"""
        dessert_wines = [
            'Dessert Wine',
            'Ice Wine',
            'Sauternes',
            'Tokaji',
        ]

        for wine in dessert_wines:
            wine_type = _extract_wine_type_from_query(wine)
            assert wine_type == 'Dessert', f"Expected {wine} to be classified as Dessert, got {wine_type}"

    def test_case_insensitive(self):
        """Test that wine type detection is case insensitive"""
        assert _extract_wine_type_from_query('CABERNET SAUVIGNON') == 'Red'
        assert _extract_wine_type_from_query('chardonnay') == 'White'
        assert _extract_wine_type_from_query('ChAmPaGnE') == 'Sparkling'

    def test_unknown_wine_defaults_to_red(self):
        """Test that unknown wines default to Red"""
        wine_type = _extract_wine_type_from_query('Unknown Wine Type XYZ')
        assert wine_type == 'Red'

    def test_wine_with_vintage_in_name(self):
        """Test wine type detection with vintage in the name"""
        assert _extract_wine_type_from_query('Caymus Cabernet Sauvignon 2019') == 'Red'
        assert _extract_wine_type_from_query('2018 Cloudy Bay Sauvignon Blanc') == 'White'


class TestVivinoSearchIntegration:
    """Integration tests for Vivino search with API endpoint"""

    def test_search_results_have_correct_wine_types(self):
        """Test that search results have correctly determined wine types"""
        # Search for red wine
        red_results = search_vivino('Cabernet Sauvignon', limit=3)
        for wine in red_results:
            assert wine['type'] == 'Red'

        # Search for white wine
        white_results = search_vivino('Chardonnay', limit=3)
        for wine in white_results:
            assert wine['type'] == 'White'

        # Search for sparkling wine
        sparkling_results = search_vivino('Champagne', limit=3)
        for wine in sparkling_results:
            assert wine['type'] == 'Sparkling'

    def test_search_results_contain_query(self):
        """Test that search results are relevant to the query"""
        query = 'Malbec'
        results = search_vivino(query, limit=5)

        # All results should contain the query term in the name
        for wine in results:
            assert query.lower() in wine['name'].lower(), \
                f"Expected '{wine['name']}' to contain '{query}'"

    def test_search_returns_valid_ratings(self):
        """Test that ratings are in valid range (1-5)"""
        results = search_vivino('Pinot Noir', limit=5)

        for wine in results:
            if wine.get('rating') is not None:
                assert 1 <= wine['rating'] <= 5, \
                    f"Rating {wine['rating']} is out of valid range (1-5)"

    def test_search_returns_valid_vintages(self):
        """Test that vintages are reasonable years"""
        results = search_vivino('Bordeaux', limit=5)

        for wine in results:
            if wine.get('vintage') is not None:
                # Vintages should be between 1900 and current year + 1
                assert 1900 <= wine['vintage'] <= 2027, \
                    f"Vintage {wine['vintage']} is not a reasonable year"

    def test_multiple_searches_are_independent(self):
        """Test that multiple searches return independent results"""
        results1 = search_vivino('Merlot', limit=2)
        results2 = search_vivino('Chardonnay', limit=2)

        # Results should be different
        assert results1 != results2

        # First result should contain respective search terms
        assert 'merlot' in results1[0]['name'].lower()
        assert 'chardonnay' in results2[0]['name'].lower()
