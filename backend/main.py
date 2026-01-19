from scraper.WebScraper import WebScraper
from scraper.AllRecipesWebCrawler import AllRecipesCrawler
from scraper.RecipeTransformer import RecipeTransformer
from scraper.utils import load_seen_urls, save_seen_urls
from .database import get_chromadb_client
from backend.search import HybridRecipeSearch


def run_recipe_pipeline(seed_url, max_recipes=5, debug=False):
    # init tools
    crawler = AllRecipesCrawler(delay=0.8)
    scraper = WebScraper()
    client = get_chromadb_client()
    
    # Load previously seen recipes
    seen_recipes = load_seen_urls()
    print(f"Loaded {len(seen_recipes)} seen recipes")

    # Create fresh collection
    collection = client.get_or_create_collection(name="recipes")

    # Determine if seed URL is a recipe page (leaf node)
    is_recipe_page = '/recipe/' in seed_url.lower() or '-recipe-' in seed_url.lower()

    # Set fallback URL to a category page if starting from a recipe page
    fallback_url = None
    if is_recipe_page:
        fallback_url = "https://www.allrecipes.com/recipes/"
        print(
            f"📌 Starting from recipe page. Fallback URL set to: {fallback_url}")

    # Crawl pages (includes both recipes and category pages)
    crawl_results = crawler.crawl(seed_url, max_pages=max_recipes)

    # Filter to only actual recipe pages (not category pages)
    recipe_urls = {url: info for url, info in crawl_results.items()
                   if '/recipe/' in url.lower() or '-recipe-' in url.lower()}

    print(
        f"\n🎯 Found {len(recipe_urls)} recipe pages out of {len(crawl_results)} crawled pages")

    # Filter out already-seen recipes
    new_recipe_urls = {url: info for url, info in recipe_urls.items()
                       if info['title'] not in seen_recipes}
    
    if len(recipe_urls) - len(new_recipe_urls) > 0:
        print(f"⏭️  Skipped {len(recipe_urls) - len(new_recipe_urls)} already-seen recipes")
    print(f"{len(new_recipe_urls)} new recipes to scrape")

    # Limit to max_recipes
    new_recipe_urls = dict(list(new_recipe_urls.items())[:max_recipes])

    for url, info in new_recipe_urls.items():
        print(f"📖 Scraping recipe: {info['title']}")

        # Get the BeautifulSoup object for the specific recipe
        soup = scraper.get_data(url)

        # Extract the structured recipe data (the list of dicts)
        try:
            raw_recipe_data = scraper.extract_data(soup)

            # Transform the data for ChromaDB
            transformer = RecipeTransformer(raw_recipe_data)
            chroma_data = transformer.transform_for_chroma()

            # 4. Step 4: Load into ChromaDB
            collection.upsert(
                documents=chroma_data["documents"],
                metadatas=chroma_data["metadatas"],
                ids=chroma_data["ids"]
            )
            print(
                f"✅ Indexed {len(chroma_data['ids'])} chunks for {info['title']}")
            
            # Mark recipe as seen
            seen_recipes.add(info['title'])

        except Exception as e:
            print(
                f"⚠️  Skipping {url} - possibly not a recipe page. Error: {e}")

    # Save updated seen_recipes.json
    save_seen_urls(seen_recipes)
    
    print("\n✨ Ingestion Complete! Your RAG database is ready.")

    searcher = HybridRecipeSearch()

    # Test search
    query = "ayam bakar"
    results = searcher.hybrid_search(query, top_k=3)

    # Display results
    for i, doc in enumerate(results['documents'], 1):
        metadata = results['metadatas'][i-1]
        score = results['scores'][i-1]
        recipe = metadata.get('recipe', 'Unknown')
        chunk_type = metadata.get('type', 'unknown')

        print(f"\n  {i}. [{chunk_type}] {recipe}")
        print(f"     Score: {score:.4f}")
        print(f"     Preview: {doc[:80]}...")

    print("queried:")
    print(results)

    print(searcher.search_and_generate(
        query="",
    ))


if __name__ == "__main__":
    START_URL = "https://www.allrecipes.com/recipe/162845/chinese-tomato-and-egg/"

    # Enable debug mode to see link discovery details
    run_recipe_pipeline(START_URL, max_recipes=1)
