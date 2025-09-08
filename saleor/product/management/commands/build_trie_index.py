"""
Django management command to build and manage the Trie search index.
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.cache import cache
from django.db import transaction
import time

from saleor.product.trie_search import trie_search, rebuild_search_index, clear_search_index


class Command(BaseCommand):
    help = 'Build and manage the Trie search index for type-ahead functionality'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--rebuild',
            action='store_true',
            help='Force rebuild the index even if it exists in cache',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear the search index cache',
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show statistics about the search index',
        )
    
    def handle(self, *args, **options):
        if options['clear']:
            self.clear_index()
        
        if options['stats']:
            self.show_stats()
        
        if options['rebuild'] or not options['clear'] and not options['stats']:
            self.build_index(force_rebuild=options['rebuild'])
    
    def clear_index(self):
        """Clear the search index cache."""
        self.stdout.write("Clearing Trie search index cache...")
        try:
            clear_search_index()
            self.stdout.write(
                self.style.SUCCESS("Successfully cleared search index cache")
            )
        except Exception as e:
            raise CommandError(f"Failed to clear search index: {e}")
    
    def show_stats(self):
        """Show statistics about the search index."""
        self.stdout.write("Trie search index statistics:")
        try:
            stats = trie_search.get_stats()
            for key, value in stats.items():
                self.stdout.write(f"  {key}: {value}")
        except Exception as e:
            raise CommandError(f"Failed to get search index stats: {e}")
    
    def build_index(self, force_rebuild=False):
        """Build the search index."""
        start_time = time.time()
        
        if force_rebuild:
            self.stdout.write("Force rebuilding Trie search index...")
        else:
            self.stdout.write("Building Trie search index...")
        
        try:
            with transaction.atomic():
                rebuild_search_index()
            
            end_time = time.time()
            duration = end_time - start_time
            
            stats = trie_search.get_stats()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully built search index in {duration:.2f} seconds"
                )
            )
            self.stdout.write(f"  Total nodes: {stats.get('total_nodes', 0)}")
            self.stdout.write(f"  End nodes: {stats.get('end_nodes', 0)}")
            self.stdout.write(f"  Index loaded: {stats.get('is_loaded', False)}")
            
        except Exception as e:
            raise CommandError(f"Failed to build search index: {e}")


