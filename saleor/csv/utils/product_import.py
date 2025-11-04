"""Utility functions for importing products from CSV files."""

import csv
import datetime
import re
from decimal import Decimal
from io import StringIO
from typing import Any

from bs4 import BeautifulSoup
from django.db import transaction

from ...attribute.models import Attribute
from ...channel.models import Channel
from ...product.models import (
    Category,
    Product,
    ProductChannelListing,
    ProductType,
    ProductVariant,
    ProductVariantChannelListing,
)
from ...warehouse.models import Stock, Warehouse


def parse_boolean(value: str) -> bool:
    """Parse a string value to boolean."""
    if not value:
        return False
    value_lower = str(value).lower().strip()
    return value_lower in ("true", "1", "yes", "y")


def parse_decimal(value: str, default: Decimal = Decimal("0.00")) -> Decimal:
    """Parse a string value to Decimal."""
    if not value:
        return default
    try:
        return Decimal(str(value).strip())
    except (ValueError, TypeError):
        return default


def parse_int(value: str, default: int = 0) -> int:
    """Parse a string value to integer."""
    if not value:
        return default
    try:
        return int(float(str(value).strip()))
    except (ValueError, TypeError):
        return default


def is_html(text: str) -> bool:
    """Check if text contains HTML tags."""
    if not text:
        return False
    return bool(re.search(r"<[^>]+>", text))


