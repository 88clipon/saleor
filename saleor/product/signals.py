"""
Django signals for Trie search index management.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
import logging

from .models import Product, ProductVariant
from .trie_search import trie_search

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Product)
def update_product_trie_index(sender, instance, created, **kwargs):
    """Update Trie index when a product is created or updated."""
    try:
        # Clear the cache to force rebuild on next access
        trie_search.clear_cache()
        logger.info(f"Trie index cache cleared due to product {'creation' if created else 'update'}: {instance.id}")
    except Exception as e:
        logger.error(f"Failed to update Trie index for product {instance.id}: {e}")


@receiver(post_delete, sender=Product)
def remove_product_from_trie_index(sender, instance, **kwargs):
    """Update Trie index when a product is deleted."""
    try:
        # Clear the cache to force rebuild on next access
        trie_search.clear_cache()
        logger.info(f"Trie index cache cleared due to product deletion: {instance.id}")
    except Exception as e:
        logger.error(f"Failed to update Trie index for product deletion {instance.id}: {e}")


@receiver(post_save, sender=ProductVariant)
def update_variant_trie_index(sender, instance, created, **kwargs):
    """Update Trie index when a product variant is created or updated."""
    try:
        # Clear the cache to force rebuild on next access
        trie_search.clear_cache()
        logger.info(f"Trie index cache cleared due to variant {'creation' if created else 'update'}: {instance.id}")
    except Exception as e:
        logger.error(f"Failed to update Trie index for variant {instance.id}: {e}")


@receiver(post_delete, sender=ProductVariant)
def remove_variant_from_trie_index(sender, instance, **kwargs):
    """Update Trie index when a product variant is deleted."""
    try:
        # Clear the cache to force rebuild on next access
        trie_search.clear_cache()
        logger.info(f"Trie index cache cleared due to variant deletion: {instance.id}")
    except Exception as e:
        logger.error(f"Failed to update Trie index for variant deletion {instance.id}: {e}")