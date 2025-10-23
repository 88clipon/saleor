import csv
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any

from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from saleor.attribute.models import Attribute, AttributeValue
from saleor.channel.models import Channel
from saleor.core.utils import build_absolute_uri
from saleor.product.models import (
    Category,
    Product,
    ProductChannelListing,
    ProductMedia,
    ProductType,
    ProductVariant,
    ProductVariantChannelListing,
    ProductMediaTypes,
)
from saleor.warehouse.models import Warehouse, Stock


class Command(BaseCommand):
    help = "Import products from CSV file with images"

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            type=str,
            required=True,
            help='Path to the CSV file to import'
        )
        parser.add_argument(
            '--images-dir',
            type=str,
            required=True,
            help='Path to the directory containing product images'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without actually creating products (for testing)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of products to import (for testing)'
        )
        parser.add_argument(
            '--skip-images',
            action='store_true',
            help='Skip image import (only import product data)'
        )

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        images_dir = options['images_dir']
        dry_run = options['dry_run']
        limit = options.get('limit')
        skip_images = options['skip_images']

        if not os.path.exists(csv_file_path):
            raise CommandError(f"CSV file not found: {csv_file_path}")

        if not os.path.exists(images_dir):
            raise CommandError(f"Images directory not found: {images_dir}")

        self.stdout.write(f"Starting product import from {csv_file_path}")
        if dry_run:
            self.stdout.write("DRY RUN MODE - No products will be created")

        # Setup required objects
        self.setup_required_objects()

        # Import products
        imported_count = 0
        error_count = 0

        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            for i, row in enumerate(reader):
                if limit and i >= limit:
                    break

                try:
                    self.import_product(row, images_dir, dry_run, skip_images)
                    imported_count += 1

                    if imported_count % 10 == 0:
                        self.stdout.write(f"Imported {imported_count} products...")

                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f"Error importing product {row.get('Product Code/SKU', 'Unknown')}: {str(e)}")
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Import completed. Imported: {imported_count}, Errors: {error_count}"
            )
        )

    def setup_required_objects(self):
        """Create required categories, product types, and channels if they don't exist"""
        # Get or create default channel
        self.channel, _ = Channel.objects.get_or_create(
            slug="default-channel",
            defaults={
                'name': 'Default Channel',
                'currency_code': 'USD',
                'is_active': True,
            }
        )
        # Ensure channel has USD currency
        if self.channel.currency_code != 'USD':
            self.channel.currency_code = 'USD'
            self.channel.save()

        # Get all active channels for multi-channel support
        self.all_channels = Channel.objects.filter(is_active=True)

        # Get or create category
        self.category, _ = Category.objects.get_or_create(
            slug="clip-on-sunglasses",
            defaults={
                'name': 'Clip-On Sunglasses',
                'description': None,  # Leave description empty for now
                'description_plaintext': 'Custom made clip-on sunglasses for prescription eyeglasses',
            }
        )

        # Get or create product type
        self.product_type, _ = ProductType.objects.get_or_create(
            name="Sunglasses",
            defaults={
                'slug': 'sunglasses',
                'is_shipping_required': True,
                'is_digital': False,
                'has_variants': False,  # Match working product type configuration
            }
        )

        # Get or create attributes
        self.brand_attribute, _ = Attribute.objects.get_or_create(
            slug="brand",
            defaults={
                'name': 'Brand',
                'type': 'dropdown',
                'input_type': 'dropdown',
            }
        )

        # Get or create default warehouse
        self.warehouse, _ = Warehouse.objects.get_or_create(
            slug="default-warehouse",
            defaults={
                'name': 'Default Warehouse',
                'email': 'warehouse@example.com',
                'address': {
                    'first_name': 'Warehouse',
                    'last_name': 'Manager',
                    'street_address_1': '123 Warehouse St',
                    'city': 'City',
                    'postal_code': '12345',
                    'country': 'US',
                }
            }
        )

    def import_product(self, row: Dict[str, Any], images_dir: str, dry_run: bool, skip_images: bool):
        """Import a single product from CSV row"""
        sku = row.get('Product Code/SKU', '').strip()
        if not sku:
            raise ValueError("Product SKU is required")

        # Check if product already exists
        if Product.objects.filter(slug=slugify(sku)).exists():
            self.stdout.write(f"Product {sku} already exists, skipping...")
            return

        product_data = {
            'name': row.get('Product Name', '').strip(),
            'description': None,  # We'll handle this separately
            'description_plaintext': row.get('Product Description', '').strip(),
            'product_type': self.product_type,
            'category': self.category,
            'weight': float(row.get('Product Weight', 0) or 0),
            'search_index_dirty': True,
        }

        # Create slug from SKU
        product_data['slug'] = slugify(sku)

        if dry_run:
            self.stdout.write(f"Would create product: {product_data['name']} (SKU: {sku})")
            return

        with transaction.atomic():
            # Create product
            product = Product.objects.create(**product_data)

            # Add to all channels
            for channel in self.all_channels:
                ProductChannelListing.objects.create(
                    product=product,
                    channel=channel,
                    is_published=True,
                    visible_in_listings=True,
                    available_for_purchase_at=product.created_at,
                    currency=channel.currency_code,  # Use channel's currency
                )

            # Create product variant
            variant = ProductVariant.objects.create(
                product=product,
                sku=sku,
                name=product.name,
                track_inventory=False,  # Match working product configuration
                weight=product.weight,
            )

            # Set variant pricing in all channels
            base_price = float(row.get('Price', 0) or 0)
            base_cost = float(row.get('Cost Price', 0) or 0)

            for channel in self.all_channels:
                # Convert price based on channel currency
                if channel.currency_code == 'USD':
                    price_amount = base_price
                    cost_amount = base_cost
                elif channel.currency_code == 'PLN':
                    # Simple USD to PLN conversion (1 USD ≈ 4 PLN)
                    price_amount = base_price * 4
                    cost_amount = base_cost * 4
                else:
                    # For other currencies, use base price
                    price_amount = base_price
                    cost_amount = base_cost

                variant_listing = ProductVariantChannelListing.objects.create(
                    variant=variant,
                    channel=channel,
                    price_amount=price_amount,
                    cost_price_amount=cost_amount,
                    currency=channel.currency_code,
                )

                # Set discounted_price to prevent tax calculation errors
                variant_listing.discounted_price = variant_listing.price
                variant_listing.save()

            # Set variant stock
            stock_quantity = row.get('Current Stock Level', 100)
            try:
                stock_quantity = int(float(stock_quantity)) if stock_quantity else 100
            except (ValueError, TypeError):
                stock_quantity = 100

            Stock.objects.create(
                product_variant=variant,
                warehouse=self.warehouse,
                quantity=stock_quantity,
            )

            # Handle images
            if not skip_images:
                self.import_product_images(product, sku, images_dir)

            # Note: Attributes are handled through a complex system in Saleor
            # For now, we'll skip attribute assignment and focus on basic product import

            self.stdout.write(f"Created product: {product.name} (SKU: {sku})")

    def import_product_images(self, product: Product, sku: str, images_dir: str):
        """Import images for a product from the images directory"""
        # The SKU format in CSV is like "RB-5121-47X22-F"
        # The image folder format is like "RB-RB5121-47X22-T-B" and "RB-RB5121-47X22-T-S"
        # We need to find both -B and -S variants and import images from both

        # Generate possible base names for the SKU
        base_names = [
            sku,  # Direct match
            sku.replace('RB-', 'RB-RB').replace('-F', '-T'),  # RB-5121-47X22-F -> RB-RB5121-47X22-T
            sku.replace('-F', ''),  # Remove -F suffix
            sku.replace('RB-', ''),  # Remove RB- prefix
        ]

        # For each base name, try both -B and -S suffixes
        found_dirs = []
        for base_name in base_names:
            for suffix in ['-B', '-S']:
                possible_dir = base_name + suffix
                test_dir = os.path.join(images_dir, possible_dir)
                if os.path.exists(test_dir):
                    found_dirs.append(test_dir)
                    self.stdout.write(f"Found image directory: {possible_dir}")

        if not found_dirs:
            self.stdout.write(f"Image directories not found for SKU: {sku}")
            self.stdout.write(f"Tried base names: {base_names}")
            return

        # Look for image files in all found directories
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        all_image_files = []

        for sku_dir in found_dirs:
            self.stdout.write(f"  Scanning directory: {os.path.basename(sku_dir)}")
            for root, dirs, files in os.walk(sku_dir):
                for file in files:
                    # Only include images that start with "img" and have valid extensions
                    if (file.lower().startswith('img') and
                        any(file.lower().endswith(ext) for ext in image_extensions)):
                        all_image_files.append(os.path.join(root, file))

        if not all_image_files:
            self.stdout.write(f"No 'img' prefixed images found for SKU: {sku}")
            return

        # Sort images to maintain consistent order
        all_image_files.sort()

        self.stdout.write(f"  Found {len(all_image_files)} 'img' prefixed images")

        for i, image_path in enumerate(all_image_files):
            try:
                # Skip if we already have enough images (limit to 10)
                if i >= 10:
                    break

                # Create unique filename to avoid duplicates
                original_filename = os.path.basename(image_path)
                filename_without_ext = os.path.splitext(original_filename)[0]
                file_extension = os.path.splitext(original_filename)[1]

                # Create unique filename: img01_sku_suffix.jpg
                unique_filename = f"{filename_without_ext}_{sku}_{i}{file_extension}"

                with open(image_path, 'rb') as img_file:
                    django_file = File(img_file, name=unique_filename)

                    # Create product media
                    media = ProductMedia.objects.create(
                        product=product,
                        image=django_file,
                        alt=f"{product.name} - Image {i + 1}",
                        type=ProductMediaTypes.IMAGE,
                        sort_order=i,
                    )

                    self.stdout.write(f"  Added image: {unique_filename} (from {original_filename})")

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"  Failed to import image {image_path}: {str(e)}")
                )

    def get_image_files_from_directory(self, directory: str) -> List[str]:
        """Get all image files from a directory recursively"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        image_files = []

        if not os.path.exists(directory):
            return image_files

        for root, dirs, files in os.walk(directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    image_files.append(os.path.join(root, file))

        return sorted(image_files)
