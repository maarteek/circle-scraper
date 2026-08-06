#!/usr/bin/env python3
"""
Circle Platform Community Crawler using Playwright
Saves authenticated pages as static HTML files with folder structure.
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


class CircleCrawler:
    def __init__(self, base_url, output_dir, max_pages):
        self.base_url = base_url.rstrip("/")
        self.output_dir = Path(output_dir)
        self.max_pages = max_pages
        self.visited = set()
        self.to_visit = []
        self.page_count = 0

    def sanitize_filename(self, url):
        """Convert URL to a safe filesystem path."""
        path = url.replace(self.base_url, "")
        if not path or path == "/":
            path = "/index"
        # Remove query params for filename
        path = path.split("?")[0]
        # Ensure it ends with .html
        if not path.endswith(".html"):
            if path.endswith("/"):
                path += "index.html"
            else:
                path += ".html"
        return path.lstrip("/")

    def extract_links(self, html):
        """Extract all same-domain links from HTML."""
        soup = BeautifulSoup(html, "html.parser")
        links = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]

            # Convert relative URLs to absolute
            if href.startswith("/"):
                href = self.base_url + href

            # Only include links on the target domain
            if href.startswith(self.base_url):
                # Remove fragments and normalize
                href = href.split("#")[0]
                links.add(href)

        return links

    async def save_page(self, url, html):
        """Save page HTML to file."""
        filepath = self.output_dir / self.sanitize_filename(url)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"[{self.page_count}/{self.max_pages}] Saved: {url}")

    async def crawl(self, cookies):
        """Main crawl function."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--disable-site-isolation-trials",
                    "--no-sandbox",
                ],
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                timezone_id="America/New_York",
                extra_http_headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                },
            )

            # Add cookies from file
            await context.add_cookies(cookies)

            page = await context.new_page()

            # Hide webdriver property and other automation signals
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });

                // Overwrite the navigator.plugins property to use a custom getter
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });

                // Overwrite the navigator.languages property
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });

                // Overwrite chrome runtime
                window.chrome = { runtime: {} };
            """)

            # Start with the base URL
            self.to_visit.append(self.base_url)

            while self.to_visit and self.page_count < self.max_pages:
                url = self.to_visit.pop(0)

                if url in self.visited:
                    continue

                self.visited.add(url)
                self.page_count += 1

                try:
                    print(f"\nVisiting: {url}")
                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)

                    # Wait for dynamic content to render
                    await page.wait_for_timeout(3000)

                    # Get HTML
                    html = await page.content()

                    # Save page
                    await self.save_page(url, html)

                    # Extract and queue new links
                    new_links = self.extract_links(html)
                    for link in new_links:
                        if link not in self.visited and link not in self.to_visit:
                            self.to_visit.append(link)

                    print(f"  Found {len(new_links)} links, {len(self.to_visit)} queued")

                except Exception as e:
                    print(f"  ERROR: {e}")
                    continue

            await browser.close()

        print(f"\nCrawl complete. Saved {self.page_count} pages to {self.output_dir}")


def load_cookies(cookie_path):
    """Load cookies from a JSON file."""
    path = Path(cookie_path)
    if not path.exists():
        print(f"Error: cookie file not found at {path}")
        print("Create a cookies.json file. See cookies.example.json for the expected format.")
        sys.exit(1)

    with open(path, "r") as f:
        cookies = json.load(f)

    if not isinstance(cookies, list):
        print("Error: cookies.json must contain a JSON array of cookie objects.")
        sys.exit(1)

    return cookies


def main():
    parser = argparse.ArgumentParser(
        description="Crawl a Circle platform community and save pages as static HTML."
    )
    parser.add_argument(
        "base_url",
        help="Base URL of the Circle community (e.g. https://community.example.com)",
    )
    parser.add_argument(
        "--output",
        default="./output",
        help="Output directory for saved HTML files (default: ./output)",
    )
    parser.add_argument(
        "--cookies",
        default="./cookies.json",
        help="Path to cookies JSON file (default: ./cookies.json)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=500,
        help="Maximum number of pages to crawl (default: 500)",
    )

    args = parser.parse_args()

    # Strip trailing slash from base URL
    base_url = args.base_url.rstrip("/")

    # Load cookies
    cookies = load_cookies(args.cookies)

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run crawler
    crawler = CircleCrawler(base_url, output_dir, args.max_pages)
    asyncio.run(crawler.crawl(cookies))


if __name__ == "__main__":
    main()
