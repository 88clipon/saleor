# HTML Product Descriptions - Complete Guide

## Overview

The product CSV import system now supports **HTML-formatted descriptions**. The system automatically detects HTML content and converts it to Saleor's EditorJS rich text format, allowing you to create beautifully formatted product descriptions.

## Your Use Case - Template Description

You have a standard HTML template that you want to use for all your clip-on sunglasses. Here's how to include it in your CSV file.

### Your Template (Formatted)

```html
<ol>
<li><strong>Ultra-light weight.</strong> The average weight of our 88 ClipOn sunglasses is less than 0.30 ounce (oz) or 8.0 gram (g).</li>
<li><strong>FDA approved PC polarized lenses.</strong> Our lenses are meticulously crafted and edge polished by hands.</li>
<li><strong>Made in USA & Ship Worldwide.</strong> All orders are hand made on the next day or two, and delivered within 5 days on the continental US with a <strong>FREE shipping</strong>. Expedited shipping is available.</li>
<li><strong>No ugly top bar and extruding prongs to scratch a frame or lenses.</strong> Our clip-on uses an alloy metal bridge with a patented hidden spring clamp to secure our clip-on on top of an eyeglasses frame and the 2 bridge legs against the 2 nose pads of the frame.</li>
<li><strong>Slide-free designs to secure our clip-on on your glasses.</strong> Our custom fit clip-on has cut notches on both lenses to fit around bumpy hinges usually seen on a metal or rimless frame so that our clip-on sits flat on top of a frame with almost no space in between our clip-on and your Rx frame.</li>
<li><strong>Stylish carrying case to protect your investment.</strong> We provide a shatter-proof case to protect your clip-on inside a tight pocket.</li>
<li><strong>Perfectly match and custom fit for any frame in plastic, metal, rimless, or semi-rimless.</strong> Our clip-on sunglasses will make your prescription eyeglasses appear like another pair of prescription sunglasses of the same model and size.</li>
<li><strong>No extra hassle to mail your frame to us.</strong> If you do not find the size of your particular model, simply place an order for a different size of the same model, and tell us the size you need.</li>
<li><strong>Custom Make Program.</strong> If you do not find the model or brand of your glasses and would like us to make a custom clip-on, please click <a href="https://www.88clipon.com/88-custom-make-program/" target="_blank">Custom Make Program</a> for your needs.</li>
</ol>
```

## How to Include HTML in CSV

### Step 1: Prepare Your HTML (One Line)

Since CSV files work best with single-line values, convert your HTML template to a single line by removing all line breaks:

```html
<ol><li><strong>Ultra-light weight.</strong> The average weight of our 88 ClipOn sunglasses is less than 0.30 ounce (oz) or 8.0 gram (g).</li><li><strong>FDA approved PC polarized lenses.</strong> Our lenses are meticulously crafted and edge polished by hands.</li><li><strong>Made in USA & Ship Worldwide.</strong> All orders are hand made on the next day or two, and delivered within 5 days on the continental US with a <strong>FREE shipping</strong>. Expedited shipping is available.</li><li><strong>No ugly top bar and extruding prongs to scratch a frame or lenses.</strong> Our clip-on uses an alloy metal bridge with a patented hidden spring clamp to secure our clip-on on top of an eyeglasses frame and the 2 bridge legs against the 2 nose pads of the frame.</li><li><strong>Slide-free designs to secure our clip-on on your glasses.</strong> Our custom fit clip-on has cut notches on both lenses to fit around bumpy hinges usually seen on a metal or rimless frame so that our clip-on sits flat on top of a frame with almost no space in between our clip-on and your Rx frame.</li><li><strong>Stylish carrying case to protect your investment.</strong> We provide a shatter-proof case to protect your clip-on inside a tight pocket.</li><li><strong>Perfectly match and custom fit for any frame in plastic, metal, rimless, or semi-rimless.</strong> Our clip-on sunglasses will make your prescription eyeglasses appear like another pair of prescription sunglasses of the same model and size.</li><li><strong>No extra hassle to mail your frame to us.</strong> If you do not find the size of your particular model, simply place an order for a different size of the same model, and tell us the size you need.</li><li><strong>Custom Make Program.</strong> If you do not find the model or brand of your glasses and would like us to make a custom clip-on, please click <a href="https://www.88clipon.com/88-custom-make-program/" target="_blank">Custom Make Program</a> for your needs.</li></ol>
```

### Step 2: Wrap in Quotes

Since your HTML contains commas, you must wrap the entire description in double quotes:

```csv
slug,name,price,description
ray-ban-rb5121,"Ray-Ban RB5121 Clip-On",29.99,"<ol><li><strong>Ultra-light weight.</strong> The average weight...</li></ol>"
```

