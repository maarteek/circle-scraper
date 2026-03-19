# Changelog

## 2026-03-19 - README rewrite: document all three archiving approaches
- Repositioned project from single-tool crawler to a guide covering three tested approaches
- Added Browsertrix as primary recommendation (full site mirror with WARC/WACZ output)
- Moved Playwright crawler.py docs to secondary option for HTML-only use cases
- Added HTTrack failure notes to save others the time
- Included comparison table, authentication steps, and ReplayWeb.page viewing instructions

## 2026-03-19 - Initial release
- Refactored from private single-use script into a shareable CLI tool
- Replaced hardcoded cookies with external cookies.json file
- Made base URL a required CLI argument
- Added --output, --cookies, and --max-pages CLI arguments via argparse
- Preserved all anti-detection measures from original script
- Added cookies.example.json template
- Created README with full setup and cookie export instructions
