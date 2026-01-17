from scraper.WebCrawler import WebCrawler
from bs4 import BeautifulSoup


class AllRecipesCrawler(WebCrawler):
    """
    A specialised crawler for AllRecipes.com that only follows 
    recipe links and ignores 'Member Profile' or 'Search' pages.
    """

    def is_valid_link(self, href: str, base_url: str) -> bool:
        """
        OVERRIDE: Follow both recipe pages AND category pages.
        - Recipe pages: contain '/recipe/' (these are what we want to scrape)
        - Category pages: contain '/recipes/' (these lead to recipe pages)
        
        This allows the crawler to navigate through categories to find recipes.
        """
        # First, run the parent's basic checks (anchors, mailto, etc.)
        if not super().is_valid_link(href, base_url):
            return False

        # Accept both recipe pages and category/listing pages
        href_lower = href.lower()
        
        # Follow recipe pages (what we want to scrape)
        if '/recipe/' in href_lower or '-recipe-' in href_lower:
            return True
        
        # Follow category pages (these contain links to recipes)
        if '/recipes/' in href_lower:
            return True
        
        # Also follow the homepage (has links to categories)
        if href_lower.endswith('allrecipes.com') or href_lower.endswith('allrecipes.com/'):
            return True
        
        return False

    def get_title(self, url: str, soup: BeautifulSoup) -> str:
        """
        OVERRIDE: AllRecipes often has 'Recipe' at the end of the <title>.
        Let's clean it up specifically for our database.
        """
        title = super().get_title(url, soup)
        return title.replace(" Recipe", "").strip()
