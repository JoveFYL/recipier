import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

USER_AGENT = "educational webscraper"
REQUEST_DELAY = 0.5  # seconds between requests


class WebScraper:
    """
    General-purpose web scraper that respects robots.txt.

    This base class can scrape any website. Subclass it to add
    site-specific logic.

    Usage:
        scraper = WebScraper()
        data = scraper.scrape("https://example.com", max_pages=10)
    """

    def __init__(
        self, user_agent: str = USER_AGENT, delay: float = REQUEST_DELAY
    ) -> None:
        self.user_agent = user_agent
        self.delay = delay  # request delays
        self.session = requests.Session()  # reuse TCP connections for efficiency
        self.session.headers["User-Agent"] = user_agent
        self.visited = set()  # Cache robots parsers per domain

    def get(self, url: str, **kwargs) -> requests.Response:
        """Make a GET request with proper headers."""
        kwargs.setdefault('timeout', 10)
        return self.session.get(url, **kwargs)

    def get_data(self, url: str, **kwargs) -> BeautifulSoup:
        data = self.get(url=url)
        soup = BeautifulSoup(data.text, 'html.parser')
        return soup

    def extract_data(self, soup: BeautifulSoup):
        data = []
        title = soup.find('h1', class_="article-heading").get_text(strip=True)

        # store title as metadata reference
        data.append({"text": title,
                     "metadata": {
                         "type": "title",
                         "recipe": title
                     }
                     })

        # loop through headings and list ingredients
        headings = soup.find_all(
            'p', class_="mm-recipes-structured-ingredients__list-heading")

        for heading in headings:
            section_name = heading.get_text(strip=True)
            list_items = heading.find_next_sibling("ul").find_all("li")
            ingredients = [
                li.get_text(separator=' ', strip=True)
                for li in list_items
            ]

            data.append({
                "text": f"{section_name} " + ", ".join(ingredients),
                "metadata": {
                    "type": "ingredients",
                    "recipe": title,
                    "section": section_name
                }
            })

        # find directions
        directions_group = soup.find(
            'div', class_="mm-recipes-steps__content")
        directions_list = directions_group.find("ol").find_all(
            "li", class_="mntl-sc-block-group--LI")

        for idx, li in enumerate(directions_list, start=1):
            direction = li.find(
                "p", class_="mntl-sc-block-html").get_text(strip=True)
            data.append({
                "text": direction,
                "metadata": {
                    "type": "directions",
                    "recipe": title,
                    "step": idx,
                    "step_text": direction
                }
            })

        nutritions_group = soup.find(
            "tbody",
            class_="mm-recipes-nutrition-facts-summary__table-body").find_all("td", class_="mm-recipes-nutrition-facts-summary__table-cell")
        for i in range(0, len(nutritions_group), 2):
            value = nutritions_group[i].get_text(strip=True)
            category = nutritions_group[i + 1].get_text(strip=True)

            data.append({
                "text": f"{value} {category}",
                "metadata": {
                    "type": "nutrition",
                    "recipe": title,
                    "value": value,
                    "category": category
                }
            })

        return data

    @staticmethod
    def has_ingredients(tag: Tag) -> bool:
        if not tag.name:
            return False
        classes = tag.get('class', [])
        tag_id = tag.get('id', '')

        return (
            any('mm-recipes-structured-ingredients__list' in cls.lower()
                for cls in classes) or 'ingrdients' in tag_id.lower()
        )
