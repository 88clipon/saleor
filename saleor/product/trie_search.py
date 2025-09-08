"""
Trie-based type-ahead search implementation for Saleor products.

This module provides a Trie data structure for efficient prefix-based searching
of product names, SKUs, and other searchable fields. It's designed to work
alongside the existing PostgreSQL full-text search functionality.
"""

from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple, Any
import json
import logging
from dataclasses import dataclass, asdict
from django.core.cache import cache
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import Product, ProductVariant

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a search result from the Trie."""
    id: str
    text: str
    type: str  # 'product', 'variant', 'sku'
    score: float = 1.0
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class TrieNode:
    """Node in the Trie data structure."""
    
    def __init__(self):
        self.children: Dict[str, 'TrieNode'] = {}
        self.is_end_of_word: bool = False
        self.results: List[SearchResult] = []
        self.frequency: int = 0  # For ranking/sorting


class TrieSearch:
    """
    Trie-based search implementation for type-ahead functionality.
    
    This class provides efficient prefix-based searching with support for:
    - Case-insensitive search
    - Ranking by frequency and relevance
    - Multiple searchable fields (product names, SKUs, etc.)
    - Caching for performance
    """
    
    def __init__(self, cache_key: str = "trie_search_index"):
        self.root = TrieNode()
        self.cache_key = cache_key
        self.is_loaded = False
        self._load_from_cache()
    
    def _load_from_cache(self) -> bool:
        """Load the Trie from cache if available."""
        try:
            cached_data = cache.get(self.cache_key)
            if cached_data:
                self._deserialize_trie(cached_data)
                self.is_loaded = True
                logger.info("Trie search index loaded from cache")
                return True
        except Exception as e:
            logger.warning(f"Failed to load Trie from cache: {e}")
        return False
    
    def _save_to_cache(self) -> None:
        """Save the Trie to cache."""
        try:
            serialized_data = self._serialize_trie()
            cache.set(self.cache_key, serialized_data, timeout=3600)  # 1 hour
            logger.info("Trie search index saved to cache")
        except Exception as e:
            logger.warning(f"Failed to save Trie to cache: {e}")
    
    def _serialize_trie(self) -> str:
        """Serialize the Trie to JSON string."""
        def serialize_node(node: TrieNode) -> Dict:
            return {
                'is_end_of_word': node.is_end_of_word,
                'frequency': node.frequency,
                'results': [result.to_dict() for result in node.results],
                'children': {
                    char: serialize_node(child) 
                    for char, child in node.children.items()
                }
            }
        
        return json.dumps(serialize_node(self.root))
    
    def _deserialize_trie(self, data: str) -> None:
        """Deserialize the Trie from JSON string."""
        def deserialize_node(node_data: Dict) -> TrieNode:
            node = TrieNode()
            node.is_end_of_word = node_data.get('is_end_of_word', False)
            node.frequency = node_data.get('frequency', 0)
            node.results = [
                SearchResult(**result_data) 
                for result_data in node_data.get('results', [])
            ]
            node.children = {
                char: deserialize_node(child_data)
                for char, child_data in node_data.get('children', {}).items()
            }
            return node
        
        self.root = deserialize_node(json.loads(data))
    
    def insert(self, text: str, result: SearchResult) -> None:
        """
        Insert a text and its associated result into the Trie.
        
        Args:
            text: The searchable text (e.g., product name, SKU)
            result: The SearchResult object containing metadata
        """
        node = self.root
        text_lower = text.lower()
        
        for char in text_lower:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        
        node.is_end_of_word = True
        node.frequency += 1
        
        # Add result if not already present
        if not any(r.id == result.id and r.type == result.type for r in node.results):
            node.results.append(result)
    
    def search(self, prefix: str, limit: int = 10) -> List[SearchResult]:
        """
        Search for all results that start with the given prefix.
        
        Args:
            prefix: The search prefix
            limit: Maximum number of results to return
            
        Returns:
            List of SearchResult objects sorted by relevance
        """
        if not prefix:
            return []
        
        prefix_lower = prefix.lower()
        node = self.root
        
        # Navigate to the prefix node
        for char in prefix_lower:
            if char not in node.children:
                return []
            node = node.children[char]
        
        # Collect all results from this node and its children
        results = self._collect_results(node, limit)
        
        # Sort by frequency and relevance
        results.sort(key=lambda x: (x.score, -node.frequency), reverse=True)
        
        return results[:limit]
    
    def _collect_results(self, node: TrieNode, limit: int) -> List[SearchResult]:
        """Recursively collect all results from a node and its children."""
        results = []
        
        if node.is_end_of_word:
            results.extend(node.results)
        
        # If we haven't reached the limit, search children
        if len(results) < limit:
            for child in node.children.values():
                child_results = self._collect_results(child, limit - len(results))
                results.extend(child_results)
                if len(results) >= limit:
                    break
        
        return results
    
    def build_index(self, force_rebuild: bool = False) -> None:
        """
        Build the search index from the database.
        
        Args:
            force_rebuild: If True, rebuild even if cache exists
        """
        if self.is_loaded and not force_rebuild:
            return
        
        logger.info("Building Trie search index...")
        self.root = TrieNode()
        
        try:
            with transaction.atomic():
                # Index products
                self._index_products()
                
                # Index product variants
                self._index_variants()
                
                # Save to cache
                self._save_to_cache()
                self.is_loaded = True
                
            logger.info("Trie search index built successfully")
            
        except Exception as e:
            logger.error(f"Failed to build Trie search index: {e}")
            raise
    
    def _index_products(self) -> None:
        """Index all products in the database."""
        products = Product.objects.select_related('product_type').only(
            'id', 'name', 'slug', 'product_type__name'
        )
        
        for product in products:
            # Index product name
            if product.name:
                result = SearchResult(
                    id=str(product.id),
                    text=product.name,
                    type='product',
                    metadata={
                        'slug': product.slug,
                        'product_type': product.product_type.name if product.product_type else None
                    }
                )
                self.insert(product.name, result)
            
            # Index product slug
            if product.slug:
                result = SearchResult(
                    id=str(product.id),
                    text=product.slug,
                    type='product_slug',
                    metadata={
                        'name': product.name,
                        'product_type': product.product_type.name if product.product_type else None
                    }
                )
                self.insert(product.slug, result)
    
    def _index_variants(self) -> None:
        """Index all product variants in the database."""
        variants = ProductVariant.objects.select_related('product').only(
            'id', 'name', 'sku', 'product__name', 'product__slug'
        )
        
        for variant in variants:
            # Index variant name
            if variant.name:
                result = SearchResult(
                    id=str(variant.id),
                    text=variant.name,
                    type='variant',
                    metadata={
                        'product_id': str(variant.product.id),
                        'product_name': variant.product.name,
                        'product_slug': variant.product.slug,
                        'sku': variant.sku
                    }
                )
                self.insert(variant.name, result)
            
            # Index SKU
            if variant.sku:
                result = SearchResult(
                    id=str(variant.id),
                    text=variant.sku,
                    type='sku',
                    metadata={
                        'product_id': str(variant.product.id),
                        'product_name': variant.product.name,
                        'product_slug': variant.product.slug,
                        'variant_name': variant.name
                    }
                )
                self.insert(variant.sku, result)
    
    def clear_cache(self) -> None:
        """Clear the search index cache."""
        cache.delete(self.cache_key)
        self.is_loaded = False
        logger.info("Trie search index cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the search index."""
        def count_nodes(node: TrieNode) -> Tuple[int, int]:
            total_nodes = 1
            end_nodes = 1 if node.is_end_of_word else 0
            
            for child in node.children.values():
                child_total, child_end = count_nodes(child)
                total_nodes += child_total
                end_nodes += child_end
            
            return total_nodes, end_nodes
        
        total_nodes, end_nodes = count_nodes(self.root)
        
        return {
            'is_loaded': self.is_loaded,
            'total_nodes': total_nodes,
            'end_nodes': end_nodes,
            'cache_key': self.cache_key
        }


# Global instance for the application
trie_search = TrieSearch()


def get_trie_search() -> TrieSearch:
    """Get the global Trie search instance."""
    if not trie_search.is_loaded:
        trie_search.build_index()
    return trie_search


def rebuild_search_index() -> None:
    """Rebuild the search index (useful for management commands)."""
    trie_search.build_index(force_rebuild=True)


def clear_search_index() -> None:
    """Clear the search index cache."""
    trie_search.clear_cache()


