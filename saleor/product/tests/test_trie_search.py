"""
Tests for Trie-based search functionality.
"""

import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, TransactionTestCase
from django.core.cache import cache
from django.db import transaction

from ..models import Product, ProductType, ProductVariant
from ..trie_search import TrieSearch, SearchResult, trie_search
from ...channel.models import Channel
from ...account.models import User


class TrieSearchTestCase(TestCase):
    """Test cases for the TrieSearch class."""
    
    def setUp(self):
        """Set up test data."""
        self.trie = TrieSearch()
        self.trie.root = TrieSearch.TrieNode()
        cache.clear()
    
    def tearDown(self):
        """Clean up after tests."""
        cache.clear()
    
    def test_insert_and_search_basic(self):
        """Test basic insert and search functionality."""
        # Insert test data
        result1 = SearchResult(id="1", text="apple", type="product")
        result2 = SearchResult(id="2", text="application", type="product")
        result3 = SearchResult(id="3", text="banana", type="product")
        
        self.trie.insert("apple", result1)
        self.trie.insert("application", result2)
        self.trie.insert("banana", result3)
        
        # Test search
        results = self.trie.search("app")
        self.assertEqual(len(results), 2)
        self.assertIn(result1, results)
        self.assertIn(result2, results)
        
        # Test exact match
        results = self.trie.search("apple")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], result1)
        
        # Test no match
        results = self.trie.search("orange")
        self.assertEqual(len(results), 0)
    
    def test_case_insensitive_search(self):
        """Test that search is case-insensitive."""
        result = SearchResult(id="1", text="Apple", type="product")
        self.trie.insert("Apple", result)
        
        # Search with different cases
        results = self.trie.search("apple")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], result)
        
        results = self.trie.search("APPLE")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], result)
        
        results = self.trie.search("ApPlE")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], result)
    
    def test_frequency_tracking(self):
        """Test that frequency is tracked correctly."""
        result = SearchResult(id="1", text="test", type="product")
        
        # Insert the same text multiple times
        self.trie.insert("test", result)
        self.trie.insert("test", result)
        self.trie.insert("test", result)
        
        # Find the node
        node = self.trie.root
        for char in "test":
            node = node.children[char]
        
        self.assertEqual(node.frequency, 3)
    
    def test_duplicate_result_prevention(self):
        """Test that duplicate results are not added."""
        result1 = SearchResult(id="1", text="test", type="product")
        result2 = SearchResult(id="1", text="test", type="product")  # Same ID and type
        
        self.trie.insert("test", result1)
        self.trie.insert("test", result2)
        
        # Find the node
        node = self.trie.root
        for char in "test":
            node = node.children[char]
        
        # Should only have one result despite two inserts
        self.assertEqual(len(node.results), 1)
    
    def test_limit_parameter(self):
        """Test that the limit parameter works correctly."""
        # Insert multiple results
        for i in range(10):
            result = SearchResult(id=str(i), text=f"test{i}", type="product")
            self.trie.insert(f"test{i}", result)
        
        # Test with limit
        results = self.trie.search("test", limit=5)
        self.assertEqual(len(results), 5)
    
    def test_serialization_deserialization(self):
        """Test that the Trie can be serialized and deserialized."""
        # Insert test data
        result1 = SearchResult(id="1", text="apple", type="product", score=0.9)
        result2 = SearchResult(id="2", text="application", type="variant", score=0.8)
        
        self.trie.insert("apple", result1)
        self.trie.insert("application", result2)
        
        # Serialize
        serialized = self.trie._serialize_trie()
        self.assertIsInstance(serialized, str)
        
        # Create new Trie and deserialize
        new_trie = TrieSearch()
        new_trie._deserialize_trie(serialized)
        
        # Test that search works on deserialized Trie
        results = new_trie.search("app")
        self.assertEqual(len(results), 2)
        
        # Check that results are properly deserialized
        result_ids = [r.id for r in results]
        self.assertIn("1", result_ids)
        self.assertIn("2", result_ids)
    
    def test_empty_search(self):
        """Test that empty search returns empty results."""
        self.trie.insert("test", SearchResult(id="1", text="test", type="product"))
        
        results = self.trie.search("")
        self.assertEqual(len(results), 0)
        
        results = self.trie.search("   ")
        self.assertEqual(len(results), 0)
    
    def test_short_prefix(self):
        """Test that very short prefixes work correctly."""
        result = SearchResult(id="1", text="a", type="product")
        self.trie.insert("a", result)
        
        results = self.trie.search("a")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], result)


