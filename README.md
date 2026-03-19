# circle-scraper

A command-line tool that crawls Circle platform communities and saves authenticated pages as static HTML files. It preserves the site's URL structure as a local folder hierarchy.

Circle (circle.so) is a community platform used by course creators, membership sites, and online communities. This tool lets you create a local archive of community content you have access to.

## Prerequisites

- Python 3.10 or later
- A Circle community account with an active session in Chrome

## Installation

```bash
git clone https://github.com/maarteek/circle-scraper.git
cd circle-scraper
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Cookie Setup

The crawler needs your authenticated session cookies to access the community. You export these from your browser after logging in.

### Step-by-step cookie export

1. Open Chrome and log into your Circle community.
2. Open DevTools (F12 or Ctrl+Shift+I).
3. Go to the **Application** tab.
4. In the left sidebar, expand **Cookies** and click on your community's domain.
5. Find these three cookies in the table:

| Cookie name          | What it does                        |
|----------------------|-------------------------------------|
| `_circle_session`    | Your active session token           |
| `remember_user_token`| Persistent login token              |
| `cf_clearance`       | Cloudflare bot-check clearance      |

6. For each cookie, note the **Name**, **Value**, **Domain**, and **Path** columns.
7. Create a file called `cookies.json` in the project root using the format below.

### Cookie file format

The file must be a JSON array of cookie objects. See `cookies.example.json` for a template.

```json
[
  {
    "name": "_circle_session",
    "value": "paste-the-full-value-here",
    "domain": "community.example.com",
    "path": "/"
  },
  {
    "name": "remember_user_token",
    "value": "paste-the-full-value-here",
    "domain": "community.example.com",
    "path": "/"
  },
  {
    "name": "cf_clearance",
    "value": "paste-the-full-value-here",
    "domain": ".example.com",
    "path": "/"
  }
]
```

Note the domain format: `_circle_session` and `remember_user_token` use the full subdomain (`community.example.com`), while `cf_clearance` typically uses a dot-prefixed parent domain (`.example.com`). Copy exactly what your browser shows.

## Usage

```bash
# Basic usage
python crawler.py https://community.example.com

# Custom output directory
python crawler.py https://community.example.com --output ./my-archive

# Custom cookie file location
python crawler.py https://community.example.com --cookies /path/to/cookies.json

# Limit the number of pages
python crawler.py https://community.example.com --max-pages 100

# All options combined
python crawler.py https://community.example.com \
  --output ./archive \
  --cookies ./my-cookies.json \
  --max-pages 200
```

### CLI arguments

| Argument       | Required | Default         | Description                              |
|----------------|----------|-----------------|------------------------------------------|
| `base_url`     | Yes      |                 | Base URL of the Circle community         |
| `--output`     | No       | `./output`      | Directory for saved HTML files           |
| `--cookies`    | No       | `./cookies.json`| Path to the cookies JSON file            |
| `--max-pages`  | No       | `500`           | Maximum number of pages to crawl         |

## Output structure

The crawler maps the community's URL paths to a local folder structure:

```
output/
  index.html                          # Homepage
  c/
    general-discussion.html           # Space page
    general-discussion/
      post-title-123456.html          # Individual post
  settings.html
  ...
```

Each file contains the full rendered HTML of the page, including any dynamically loaded content (the crawler waits 3 seconds after page load for JavaScript rendering).

## How it works

1. Launches a headless Chromium browser via Playwright.
2. Injects your session cookies to authenticate.
3. Applies anti-detection measures (custom user agent, hidden webdriver property, realistic browser headers).
4. Starts at the base URL and follows all internal links breadth-first.
5. Saves each page's rendered HTML to the output directory.
6. Continues until all reachable pages are saved or the max-pages limit is hit.

## Limitations

- **Session cookies expire.** Circle session cookies are typically valid for days to weeks, but they do expire. If the crawler starts getting redirected to login pages, re-export your cookies.
- **HTML only.** The crawler saves rendered HTML. It does not download images, videos, CSS, or JavaScript files. The saved pages reference the original URLs for these assets.
- **No incremental updates.** Each run starts fresh. It will overwrite previously saved files at the same paths.
- **Rate sensitivity.** The 3-second delay between pages is conservative but not configurable. Aggressive crawling could trigger rate limiting or Cloudflare challenges.
- **Single-page app content.** Some Circle content loads via client-side JavaScript after the initial page render. The 3-second wait handles most cases, but deeply nested lazy-loaded content may be missed.

## License

MIT
