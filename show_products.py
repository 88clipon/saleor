#!/usr/bin/env python3
"""
Script to show imported products in the database
"""
import os
import sys
import django

# Add the Saleor project to the Python path
sys.path.insert(0, '/home/lei/workspace/88clipon/saleor')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saleor.settings')
django.setup()

from saleor.product.models import Product, ProductVariant, ProductChannelListing, ProductVariantChannelListing, ProductMedia
from saleor.warehouse.models import Stock
from saleor.channel.models import Channel
from saleor.product.models import Category, ProductType

def show_products():
    """Display information about imported products"""

    print("=" * 80)
    print("IMPORTED PRODUCTS IN DATABASE")
    print("=" * 80)

    # Get the most recent products (the ones we just imported)
    products = Product.objects.filter(
        slug__startswith='rb-5121'  # Filter for the Ray-Ban products we imported
    ).order_by('-created_at')[:2]

    if not products:
        print("No products found. Let's check what products exist:")
        all_products = Product.objects.all().order_by('-created_at')[:5]
        for p in all_products:
            print(f"  - {p.name} (SKU: {p.slug})")
        return

    for i, product in enumerate(products, 1):
        print(f"\n{'='*60}")
        print(f"PRODUCT #{i}: {product.name}")
        print(f"{'='*60}")

        # Basic product info
        print(f"ID: {product.id}")
        print(f"Name: {product.name}")
        print(f"Slug: {product.slug}")
        print(f"Description (plaintext): {product.description_plaintext[:200]}...")
        print(f"Product Type: {product.product_type.name}")
        print(f"Category: {product.category.name if product.category else 'None'}")
        print(f"Weight: {product.weight}")
        print(f"Created: {product.created_at}")
        print(f"Updated: {product.updated_at}")

        # Channel listings
        print(f"\n--- CHANNEL LISTINGS ---")
        for listing in product.channel_listings.all():
            print(f"Channel: {listing.channel.name} ({listing.channel.currency_code})")
            print(f"  Published: {listing.is_published}")
            print(f"  Visible in listings: {listing.visible_in_listings}")
            print(f"  Available for purchase: {listing.available_for_purchase_at}")

        # Product variants
        print(f"\n--- VARIANTS ---")
        for variant in product.variants.all():
            print(f"Variant ID: {variant.id}")
            print(f"SKU: {variant.sku}")
            print(f"Name: {variant.name}")
            print(f"Track inventory: {variant.track_inventory}")
            print(f"Weight: {variant.weight}")

            # Variant channel listings (pricing)
            print(f"\n  --- PRICING ---")
            for v_listing in variant.channel_listings.all():
                print(f"  Channel: {v_listing.channel.name}")
                print(f"  Price: {v_listing.price_amount} {v_listing.currency}")
                print(f"  Cost Price: {v_listing.cost_price_amount} {v_listing.currency}")

            # Stock
            print(f"\n  --- STOCK ---")
            for stock in variant.stocks.all():
                print(f"  Warehouse: {stock.warehouse.name}")
                print(f"  Quantity: {stock.quantity}")

        # Product media (images)
        print(f"\n--- IMAGES ---")
        media_count = product.media.count()
        print(f"Total images: {media_count}")
        for j, media in enumerate(product.media.all()[:5], 1):  # Show first 5 images
            print(f"  Image {j}:")
            print(f"    Alt text: {media.alt}")
            print(f"    Type: {media.type}")
            print(f"    Sort order: {media.sort_order}")
            if media.image:
                print(f"    File: {media.image.name}")
            else:
                print(f"    File: None")

        if media_count > 5:
            print(f"  ... and {media_count - 5} more images")

def show_database_summary():
    """Show summary of what's in the database"""
    print(f"\n{'='*60}")
    print("DATABASE SUMMARY")
    print(f"{'='*60}")

    print(f"Total Products: {Product.objects.count()}")
    print(f"Total Variants: {ProductVariant.objects.count()}")
    print(f"Total Channels: {Channel.objects.count()}")
    print(f"Total Categories: {Category.objects.count()}")
    print(f"Total Product Types: {ProductType.objects.count()}")
    print(f"Total Product Media: {ProductMedia.objects.count()}")

    # Show recent products
    recent_products = Product.objects.all().order_by('-created_at')[:5]
    print(f"\nRecent Products:")
    for p in recent_products:
        print(f"  - {p.name} ({p.created_at})")

if __name__ == "__main__":
    show_database_summary()
    show_products()

