# Gideon's Trading Card Collector (fan-made)

Static, responsive collector gallery with five original series, card ownership and duplicate counts, search, viewing front/back artwork, and JSON backup/import.

## Run locally

From the project directory: `python -m http.server 8000`, then visit `http://localhost:8000`. Opening `index.html` directly as a `file://` URL will not load `cards.json` in many browsers.

## Fetch official artwork and new card records

Install `requests` and `beautifulsoup4`, then run `python update_cards.py` while online. It scrapes the publicly displayed card names and image URLs from https://gideonsbakehouse.com/collectors-hub/ and updates `cards.json`. It does not store copyrighted images locally. The starting catalog has names only; images populate after the first successful update.

The updater is intentionally conservative: if fewer than 30 matching images are found, it fails without overwriting the catalog. If the official site's markup or image alt text changes, the parser may need maintenance. Series attribution for newly released cards is estimated from card numbering and **should be verified manually**, especially for promotional cards. The source currently skips card #50, and this catalog does not fabricate it.

## Host on GitHub Pages

Create a GitHub repository and upload the contents of this directory, including `.github/workflows/update.yml`. In **Settings → Pages**, choose **Deploy from a branch**, `main`, `/ (root)` (or corresponding branch). In **Actions**, enable workflows and run **Update Gideon's card catalog** manually once. The workflow then attempts a daily update at 10:15 UTC, provided GitHub Actions remains enabled and has permission to push changes. The update is not instantaneous when new cards appear and may fail if the source layout or access rules change. GitHub Pages publication may take a little while after a commit.

## Tracking and privacy

The collection is stored as `localStorage` on a specific browser and domain, not on a server. Back up using **Export backup**, restore using **Import backup**. Clearing browser data or switching devices loses access to locally saved collection state unless a backup is imported. No account synchronization is provided.

Fan-created reference, not affiliated with Gideon's Bakehouse. Image rights remain with the original owner. Respect the site and don't bypass access limitations.

## NEW: Cookies and Cake Slices tasting tracker

This update adds two tabs to the existing Trading Cards gallery. Each bakery flavor
has a Tried button, a five-star rating and optional notes. Existing local card
ownership data remains untouched. The export backup now includes both cards and
bakery tastings; the importer also accepts older card-only backups.

Files to upload at the **root** of the GitHub repository:
`index.html`, `cards.json`, `menu.json`, `update_cards.py`, `update_menu.py`.
Also **replace** `.github/workflows/update.yml` with the updated workflow in this package.

The scheduled GitHub Action checks the official Collector's Hub and bakery menu
once daily. It **adds** newly discoverable bakery flavors while retaining
out-of-season flavors already collected. Menu extraction and photos depend on
Gideon's public site structure and may need maintenance if that changes. Daily
cake schedules aren't a guarantee of in-store inventory. Card auto-classification
into series is heuristic: verify unusual promos and future series.

Backup your collection before changing browsers or clearing browser data.
