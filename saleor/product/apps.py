from django.apps import AppConfig
from django.db.models.signals import post_delete


class ProductAppConfig(AppConfig):
    name = "saleor.product"

    def ready(self):
        from .models import Product, ProductVariant
        from .signals import (
            update_product_trie_index,
            remove_product_from_trie_index,
            update_variant_trie_index,
            remove_variant_from_trie_index,
        )
        from django.db.models.signals import post_save, post_delete

        # Connect trie search signals
        post_save.connect(
            update_product_trie_index,
            sender=Product,
            dispatch_uid="update_product_trie_index",
        )
        post_delete.connect(
            remove_product_from_trie_index,
            sender=Product,
            dispatch_uid="remove_product_from_trie_index",
        )
        post_save.connect(
            update_variant_trie_index,
            sender=ProductVariant,
            dispatch_uid="update_variant_trie_index",
        )
        post_delete.connect(
            remove_variant_from_trie_index,
            sender=ProductVariant,
            dispatch_uid="remove_variant_from_trie_index",
        )
