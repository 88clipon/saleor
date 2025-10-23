# Product CSV Import - Dashboard Integration Guide

This guide explains how to use the new Product CSV Import feature from the Saleor Dashboard.

## Overview

The Product CSV Import feature allows you to bulk import products into your Saleor store by uploading a CSV file through the GraphQL API. This is accessible from the Saleor Dashboard.

## GraphQL Mutation

The import functionality is exposed through the `importProducts` GraphQL mutation.

### Mutation Definition

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

### Response Structure

```json
{
  "data": {
    "importProducts": {
      "result": {
        "success": true,
        "importedCount": 5,
        "skippedCount": 2,
        "errorCount": 1,
        "errors": [
          {
            "row": 3,
            "slug": "invalid-product",
            "error": "Invalid price value: not-a-number"
          }
        ]
      },
      "exportErrors": []
    }
  }
}
```

## Using from the Dashboard

### Method 1: GraphQL Playground (Built-in)

1. **Access the GraphQL Playground**
   - Navigate to your Saleor GraphQL endpoint (usually `/graphql/`)
   - Example: `http://localhost:8000/graphql/`

2. **Authenticate**
   - Log in to the Saleor Dashboard first
   - The GraphQL Playground will use your session authentication
   - Ensure you have `MANAGE_PRODUCTS` permission

3. **Prepare the Mutation**
   - Copy the mutation from above into the left panel
   - Set up the variables in the "QUERY VARIABLES" section (bottom left)

4. **Upload the CSV File**
   - Since this is a file upload mutation, you need to use multipart request
   - In the HTTP Headers section, add:
     ```json
     {
       "Apollo-Require-Preflight": "true"
     }
     ```
   - Use the file upload functionality in your GraphQL client

5. **Execute the Mutation**
   - Click the "Execute" button
   - Review the results in the right panel

### Method 2: Using Postman or Similar Tools

For easier file upload handling, you can use tools like Postman:

1. **Set Up the Request**
   - Method: `POST`
   - URL: `http://localhost:8000/graphql/`
   - Headers:
     ```
     Content-Type: multipart/form-data
     Authorization: Bearer <your-token>
     ```

2. **Configure Multipart Form Data**
   - Add a field named `operations` with value:
     ```json
     {
       "query": "mutation ImportProducts($file: Upload!) { importProducts(input: { file: $file }) { result { success importedCount skippedCount errorCount errors { row slug error } } exportErrors { field message code } } }",
       "variables": { "file": null }
     }
     ```

   - Add a field named `map` with value:
     ```json
     { "0": ["variables.file"] }
     ```

   - Add a file field named `0` and select your CSV file

3. **Send the Request**

### Method 3: Custom Dashboard Extension

You can create a custom page in the Saleor Dashboard:

**Example React Component:**

```tsx
import React, { useState } from 'react';
import { useMutation } from '@apollo/client';
import { gql } from '@apollo/client';

const IMPORT_PRODUCTS_MUTATION = gql`
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
`;

export const ProductImportPage = () => {
  const [file, setFile] = useState(null);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState(null);

  const [importProducts] = useMutation(IMPORT_PRODUCTS_MUTATION);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleImport = async () => {
    if (!file) {
      alert('Please select a CSV file');
      return;
    }

    setImporting(true);
    try {
      const { data } = await importProducts({
        variables: { file }
      });
      setResult(data.importProducts.result);
    } catch (error) {
      console.error('Import failed:', error);
      alert('Import failed: ' + error.message);
    } finally {
      setImporting(false);
    }
  };

  return (
    <div>
      <h1>Import Products from CSV</h1>

      <div>
        <input
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          disabled={importing}
        />
        <button onClick={handleImport} disabled={!file || importing}>
          {importing ? 'Importing...' : 'Import Products'}
        </button>
      </div>

      {result && (
        <div>
          <h2>Import Results</h2>
          <p>Success: {result.success ? 'Yes' : 'No'}</p>
          <p>Imported: {result.importedCount}</p>
          <p>Skipped: {result.skippedCount}</p>
          <p>Errors: {result.errorCount}</p>

          {result.errors.length > 0 && (
            <div>
              <h3>Error Details</h3>
              <ul>
                {result.errors.map((error, index) => (
                  <li key={index}>
                    Row {error.row} - {error.slug}: {error.error}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
```

