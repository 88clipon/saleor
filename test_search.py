#!/usr/bin/env python3
"""
Simple test script for the enhanced Trie search functionality.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saleor.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

def test_simple_search():
    """Test the simplified search functionality."""
    try:
        from saleor.product.trie_search import TrieSearch, SearchResult
        
        print("=== Testing Simple Substring Search ===\n")
        
        # Create a test instance with manual data
        trie = TrieSearch(cache_key="test_search_simple")
        trie.clear_cache()
        
        # Manually add some test data
        print("1. Adding test data...")
        test_products = [
            ("Saleor White Cubes Tee Front", "product", {"slug": "white-cubes-tee"}),
            ("Saleor Dark Polygon Tee", "product", {"slug": "dark-polygon-tee"}),
            ("Blue Hoodie", "product", {"slug": "blue-hoodie"}),
            ("White Plimsolls", "product", {"slug": "white-plimsolls"}),
        ]
        
        for text, result_type, metadata in test_products:
            result = SearchResult(
                id=f"test_{text.lower().replace(' ', '_')}",
                text=text,
                type=result_type,
                score=1.0,
                metadata=metadata
            )
            trie.insert(text, result)
            print(f"   Added: {text}")
        
        print(f"\n2. Stats after adding data:")
        print(f"   Trie loaded: {trie.is_loaded}")
        print(f"   Text index size: {len(trie.text_to_results)}")
        
        # Test different search modes
        print(f"\n3. Testing searches...")
        
        test_queries = [
            ("sal", "prefix only"),
            ("white", "should find both white items"),
            ("tee", "should find both tee items"),
            ("poly", "should find polygon tee"),
            ("hood", "should find hoodie"),
        ]
        
        for query, description in test_queries:
            print(f"\n   Query: '{query}' ({description})")
            
            # Test prefix search only
            prefix_results = trie.search(query, limit=5, substring_search=False)
            print(f"     Prefix only: {len(prefix_results)} results")
            for r in prefix_results:
                print(f"       → {r.text}")
            
            # Test with substring search
            substring_results = trie.search(query, limit=5, substring_search=True)
            print(f"     With substring: {len(substring_results)} results")
            for r in substring_results:
                print(f"       → {r.text} (score: {r.score:.2f})")
        
        print(f"\n4. Direct substring search test...")
        substring_only = trie._substring_search("white", 5)
        print(f"   Direct substring search for 'white': {len(substring_only)} results")
        for r in substring_only:
            print(f"     → {r.text}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_search()
