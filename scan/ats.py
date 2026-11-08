import json,re,requests,sys,csv,glob,html
from concurrent.futures import ThreadPoolExecutor
S=sys.argv[1]  # scratch dir
UA={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
comps=json.load(open(S+'/companies.json'))
comeet,gh,lv,ash,sr,wk,bz=set(),set(),set(),set(),set(),set(),set()
def scan_url(u):
  if not u: return
  m=re.search(r'comeet\.(?:com|co)/jobs/([^/]+)/([0-9A-F]{2}\.[0-9A-F]{3})',u,re.I)
  if m: comeet.add(m.group(1)+'/'+m.group(2))
  m=re.search(r'greenhouse\.io/(?:embed/job_board\?for=)?([a-z0-9_-]+)',u,re.I)
  if m and m.group(1) not in('v1','embed','boards'): gh.add(m.group(1).lower())
  m=re.search(r'lever\.co/([a-z0-9_-]+)',u,re.I)
  if m: lv.add(m.group(1).lower())
  m=re.search(r'ashbyhq\.com/([A-Za-z0-9_.-]+)',u)
  if m: ash.add(m.group(1))
  m=re.search(r'smartrecruiters\.com/([A-Za-z0-9_-]+)',u)
  if m: sr.add(m.group(1))
  m=re.search(r'apply\.workable\.com/([a-z0-9_-]+)',u,re.I)
  if m: wk.add(m.group(1).lower())
  m=re.search(r'([a-z0-9-]+)\.breezy\.hr',u,re.I)
  if m: bz.add(m.group(1).lower())
for c in comps:
  if c['comeetId']: comeet.add(c['comeetId'])
  if c['greenhouseId']: gh.add(c['greenhouseId'].lower())
  if c['leverId']: lv.add(c['leverId'].lower())
  if c['breezyId']: bz.add(c['breezyId'].lower())
  scan_url(c['careersUrl'])
for f in glob.glob(S+'/techmap/jobs/*.csv'):
  for r in csv.reader(open(f,encoding='utf-8-sig')): scan_url(r[6] if len(r)>6 else '')
# extra known Israeli greenhouse/comeet boards (guesses; 404s are ignored)
for g in "wix monday riskified taboola outbrain lemonade similarweb fiverr payoneer appsflyer ironsource unity cato catonetworks snyk wizinc wiz orca armis axonius cybereason sentinelone transmitsecurity pagaya yotpo melio hibob nayax tipalti papaya papayaglobal gong fireblocks varonis checkmarx jfrog redis via gloat lightricks playtika moonactive taranis forter bigid pentera claroty aquasecurity aqua cyera island nice hunters upwind silverfort zesty sygnia stripe datadog cloudflare mongodb elastic okta crowdstrike paloaltonetworks zscaler doubleverify yahoo booking eToro etoro plarium solaredge vastdata vast run-ai runai deci hailo innoviz arbe nexar viz aidoc zebra-medical tabnine ai21 ai21labs lusha guesty honeybook bringg lili rapyd global-e nuvei walkme sapiens kaltura cellebrite perion".split():
  gh.add(g.lower())
print('comeet',len(comeet),'gh',len(gh),'lever',len(lv),'ashby',len(ash),'sr',len(sr),'workable',len(wk),'breezy',len(bz),file=sys.stderr)
STU=re.compile(r'student|intern\b|internship|interns\b|סטודנט|working student|co-?op\b|summer\s+\d{4}',re.I)
IL=re.compile(r'israel|tel[- ]?aviv|haifa|jerusalem|herzliya|herzlia|petah|petach|ra.?anana|be.?er|beer|netanya|rehovot|yokneam|ramat|givatayim|rosh|kfar|hod|modiin|ashdod|airport city|caesarea|lod|holon|bnei|or yehuda|kiryat|matam|נתניה|ישראל|תל|חיפה|באר|הרצליה|רעננה|פתח|ירושלים|IL\b',re.I)
out=[]
def add(**d): out.append(d)
def get(u,**k):
  try: return requests.get(u,headers=UA,timeout=30,**k)
  except Exception as e: return None
def do_comeet(cid):
  r=get('https://www.comeet.com/jobs/'+cid)
  if not r or r.status_code!=200: return
  m=re.search(r'COMPANY_POSITIONS_DATA\s*=\s*(\[.*?\]);\s*\n',r.text,re.S)
  cn=re.search(r'COMPANY_DATA\s*=\s*\{.*?"name":\s*"([^"]+)"',r.text,re.S)
  if not m: return
  try: data=json.loads(m.group(1))
  except Exception: return
  for p in data:
    loc=p.get('location') or {}
    locs=' '.join(str(loc.get(k) or '') for k in ('name','country','city'))
    if STU.search(p.get('name','')) and (loc.get('country')=='IL' or IL.search(locs)):
      add(src='comeet',company=cn.group(1) if cn else cid.split('/')[0],title=p['name'],location=locs.strip(),url=p.get('url_comeet_hosted_page') or p.get('url_active_page') or '',updated=p.get('time_updated',''),dept=p.get('department'))
def do_gh(b):
  r=get(f'https://boards-api.greenhouse.io/v1/boards/{b}/jobs')
  if not r or r.status_code!=200: return
  for j in r.json().get('jobs',[]):
    loc=(j.get('location') or {}).get('name','')
    if STU.search(j['title']) and IL.search(loc): add(src='greenhouse',company=b,title=j['title'],location=loc,url=j['absolute_url'],updated=j.get('updated_at',''),id=j['id'])
def do_lv(b):
  r=get(f'https://api.lever.co/v0/postings/{b}?mode=json')
  if not r or r.status_code!=200: return
  for j in r.json():
    loc=(j.get('categories') or {}).get('location','') or ''
    if STU.search(j['text']) and IL.search(loc+' '+str(j.get('country',''))): add(src='lever',company=b,title=j['text'],location=loc,url=j['hostedUrl'],updated=j.get('createdAt'),desc=j.get('descriptionPlain','')[:3000])
def do_ash(b):
  r=get(f'https://api.ashbyhq.com/posting-api/job-board/{b}')
  if not r or r.status_code!=200: return
  for j in r.json().get('jobs',[]):
    loc=j.get('location','')+' '+' '.join(x.get('location','') for x in j.get('secondaryLocations',[]) or [])
    if STU.search(j['title']) and IL.search(loc): add(src='ashby',company=b,title=j['title'],location=loc,url=j['jobUrl'],updated=j.get('publishedAt'),desc=(j.get('descriptionPlain') or '')[:3000])
def do_sr(b):
  r=get(f'https://api.smartrecruiters.com/v1/companies/{b}/postings?country=il&limit=100')
  if not r or r.status_code!=200: return
  for j in r.json().get('content',[]):
    if STU.search(j['name']): add(src='smartrecruiters',company=b,title=j['name'],location=str(j.get('location',{}).get('city')),url=f"https://jobs.smartrecruiters.com/{b}/{j['id']}",updated=j.get('releasedDate'))
def do_wk(b):
  r=get(f'https://apply.workable.com/api/v1/widget/accounts/{b}')
  if not r or r.status_code!=200: return
  for j in r.json().get('jobs',[]):
    loc=' '.join(str(j.get(k,'')) for k in('city','country'))
    if STU.search(j['title']) and IL.search(loc): add(src='workable',company=b,title=j['title'],location=loc,url=j.get('url') or j.get('shortlink'),updated=j.get('published_on'))
def do_bz(b):
  r=get(f'https://{b}.breezy.hr/json')
  if not r or r.status_code!=200: return
  try: js=r.json()
  except Exception: return
  for j in js:
    loc=str(j.get('location',{}).get('name',''))
    if STU.search(j['name']) and IL.search(loc): add(src='breezy',company=b,title=j['name'],location=loc,url=j['url'],updated=j.get('published_date'))
tasks=[(do_comeet,x) for x in comeet]+[(do_gh,x) for x in gh]+[(do_lv,x) for x in lv]+[(do_ash,x) for x in ash]+[(do_sr,x) for x in sr]+[(do_wk,x) for x in wk]+[(do_bz,x) for x in bz]
with ThreadPoolExecutor(12) as ex: list(ex.map(lambda t:t[0](t[1]),tasks))
json.dump(out,open(S+'/ats_jobs.json','w'),ensure_ascii=False,indent=0)
print(len(out),file=sys.stderr)
