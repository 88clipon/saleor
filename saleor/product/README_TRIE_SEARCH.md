# Trie-based Type-ahead Search for Saleor

This module provides a high-performance Trie-based search implementation for Saleor's product catalog, designed to work alongside the existing PostgreSQL full-text search functionality.

## Features

- **Fast Prefix Search**: O(m) search time where m is the length of the search prefix
- **Case-insensitive**: Automatically handles different cases
- **Multiple Search Types**: Search products, variants, and SKUs
- **Caching**: Built-in caching for improved performance
- **Auto-updates**: Automatically rebuilds when products/variants change
- **GraphQL Integration**: Full GraphQL API support
- **Management Commands**: Easy index management via Django commands

## Architecture

### Core Components

1. **TrieSearch Class**: Main search implementation
2. **SearchResult Class**: Represents search results with metadata
3. **GraphQL Types**: API integration for frontend consumption
4. **Signals**: Automatic index updates on data changes
5. **Management Commands**: Index building and maintenance

### Data Structure

The Trie (prefix tree) stores:
- Product names and slugs
- Product variant names and SKUs
- Metadata for each searchable item
- Frequency counts for ranking

## Usage

### GraphQL API

```graphql
query TrieSearch($query: String!, $limit: Int, $types: [String]) {
  trieSearch(query: $query, limit: $limit, types: $types) {
    id
    text
    type
    score
    metadata
  }
}
```

**Parameters:**
- `query`: Search prefix (minimum 2 characters)
- `limit`: Maximum number of results (default: 10)
- `types`: Filter by result types (`["product", "variant", "sku"]`)

**Response:**
- `id`: Unique identifier
- `text`: The matched text
- `type`: Result type (product, variant, sku, product_slug)
- `score`: Relevance score
- `metadata`: Additional information (product type, SKU, etc.)

### Python API

```python
from saleor.product.trie_search import get_trie_search

# Get the search instance
trie = get_trie_search()

# Search for products
results = trie.search("apple", limit=5)

# Filter by type
product_results = [r for r in results if r.type == "product"]
```

### Management Commands

```bash
# Build the search index
python manage.py build_trie_index

# Force rebuild (ignore cache)
python manage.py build_trie_index --rebuild

# Clear the cache
python manage.py build_trie_index --clear

# View statistics
python manage.py build_trie_index --stats
```

## Configuration

### Cache Settings

The search index is cached using Django's cache framework. Default settings:

```python
# Cache timeout: 1 hour
CACHE_TIMEOUT = 3600

# Cache key
CACHE_KEY = "trie_search_index"
```

### Performance Tuning

1. **Index Size**: The index size depends on the number of products and variants
2. **Memory Usage**: Approximately 1MB per 1000 products (estimated)
3. **Build Time**: Varies with dataset size (typically < 1 second for 10k products)

## Implementation Details

### Trie Structure

```
Root
├── a
│   └── p
│       └── p
│           └── l
│               └── e (end_node: true, results: [ProductResult])
└── s
    └── a
        └── m
            └── s
                └── u
                    └── n
                        └── g (end_node: true, results: [ProductResult])
```

### Search Process

1. Navigate to prefix node: O(m) where m = prefix length
2. Collect all results from node and children: O(k) where k = number of results
3. Sort by relevance: O(k log k)
4. Return top N results: O(limit)

### Caching Strategy

- **Cache Key**: `trie_search_index`
- **Cache Timeout**: 1 hour
- **Invalidation**: On product/variant changes
- **Fallback**: Rebuild from database if cache miss

## Error Handling

The implementation includes comprehensive error handling:

- **Graceful Degradation**: Returns empty results on errors
- **Logging**: All errors are logged for debugging
- **Cache Failures**: Falls back to database rebuild
- **Serialization Errors**: Handles JSON serialization issues

## Testing

Run the test suite:

```bash
python manage.py test saleor.product.tests.test_trie_search
```

Test coverage includes:
- Basic search functionality
- Case-insensitive search
- Type filtering
- Caching behavior
- GraphQL integration
- Error handling
- Database integration

## Performance Considerations

### Memory Usage

- **Trie Nodes**: ~100 bytes per node
- **Search Results**: ~200 bytes per result
- **Total**: ~1MB per 1000 products

### Search Performance

- **Prefix Search**: O(m) where m = prefix length
- **Result Collection**: O(k) where k = number of results
- **Typical Response Time**: < 10ms for most queries

### Index Building

- **Time Complexity**: O(n) where n = total characters in all searchable text
- **Database Queries**: Optimized with select_related
- **Memory Usage**: Temporary spike during build

## Monitoring

### Statistics

The `get_stats()` method provides:

```python
stats = trie.get_stats()
# Returns:
# {
#     'is_loaded': True,
#     'total_nodes': 15432,
#     'end_nodes': 1234,
#     'cache_key': 'trie_search_index'
# }
```

### Logging

Enable debug logging:

```python
LOGGING = {
    'loggers': {
        'saleor.product.trie_search': {
            'level': 'DEBUG',
            'handlers': ['console'],
        }
    }
}
```

## Troubleshooting

### Common Issues

1. **Empty Results**: Check if index is built and products exist
2. **Slow Performance**: Verify cache is working and index is loaded
3. **Memory Issues**: Monitor index size and consider pagination
4. **Cache Misses**: Check cache configuration and Redis/memcached status

### Debug Commands

```bash
# Check index status
python manage.py build_trie_index --stats

# Rebuild index
python manage.py build_trie_index --rebuild

# Clear cache
python manage.py build_trie_index --clear
```

## Future Enhancements

Potential improvements:

1. **Fuzzy Search**: Add Levenshtein distance for typo tolerance
2. **Weighted Results**: Implement more sophisticated scoring
3. **Multi-language**: Support for different languages
4. **Real-time Updates**: WebSocket-based live updates
5. **Analytics**: Search analytics and popular queries
6. **Custom Fields**: Support for custom searchable fields

## Contributing

When contributing to this module:

1. Follow the existing code style
2. Add comprehensive tests
3. Update documentation
4. Consider performance implications
5. Test with large datasets

## License

This module is part of Saleor and follows the same BSD-3-Clause license.


