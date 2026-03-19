# circle-scraper - Claude Code Guide

CLI tool to crawl and archive Circle platform communities as static HTML.

Project-specific instructions. Supplements global ~/CLAUDE.md.

---

## Quick Commands

```bash
# Run
python crawler.py https://community.example.com --output ./output

# Install deps
pip install -r requirements.txt && playwright install chromium
```

---

## Architecture

- Single-file Python CLI using Playwright for headless browser crawling
- Cookie-based authentication (user exports from browser, loads from cookies.json)
- Breadth-first link discovery within the target domain
- Anti-detection measures: custom UA, hidden webdriver, realistic HTTP headers
- No external API dependencies

---

## Domain Knowledge

- Circle communities use Cloudflare for bot protection. The `cf_clearance` cookie is required alongside session cookies.
- Circle is a Rails app. `_circle_session` is the Rails session cookie, `remember_user_token` is Devise's persistent login.
- Pages are SPAs with server-rendered initial content. The 3-second wait after `domcontentloaded` captures most dynamic content.
- Session cookies expire after days to weeks. Users need to re-export when crawls start returning login pages.