### Step 3: Handle Quotes in HTML

If your HTML contains double quotes (like in `href="..."`), you need to **double them** (replace `"` with `""`):

**Before:**
```html
<a href="https://example.com">Link</a>
```

**After (for CSV):**
```html
<a href=""https://example.com"">Link</a>
```

However, in your case, your HTML already has the quotes, so when you put it in the CSV with outer quotes, most spreadsheet programs will handle this automatically.

## Complete Example CSV

Here's a complete example using your template:

```csv
slug,name,price,description,cost_price,stock_quantity,brand,is_published
ray-ban-rb5121-47x22,Ray-Ban RB5121 47x22 Clip-On Sunglasses,29.99,"<ol><li><strong>Ultra-light weight.</strong> The average weight of our 88 ClipOn sunglasses is less than 0.30 ounce (oz) or 8.0 gram (g).</li><li><strong>FDA approved PC polarized lenses.</strong> Our lenses are meticulously crafted and edge polished by hands.</li><li><strong>Made in USA & Ship Worldwide.</strong> All orders are hand made on the next day or two, and delivered within 5 days on the continental US with a <strong>FREE shipping</strong>. Expedited shipping is available.</li></ol>",15.50,100,Ray-Ban,true
oakley-ox8156-56x18,Oakley OX8156 56x18 Clip-On Sunglasses,34.99,"<ol><li><strong>Ultra-light weight.</strong> The average weight of our 88 ClipOn sunglasses is less than 0.30 ounce (oz) or 8.0 gram (g).</li><li><strong>FDA approved PC polarized lenses.</strong> Our lenses are meticulously crafted and edge polished by hands.</li><li><strong>Made in USA & Ship Worldwide.</strong> All orders are hand made on the next day or two, and delivered within 5 days on the continental US with a <strong>FREE shipping</strong>. Expedited shipping is available.</li></ol>",18.00,75,Oakley,true
```

## Supported HTML Elements

### Lists (Your Main Use Case)

**Ordered Lists:**
```html
<ol>
  <li>First item</li>
  <li>Second item</li>
</ol>
```

**Unordered Lists:**
```html
<ul>
  <li>Bullet point 1</li>
  <li>Bullet point 2</li>
</ul>
```

### Text Formatting

- `<strong>Bold text</strong>` - Bold text
- `<em>Italic text</em>` - Italic text
- `<b>Bold</b>` - Alternative bold
- `<i>Italic</i>` - Alternative italic

### Headers

```html
<h1>Main Heading</h1>
<h2>Subheading</h2>
<h3>Section Title</h3>
```

### Paragraphs

```html
<p>This is a paragraph of text.</p>
```

### Links

```html
<a href="https://example.com">Click here</a>
```

## How It Works Behind the Scenes

1. **Detection**: System detects HTML by looking for `<` and `>` characters
2. **Parsing**: BeautifulSoup4 parses your HTML
3. **Conversion**: HTML is converted to EditorJS JSON format
4. **Storage**: EditorJS format is stored in the `description` field
5. **Plain Text**: HTML tags are stripped and stored in `description_plaintext` for search

**EditorJS Format (what gets stored):**
```json
{
  "blocks": [
    {
      "type": "list",
      "data": {
        "style": "ordered",
        "items": [
          "Ultra-light weight. The average weight...",
          "FDA approved PC polarized lenses...",
          "Made in USA & Ship Worldwide..."
        ]
      }
    }
  ],
  "time": 0,
  "version": "2.22.2"
}
```

## Creating Your CSV File

### Method 1: Using Excel or Google Sheets

1. Open Excel/Google Sheets
2. Create columns: `slug`, `name`, `price`, `description`, etc.
3. **Paste your HTML directly into the description cell**
4. Excel will automatically handle quotes
5. Save as CSV (UTF-8)

**Important:** When saving in Excel, choose **"CSV UTF-8 (Comma delimited)"** format.

### Method 2: Using a Text Editor

1. Open a text editor (VS Code, Sublime, Notepad++)
2. Create your CSV with the description wrapped in quotes
3. Save with UTF-8 encoding

### Method 3: Programmatic Generation

If you're generating CSVs with Python:

```python
import csv

products = [
    {
        'slug': 'ray-ban-rb5121',
        'name': 'Ray-Ban RB5121 Clip-On',
        'price': '29.99',
        'description': '<ol><li><strong>Feature 1</strong> Description</li></ol>',
        'cost_price': '15.50',
        'stock_quantity': '100',
        'brand': 'Ray-Ban',
        'is_published': 'true'
    }
]

with open('products.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=products[0].keys())
    writer.writeheader()
    writer.writerows(products)
```

