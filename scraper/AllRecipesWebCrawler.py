from scraper.WebCrawler import WebCrawler
from bs4 import BeautifulSoup


class AllRecipesCrawler(WebCrawler):
    """
    A specialised crawler for AllRecipes.com that only follows 
    recipe links and ignores 'Member Profile' or 'Search' pages.
    """

    def is_valid_link(self, href: str, base_url: str) -> bool:
        """
        OVERRIDE: Only follow links that look like actual recipes.
        AllRecipes recipes usually contain '/recipe/' in the URL.
        """
        # First, run the parent's basic checks (anchors, mailto, etc.)
        if not super().is_valid_link(href, base_url):
            return False

        # Then, add our custom site-specific filter
        return "/recipe/" in href.lower() or "-recipe-" in href.lower()

    def get_title(self, url: str, soup: BeautifulSoup) -> str:
        """
        OVERRIDE: AllRecipes often has 'Recipe' at the end of the <title>.
        Let's clean it up specifically for our database.
        """
        title = super().get_title(url, soup)
        return title.replace(" Recipe", "").strip()
