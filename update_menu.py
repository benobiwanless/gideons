"""Refresh Gideon's cookie and cake photos; retain historical dessert entries and user data."""
import datetime
import json
import re
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
FILE = ROOT / 'menu.json'
SOURCES = {
    'cookie': 'https://gideonsbakehouse.com/bakery-menu/',
    'cake': 'https://gideonsbakehouse.com/cake-slice-menu/',
}

def normalize(value):
    return re.sub(r'[^a-z0-9]+', '', value.casefold().replace('’', "'").replace('&', 'and'))

def slug(value):
    return re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')

def image_url(img, base):
    if img is None:
        return ''
    for key in ('data-src', 'data-lazy-src', 'data-original', 'src', 'data-srcset', 'srcset'):
        val = img.get(key, '')
        if not val:
            continue
        if key.endswith('srcset'):
            val = val.split(',')[0].strip().split(' ')[0]
        url = urljoin(base, val.strip())
        if url.startswith('https://') and not val.startswith('data:'):
            return url
    return ''

def get_heading_photo(heading, base):
    # Published Gideon's menu items place the image directly before the H3.
    # Search nearby DOM only to avoid assigning a previous *flavor's* photo.
    for node in heading.previous_elements:
        if getattr(node, 'name', '') in ('h2', 'h3'):
            break
        if getattr(node, 'name', '') == 'img':
            return image_url(node, base)
    return ''

def main():
    data = json.loads(FILE.read_text(encoding='utf-8'))
    items = data['items']
    index = {(x['type'], normalize(x['name'])): x for x in items}
    added = 0
    updated = 0
    failures = []
    for kind, url in SOURCES.items():
        try:
            response = requests.get(url, timeout=45, headers={'User-Agent': 'Mozilla/5.0 GideonsCollector/2.0'})
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            # The headings follow image blocks throughout both official pages.
            candidates = []
            for heading in soup.find_all('h3'):
                name = heading.get_text(' ', strip=True)
                if not name or len(name) > 90 or name.casefold().startswith(('cake slices for ', 'these are just here')):
                    continue
                pic = get_heading_photo(heading, url)
                if pic:
                    candidates.append((name, pic))
            if len(candidates) < (12 if kind == 'cookie' else 8):
                raise RuntimeError(f'Only {len(candidates)} photographed headings found')
            for name, photo in candidates:
                key = (kind, normalize(name))
                entry = index.get(key)
                if entry is None:
                    entry = {'id': kind + '-' + slug(name), 'name': name, 'type': kind,
                             'image': photo, 'first_seen': datetime.date.today().isoformat()}
                    items.append(entry)
                    index[key] = entry
                    added += 1
                elif entry.get('image') != photo:
                    entry['image'] = photo
                    updated += 1
            print(f'{kind}: found {len(candidates)} photographed menu items')
        except Exception as exc:
            failures.append(f'{kind}: {exc}')
            print('Warning:', failures[-1])
    if failures:
        raise RuntimeError('Could not safely update all menu photos: ' + '; '.join(failures))
    data['updated'] = datetime.date.today().isoformat()
    FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Added {added} new desserts, refreshed {updated} photos.')

if __name__ == '__main__':
    main()
