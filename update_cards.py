"""Update the public card catalog from Gideon's published Collector's Hub HTML.
Does not download or rehost artwork. Uses Gideon's image URLs.
"""
import datetime,json,re,sys
from pathlib import Path
from urllib.parse import urljoin,urlparse
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parent
URL='https://gideonsbakehouse.com/collectors-hub/'
CAT=ROOT/'cards.json'

def clean(text):
 return re.sub(r'\s+',' ',text or '').strip()

def norm(text):
 return re.sub(r'[^a-z0-9]+','',text.casefold())

def image_url(img):
 for key in ('data-src','data-lazy-src','data-original','src'):
  val=img.get(key,'')
  if val and not val.startswith('data:'):
   result=urljoin(URL,val)
   if urlparse(result).scheme=='https':return result
 return ''

def alt_from_image(img):
 alt=clean(img.get('alt'))
 if alt:return alt
 # WordPress attachments often have an accessible title on wrapping link
 parent=img.find_parent('a')
 return clean(parent.get('title','')) if parent else ''

def main():
 payload=json.loads(CAT.read_text())
 cards=payload['cards']
 response=requests.get(URL,headers={'User-Agent':'Mozilla/5.0 (compatible; CollectorGallery/1.0; personal card archive)'},timeout=35)
 response.raise_for_status()
 soup=BeautifulSoup(response.text,'html.parser')
 images=[]
 for im in soup.select('img'):
  alt=alt_from_image(im)
  if not alt:continue
  back=bool(re.search(r'\s*-\s*back\s*$',alt,re.I))
  base=re.sub(r'\s*-\s*back\s*$','',alt,flags=re.I).strip()
  url=image_url(im)
  if url and base:images.append((base,back,url))
 seen=set();matched=0
 for c in cards:
  for base,back,url in images:
   if norm(base)==norm(c['name']):
    c['back' if back else 'front']=url
    if not back:seen.add(norm(base))
    matched+=1
 # New cards are assigned using their printed numbers; promos are kept in latest known series.
 new=[]
 known={norm(c['name']) for c in cards}
 for base,back,url in images:
  if back or norm(base) in known:continue
  known.add(norm(base));m=re.match(r'^(\d{1,3})\s+(.+)',base)
  if m:
   number=int(m.group(1));last=max((int(c['number']) for c in cards if c.get('number')),default=0)
   current=max((int(c['series']) for c in cards),default=5)
   s=current if number>last else next((c['series'] for c in cards if c.get('number') and int(c['number'])>number),current)
   ident='s%s-%03d'%(s,number)
  else:
   s=max((int(c['series']) for c in cards),default=5)
   ident='s%s-%s'%(s,re.sub('[^a-z0-9]+','-',base.lower()).strip('-'))
  if any(c['id']==ident for c in cards):continue
  new.append({'id':ident,'name':base,'number':m.group(1) if m else '', 'series':s,'promo':not bool(m),'front':url,'back':''})
 cards.extend(new)
 # Populate backs for newly discovered entries.
 for c in new:
  for base,back,url in images:
   if norm(base)==norm(c['name']) and back:c['back']=url
 if matched<30:
  raise RuntimeError(f'Only {matched} matching card images found. Source layout may have changed; refusing to overwrite. Found {len(images)} labeled images.')
 payload['updated']=datetime.date.today().isoformat()
 CAT.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n')
 print(f'Synced {matched} images, added {len(new)} new cards; total {len(cards)}')
if __name__=='__main__':
 try:main()
 except Exception as e:print('Update failed:',e,file=sys.stderr);sys.exit(1)
