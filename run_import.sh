#!/bin/bash

# Script to run the CSV product import
# Make sure you're in the Saleor directory and have the virtual environment activated

echo "Starting CSV Product Import..."
echo "=============================="

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Please activate your virtual environment first:"
    echo "cd /home/lei/workspace/88clipon/saleor"
    echo "source .venv/bin/activate"
    exit 1
fi

# Check if required files exist
CSV_FILE="/home/lei/workspace/88clipon/data/products-2025-09-13-update.csv"
IMAGES_DIR="/home/lei/workspace/88clipon/product-image-repo"

if [ ! -f "$CSV_FILE" ]; then
    echo "Error: CSV file not found at $CSV_FILE"
    exit 1
fi

if [ ! -d "$IMAGES_DIR" ]; then
    echo "Error: Images directory not found at $IMAGES_DIR"
    exit 1
fi

echo "CSV file: $CSV_FILE"
echo "Images directory: $IMAGES_DIR"
echo ""

# Ask user for options
echo "Import options:"
echo "1. Dry run (test without creating products) - limit 10 products"
echo "2. Import first 50 products (for testing)"
echo "3. Import all products (full import)"
echo "4. Import with custom limit"
echo ""
read -p "Choose option (1-4): " choice

case $choice in
    1)
        echo "Running dry run with 10 products..."
        python manage.py import_products_csv \
            --csv-file "$CSV_FILE" \
            --images-dir "$IMAGES_DIR" \
            --dry-run \
            --limit 10
        ;;
    2)
        echo "Importing first 50 products..."
        python manage.py import_products_csv \
            --csv-file "$CSV_FILE" \
            --images-dir "$IMAGES_DIR" \
            --limit 50
        ;;
    3)
        echo "Importing ALL products (this may take a while)..."
        read -p "Are you sure? (y/N): " confirm
        if [[ $confirm == [yY] ]]; then
            python manage.py import_products_csv \
                --csv-file "$CSV_FILE" \
                --images-dir "$IMAGES_DIR"
        else
            echo "Import cancelled."
        fi
        ;;
    4)
        read -p "Enter limit (number of products): " limit
        echo "Importing $limit products..."
        python manage.py import_products_csv \
            --csv-file "$CSV_FILE" \
            --images-dir "$IMAGES_DIR" \
            --limit "$limit"
        ;;
    *)
        echo "Invalid option. Exiting."
        exit 1
        ;;
esac

echo ""
echo "Import process completed!"

