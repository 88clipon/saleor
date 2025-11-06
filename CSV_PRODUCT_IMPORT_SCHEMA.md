# Product CSV Import Schema

This document describes the CSV file format required for importing products into the Saleor e-commerce platform.

## CSV File Structure

The CSV file should use commas (`,`) as delimiters and UTF-8 encoding. The first row must contain the column headers.

## Required Fields

These fields **must** be present in every row:

| Field Name | Description | Example | Notes |
|------------|-------------|---------|-------|
| `slug` | Unique product identifier used as SKU | `ray-ban-rb5121-47x22` | Must be unique across all products. Will be used as both product slug and variant SKU. Lowercase, alphanumeric with hyphens. |
| `name` | Product display name | `Ray-Ban RB5121 47x22 Clip-On Sunglasses` | Maximum 250 characters |
| `price` | Product selling price | `29.99` | Numeric value in USD. No currency symbols. |
| `brand` | Brand name | `Ray-Ban` | Brand of the eyeglasses frame (e.g. Ray-Ban, Oakley, Prada) |
| `model` | Model number | `RB5154` | Model number printed on the frame |
| `size` | Frame size | `49x21` | Frame size (e.g. 49x21, 52x18) |

## Optional Fields

These fields are optional but recommended:

| Field Name | Description | Example | Default | Notes |
|------------|-------------|---------|---------|-------|
| `description` | Product description (plain text or HTML) | `Premium clip-on sunglasses...` or `<p>HTML content</p>` | Empty string | Supports both plain text and HTML. HTML will be automatically converted to EditorJS format for rich text display in dashboard |
| `cost_price` | Cost/wholesale price | `15.50` | `0.00` | Numeric value in USD |
| `weight` | Product weight | `0.05` | `0.0` | Weight in kg |
| `stock_quantity` | Initial stock quantity | `100` | `100` | Integer value |
| `is_published` | Whether product is visible | `true` or `false` | `true` | Boolean value |
| `available_for_purchase` | Whether product is available for purchase | `true` or `false` | `true` | Boolean value. When true, sets product as available for purchase immediately |
| `track_inventory` | Enable inventory tracking | `true` or `false` | `false` | Boolean value |

## Additional Optional Fields

| Field Name | Description | Example | Default | Notes |
|------------|-------------|---------|---------|-------|
| `seo_title` | SEO page title | `Buy Ray-Ban Clip-On Sunglasses` | Uses product name | Maximum 70 characters |
| `seo_description` | SEO meta description | `Premium clip-on sunglasses...` | Empty | Maximum 300 characters |
| `external_reference` | External system reference ID | `EXT-12345` | Empty | For integration with external systems |

## CSV Example

```csv
slug,name,price,brand,model,size,description,cost_price,weight,stock_quantity,is_published,available_for_purchase,track_inventory
ray-ban-rb5121-47x22,Ray-Ban RB5121 47x22 Clip-On Sunglasses,29.99,Ray-Ban,RB5121,47x22,Premium clip-on sunglasses for Ray-Ban RB5121 frames,15.50,0.05,100,true,true,false
oakley-ox8156-56x18,Oakley OX8156 56x18 Clip-On Sunglasses,34.99,Oakley,OX8156,56x18,Sport clip-on sunglasses for Oakley frames,18.00,0.06,75,true,true,false
generic-52x20-round,Generic 52x20 Round Clip-On,19.99,Generic,ROUND-52,52x20,Affordable clip-on sunglasses for round frames,8.00,0.04,200,true,true,false
```

## HTML Descriptions

The `description` field supports both **plain text** and **HTML formatting**. The system automatically detects HTML content and converts it to Saleor's EditorJS format.

### Supported HTML Tags

- **Headers**: `<h1>`, `<h2>`, `<h3>`, `<h4>`, `<h5>`, `<h6>`
- **Lists**: `<ul>` (unordered), `<ol>` (ordered)
- **List Items**: `<li>`
- **Paragraphs**: `<p>`, `<div>`
- **Text Formatting**: `<strong>`, `<em>`, `<b>`, `<i>` (styling preserved as text)
- **Links**: `<a href="...">` (converted to plain text with URL)

