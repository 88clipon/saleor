"""
Example script demonstrating how to use the Trie search functionality.

This script shows how to:
1. Build the search index
2. Perform searches
3. Handle different types of results
4. Use the GraphQL API
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saleor.settings')
django.setup()

from saleor.product.trie_search import get_trie_search, rebuild_search_index
from saleor.product.models import Product, ProductVariant


def example_basic_usage():
    """Example of basic Trie search usage."""
    print("=== Basic Trie Search Usage ===")
    
    # Get the Trie search instance
    trie = get_trie_search()
    
    # Perform a search
    results = trie.search("apple", limit=5)
    
    print(f"Found {len(results)} results for 'apple':")
    for result in results:
        print(f"  - {result.text} ({result.type}) - ID: {result.id}")
        if result.metadata:
            print(f"    Metadata: {result.metadata}")


def example_search_by_type():
    """Example of searching by specific types."""
    print("\n=== Search by Type ===")
    
    trie = get_trie_search()
    
    # Search only for products
    product_results = trie.search("test", limit=10)
    products = [r for r in product_results if r.type == "product"]
    
    print(f"Found {len(products)} products for 'test':")
    for result in products:
        print(f"  - {result.text} (Product)")
    
    # Search only for variants
    variants = [r for r in product_results if r.type == "variant"]
    print(f"Found {len(variants)} variants for 'test':")
    for result in variants:
        print(f"  - {result.text} (Variant)")


def example_graphql_query():
    """Example of how to use the GraphQL API."""
    print("\n=== GraphQL Query Example ===")
    
    # Example GraphQL query
    graphql_query = """
    query TrieSearch($query: String!, $limit: Int, $types: [String]) {
        trieSearch(query: $query, limit: $limit, types: $types) {
            id
            text
            type
            score
            metadata
        }
    }
    """
    
    print("GraphQL Query:")
    print(graphql_query)
    
    print("\nExample variables:")
    print('{"query": "apple", "limit": 5, "types": ["product", "variant"]}')


def example_management_commands():
    """Example of using management commands."""
    print("\n=== Management Commands ===")
    
    print("To build the search index:")
    print("python manage.py build_trie_index")
    
    print("\nTo rebuild the index (force):")
    print("python manage.py build_trie_index --rebuild")
    
    print("\nTo clear the cache:")
    print("python manage.py build_trie_index --clear")
    
    print("\nTo view statistics:")
    print("python manage.py build_trie_index --stats")


def example_performance_tips():
    """Example of performance tips and best practices."""
    print("\n=== Performance Tips ===")
    
    print("1. The search index is automatically cached for 1 hour")
    print("2. The index is rebuilt automatically when products/variants change")
    print("3. For large datasets, consider running the build command in the background")
    print("4. Use the 'types' parameter to filter results and improve performance")
    print("5. Set appropriate limits to avoid returning too many results")


def main():
    """Main example function."""
    print("Trie Search Example")
    print("==================")
    
    try:
        # Build the index first
        print("Building search index...")
        rebuild_search_index()
        print("Index built successfully!")
        
        # Run examples
        example_basic_usage()
        example_search_by_type()
        example_graphql_query()
        example_management_commands()
        example_performance_tips()
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have products in your database and the index is built.")


if __name__ == "__main__":
    main()