class TrieSearchIntegrationTestCase(TransactionTestCase):
    """Integration tests for Trie search with database."""
    
    def setUp(self):
        """Set up test data with database objects."""
        cache.clear()
        
        # Create test data
        self.product_type = ProductType.objects.create(
            name="Test Product Type",
            slug="test-product-type"
        )
        
        self.product1 = Product.objects.create(
            name="Apple iPhone",
            slug="apple-iphone",
            product_type=self.product_type
        )
        
        self.product2 = Product.objects.create(
            name="Samsung Galaxy",
            slug="samsung-galaxy",
            product_type=self.product_type
        )
        
        self.variant1 = ProductVariant.objects.create(
            product=self.product1,
            name="iPhone 14",
            sku="IPHONE14"
        )
        
        self.variant2 = ProductVariant.objects.create(
            product=self.product2,
            name="Galaxy S23",
            sku="GALAXYS23"
        )
    
    def tearDown(self):
        """Clean up after tests."""
        cache.clear()
    
    def test_build_index_from_database(self):
        """Test building the index from database objects."""
        trie = TrieSearch()
        trie.build_index()
        
        # Test product search
        results = trie.search("apple")
        self.assertGreater(len(results), 0)
        
        # Check that we have product results
        product_results = [r for r in results if r.type == "product"]
        self.assertGreater(len(product_results), 0)
        
        # Test variant search
        results = trie.search("iphone")
        self.assertGreater(len(results), 0)
        
        # Check that we have variant results
        variant_results = [r for r in results if r.type == "variant"]
        self.assertGreater(len(variant_results), 0)
        
        # Test SKU search
        results = trie.search("IPHONE")
        self.assertGreater(len(results), 0)
        
        # Check that we have SKU results
        sku_results = [r for r in results if r.type == "sku"]
        self.assertGreater(len(sku_results), 0)
    
    def test_cache_functionality(self):
        """Test that the Trie is properly cached and loaded."""
        # Build index
        trie = TrieSearch()
        trie.build_index()
        
        # Create new instance (should load from cache)
        new_trie = TrieSearch()
        self.assertTrue(new_trie.is_loaded)
        
        # Test that search works
        results = new_trie.search("apple")
        self.assertGreater(len(results), 0)
    
    def test_clear_cache(self):
        """Test that cache can be cleared."""
        trie = TrieSearch()
        trie.build_index()
        
        # Clear cache
        trie.clear_cache()
        self.assertFalse(trie.is_loaded)
    
    def test_get_stats(self):
        """Test that statistics are returned correctly."""
        trie = TrieSearch()
        trie.build_index()
        
        stats = trie.get_stats()
        
        self.assertIn('is_loaded', stats)
        self.assertIn('total_nodes', stats)
        self.assertIn('end_nodes', stats)
        self.assertIn('cache_key', stats)
        
        self.assertTrue(stats['is_loaded'])
        self.assertGreater(stats['total_nodes'], 0)
        self.assertGreater(stats['end_nodes'], 0)


class TrieSearchGraphQLTestCase(TestCase):
    """Test cases for GraphQL integration."""
    
    def setUp(self):
        """Set up test data."""
        cache.clear()
        
        # Create test data
        self.product_type = ProductType.objects.create(
            name="Test Product Type",
            slug="test-product-type"
        )
        
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            product_type=self.product_type
        )
    
    def tearDown(self):
        """Clean up after tests."""
        cache.clear()
    
    @patch('saleor.product.trie_search.get_trie_search')
    def test_trie_search_resolver(self, mock_get_trie_search):
        """Test the GraphQL resolver for Trie search."""
        from ..graphql.product.types.trie_search import TrieSearchQuery
        
        # Mock the Trie search
        mock_trie = MagicMock()
        mock_results = [
            SearchResult(id="1", text="test", type="product", score=0.9),
            SearchResult(id="2", text="testing", type="variant", score=0.8)
        ]
        mock_trie.search.return_value = mock_results
        mock_get_trie_search.return_value = mock_trie
        
        # Test resolver
        query = TrieSearchQuery()
        results = query.resolve_trie_search(None, None, "test", limit=10)
        
        # Verify results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].id, "1")
        self.assertEqual(results[0].text, "test")
        self.assertEqual(results[0].type, "product")
        self.assertEqual(results[0].score, 0.9)
    
    @patch('saleor.product.trie_search.get_trie_search')
    def test_trie_search_with_types_filter(self, mock_get_trie_search):
        """Test Trie search with type filtering."""
        from ..graphql.product.types.trie_search import TrieSearchQuery
        
        # Mock the Trie search
        mock_trie = MagicMock()
        mock_results = [
            SearchResult(id="1", text="test", type="product", score=0.9),
            SearchResult(id="2", text="testing", type="variant", score=0.8),
            SearchResult(id="3", text="test-sku", type="sku", score=0.7)
        ]
        mock_trie.search.return_value = mock_results
        mock_get_trie_search.return_value = mock_trie
        
        # Test resolver with type filter
        query = TrieSearchQuery()
        results = query.resolve_trie_search(
            None, None, "test", limit=10, types=["product", "variant"]
        )
        
        # Should filter out SKU results
        self.assertEqual(len(results), 2)
        result_types = [r.type for r in results]
        self.assertIn("product", result_types)
        self.assertIn("variant", result_types)
        self.assertNotIn("sku", result_types)
    
    def test_trie_search_empty_query(self):
        """Test Trie search with empty query."""
        from ..graphql.product.types.trie_search import TrieSearchQuery
        
        query = TrieSearchQuery()
        results = query.resolve_trie_search(None, None, "", limit=10)
        
        self.assertEqual(len(results), 0)
    
    def test_trie_search_short_query(self):
        """Test Trie search with very short query."""
        from ..graphql.product.types.trie_search import TrieSearchQuery
        
        query = TrieSearchQuery()
        results = query.resolve_trie_search(None, None, "a", limit=10)
        
        self.assertEqual(len(results), 0)
    
    @patch('saleor.product.trie_search.get_trie_search')
    def test_trie_search_error_handling(self, mock_get_trie_search):
        """Test that errors are handled gracefully."""
        from ..graphql.product.types.trie_search import TrieSearchQuery
        
        # Mock error
        mock_get_trie_search.side_effect = Exception("Test error")
        
        query = TrieSearchQuery()
        results = query.resolve_trie_search(None, None, "test", limit=10)
        
        # Should return empty list on error
        self.assertEqual(len(results), 0)


