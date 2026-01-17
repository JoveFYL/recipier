import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote
from urllib.robotparser import RobotFileParser
from collections import deque
import time
from tqdm import tqdm

# Configuration
USER_AGENT = "HybridSearchWorkshop/1.0 (Educational)"
REQUEST_DELAY = 0.5  # seconds between requests


class WebCrawler:
    """
    General-purpose web crawler that respects robots.txt.

    This base class can crawl any website. Subclass it to add 
    site-specific logic (like WikipediaCrawler below).

    Usage:
        crawler = WebCrawler()
        data = crawler.crawl("https://example.com", max_pages=10)
    """

    def __init__(self, user_agent: str = USER_AGENT, delay: float = REQUEST_DELAY) -> None:
        self.user_agent = user_agent
        self.delay = delay
        self.session = requests.Session()
        self.session.headers["User-Agent"] = user_agent
        self.robots_cache = {}  # Cache robots parsers per domain

    def get_domain(self, url: str) -> str:
        """Extract the domain from a URL."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def can_fetch(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt."""
        domain = self.get_domain(url)
        if domain not in self.robots_cache:
            try:
                rp = RobotFileParser()
                robots_url = f"{domain}/robots.txt"
                robots_txt = self.session.get(robots_url, timeout=5).text
                rp.parse(robots_txt.splitlines())
                self.robots_cache[domain] = rp
            except:
                # If we can't fetch robots.txt, assume allowed
                return True
        return self.robots_cache[domain].can_fetch("*", url)

    def get(self, url: str, **kwargs) -> requests.Response:
        """Make a GET request with proper headers."""
        kwargs.setdefault('timeout', 10)
        return self.session.get(url, **kwargs)

    def get_title(self, url: str, soup: BeautifulSoup) -> str:
        """Extract page title. Override in subclass for custom logic."""
        title_tag = soup.find('title')
        return title_tag.get_text(strip=True) if title_tag else url

    def extract_text(self, soup: BeautifulSoup) -> str:
        """Extract main text content. Override in subclass for custom logic."""
        # Remove script and style elements
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()
        return soup.get_text(separator=' ', strip=True)[:5000]

    def is_valid_link(self, href: str, base_url: str) -> bool:
        """Check if a link should be followed. Override in subclass."""
        if not href:
            return False
        # Skip anchors, javascript, mailto, etc.
        if href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
            return False
        return True

    def extract_links(self, soup: BeautifulSoup, base_url: str) -> list[str]:
        """Extract all valid links from the page."""
        links = []
        data_tracking_target_url_list = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if self.is_valid_link(href, base_url):
                # Convert relative URLs to absolute
                full_url = urljoin(base_url, href)
                # Only follow links on the same domain
                if self.get_domain(full_url) == self.get_domain(base_url):
                    links.append(full_url)
        return list(dict.fromkeys(links))  # Remove duplicates, preserve order

    def crawl_page(self, url: str) -> dict | None:
        """Crawl a single page and extract title, text, and links."""
        if not self.can_fetch(url):
            print(f"[robots.txt blocked] {url}")
            return None

        try:
            response = self.get(url)
            if response.status_code != 200:
                print(f"[HTTP {response.status_code}] {url}")
                return None

            soup = BeautifulSoup(response.text, 'lxml')

            return {
                'url': url,
                'title': self.get_title(url, soup),
                'text': self.extract_text(soup),
                'links': self.extract_links(soup, url)
            }

        except Exception as e:
            print(f"[Error] {url}: {e}")
            return None

    def crawl(self, seed_url: str, max_pages: int = 20) -> dict[str, dict]:
        """
        Crawl starting from seed_url using Breadth-First Search (BFS).

        Args:
            seed_url: Starting URL
            max_pages: Maximum number of pages to crawl

        Returns:
            Dictionary mapping URL -> page data
        """
        crawled = {}
        visited = set()
        queue = deque([seed_url])

        pbar = tqdm(total=max_pages, desc="Crawling")

        while queue and len(crawled) < max_pages:
            url = queue.popleft()
            if url in visited:
                continue

            visited.add(url)
            result = self.crawl_page(url)

            if result:
                crawled[url] = result
                pbar.update(1)
                pbar.set_description(f"Crawling: {result['title'][:25]}...")

                # Add new links to the queue (BFS)
                for link in result['links']:
                    if link not in visited:
                        queue.append(link)

            time.sleep(self.delay)

        pbar.close()
        print(f"\nCrawled {len(crawled)} pages!")
        return crawled

    def show_robots_txt(self, url: str, max_rules: int = 10) -> None:
        """Fetch and display important rules from a site's robots.txt."""
        try:
            response = self.get(f"{self.get_domain(url)}/robots.txt")

            print(f"\n{'='*50}")
            print(f"📄 {self.get_domain(url)}/robots.txt")
            print('='*50)

            # Filter to show only important lines
            important_prefixes = (
                'user-agent:', 'disallow:', 'allow:', 'sitemap:')
            rules_shown = 0

            for line in response.text.split('\n'):
                line_lower = line.lower().strip()
                if any(line_lower.startswith(prefix) for prefix in important_prefixes):
                    print(line.strip())
                    rules_shown += 1
                    if rules_shown >= max_rules:
                        print("...")
                        break
        except Exception as e:
            print(f"Error: {e}")


print("WebCrawler base class ready!")
