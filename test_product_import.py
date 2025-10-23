#!/usr/bin/env python
"""
Test script for product CSV import functionality.

Usage:
    python test_product_import.py

This script tests the product import utility without going through GraphQL.
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
django.setup()

from saleor.csv.utils.product_import import import_products_from_csv


def test_import():
    """Test the product import functionality."""

    # Sample CSV content
    csv_content = """slug,name,price,description,category_slug,product_type_slug,cost_price,weight,stock_quantity,brand,is_published,track_inventory
test-product-001,Test Product 001,29.99,This is a test product for import testing.,clip-on-sunglasses,sunglasses,15.00,0.05,100,TestBrand,true,false
test-product-002,Test Product 002,39.99,Another test product with different specs.,clip-on-sunglasses,sunglasses,20.00,0.06,75,TestBrand,true,false
test-product-003,Test Product 003,19.99,Budget test product.,clip-on-sunglasses,sunglasses,8.00,0.04,200,Generic,true,false"""

    print("=" * 60)
    print("Product CSV Import Test")
    print("=" * 60)
    print()

    print("Importing products from CSV...")
    print()

    # Import products
    result = import_products_from_csv(csv_content)

    # Display results
    print("=" * 60)
    print("Import Results")
    print("=" * 60)
    print(f"Success: {result['success']}")
    print(f"Imported: {result['imported_count']} products")
    print(f"Skipped: {result['skipped_count']} products (already exist)")
    print(f"Errors: {result['error_count']}")
    print()

    if result["errors"]:
        print("=" * 60)
        print("Error Details")
        print("=" * 60)
        for error in result["errors"]:
            print(f"Row {error['row']} - {error['slug']}: {error['error']}")
        print()

    if result["success"]:
        print("✓ Import completed successfully!")
    else:
        print("✗ Import failed with errors.")

    print()
    print("To view the imported products:")
    print("  1. Log in to the Saleor Dashboard")
    print("  2. Navigate to Products")
    print(
        "  3. Look for products with slugs: test-product-001, test-product-002, test-product-003"
    )
    print()


def test_import_with_errors():
    """Test import with intentional errors to verify error handling."""

    # CSV with errors
    csv_content = """slug,name,price,description
,Missing Slug Product,29.99,This product is missing a slug
missing-price-product,Product Without Price,,This product has no price
invalid-price,Product With Invalid Price,not-a-number,Invalid price format
valid-product,Valid Test Product,49.99,This one should import successfully"""

    print("=" * 60)
    print("Error Handling Test")
    print("=" * 60)
    print()

    print("Importing CSV with intentional errors...")
    print()

    # Import products
    result = import_products_from_csv(csv_content)

    # Display results
    print("=" * 60)
    print("Import Results")
    print("=" * 60)
    print(f"Success: {result['success']}")
    print(f"Imported: {result['imported_count']} products")
    print(f"Skipped: {result['skipped_count']} products")
    print(f"Errors: {result['error_count']}")
    print()

    if result["errors"]:
        print("=" * 60)
        print("Expected Errors (for testing)")
        print("=" * 60)
        for error in result["errors"]:
            print(f"Row {error['row']} - {error['slug']}: {error['error']}")
        print()

    print("✓ Error handling test completed!")
    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Test product CSV import functionality"
    )
    parser.add_argument(
        "--with-errors", action="store_true", help="Run error handling test"
    )
    parser.add_argument("--csv-file", type=str, help="Path to CSV file to import")

    args = parser.parse_args()

    if args.csv_file:
        # Import from file
        print(f"Importing from file: {args.csv_file}")
        print()

        if not os.path.exists(args.csv_file):
            print(f"Error: File not found: {args.csv_file}")
            sys.exit(1)

        with open(args.csv_file, "r", encoding="utf-8") as f:
            csv_content = f.read()

        result = import_products_from_csv(csv_content)

        print("=" * 60)
        print("Import Results")
        print("=" * 60)
        print(f"Success: {result['success']}")
        print(f"Imported: {result['imported_count']} products")
        print(f"Skipped: {result['skipped_count']} products")
        print(f"Errors: {result['error_count']}")
        print()

        if result["errors"]:
            print("=" * 60)
            print("Errors")
            print("=" * 60)
            for error in result["errors"]:
                print(f"Row {error['row']} - {error['slug']}: {error['error']}")
            print()

    elif args.with_errors:
        # Run error handling test
        test_import_with_errors()
    else:
        # Run normal test
        test_import()

    print("Test completed!")
