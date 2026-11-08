# Pull student/intern roles from hiring systems discovered on company careers pages (sites.json) -> ats2_jobs.json
import json,re,sys,requests,html
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,__import__('os').path.dirname(__file__))
S=sys.argv[1]
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
STU=re.compile(r'student|intern\b|internship|interns\b|סטודנט',re.I)
IL=re.compile(r'israel|tel[- ]?aviv|haifa|jerusalem|herzli|petah|petach|ra.?anana|be.?er|netanya|rehovot|yokneam|yoqneam|ramat|givatayim|rosh|kfar|hod|modiin|ashdod|airport city|caesarea|lod|holon|bnei|or yehuda|kiryat|matam|נתניה|ישראל|תל|חיפה|באר|הרצליה|רעננה|פתח|ירושלים|\bIL\b|\bISR\b',re.I)
R=json.load(open(S+'/sites.json'))
out=[]
def get(u,**k):
  try: return requests.get(u,headers=UA,timeout=30,**k)
  except Exception: return None
def comeet_page(company,url):
  r=get(url)
  if not r: return
  for loc,uid,slug in set(re.findall(r'/co/([^/"\']+)/([0-9A-F]{2}\.[0-9A-F]{3})/([^/"\']+)/all',r.text)):
    title=slug.replace('-',' ')
    if STU.search(title) and (IL.search(loc) or not re.search(r'new-york|london|usa|united|germany|india|poland|uk|boston|chicago|texas|california|paris|berlin|madrid|tokyo|singapore|sydney|toronto|ny\b',loc,re.I)):
      out.append(dict(src='comeet-site',company=company,title=title,location=loc,url=re.sub(r'(https?://[^/]+).*',r'\1',r.url)+re.search(r'[^"\']*/co/'+re.escape(loc)+'/'+re.escape(uid)+'/'+re.escape(slug)+'/all',r.text).group(0).split('//')[-1].split('/',1)[-1].join(['/','']) if False else f"{r.url.rstrip('/')}  (role: {title})"))
def comeet_board(company,cid):
  u='https://www.comeet.com/jobs/'+cid if '/' in cid else 'https://www.comeet.com/jobs/x/'+cid
  r=get(u)
  if not r or r.status_code!=200: return
  m=re.search(r'COMPANY_POSITIONS_DATA\s*=\s*(\[.*?\]);\s*\n',r.text,re.S)
  if not m: return
  try: data=json.loads(m.group(1))
  except Exception: return
  for p in data:
    loc=p.get('location') or {}; locs=' '.join(str(loc.get(k) or '') for k in ('name','country','city'))
    if STU.search(p.get('name','')) and (loc.get('country')=='IL' or IL.search(locs)):
      out.append(dict(src='comeet',company=company,title=p['name'],location=locs.strip(),url=p.get('url_comeet_hosted_page') or '',updated=p.get('time_updated','')))
def gh(company,b):
  r=get(f'https://boards-api.greenhouse.io/v1/boards/{b}/jobs')
  if r and r.status_code==200:
    for j in r.json().get('jobs',[]):
      loc=(j.get('location') or {}).get('name','')
      if STU.search(j['title']) and IL.search(loc): out.append(dict(src='greenhouse',company=company,title=j['title'],location=loc,url=j['absolute_url']))
def lever(company,b):
  r=get(f'https://api.lever.co/v0/postings/{b}?mode=json')
  if r and r.status_code==200:
    for j in r.json():
      loc=(j.get('categories') or {}).get('location','') or ''
      if STU.search(j['text']) and IL.search(loc+' '+str(j.get('country',''))): out.append(dict(src='lever',company=company,title=j['text'],location=loc,url=j['hostedUrl'],desc=j.get('descriptionPlain','')[:3000]))
def ashby(company,b):
  r=get(f'https://api.ashbyhq.com/posting-api/job-board/{b}')
  if r and r.status_code==200:
    for j in r.json().get('jobs',[]):
      loc=j.get('location','')+' '+' '.join(x.get('location','') for x in j.get('secondaryLocations',[]) or [])
      if STU.search(j['title']) and IL.search(loc): out.append(dict(src='ashby',company=company,title=j['title'],location=loc,url=j['jobUrl'],desc=(j.get('descriptionPlain') or '')[:3000]))
def sr(company,b):
  r=get(f'https://api.smartrecruiters.com/v1/companies/{b}/postings?country=il&limit=100')
  if r and r.status_code==200:
    for j in r.json().get('content',[]):
      if STU.search(j['name']): out.append(dict(src='smartrecruiters',company=company,title=j['name'],location=str(j.get('location',{}).get('city')),url=f"https://jobs.smartrecruiters.com/{b}/{j['id']}"))
