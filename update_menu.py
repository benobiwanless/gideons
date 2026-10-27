"""Discover bakery cookie and daily cake names, preserve historical flavors, refresh available photos.
The collector's personal tasting data is stored in the visitor's browser, not this JSON file.
"""
import datetime,json,re,sys
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parent
URL='https://gideonsbakehouse.com/bakery-menu/'
CAT=ROOT/'menu.json'
def clean(t):return re.sub(r'\s+',' ',t or '').strip()
def slug(t):return re.sub(r'[^a-z0-9]+','-',t.lower()).strip('-')
def pic(im):
 if im is None:return ''
 for k in ('data-src','data-lazy-src','data-original','src'):
  val=im.get(k,'')
  if val and not val.startswith('data:'):
   result=urljoin(URL,val)
   if result.startswith('https://'):return result
 return ''
def main():
 d=json.loads(CAT.read_text(encoding='utf8'));items=d['items'];existing={x['id'] for x in items}
 resp=requests.get(URL,timeout=35,headers={'User-Agent':'Mozilla/5.0 (compatible; GideonsFanCollectionUpdater/1.0)'})
 resp.raise_for_status();soup=BeautifulSoup(resp.text,'html.parser')
 main=soup.select_one('main') or soup.select_one('article') or soup
 headers=main.find_all(re.compile('^h[1-6]$'))
 section='';seen=set();added=0;photos=0
 for h in headers:
  name=clean(h.get_text(' ',strip=True));lower=name.casefold()
  if 'small batch cookies' in lower:section='cookie';continue
  if 'cake slices' in lower:section='cake';continue
  if 'out of season cookies' in lower:section='cookie';continue
  if 'slice schedule' in lower:section='cake';continue
  if lower in ('sunday','monday','tuesday','wednesday','thursday','friday','saturday'):section='cake'
  # On Gideon's site cookie flavor names are h3 headings; skip the general headings.
  if section=='cookie' and h.name in ('h3','h4') and len(name)<85 and not any(t in lower for t in ('just here','available','cookie of the','limited edition')):
   ident='cookie-'+slug(name);seen.add(ident)
   # usually the featured image sits immediately before the heading
   image='';prev=h.find_previous('img');
   if prev:image=pic(prev)
   match=next((x for x in items if x['id']==ident),None)
   if match:
    if image and match.get('image')!=image:match['image']=image;photos+=1
   else:
    items.append({'id':ident,'name':name,'type':'cookie','image':image,'first_seen':datetime.date.today().isoformat()});existing.add(ident);added+=1
  # A weekday heading is followed by links for that day's cake flavors.
  if section=='cake' and lower in ('sunday','monday','tuesday','wednesday','thursday','friday','saturday'):
   for elem in h.next_elements:
    if getattr(elem,'name',None) in ('h1','h2','h3','h4'):break
    if getattr(elem,'name',None)=='a':
     cake=clean(elem.get_text(' ',strip=True))
     if not cake or len(cake)>70:continue
     ident='cake-'+slug(cake);seen.add(ident)
     if ident not in existing:
      items.append({'id':ident,'name':cake,'type':'cake','image':'','first_seen':datetime.date.today().isoformat()});existing.add(ident);added+=1
 if len(seen)<8:raise RuntimeError(f'Only {len(seen)} menu flavors found; refusing to overwrite in case page changed')
 d['updated']=datetime.date.today().isoformat();CAT.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(f'Found {len(seen)} bakery flavors; added {added} new flavors, refreshed {photos} photos; total {len(items)}')
if __name__=='__main__':
 try:main()
 except Exception as ex:print('Bakery update failed:',ex,file=sys.stderr);sys.exit(1)
