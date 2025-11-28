# How to Maintain Category Configuration

The scraper uses two files:
- `bershka_categories.txt` - lists category IDs to process
- `config.py` - contains the mapping from category IDs to JSON URLs

## Step 1: The Category IDs File

`bershka_categories.txt` contains category IDs (one per line):

```
# Bershka categories to process
# Comment out categories you don't want to process

# Men's All
1010834564

# Women's categories
1010193212
1010240019
...
```

## Step 2: Configure URLs in config.py

Update `CATEGORY_URLS` in `config.py` with your actual JSON URLs:

```python
CATEGORY_URLS = {
    '1010834564': 'https://www.bershka.com/your/real/mens/json/url.json',
    '1010193212': 'https://www.bershka.com/your/real/womens/jackets/json/url.json',
    # ... add all your URLs here
}
```

## Step 3: Run the Scraper

```bash
python bershka_scraper.py
```

The scraper will automatically:
1. Read category IDs from `bershka_categories.txt`
2. Look up URLs from `CATEGORY_URLS` in config.py
3. Fetch JSON data directly from each URL
4. Process all products from the JSON
5. Generate embeddings and save to database

## Advantages of This Approach

- **Clean separation**: IDs in txt file, URLs in config
- **Always up-to-date**: URLs stay current without manual updates
- **Simple**: Just fetch JSON and process - no complex API logic
- **Easy maintenance**: Add/remove category IDs or update URLs independently

## File Format Details

- Lines starting with `#` are comments and ignored
- Empty lines are ignored
- One category ID per line
- Category IDs must exist in `CATEGORY_URLS` mapping in config.py