def workable(company,b):
  r=get(f'https://apply.workable.com/api/v1/widget/accounts/{b}')
  if r and r.status_code==200:
    for j in r.json().get('jobs',[]):
      loc=' '.join(str(j.get(k,'')) for k in('city','country'))
      if STU.search(j['title']) and IL.search(loc): out.append(dict(src='workable',company=company,title=j['title'],location=loc,url=j.get('url') or j.get('shortlink')))
def breezy(company,b):
  r=get(f'https://{b}.breezy.hr/json')
  try: js=r.json() if r else []
  except Exception: js=[]
  for j in js:
    loc=str(j.get('location',{}).get('name',''))
    if STU.search(j['name']) and IL.search(loc): out.append(dict(src='breezy',company=company,title=j['name'],location=loc,url=j['url']))
def bamboo(company,b):
  r=get(f'https://{b}.bamboohr.com/careers/list')
  try: js=r.json().get('result',[]) if r else []
  except Exception: js=[]
  for j in js:
    loc=json.dumps(j.get('location',{}))+json.dumps(j.get('atsLocation',{}))
    if STU.search(j.get('jobOpeningName','')) and IL.search(loc): out.append(dict(src='bamboohr',company=company,title=j['jobOpeningName'],location=loc[:80],url=f"https://{b}.bamboohr.com/careers/{j['id']}"))
def recruitee(company,b):
  r=get(f'https://{b}.recruitee.com/api/offers/')
  try: js=r.json().get('offers',[]) if r else []
  except Exception: js=[]
  for j in js:
    loc=str(j.get('location',''))+' '+str(j.get('country',''))
    if STU.search(j['title']) and IL.search(loc): out.append(dict(src='recruitee',company=company,title=j['title'],location=loc,url=j.get('careers_url','')))
def teamtailor(company,b):
  r=get(f'https://{b}.teamtailor.com/jobs')
  if r:
    for href,t in set(re.findall(r'href="(https://[^"]*?/jobs/\d+[^"]*)"[^>]*>\s*(?:<[^>]+>\s*)*([^<]{3,120})',r.text)):
      if STU.search(t): out.append(dict(src='teamtailor',company=company,title=html.unescape(t.strip()),location='',url=href))
def hibob(company,b):
  r=get(f'https://{b}.careers.hibob.com/api/job-ad')
  try: js=r.json().get('jobAdDetails',[]) if r else []
  except Exception: js=[]
  for j in js:
    if STU.search(j.get('title','')) and IL.search(json.dumps(j.get('site',''))+str(j.get('country',''))): out.append(dict(src='hibob',company=company,title=j['title'],location=str(j.get('site')),url=f"https://{b}.careers.hibob.com/jobs/{j.get('id')}"))
WD=set()
tasks=[]
for s in R:
  a=s.get('ats',{}); c=s['company']
  for x in a.get('comeet',[]): tasks.append((comeet_board,c,x))
  for x in a.get('comeet_uid',[]): tasks.append((comeet_board,c,x))
  if a.get('comeet_plugin'): tasks.append((comeet_page,c,s['url']))
  for x in a.get('greenhouse',[]): tasks.append((gh,c,x))
  for x in a.get('lever',[]): tasks.append((lever,c,x))
  for x in a.get('ashby',[]): tasks.append((ashby,c,x))
  for x in a.get('smartrecruiters',[]): tasks.append((sr,c,x))
  for x in a.get('workable',[]): tasks.append((workable,c,x))
  for x in a.get('breezy',[]): tasks.append((breezy,c,x))
  for x in a.get('bamboo',[]): tasks.append((bamboo,c,x))
  for x in a.get('recruitee',[]): tasks.append((recruitee,c,x))
  for x in a.get('teamtailor',[]): tasks.append((teamtailor,c,x))
  for x in a.get('hibob',[]): tasks.append((hibob,c,x))
  for x in a.get('workday',[]): WD.add(re.sub(r'/[a-z]{2}-[A-Z]{2}/','/',x))
seen=set(); uniq=[]
for t in tasks:
  if (t[0].__name__,t[2]) not in seen: seen.add((t[0].__name__,t[2])); uniq.append(t)
with ThreadPoolExecutor(16) as ex: list(ex.map(lambda t:t[0](t[1],t[2]),uniq))
json.dump(out,open(S+'/ats2_jobs.json','w'),ensure_ascii=False,indent=0)
open(S+'/workday_sites.txt','w').write(' '.join(sorted(x.replace('.myworkdayjobs.com','') for x in WD)))
print('ats2 tasks',len(uniq),'student roles',len(out),'workday sites',len(WD),file=sys.stderr)
