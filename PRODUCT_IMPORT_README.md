# Product CSV Import System

This system allows you to import products from a CSV file into your Saleor e-commerce platform, including product images.

## Database Information

**Database Type**: PostgreSQL
- Saleor uses PostgreSQL as its primary database
- Configuration is in `saleor/settings.py` with connection details in environment variables
- Default connection: `postgres://saleor:saleor@localhost:5432/saleor`

## Files Created

1. **Management Command**: `saleor/core/management/commands/import_products_csv.py`
   - Main import logic
   - Handles CSV parsing, product creation, and image import

2. **Test Script**: `test_import.py`
   - Simple test script to verify the import works

3. **Run Script**: `run_import.sh`
   - Interactive bash script to run imports with different options

## CSV File Structure

Your CSV file should contain these key columns:
- `Product Code/SKU` - Unique product identifier
- `Product Name` - Product title
- `Product Description` - HTML description
- `Brand Name` - Brand attribute
- `Price` - Selling price
- `Cost Price` - Cost price
- `Product Weight` - Weight in appropriate units
- `Current Stock Level` - Initial stock quantity

## Image Structure

Images are organized in folders named by SKU:
```
product-image-repo/
├── 0107-55X16-B/
│   ├── image1.jpg
│   ├── image2.png
│   └── ...
├── 0107-55X16-S/
│   ├── image1.jpg
│   └── ...
└── ...
```

## How to Use

### Option 1: Using the Run Script (Recommended)

1. Navigate to the Saleor directory:
   ```bash
   cd /home/lei/workspace/88clipon/saleor
   ```

2. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

3. Run the import script:
   ```bash
   ./run_import.sh
   ```

4. Choose from the interactive options:
   - Dry run (test without creating products)
   - Import first 50 products (for testing)
   - Import all products (full import)
   - Import with custom limit

### Option 2: Using Django Management Command Directly

1. Activate the virtual environment:
   ```bash
   cd /home/lei/workspace/88clipon/saleor
   source .venv/bin/activate
   ```

2. Run the command with options:
   ```bash
   # Dry run (test mode)
   python manage.py import_products_csv \
       --csv-file /home/lei/workspace/88clipon/data/products-2025-09-13-update.csv \
       --images-dir /home/lei/workspace/88clipon/product-image-repo \
       --dry-run \
       --limit 10

   # Import first 50 products
   python manage.py import_products_csv \
       --csv-file /home/lei/workspace/88clipon/data/products-2025-09-13-update.csv \
       --images-dir /home/lei/workspace/88clipon/product-image-repo \
       --limit 50

   # Import all products
   python manage.py import_products_csv \
       --csv-file /home/lei/workspace/88clipon/data/products-2025-09-13-update.csv \
       --images-dir /home/lei/workspace/88clipon/product-image-repo
   ```

### Option 3: Using the Test Script

```bash
cd /home/lei/workspace/88clipon/saleor
source .venv/bin/activate
python test_import.py
```

## Command Options

- `--csv-file`: Path to the CSV file (required)
- `--images-dir`: Path to the images directory (required)
- `--dry-run`: Test mode - shows what would be imported without creating products
- `--limit`: Limit number of products to import (useful for testing)
- `--skip-images`: Skip image import (only import product data)

## What Gets Created

For each product, the system creates:

1. **Product**: Basic product information
2. **Product Variant**: SKU, pricing, inventory tracking
3. **Channel Listing**: Makes product available in the default channel
4. **Pricing**: Sets price and cost price in the channel
5. **Stock**: Sets initial stock quantity in the warehouse
6. **Attributes**: Brand attribute if specified
7. **Images**: All images from the SKU folder (up to 10 images per product)

## Database Storage

- **Product data**: Stored in PostgreSQL database tables
- **Images**: Stored in Django's media storage (typically `/media/products/`)
- **Image paths**: Referenced in the `ProductMedia` model with links to actual files

## Troubleshooting

### Common Issues

1. **CSV file not found**: Check the file path is correct
2. **Images not found**: Ensure the images directory structure matches SKU names
3. **Permission errors**: Make sure the Django process can write to the media directory
4. **Database errors**: Ensure the database is running and accessible

### Frontend Currency Error

**Error**: `'NoneType' object has no attribute 'currency'` on the storefront

**Cause**: Products imported without channel listings in all active channels. When the frontend tries to access pricing information for a product in a channel where it's not listed, the pricing resolver returns `None`, causing the currency access error.

**Solution**:
- The import command now automatically adds products to all active channels
- For existing products, run the channel listing fix script:

```bash
python manage.py shell -c "
from saleor.product.models import Product, ProductChannelListing, ProductVariantChannelListing
from saleor.channel.models import Channel

# Add missing channel listings for Ray-Ban products
rayban_products = Product.objects.filter(name__icontains='Ray-Ban')
channels = Channel.objects.filter(is_active=True)

for product in rayban_products:
    for channel in channels:
        if not ProductChannelListing.objects.filter(product=product, channel=channel).exists():
            # Create product channel listing
            ProductChannelListing.objects.create(
                product=product, channel=channel,
                is_published=True, visible_in_listings=True,
                currency=channel.currency_code
            )
            # Create variant channel listings with converted pricing
            for variant in product.variants.all():
                usd_listing = ProductVariantChannelListing.objects.filter(
                    variant=variant, channel__currency_code='USD'
                ).first()
                if usd_listing:
                    converted_price = usd_listing.price_amount * 4 if channel.currency_code == 'PLN' else usd_listing.price_amount
                    ProductVariantChannelListing.objects.create(
                        variant=variant, channel=channel,
                        price_amount=converted_price,
                        currency=channel.currency_code
                    )
"
```

### Testing

Always start with a dry run to test:
```bash
python manage.py import_products_csv \
    --csv-file /path/to/your/csv \
    --images-dir /path/to/images \
    --dry-run \
    --limit 5
```

### Checking Results

After import, you can check the results in:
- Django Admin: `/admin/products/product/`
- Saleor Dashboard: Check products and variants
- Database: Query the `product_product` and related tables

## Performance Notes

- Large imports (1000+ products) may take several minutes
- Images are processed sequentially to avoid memory issues
- Use `--limit` for testing before full import
- Consider running during off-peak hours for production imports

