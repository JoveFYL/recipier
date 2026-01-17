# Recipe Crawler - Seen URLs Tracking

## Overview

Your recipe crawler now automatically tracks all visited URLs in `data/seen_recipes.json`. Every new run will:
- Start from the same seed URL
- Skip URLs that have already been processed
- Only scrape new recipes
- Persist the updated list of seen URLs

## How It Works

### 1. **Loading Seen URLs**
When `run_recipe_pipeline()` starts, it loads all previously seen URLs:
```python
seen_urls = load_seen()  # Loads from data/seen_recipes.json
```

### 2. **Crawler Integration**
The crawler receives the seen URLs and skips them during crawling:
```python
crawl_results = crawler.crawl(seed_url, max_pages=max_recipes, skip_urls=seen_urls)
```

### 3. **Processing & Tracking**
As each new recipe is processed:
- Successfully scraped recipes are added to `seen_urls`
- Failed recipes are also marked as seen (to avoid retrying)
- URLs are saved to disk after all processing completes

### 4. **Persistence**
All seen URLs are saved to `data/seen_recipes.json`:
```python
save_seen(seen_urls)  # Saves the complete set of URLs
```

## Usage Examples

### Running the Crawler
```bash
cd /Users/Jove/recipier
python backend/main.py
```

### Check Seen URLs Stats
```bash
python scraper/utils.py
```

This will show:
- Total number of seen URLs
- First 5 URLs
- File location

### Clear Seen URLs (Start Fresh)
```python
from scraper.utils import clear_seen_urls
clear_seen_urls()
```

## File Structure

```
recipier/
├── data/
│   └── seen_recipes.json          # Persisted seen URLs
├── backend/
│   └── main.py                    # Main pipeline with tracking
├── scraper/
│   ├── WebCrawler.py              # Base crawler with skip_urls support
│   ├── AllRecipesWebCrawler.py   # Site-specific crawler
│   └── utils.py                   # Utility functions
```

## Key Functions

### In `backend/main.py`:
- `load_seen()` - Load seen URLs from JSON file
- `save_seen(seen_set)` - Save seen URLs to JSON file
- `run_recipe_pipeline()` - Main pipeline with tracking

### In `scraper/utils.py`:
- `load_seen_urls()` - Load seen URLs
- `save_seen_urls(seen_set)` - Save seen URLs
- `clear_seen_urls()` - Clear all seen URLs
- `print_seen_stats()` - Display statistics

### In `scraper/WebCrawler.py`:
- `crawl(seed_url, max_pages, skip_urls)` - Crawl with optional skip set

## Example Output

```
📚 Starting crawl with 0 previously seen URLs
Crawling: 100%|████████████| 5/5 [00:15<00:00, 3.00s/it]

Crawled 5 pages! (Skipped 0 already-seen URLs)
📖 Scraping recipe: Chicken Parmesan
✅ Indexed 12 chunks for Chicken Parmesan
📖 Scraping recipe: Beef Stew
✅ Indexed 15 chunks for Beef Stew
...
💾 Saved 5 total seen URLs (5 newly processed)
```

On subsequent runs:
```
📚 Starting crawl with 5 previously seen URLs
Crawling: 100%|████████████| 3/3 [00:10<00:00, 3.33s/it]

Crawled 3 pages! (Skipped 5 already-seen URLs)
⏭️  Skipping already seen: Chicken Parmesan
⏭️  Skipping already seen: Beef Stew
📖 Scraping recipe: Fish Tacos
✅ Indexed 10 chunks for Fish Tacos
...
💾 Saved 8 total seen URLs (3 newly processed)
```

## Benefits

1. **Efficiency**: Don't re-scrape recipes you already have
2. **Incremental Updates**: Add new recipes without duplicating work
3. **Resume Capability**: Can stop and restart without losing progress
4. **Error Handling**: Failed URLs are tracked to avoid infinite retries
5. **Persistence**: Survives script restarts and system reboots

## Notes

- The file is automatically created if it doesn't exist
- Empty or corrupted JSON files are handled gracefully
- URLs are saved in sorted order for readability
- Both successful and failed URLs are tracked to avoid retries
