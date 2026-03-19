# circle-scraper

Tools for archiving Circle platform communities behind authentication.

Circle (circle.so) is a community platform used by course creators, membership sites, and online communities. This repository documents three approaches to creating a local archive of community content, tested against a real Circle community (AAA Accelerator, hub.aaaaccelerator.com) in October 2025.

## Approaches Compared

| Approach | Output | Auth Handling | JS Rendering | Assets (images, CSS, video) | Recommendation |
|----------|--------|---------------|--------------|----------------------------|----------------|
| **Browsertrix** | WARC/WACZ archives (8.2 GB across 5 segments) | Built-in login browser | Full Chromium rendering | Yes, all captured | Recommended for full site mirror |
| **Playwright script** (crawler.py) | Static HTML files | Cookie injection | Partial (3s wait) | No, HTML only | Lightweight alternative for text content |
| **HTTrack** | Nothing usable | Cookie passthrough | None | N/A | Does not work on Circle |

## Option 1: Browsertrix (Recommended)

Browsertrix is a browser-based web archiver built on Playwright. It runs in Docker, renders JavaScript fully, and produces standard web archive files (WARC/WACZ) that preserve the complete site: HTML, images, CSS, JavaScript, video embeds.

In testing, Browsertrix produced a 5.3 GB standalone .wacz file containing thousands of indexed pages from the target community.

### Prerequisites

- Docker

### Installation

```bash
docker pull webrecorder/browsertrix-crawler
```

### Authentication

Circle communities require login. Browsertrix offers two approaches:

**Option A: Interactive login (simpler)**

Use the `--profile` flag to open a browser window where you log in manually. Browsertrix saves the authenticated session as a browser profile for the crawl.

```bash
# Step 1: Create an authenticated browser profile
docker run -p 6080:6080 -p 9223:9223 \
  -v $(pwd)/profiles:/crawls/profiles \
  -it webrecorder/browsertrix-crawler create-login-profile \
  --url https://community.example.com \
  --filename profile.tar.gz

# This opens a browser at http://localhost:6080
# Log in to the Circle community, then close the browser window
```

**Option B: Existing browser profile**

If you have a Chrome/Chromium profile already logged into the community, you can pass it directly.

### Running the Crawl

```bash
docker run -v $(pwd)/crawls:/crawls \
  -v $(pwd)/profiles:/crawls/profiles \
  webrecorder/browsertrix-crawler crawl \
  --url https://community.example.com \
  --profile /crawls/profiles/profile.tar.gz \
  --scopeType host \
  --generateWACZ \
  --collection circle-archive
```

Key options:

| Flag | Purpose |
|------|---------|
| `--url` | Starting URL for the crawl |
| `--profile` | Path to the authenticated browser profile |
| `--scopeType host` | Stay within the community's domain |
| `--generateWACZ` | Produce a self-contained .wacz archive |
| `--collection` | Name for the output collection |
| `--workers N` | Number of parallel browser instances (default 1) |
| `--limit N` | Maximum number of pages to crawl |

### Output

Crawl results are saved to `./crawls/collections/circle-archive/`:

```
crawls/collections/circle-archive/
  circle-archive.wacz          # Self-contained archive (single file)
  archive/                     # Raw WARC segments
    data-00000.warc.gz
    data-00001.warc.gz
    ...
  pages/
    pages.jsonl                # Index of all crawled pages
  logs/
    ...
```

### Viewing the Archive

WACZ files are standard web archive format. Open them with [ReplayWeb.page](https://replayweb.page/), which runs entirely in the browser:

1. Go to https://replayweb.page/
2. Drag and drop the .wacz file onto the page
3. Browse the archived community as it appeared at crawl time

ReplayWeb.page also has a desktop app and can be self-hosted.

## Option 2: Playwright Script (HTML Only)

The included `crawler.py` is a lightweight Playwright-based crawler that saves rendered HTML files. It does not capture images, CSS, or other assets. Use this when you only need the text content of posts and pages, not a full visual mirror.

### Prerequisites

- Python 3.10 or later
- A Circle community account with an active session in Chrome

### Installation

```bash
git clone https://github.com/maarteek/circle-scraper.git
cd circle-scraper
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### Cookie Setup

The crawler needs your authenticated session cookies to access the community. You export these from your browser after logging in.

#### Step-by-step cookie export

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

#### Cookie file format

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

### Usage

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

### CLI Arguments

| Argument       | Required | Default         | Description                              |
|----------------|----------|-----------------|------------------------------------------|
| `base_url`     | Yes      |                 | Base URL of the Circle community         |
| `--output`     | No       | `./output`      | Directory for saved HTML files           |
| `--cookies`    | No       | `./cookies.json`| Path to the cookies JSON file            |
| `--max-pages`  | No       | `500`           | Maximum number of pages to crawl         |

### Output Structure

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

### Limitations

- **Session cookies expire.** Circle session cookies are typically valid for days to weeks, but they do expire. If the crawler starts getting redirected to login pages, re-export your cookies.
- **HTML only.** The crawler saves rendered HTML. It does not download images, videos, CSS, or JavaScript files. The saved pages reference the original URLs for these assets.
- **No incremental updates.** Each run starts fresh. It will overwrite previously saved files at the same paths.
- **Rate sensitivity.** The 3-second delay between pages is conservative but not configurable. Aggressive crawling could trigger rate limiting or Cloudflare challenges.
- **SPA content.** Some Circle content loads via client-side JavaScript after the initial page render. The 3-second wait handles most cases, but deeply nested lazy-loaded content may be missed. In testing, this script captured only 1 page (index.html) from the target community, while Browsertrix captured thousands.

## What Didn't Work: HTTrack

Traditional crawlers like HTTrack and wget do not work on Circle communities. Circle is a JavaScript single-page application. HTTrack captured only cache and log files with zero usable content. These tools cannot execute JavaScript, so they never see the rendered page content. If you are considering HTTrack or wget for a Circle archive, save yourself the time and use Browsertrix instead.

## License

MIT