def html_to_editorjs(html_content: str) -> dict[str, Any]:
    """Convert HTML content to EditorJS format used by Saleor.

    Args:
        html_content: HTML string to convert

    Returns:
        EditorJS JSON structure

    """
    if not html_content or not html_content.strip():
        return {"blocks": [], "time": 0, "version": "2.22.2"}

    try:
        soup = BeautifulSoup(html_content, "html.parser")
        blocks = []

        # Process each top-level element
        for element in soup.find_all(
            ["p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "div"]
        ):
            if element.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                # Header block
                level = int(element.name[1])
                text = element.get_text(strip=True)
                if text:
                    blocks.append(
                        {"type": "header", "data": {"text": text, "level": level}}
                    )
            elif element.name in ["ul", "ol"]:
                # List block
                items = [li.get_text(strip=True) for li in element.find_all("li")]
                if items:
                    blocks.append(
                        {
                            "type": "list",
                            "data": {
                                "style": "ordered"
                                if element.name == "ol"
                                else "unordered",
                                "items": items,
                            },
                        }
                    )
            elif element.name in ["p", "div"]:
                # Paragraph block
                text = element.get_text(strip=True)
                if text:
                    blocks.append({"type": "paragraph", "data": {"text": text}})

        # If no blocks were created, create a simple paragraph with all text
        if not blocks:
            text = soup.get_text(strip=True)
            if text:
                blocks.append({"type": "paragraph", "data": {"text": text}})

        return {"blocks": blocks, "time": 0, "version": "2.22.2"}

    except Exception:
        # If HTML parsing fails, return as simple paragraph
        clean_text = re.sub(r"<[^>]+>", "", html_content).strip()
        return {
            "blocks": [{"type": "paragraph", "data": {"text": clean_text}}],
            "time": 0,
            "version": "2.22.2",
        }


class ProductCSVImporter:
    """Handles importing products from CSV data."""

    def __init__(self):
        """Initialize the importer with required objects."""
        self.default_channel = None
        self.all_channels = []
        self.default_category = None
        self.default_product_type = None
        self.default_warehouse = None
        self.brand_attribute = None
        self.errors = []
        self.imported_count = 0
        self.skipped_count = 0

    def setup_defaults(self):
        """Create or get default objects needed for import."""
        # Get or create default channel
        self.default_channel, _ = Channel.objects.get_or_create(
            slug="default-channel",
            defaults={
                "name": "Default Channel",
                "currency_code": "USD",
                "is_active": True,
            },
        )

        # Get only the Global Store channel
        self.all_channels = list(
            Channel.objects.filter(slug="global-store", is_active=True)
        )
        if not self.all_channels:
            # Fallback to all active channels if global-store doesn't exist
            self.all_channels = list(Channel.objects.filter(is_active=True))

        # Get or create default category
        self.default_category, _ = Category.objects.get_or_create(
            slug="clip-on-sunglasses",
            defaults={
                "name": "Clip-On Sunglasses",
                "description": None,
                "description_plaintext": "Custom made clip-on sunglasses for prescription eyeglasses",
            },
        )

        # Get or create default product type
        self.default_product_type, _ = ProductType.objects.get_or_create(
            slug="clip-on-sunglasses",
            defaults={
                "name": "Clip-On Sunglasses Product Type",
                "kind": "normal",
                "is_shipping_required": True,
                "is_digital": False,
                "has_variants": True,  # Enable variants for lens colors
            },
        )

        # Get or create brand attribute
        self.brand_attribute, _ = Attribute.objects.get_or_create(
            slug="brand",
            defaults={
                "name": "Brand",
                "type": "PRODUCT_TYPE",
                "input_type": "DROPDOWN",
            },
        )

        # Ensure lens color attribute is assigned to the product type
        lens_color_attribute = Attribute.objects.filter(slug="lens-color").first()
        if lens_color_attribute and self.default_product_type:
            from saleor.attribute.models import AttributeVariant

            AttributeVariant.objects.get_or_create(
                attribute=lens_color_attribute,
                product_type=self.default_product_type,
            )

        # Get or create default warehouse
        self.default_warehouse, _ = Warehouse.objects.get_or_create(
            slug="default-warehouse",
            defaults={
                "name": "Default Warehouse",
                "email": "warehouse@example.com",
                "address": {
                    "first_name": "Warehouse",
                    "last_name": "Manager",
                    "street_address_1": "123 Warehouse St",
                    "city": "City",
                    "postal_code": "12345",
                    "country": "US",
                },
            },
        )

    def validate_row(self, row: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate a CSV row has all required fields."""
        # Check required fields
        slug = row.get("slug", "").strip()
        if not slug:
            return False, "Missing required field: slug"

        name = row.get("name", "").strip()
        if not name:
            return False, "Missing required field: name"

        price = row.get("price", "").strip()
        if not price:
            return False, "Missing required field: price"

        try:
            Decimal(price)
        except (ValueError, TypeError):
            return False, f"Invalid price value: {price}"

        return True, None

    def get_category(self, category_slug: str) -> Category:
        """Get category by slug or return default."""
        if category_slug:
            try:
                return Category.objects.get(slug=category_slug)
            except Category.DoesNotExist:
                pass
        return self.default_category

    def get_product_type(self, product_type_slug: str) -> ProductType:
        """Get product type by slug or return default."""
        if product_type_slug:
            try:
                return ProductType.objects.get(slug=product_type_slug)
            except ProductType.DoesNotExist:
                pass
        return self.default_product_type

    def _create_variant_listings_and_stock(
        self,
        variant: ProductVariant,
        price: Decimal,
        cost_price: Decimal,
        stock_quantity: int,
    ):
        """Helper method to create variant listings and stock."""
        # Set variant pricing in all channels
        for channel in self.all_channels:
            variant_listing = ProductVariantChannelListing.objects.create(
                variant=variant,
                channel=channel,
                price_amount=price,
                cost_price_amount=cost_price,
                currency=channel.currency_code,
            )

            # Set discounted_price to prevent errors
            variant_listing.discounted_price = variant_listing.price
            variant_listing.save()

        # Set stock
        Stock.objects.create(
            product_variant=variant,
            warehouse=self.default_warehouse,
            quantity=stock_quantity,
        )

    def create_product_from_row(self, row: dict[str, Any]) -> Product | None:
        """Create a product from a CSV row."""
        slug = row.get("slug", "").strip()

        # Check if product already exists
        if Product.objects.filter(slug=slug).exists():
            self.skipped_count += 1
            return None

        # Extract fields from row
        name = row.get("name", "").strip()
        description = row.get("description", "").strip()
        category_slug = row.get("category_slug", "").strip()
        product_type_slug = row.get("product_type_slug", "").strip()
        weight = parse_decimal(row.get("weight", ""), Decimal("0.0"))
        is_published = parse_boolean(row.get("is_published", "true"))
        seo_title = row.get("seo_title", "").strip()
        seo_description = row.get("seo_description", "").strip()
        external_reference = row.get("external_reference", "").strip()

        # Get category and product type
        category = self.get_category(category_slug)
        product_type = self.get_product_type(product_type_slug)

        with transaction.atomic():
            # Create product
            # Handle description - convert HTML to EditorJS format if HTML detected
            description_json = None
            description_plain = description

            if description and is_html(description):
                # Convert HTML to EditorJS format
                description_json = html_to_editorjs(description)
                # Also extract plain text for search
                description_plain = re.sub(r"<[^>]+>", "", description).strip()
            elif description:
                # Plain text - also create EditorJS format for consistency
                description_json = {
                    "blocks": [{"type": "paragraph", "data": {"text": description}}],
                    "time": 0,
                    "version": "2.22.2",
                }

            product = Product.objects.create(
                name=name,
                slug=slug,
                description=description_json,
                description_plaintext=description_plain,
                product_type=product_type,
                category=category,
                weight=weight,
                search_index_dirty=True,
                seo_title=seo_title or None,
                seo_description=seo_description or None,
                external_reference=external_reference or None,
            )

            # Add to all channels
            # Handle available_for_purchase - default to True (available now)
            available_for_purchase = parse_boolean(
                row.get("available_for_purchase", "true")
            )
            available_for_purchase_at = (
                datetime.datetime.now(tz=datetime.UTC)
                if available_for_purchase
                else None
            )

            for channel in self.all_channels:
                ProductChannelListing.objects.create(
                    product=product,
                    channel=channel,
                    is_published=is_published,
                    visible_in_listings=is_published,
                    available_for_purchase_at=available_for_purchase_at,
                    currency=channel.currency_code,
                )

            # Create variants for each lens color
            price = parse_decimal(row.get("price", "0"))
            cost_price = parse_decimal(row.get("cost_price", "0"))
            track_inventory = parse_boolean(row.get("track_inventory", "false"))
            stock_quantity = parse_int(row.get("stock_quantity", "100"), 100)

            # Get lens color attribute and its values
            lens_color_attribute = Attribute.objects.filter(slug="lens-color").first()
            if not lens_color_attribute:
                # Fallback: create a single variant if lens color attribute doesn't exist
                variant = ProductVariant.objects.create(
                    product=product,
                    sku=slug,
                    name=name,
                    track_inventory=track_inventory,
                    weight=weight,
                )
                self._create_variant_listings_and_stock(
                    variant, price, cost_price, stock_quantity
                )
            else:
                # Get lens color values - only use the 13 main colors
                from saleor.attribute.models import AttributeValue

                # Define the 13 lens colors to use (in order of preference)
                preferred_lens_color_slugs = [
                    "purple-gradient",
                    "grey-gradient",
                    "green-g-15",
                    "non-polarized-grey-for-pilots",
                    "brown",
                    "grey",
                    "night-vision",
                    "brown-gradient",
                    "computer-blue-light-blocking",
                    "rose-pink-mirrored",
                    "revo-blue-mirrored",
                    "silver-mirrored",
                    "orange-gold-mirrored",
                ]

                # Get lens colors filtered by the preferred list
                lens_colors = AttributeValue.objects.filter(
                    attribute=lens_color_attribute, slug__in=preferred_lens_color_slugs
                ).order_by("sort_order", "pk")

                # Create a variant for each lens color
                for lens_color in lens_colors:
                    # Use lens color name as variant name
                    variant_name = lens_color.name

                    variant = ProductVariant.objects.create(
                        product=product,
                        name=variant_name,
                        track_inventory=track_inventory,
                        weight=weight,
                    )

                    # Set variant attribute value using the proper Saleor method
                    from saleor.attribute.utils import (
                        associate_attribute_values_to_instance,
                    )

                    attr_val_map = {lens_color_attribute.pk: [lens_color]}
                    associate_attribute_values_to_instance(variant, attr_val_map)

                    # Create listings and stock for this variant
                    self._create_variant_listings_and_stock(
                        variant, price, cost_price, stock_quantity
                    )

            # Handle brand attribute if provided
            brand = row.get("brand", "").strip()
            if brand:
                # This is a simplified version - full attribute assignment
                # requires more complex logic in Saleor
                pass

            self.imported_count += 1
            return product

    def import_from_csv_content(
        self,
        csv_content: str,
        delimiter: str = ",",
    ) -> dict[str, Any]:
        """Import products from CSV content.

        Args:
            csv_content: CSV file content as string
            delimiter: CSV delimiter (default: comma)

        Returns:
            Dictionary with import results

        """
        self.setup_defaults()
        self.errors = []
        self.imported_count = 0
        self.skipped_count = 0

        try:
            # Parse CSV
            csv_file = StringIO(csv_content)
            reader = csv.DictReader(csv_file, delimiter=delimiter)

            for row_num, row in enumerate(
                reader, start=2
            ):  # Start at 2 (header is row 1)
                # Validate row
                is_valid, error_message = self.validate_row(row)
                if not is_valid:
                    self.errors.append(
                        {
                            "row": row_num,
                            "slug": row.get("slug", "Unknown"),
                            "error": error_message,
                        }
                    )
                    continue

                # Import product
                try:
                    self.create_product_from_row(row)
                except Exception as e:
                    self.errors.append(
                        {
                            "row": row_num,
                            "slug": row.get("slug", "Unknown"),
                            "error": str(e),
                        }
                    )

            return {
                "success": True,
                "imported_count": self.imported_count,
                "skipped_count": self.skipped_count,
                "error_count": len(self.errors),
                "errors": self.errors,
            }

        except Exception as e:
            return {
                "success": False,
                "imported_count": self.imported_count,
                "skipped_count": self.skipped_count,
                "error_count": len(self.errors) + 1,
                "errors": self.errors + [{"row": 0, "slug": "", "error": str(e)}],
            }


def import_products_from_csv(csv_content: str) -> dict[str, Any]:
    """Import products from CSV content.

    Args:
        csv_content: CSV file content as string

    Returns:
        Dictionary with import results containing:
        - success: bool
        - imported_count: int
        - skipped_count: int
        - error_count: int
        - errors: list of error details

    """
    importer = ProductCSVImporter()
    return importer.import_from_csv_content(csv_content)
