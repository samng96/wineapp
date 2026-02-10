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

        # All fields should be present
        assert 'name' in wine
        assert 'type' in wine
        assert 'vintage' in wine
        assert 'producer' in wine
        assert 'region' in wine
        assert 'country' in wine
        assert 'rating' in wine
        assert 'labelImageUrl' in wine

    def test_search_includes_query_in_results(self):
        """Test that search results include the query term"""
        query = 'Chardonnay'
        results = search_vivino(query, limit=3)

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
    """Integration tests for Vivino search - hits live Vivino"""

    def test_search_returns_real_wine_data(self):
        """Test that search returns real data from Vivino (not fallback)"""
        results = search_vivino('Caymus', limit=3)

        assert len(results) > 0
        # Should not be fallback "Sample Winery" data
        for wine in results:
            assert wine.get('producer') != 'Sample Winery', \
                "Got fallback data instead of real Vivino results"

    def test_search_results_have_vivino_images(self):
        """Test that results include Vivino image URLs"""
        results = search_vivino('Opus One', limit=3)

        assert len(results) > 0
        # At least some results should have images
        has_image = any(wine.get('labelImageUrl') for wine in results)
        assert has_image, "Expected at least one result to have an image URL"

    def test_search_results_have_ratings(self):
        """Test that results include ratings from Vivino"""
        results = search_vivino('Pinot Noir', limit=5)

        assert len(results) > 0
        for wine in results:
            if wine.get('rating') is not None:
                assert 1 <= wine['rating'] <= 5, \
                    f"Rating {wine['rating']} is out of valid range (1-5)"

    def test_search_results_have_valid_vintages(self):
        """Test that vintages are reasonable years"""
        results = search_vivino('Bordeaux', limit=5)

        for wine in results:
            if wine.get('vintage') is not None:
                assert 1900 <= wine['vintage'] <= 2027, \
                    f"Vintage {wine['vintage']} is not a reasonable year"

    def test_search_results_have_producers(self):
        """Test that results include producer/winery names"""
        results = search_vivino('Cabernet Sauvignon', limit=5)

        assert len(results) > 0
        has_producer = any(wine.get('producer') for wine in results)
        assert has_producer, "Expected at least one result to have a producer"

    def test_search_results_have_regions(self):
        """Test that results include region info"""
        results = search_vivino('Napa Valley Cabernet', limit=5)

        assert len(results) > 0
        has_region = any(wine.get('region') for wine in results)
        assert has_region, "Expected at least one result to have a region"

    def test_multiple_searches_are_independent(self):
        """Test that multiple searches return independent results"""
        results1 = search_vivino('Merlot', limit=2)
        results2 = search_vivino('Chardonnay', limit=2)

        # Results should be different
        assert results1 != results2

        # First result should contain respective search terms
        assert 'merlot' in results1[0]['name'].lower()
        assert 'chardonnay' in results2[0]['name'].lower()
