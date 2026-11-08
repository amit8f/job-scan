# Public-sector employers that post on their own sites, not on LinkedIn or a hiring system:
# Bank of Israel (RSS), Israel Electric Corp (server-rendered list), Ministry of Defense tenders (JSON API),
# National Cyber Directorate (carousel API). Writes public_jobs.json; merge.py filters titles.
import requests,json,re,sys,html,time
S=sys.argv[1]; out=[]
UA={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
def req(method,u,**kw):
  for k in range(3):
    try:
      r=requests.request(method,u,headers={**UA,**kw.pop('headers',{})},timeout=40,**kw)
      if r.status_code==200: return r
    except Exception: pass
    time.sleep(3)
  return None
try:  # Bank of Israel
  r=req('GET','https://careers.boi.org.il/services/rss/job/',params={'locale':'he_IL','keywords':'(סטודנט)'},headers={'User-Agent':'curl/8.5.0'})
  for it in re.findall(r'<item>(.*?)</item>',r.text if r else '',re.S):
    t=re.search(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>',it,re.S); l=re.search(r'<link>(.*?)</link>',it,re.S)
    if t and l: out.append(dict(src='boi',company='Bank of Israel',title=html.unescape(t.group(1)).strip(),location='Jerusalem',url=html.unescape(l.group(1)).split('?')[0]))
except Exception as e: print('boi failed',e,file=sys.stderr)
try:  # Israel Electric Corp
  r=req('GET','https://careers.iec.co.il/'); h=r.text if r else ''
  for m in re.finditer(r"משרה מס'\s*(\d+)</p>\s*<button[^>]*>([^<]+)</button>",h):
    loc=re.search(r"<span class='hidden_span1'>מיקום</span>([^<]+)",h[m.end():m.end()+6000])
    out.append(dict(src='iec',company='Israel Electric Corporation',title=html.unescape(m.group(2)).strip(),location=loc.group(1).strip() if loc else '',url=f'https://careers.iec.co.il/order/{m.group(1)}/'))
except Exception as e: print('iec failed',e,file=sys.stderr)
try:  # Ministry of Defense civil tenders
  r=req('POST','https://jobs.mod.gov.il//api/TenderPublish/GetAllPublished',json={})
  for t in (r.json().get('Data') or []) if r else []:
    bj=t.get('BankJob') or {}; hr=bj.get('HrJob') or {}
    out.append(dict(src='mod',company='Ministry of Defense',title=f"{bj.get('JobName','')} (tender {t.get('TenderObjectID','')})",location=hr.get('JobAreaDescription',''),url='https://jobs.mod.gov.il/',deadline=(t.get('NomineesApplyingDate') or '')[:10]))
except Exception as e: print('mod failed',e,file=sys.stderr)
try:  # National Cyber Directorate; items without a link are closed
  r=req('POST','https://govextra.gov.il/umbraco/api/Carousel/GetCarousel',json={'id':'25914','CurrentPageId':'26642'})
  for x in r.json() if r else []:
    u=((x.get('link') or {}).get('url') or '')
    if u: out.append(dict(src='incd',company='Israel National Cyber Directorate',title=' '.join(x.get('title','').split())+' '+re.sub(r'<[^>]+>|&nbsp;',' ',x.get('content','')).strip(),location='Tel Aviv',url='https://govextra.gov.il'+requests.utils.quote(u)))
except Exception as e: print('incd failed',e,file=sys.stderr)
json.dump(out,open(S+'/public_jobs.json','w'),ensure_ascii=False)
from collections import Counter
print('public',len(out),dict(Counter(o['company'] for o in out)),file=sys.stderr)