## CSV File Requirements

See `CSV_PRODUCT_IMPORT_SCHEMA.md` for detailed CSV file format specifications.

### Quick Reference

**Required Fields:**
- `slug` - Unique product identifier (will be used as SKU)
- `name` - Product name
- `price` - Product price (in USD)

**Common Optional Fields:**
- `description` - Product description
- `cost_price` - Cost/wholesale price
- `weight` - Product weight in kg
- `stock_quantity` - Initial stock quantity
- `brand` - Brand name
- `is_published` - Whether product should be visible
- `category_slug` - Category identifier
- `product_type_slug` - Product type identifier

## Testing the Import

### 1. Prepare Test Data

Use the sample CSV file:
```bash
/home/lei/workspace/88clipon/data/sample_products_import.csv
```

### 2. Verify Prerequisites

Before importing, ensure:
- You have `MANAGE_PRODUCTS` permission
- The default channel exists and is active
- The default category and product type exist (auto-created if not)
- The default warehouse exists (auto-created if not)

### 3. Execute Import

Use one of the methods described above to upload the CSV file.

### 4. Verify Results

Check the dashboard to verify:
- Products appear in the product list
- Prices are correct in all channels
- Stock levels are set correctly
- Product information is complete

## Common Issues and Solutions

### Issue: "File must be a CSV file"
**Solution:** Ensure your file has a `.csv` extension and is properly formatted.

### Issue: "CSV file must be UTF-8 encoded"
**Solution:** Save your CSV file with UTF-8 encoding. In Excel, use "Save As" and select "CSV UTF-8" format.

### Issue: "Missing required field: slug"
**Solution:** Ensure every row has a value in the `slug` column.

### Issue: Products are skipped
**Reason:** Products with the same slug already exist in the database.
**Solution:** Use unique slugs or delete existing products before re-importing.

### Issue: "Invalid price value"
**Solution:** Ensure prices are numeric values without currency symbols (e.g., `29.99` not `$29.99`).

### Issue: Products not visible on storefront
**Solution:** Check that:
- `is_published` is set to `true` in the CSV
- Products are assigned to active channels
- Products have valid pricing in all channels

## Performance Considerations

- **Small Imports (< 100 products):** Import completes instantly
- **Medium Imports (100-1000 products):** May take 10-60 seconds
- **Large Imports (> 1000 products):** Consider breaking into smaller batches

For very large imports, consider using the command-line import tool instead:
```bash
python manage.py import_products_csv --csv-file products.csv --images-dir images/
```

## Security

- Only users with `MANAGE_PRODUCTS` permission can import products
- File size is limited to 10MB
- Only CSV files are accepted
- Input is validated and sanitized

## Next Steps

After importing products, you may want to:
1. Add product images (via separate mutation or management command)
2. Assign products to collections
3. Set up product variants (if needed)
4. Configure shipping weights and dimensions
5. Set up product attributes
6. Review and adjust SEO metadata

## Support

For issues or questions:
1. Check the CSV schema documentation: `CSV_PRODUCT_IMPORT_SCHEMA.md`
2. Review error messages in the import result
3. Check Django logs for detailed error information
4. Verify CSV file format matches the schema

## Example Files

- **CSV Schema Documentation:** `/home/lei/workspace/88clipon/saleor/CSV_PRODUCT_IMPORT_SCHEMA.md`
- **Sample CSV File:** `/home/lei/workspace/88clipon/data/sample_products_import.csv`
- **Import Utility:** `/home/lei/workspace/88clipon/saleor/saleor/csv/utils/product_import.py`
- **GraphQL Mutation:** `/home/lei/workspace/88clipon/saleor/saleor/graphql/csv/mutations/import_products.py`

