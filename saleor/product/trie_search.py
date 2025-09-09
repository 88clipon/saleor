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
import re
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
    Hybrid search implementation combining prefix-based Trie with keyword search.
    
    This class provides both:
    - Efficient prefix-based searching (type-ahead)
    - Keyword-based searching (substring matching anywhere in text)
    - Case-insensitive search
    - Ranking by frequency and relevance
    - Multiple searchable fields (product names, SKUs, etc.)
    - Caching for performance
    """
    
    def __init__(self, cache_key: str = "trie_search_index"):
        self.root = TrieNode()
        self.cache_key = cache_key
        self.is_loaded = False
        
        # Keyword search index: maps tokens to SearchResults
        self.keyword_index: Dict[str, List[SearchResult]] = defaultdict(list)
        
        # Full text index for exact and partial matching
        self.text_to_results: Dict[str, List[SearchResult]] = defaultdict(list)
        
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
        """Serialize the Trie and keyword indexes to JSON string."""
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
        
        data = {
            'trie': serialize_node(self.root),
            'keyword_index': {
                token: [result.to_dict() for result in results]
                for token, results in self.keyword_index.items()
            },
            'text_to_results': {
                text: [result.to_dict() for result in results]
                for text, results in self.text_to_results.items()
            }
        }
        
        return json.dumps(data)
    
    def _deserialize_trie(self, data: str) -> None:
        """Deserialize the Trie and keyword indexes from JSON string."""
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
        
        parsed_data = json.loads(data)
        
        # Handle both old format (just trie) and new format (with indexes)
        if 'trie' in parsed_data:
            # New format with keyword indexes
            self.root = deserialize_node(parsed_data['trie'])
            
            # Restore keyword index
            self.keyword_index = defaultdict(list)
            for token, results_data in parsed_data.get('keyword_index', {}).items():
                self.keyword_index[token] = [
                    SearchResult(**result_data) for result_data in results_data
                ]
            
            # Restore text to results index
            self.text_to_results = defaultdict(list)
            for text, results_data in parsed_data.get('text_to_results', {}).items():
                self.text_to_results[text] = [
                    SearchResult(**result_data) for result_data in results_data
                ]
        else:
            # Old format (backward compatibility)
            self.root = deserialize_node(parsed_data)
            self.keyword_index = defaultdict(list)
            self.text_to_results = defaultdict(list)
    
    def insert(self, text: str, result: SearchResult) -> None:
        """
        Insert a text and its associated result into both Trie and keyword indexes.
        
        Args:
            text: The searchable text (e.g., product name, SKU)
            result: The SearchResult object containing metadata
        """
        text_lower = text.lower()
        
        # Insert into prefix Trie (existing functionality)
        node = self.root
        for char in text_lower:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        
        node.is_end_of_word = True
        node.frequency += 1
        
        # Add result if not already present
        if not any(r.id == result.id and r.type == result.type for r in node.results):
            node.results.append(result)
        
        # Index for keyword search - tokenize and index individual words
        tokens = self._tokenize(text_lower)
        for token in tokens:
            if not any(r.id == result.id and r.type == result.type for r in self.keyword_index[token]):
                self.keyword_index[token].append(result)
        
        # Index full text for exact and partial matching
        if not any(r.id == result.id and r.type == result.type for r in self.text_to_results[text_lower]):
            self.text_to_results[text_lower].append(result)
    
    def search(self, prefix: str, limit: int = 10, substring_search: bool = False) -> List[SearchResult]:
        """
        Search for all results that start with the given prefix, with optional substring search.
        
        Args:
            prefix: The search prefix/query
            limit: Maximum number of results to return
            substring_search: If True, also search for substring matches anywhere in text
            
        Returns:
            List of SearchResult objects sorted by relevance
        """
        if not prefix:
            return []
        
        prefix_lower = prefix.lower()
        results = []
        
        # First, try prefix search (existing functionality)
        node = self.root
        can_navigate = True
        
        # Navigate to the prefix node
        for char in prefix_lower:
            if char not in node.children:
                can_navigate = False
                break
            node = node.children[char]
        
        if can_navigate:
            # Collect all results from this node and its children
            prefix_results = self._collect_results(node, limit)
            results.extend(prefix_results)
        
        # If we want substring search or didn't find enough prefix matches
        if substring_search or len(results) < limit:
            substring_results = self._substring_search(prefix_lower, limit - len(results))
            
            # Add substring results that aren't already in prefix results
            existing_ids = {(r.id, r.type) for r in results}
            for result in substring_results:
                if (result.id, result.type) not in existing_ids:
                    # Lower score for substring matches
                    result.score *= 0.8
                    results.append(result)
        
        # Sort by frequency and relevance
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:limit]
    
    def keyword_search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """
        Search for results containing the query as a keyword anywhere in the text.
        
        Args:
            query: The search query (can be multiple words)
            limit: Maximum number of results to return
            
        Returns:
            List of SearchResult objects sorted by relevance
        """
        if not query:
            return []
        
        query_lower = query.lower().strip()
        
        # For single word queries, use token search
        tokens = self._tokenize(query_lower)
        if len(tokens) == 1:
            return self._search_by_token(tokens[0], limit)
        
        # For multi-word queries, find intersection of results
        return self._search_by_multiple_tokens(tokens, limit)
    
    def hybrid_search(self, query: str, limit: int = 10, prefer_prefix: bool = True) -> List[SearchResult]:
        """
        Hybrid search combining prefix and keyword search.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            prefer_prefix: If True, prioritize prefix matches over keyword matches
            
        Returns:
            List of SearchResult objects sorted by relevance
        """
        if not query:
            return []
        
        query_lower = query.lower().strip()
        
        # Get prefix matches
        prefix_results = self.search(query_lower, limit)
        
        # Get keyword matches
        keyword_results = self.keyword_search(query_lower, limit)
        
        # Combine and deduplicate results
        combined_results = self._combine_results(
            prefix_results, keyword_results, limit, prefer_prefix
        )
        
        return combined_results[:limit]
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into searchable tokens.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of tokens (words)
        """
        # Split by word boundaries and filter out short/empty tokens
        tokens = re.findall(r'\b\w+\b', text.lower())
        return [token for token in tokens if len(token) >= 2]
    
    def _search_by_token(self, token: str, limit: int) -> List[SearchResult]:
        """Search by a single token."""
        results = []
        
        # Exact token match
        if token in self.keyword_index:
            results.extend(self.keyword_index[token])
        
        # Partial token matches (substring)
        for indexed_token, token_results in self.keyword_index.items():
            if token in indexed_token and indexed_token != token:
                for result in token_results:
                    if not any(r.id == result.id and r.type == result.type for r in results):
                        # Lower score for partial matches
                        partial_result = SearchResult(
                            id=result.id,
                            text=result.text,
                            type=result.type,
                            score=result.score * 0.8,  # Reduce score for partial match
                            metadata=result.metadata
                        )
                        results.append(partial_result)
        
        # Substring search in full text
        for text, text_results in self.text_to_results.items():
            if token in text:
                for result in text_results:
                    if not any(r.id == result.id and r.type == result.type for r in results):
                        # Score based on position (earlier = higher score)
                        position_score = 1.0 - (text.find(token) / len(text) * 0.3)
                        substring_result = SearchResult(
                            id=result.id,
                            text=result.text,
                            type=result.type,
                            score=result.score * position_score * 0.7,  # Reduce score for substring match
                            metadata=result.metadata
                        )
                        results.append(substring_result)
        
        # Sort by score (descending)
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
    
    def _search_by_multiple_tokens(self, tokens: List[str], limit: int) -> List[SearchResult]:
        """Search by multiple tokens (AND logic)."""
        if not tokens:
            return []
        
        # Find results that contain ALL tokens
        candidate_results = None
        
        for token in tokens:
            token_results = self._search_by_token(token, limit * 2)  # Get more to allow intersection
            token_result_ids = {(r.id, r.type) for r in token_results}
            
            if candidate_results is None:
                candidate_results = token_result_ids
            else:
                candidate_results = candidate_results.intersection(token_result_ids)
        
        if not candidate_results:
            return []
        
        # Get the actual results and calculate combined scores
        final_results = []
        for result_id, result_type in candidate_results:
            # Find the result object from any token's results
            for token in tokens:
                token_results = self._search_by_token(token, limit * 2)
                for result in token_results:
                    if result.id == result_id and result.type == result_type:
                        final_results.append(result)
                        break
                if final_results and final_results[-1].id == result_id:
                    break
        
        # Sort by score
        final_results.sort(key=lambda x: x.score, reverse=True)
        return final_results[:limit]
    
    def _combine_results(self, prefix_results: List[SearchResult], 
                        keyword_results: List[SearchResult], 
                        limit: int, prefer_prefix: bool = True) -> List[SearchResult]:
        """Combine prefix and keyword results with deduplication."""
        combined = []
        seen_ids = set()
        
        # Add results in order based on preference
        primary_results = prefix_results if prefer_prefix else keyword_results
        secondary_results = keyword_results if prefer_prefix else prefix_results
        
        # Add primary results first
        for result in primary_results:
            result_key = (result.id, result.type)
            if result_key not in seen_ids:
                combined.append(result)
                seen_ids.add(result_key)
        
        # Add secondary results that weren't already included
        for result in secondary_results:
            result_key = (result.id, result.type)
            if result_key not in seen_ids and len(combined) < limit:
                # Slightly reduce score for secondary results
                secondary_result = SearchResult(
                    id=result.id,
                    text=result.text,
                    type=result.type,
                    score=result.score * 0.9,
                    metadata=result.metadata
                )
                combined.append(secondary_result)
                seen_ids.add(result_key)
        
        return combined
    
    def _substring_search(self, query: str, limit: int) -> List[SearchResult]:
        """
        Simple substring search through the text_to_results index.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            
        Returns:
            List of SearchResult objects that contain the query as a substring
        """
        if not query or limit <= 0:
            return []
        
        results = []
        query_lower = query.lower()
        
        # Search through all indexed text
        for text, text_results in self.text_to_results.items():
            if query_lower in text:
                for result in text_results:
                    if len(results) >= limit:
                        break
                    
                    # Calculate position-based score (earlier in text = higher score)
                    position = text.find(query_lower)
                    position_score = 1.0 - (position / len(text) * 0.5)  # Reduce impact by half
                    
                    # Create a copy with adjusted score
                    substring_result = SearchResult(
                        id=result.id,
                        text=result.text,
                        type=result.type,
                        score=result.score * position_score,
                        metadata=result.metadata
                    )
                    results.append(substring_result)
                
                if len(results) >= limit:
                    break
        
        return results
    
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
        self.keyword_index = defaultdict(list)
        self.text_to_results = defaultdict(list)
        
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
        self.keyword_index = defaultdict(list)
        self.text_to_results = defaultdict(list)
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


