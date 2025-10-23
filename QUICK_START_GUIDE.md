# Product CSV Import - Quick Start Guide

## Setup Complete! ✓

Your product CSV import system is now fully implemented and ready to use.

## What You Can Do Now

### 1. Import Products via Dashboard (Recommended)

**Step 1: Start Your Saleor Server**
```bash
cd /home/lei/workspace/88clipon/saleor
source .venv/bin/activate  # Activate your virtual environment
./start_app.sh  # Or however you start your Saleor server
```

**Step 2: Access GraphQL Playground**
- Open your browser and go to: `http://localhost:8000/graphql/`
- Make sure you're logged in to the Dashboard first

**Step 3: Use the Import Mutation**
```graphql
mutation ImportProducts($file: Upload!) {
  importProducts(input: { file: $file }) {
    result {
      success
      importedCount
      skippedCount
      errorCount
      errors {
        row
        slug
        error
      }
    }
    exportErrors {
      field
      message
      code
    }
  }
}
```

**Step 4: Upload Your CSV File**
- Use the sample file: `/home/lei/workspace/88clipon/data/sample_products_import.csv`
- Or create your own following the schema in `CSV_PRODUCT_IMPORT_SCHEMA.md`

### 2. Test the Import Utility (Command Line)

**Activate Virtual Environment:**
```bash
cd /home/lei/workspace/88clipon/saleor
source .venv/bin/activate
```

**Run Test Script:**
```bash
# Basic test with sample data
python test_product_import.py

# Test error handling
python test_product_import.py --with-errors

# Import from sample CSV file
python test_product_import.py --csv-file /home/lei/workspace/88clipon/data/sample_products_import.csv
```

### 3. Use the Existing Command-Line Tool

If you prefer the command-line interface (which also supports images):
```bash
cd /home/lei/workspace/88clipon/saleor
source .venv/bin/activate

python manage.py import_products_csv \
    --csv-file /home/lei/workspace/88clipon/data/sample_products_import.csv \
    --images-dir /home/lei/workspace/88clipon/product-image-repo \
    --limit 10
```

Note: The command-line tool uses a different CSV format with "Product Code/SKU" instead of "slug".

## Files Created

### Documentation
1. **CSV_PRODUCT_IMPORT_SCHEMA.md** - Complete CSV format specification
2. **PRODUCT_IMPORT_DASHBOARD_GUIDE.md** - How to use from dashboard
3. **PRODUCT_CSV_IMPORT_README.md** - Complete implementation overview
4. **QUICK_START_GUIDE.md** - This file

### Code
1. **saleor/csv/utils/product_import.py** - Core import logic
2. **saleor/graphql/csv/mutations/import_products.py** - GraphQL mutation
3. **test_product_import.py** - Test script

### Sample Data
1. **../data/sample_products_import.csv** - Sample CSV with 5 products

## CSV File Format

### Required Columns
- `slug` - Unique product identifier (used as SKU)
- `name` - Product name
- `price` - Product price in USD

### Optional Columns
- `description` - Product description
- `category_slug` - Category identifier
- `product_type_slug` - Product type identifier
- `cost_price` - Cost/wholesale price
- `weight` - Weight in kg
- `stock_quantity` - Initial stock
- `brand` - Brand name
- `is_published` - true/false
- `track_inventory` - true/false
- And more... (see CSV_PRODUCT_IMPORT_SCHEMA.md)

## Example CSV

```csv
slug,name,price,description,cost_price,stock_quantity,brand
ray-ban-rb5121-47x22,Ray-Ban RB5121 Clip-On,29.99,Premium clip-on sunglasses,15.50,100,Ray-Ban
oakley-ox8156-56x18,Oakley OX8156 Clip-On,34.99,Sport clip-on sunglasses,18.00,75,Oakley
```

## Testing Your Setup

### Option A: Quick Test with Python Script

```bash
cd /home/lei/workspace/88clipon/saleor
source .venv/bin/activate
python test_product_import.py
```

Expected output:
```
============================================================
Product CSV Import Test
============================================================

Importing products from CSV...

============================================================
Import Results
============================================================
Success: True
Imported: 3 products
Skipped: 0 products (already exist)
Errors: 0

✓ Import completed successfully!
```

### Option B: Test via GraphQL

1. Start your Saleor server
2. Open GraphQL Playground: `http://localhost:8000/graphql/`
3. Run the ImportProducts mutation
4. Upload the sample CSV file
5. Check the results

### Option C: Verify in Dashboard

1. Log in to Saleor Dashboard
2. Navigate to Products
3. Look for the imported products

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'dj_database_url'"
**Solution:** Activate your virtual environment first:
```bash
source .venv/bin/activate
```

### Error: "Missing required field: slug"
**Solution:** Ensure every row in your CSV has a value in the `slug` column.

### Error: "Product already exists, skipping"
**Solution:** The product with that slug already exists. Use a different slug or delete the existing product.

### Products Not Visible on Storefront
**Solution:**
- Ensure `is_published` is set to `true` in CSV
- Check that products have pricing in all active channels
- Verify products are in published categories

## Quick Reference

| Task | Command/Location |
|------|------------------|
| CSV Schema | `CSV_PRODUCT_IMPORT_SCHEMA.md` |
| Dashboard Guide | `PRODUCT_IMPORT_DASHBOARD_GUIDE.md` |
| Sample CSV | `../data/sample_products_import.csv` |
| Test Script | `python test_product_import.py` |
| GraphQL Mutation | `importProducts` |
| GraphQL Playground | `http://localhost:8000/graphql/` |

## Support Documents

For more details, see:
- **CSV_PRODUCT_IMPORT_SCHEMA.md** - Complete CSV format specification
- **PRODUCT_IMPORT_DASHBOARD_GUIDE.md** - Detailed dashboard usage instructions
- **PRODUCT_CSV_IMPORT_README.md** - Complete technical documentation

## Next Steps

1. ✓ Review the sample CSV file: `../data/sample_products_import.csv`
2. ✓ Read the CSV schema: `CSV_PRODUCT_IMPORT_SCHEMA.md`
3. ✓ Test the import with the sample file
4. ✓ Create your own CSV file with your products
5. ✓ Import via GraphQL or command line
6. ✓ Verify products in the Dashboard

Enjoy your new product import feature! 🎉

