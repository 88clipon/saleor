"""
GraphQL types for Trie-based type-ahead search functionality.
"""

import graphene
from graphene import relay
from typing import List, Optional

from ...core.connection import CountableConnection
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.types import BaseObjectType
from ....product.trie_search import get_trie_search, SearchResult


class TrieSearchResult(BaseObjectType):
    """Represents a single search result from Trie search."""
    
    id = graphene.String(required=True, description="The ID of the search result.")
    text = graphene.String(required=True, description="The text that matched the search.")
    type = graphene.String(required=True, description="The type of result (product, variant, sku, etc.).")
    score = graphene.Float(description="The relevance score of the result.")
    metadata = graphene.JSONString(description="Additional metadata about the result.")
    
    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        description = "Represents a single result from Trie-based type-ahead search."


class TrieSearchResultConnection(CountableConnection):
    """Connection type for Trie search results."""
    
    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        node = TrieSearchResult


class TrieSearchQuery(BaseObjectType):
    """Query type for Trie-based search operations."""
    
    def resolve_trie_search(
        self, 
        info, 
        query: str, 
        limit: int = 10,
        types: Optional[List[str]] = None
    ) -> List[TrieSearchResult]:
        """
        Perform a Trie-based type-ahead search.
        
        Args:
            query: The search query (prefix)
            limit: Maximum number of results to return
            types: Optional list of result types to filter by
            
        Returns:
            List of search results
        """
        if not query or len(query.strip()) < 2:
            return []
        
        try:
            trie = get_trie_search()
            results = trie.search(query.strip(), limit=limit)
            
            # Filter by types if specified
            if types:
                results = [r for r in results if r.type in types]
            
            # Convert to GraphQL objects
            return [
                TrieSearchResult(
                    id=r.id,
                    text=r.text,
                    type=r.type,
                    score=r.score,
                    metadata=r.metadata
                )
                for r in results
            ]
            
        except Exception as e:
            # Log error but don't expose it to the client
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Trie search error: {e}")
            return []
    
    def resolve_trie_search_stats(self, info) -> dict:
        """Get statistics about the Trie search index."""
        try:
            trie = get_trie_search()
            return trie.get_stats()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Trie search stats error: {e}")
            return {"error": "Failed to get search statistics"}


# Add the search query to the main Query type
def add_trie_search_to_query(query_class):
    """Add Trie search fields to the main Query class."""
    
    # Add the search field
    query_class.trie_search = graphene.Field(
        graphene.List(TrieSearchResult),
        query=graphene.String(required=True, description="The search query (prefix)"),
        limit=graphene.Int(description="Maximum number of results to return", default_value=10),
        types=graphene.List(graphene.String, description="Filter by result types"),
        description="Perform a Trie-based type-ahead search for products and variants."
    )
    
    # Add the stats field
    query_class.trie_search_stats = graphene.Field(
        graphene.JSONString,
        description="Get statistics about the Trie search index."
    )
    
    # Add resolver methods
    query_class.resolve_trie_search = TrieSearchQuery.resolve_trie_search
    query_class.resolve_trie_search_stats = TrieSearchQuery.resolve_trie_search_stats
    
    return query_class