## Sample File

A sample CSV file with HTML descriptions is available at:
```
/home/lei/workspace/88clipon/data/products_with_html_description.csv
```

## Tips for Success

### ✓ DO:
- Wrap HTML descriptions in double quotes
- Use UTF-8 encoding when saving CSV
- Keep HTML on a single line (or use proper CSV escaping)
- Test with a small batch first
- Use standard HTML tags (ol, ul, li, p, strong, etc.)

### ✗ DON'T:
- Don't include inline CSS styles (like `style="font-family: Verdana"`) - they will be stripped
- Don't use complex nested structures
- Don't forget to quote the description field
- Don't use non-standard HTML tags

## Simplifying Your Template

Your current template has inline styles that will be removed during conversion. Here's a **simplified version** that will work perfectly:

```html
<ol><li><strong>Ultra-light weight.</strong> The average weight of our 88 ClipOn sunglasses is less than 0.30 ounce (oz) or 8.0 gram (g).</li><li><strong>FDA approved PC polarized lenses.</strong> Our lenses are meticulously crafted and edge polished by hands.</li><li><strong>Made in USA & Ship Worldwide.</strong> All orders are hand made on the next day or two, and delivered within 5 days on the continental US with <strong>FREE shipping</strong>. Expedited shipping is available.</li><li><strong>No ugly top bar and extruding prongs to scratch a frame or lenses.</strong> Our clip-on uses an alloy metal bridge with a patented hidden spring clamp to secure our clip-on on top of an eyeglasses frame and the 2 bridge legs against the 2 nose pads of the frame.</li><li><strong>Slide-free designs to secure our clip-on on your glasses.</strong> Our custom fit clip-on has cut notches on both lenses to fit around bumpy hinges usually seen on a metal or rimless frame so that our clip-on sits flat on top of a frame with almost no space in between our clip-on and your Rx frame. For some models, we have 2 tiny tabs attached on each lens, making our clip-on grab onto the edge of an eyeglasses frame to further prevent sliding.</li><li><strong>Stylish carrying case to protect your investment.</strong> We provide a shatter-proof case to protect your clip-on inside a tight pocket. Other custom clip-on companies supply a plastic bag to hold a clip-on.</li><li><strong>Perfectly match and custom fit for any frame in plastic, metal, rimless, or semi-rimless.</strong> Our clip-on sunglasses will make your prescription eyeglasses appear like another pair of prescription sunglasses of the same model and size because we custom make it based on the exact shape, size, and curvature of your frame.</li><li><strong>No extra hassle to mail your frame to us.</strong> If you do not find the size of your particular model, simply place an order for a different size of the same model, and tell us the size you need inside the Confirm Brand Model & Size box at the product detail page or the Customer Comment Box during order check-out. We will custom make it for you without extra charge.</li><li><strong>Custom Make Program.</strong> If you do not find the model or brand of your glasses and would like us to make a custom clip-on please click <a href="https://www.88clipon.com/88-custom-make-program/">Custom Make Program</a> for your needs.</li></ol>
```

**Key changes:**
- Removed all `<span style="font-family: Verdana;">` tags
- Kept all `<strong>` tags for bold text
- Kept the ordered list structure `<ol>` and `<li>`
- Kept the link `<a href="...">`
- Removed `target="_blank"` (not needed in product descriptions)
- Removed non-breaking spaces (`&nbsp;`) - use regular spaces

## Testing Your CSV

Before importing all your products:

1. Create a test CSV with 2-3 products
2. Import using the test script:
   ```bash
   cd /home/lei/workspace/88clipon/saleor
   source .venv/bin/activate
   python test_product_import.py --csv-file /path/to/your/test.csv
   ```
3. Check the products in the Saleor Dashboard
4. Verify the description displays correctly
5. If all looks good, proceed with the full import!

## Troubleshooting

### Issue: Description appears as plain HTML text
**Cause:** CSV wasn't properly quoted or encoding is wrong
**Solution:** Ensure UTF-8 encoding and wrap description in quotes

### Issue: Some HTML tags don't appear
**Cause:** Tags not supported or parsing failed
**Solution:** Stick to supported tags (ol, ul, li, p, strong, em, h1-h6)

### Issue: Quotes causing errors
**Cause:** Quotes in HTML not properly escaped
**Solution:** Use `""` for quotes inside the CSV cell

## Summary

✅ **Yes, you can use HTML descriptions!**
✅ **Your template will work** - just remove the inline styles
✅ **Wrap in quotes** when putting in CSV
✅ **UTF-8 encoding** is required
✅ **Test first** with a small batch

Your ordered list with bold features will display beautifully in the Saleor Dashboard and on your storefront! 🎉