### HTML Description Example

```csv
slug,name,price,description
example-product,Example Product,29.99,"<ol><li><strong>Feature 1:</strong> Description of feature 1</li><li><strong>Feature 2:</strong> Description of feature 2</li></ol>"
```

### CSV Escaping for HTML

When including HTML in CSV files:
1. **Wrap the entire description in quotes** if it contains commas
2. **Escape quotes** inside HTML by doubling them (`""`) if using quotes in HTML attributes
3. Keep HTML on a single line or use proper CSV multi-line format

**Example with quotes in HTML:**
```csv
slug,name,price,brand,model,size,description
product-1,Product Name,29.99,BrandName,MODEL123,52x18,"<p>Description with ""quoted"" text</p>"
```

### Plain Text Alternative

If you don't want to use HTML, you can use plain text and it will be automatically formatted:
```csv
slug,name,price,brand,model,size,description
product-2,Simple Product,19.99,BrandName,MODEL456,54x20,This is a simple plain text description.
```

## Important Notes

1. **Slug as SKU**: The `slug` field serves as both the product slug and the variant SKU. This ensures unique product identification.

2. **Uniqueness**: Each `slug` must be unique. If a product with the same slug already exists, it will be skipped during import.

3. **Channel Support**: Products will be automatically added to all active channels in the system. Prices will be converted based on channel currency (USD as base, PLN = USD * 4).

4. **Product Type**: All products are automatically assigned to the "Clip-On Sunglasses" product type with these settings:
   - `has_variants`: true (multiple lens color variants)
   - `is_shipping_required`: true
   - `is_digital`: false

5. **Category**: All products are automatically assigned to the "Clip-On Sunglasses" category.

6. **Warehouse**: Products will be added to the default warehouse. Stock quantity will be set according to the `stock_quantity` field.

7. **Pricing**: Base prices should be in USD. The system will automatically convert prices for other channels (e.g., PLN).

8. **Boolean Values**: Use `true`, `false`, `1`, `0`, `yes`, `no` (case-insensitive) for boolean fields.

9. **Empty Values**: Optional fields can be left empty. Use empty strings or omit the value between commas.

## Import Process

When a CSV file is imported:

1. **Validation**: Each row is validated for required fields and data types
2. **Duplicate Check**: Products with existing slugs are skipped
3. **Product Creation**: Product record is created with basic information
4. **Variant Creation**: A single variant is created with the slug as SKU
5. **Channel Listing**: Product is added to all active channels with appropriate pricing
6. **Stock Assignment**: Initial stock is set in the default warehouse
7. **Attributes**: Brand attribute is assigned if provided

## Error Handling

- Invalid rows will be skipped and logged
- The import process will continue even if some rows fail
- A summary report will be provided showing:
  - Number of products successfully imported
  - Number of products skipped (duplicates)
  - Number of errors with details

## Recommendations

1. **Test First**: Always test with a small batch (5-10 products) using the dry-run option
2. **Backup**: Backup your database before large imports
3. **Validate Data**: Ensure all slugs are unique and follow the naming convention
4. **Price Format**: Use decimal format with dot separator (e.g., `29.99`, not `29,99`)
5. **Encoding**: Save CSV files in UTF-8 encoding to support international characters
6. **Line Endings**: Use standard line endings (LF or CRLF)

## Multi-Channel Pricing

If you have multiple channels with different currencies, the base price (in USD) will be converted:
- USD channel: Uses the specified price
- PLN channel: Price × 4
- Other channels: Uses the specified price (you may want to customize conversion rates)

## Future Extensions

The schema may be extended in the future to support:
- Multiple variants per product
- Product collections
- Product images (via URLs or file paths)
- Custom attributes
- SEO metadata
- Tax classes

