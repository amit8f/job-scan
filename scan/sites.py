# Visit every company careers page (techmap careersUrl, plus website/careers for size m+),
# detect embedded hiring systems and student/intern mentions. Output: <S>/sites.json
import json,glob,re,sys,requests,html
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
S=sys.argv[1]
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36","Accept-Language":"en-US,en;q=0.9,he;q=0.8"}
C=[json.load(open(f)) for f in glob.glob(S+'/techmap/companies/*.json')]
import os
X=os.path.join(os.path.dirname(os.path.abspath(__file__)),'extra_companies.json')  # companies Tech Map lacks (e.g. 2026-funded startups)
if os.path.exists(X): C+=json.load(open(X))
C=[c for c in C if c.get('isActive')]
targets=[]
for c in C:
  # careers page first, then fall back to the company website (careers pages move or die, the homepage usually links the new one)
  w=(c.get('websiteUrl') or '').rstrip('/')
  fb=[w+'/careers',w+'/careers/',w+'/jobs',w+'/about/careers',w+'/he/careers',w] if w else []
  if c.get('careersUrl'): targets.append((c['name'],c['size'],[c['careersUrl']]+[u for u in fb if u!=c['careersUrl']]))
  elif c['size'] in('m','l','xl') and fb: targets.append((c['name'],c['size'],fb))
PAT={
 'comeet':r'comeet\.(?:com|co)/jobs/([^/"\'\s]+/[0-9A-F]{2}\.[0-9A-F]{3})',
 'comeet_plugin':r'careers/co/[^"\']*?/([0-9A-F]{2}\.[0-9A-F]{3})',
 'comeet_uid':r'company[-_]uid["\'=:\s]+["\']?([0-9A-F]{2}\.[0-9A-F]{3})',
 'greenhouse':r'(?:boards|job-boards)(?:\.eu)?\.greenhouse\.io/(?:embed/job_board(?:/js)?\?for=)?([A-Za-z0-9_-]+)',
 'greenhouse2':r'greenhouse\.io/embed/job_board(?:/js)?\?for=([A-Za-z0-9_-]+)',
 'lever':r'jobs\.(?:eu\.)?lever\.co/([A-Za-z0-9_.-]+)',
 'ashby':r'jobs\.ashbyhq\.com/([A-Za-z0-9_.%-]+)',
 'smartrecruiters':r'(?:careers|jobs)\.smartrecruiters\.com/([A-Za-z0-9_-]+)',
 'workable':r'apply\.workable\.com/([A-Za-z0-9_-]+)',
 'breezy':r'https?://([a-z0-9-]+)\.breezy\.hr',
 'bamboo':r'https?://([a-z0-9-]+)\.bamboohr\.com',
 'recruitee':r'https?://([a-z0-9-]+)\.recruitee\.com',
 'workday':r'https?://([a-z0-9-]+\.wd\d+\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?[A-Za-z0-9_-]+)',
 'teamtailor':r'https?://([a-z0-9-]+)\.teamtailor\.com',
 'hibob':r'https?://([a-z0-9-]+)\.careers\.hibob\.com',
}
STU=re.compile(r'[^<>\n]{0,80}\b(?:student|intern|internship)\b[^<>\n]{0,80}|[^<>\n]{0,60}סטודנט[^<>\n]{0,60}',re.I)
def one(t,depth=0):
  name,size,urls=t
  for u in urls:
    try: r=requests.get(u,headers=UA,timeout=20,allow_redirects=True)
    except Exception: continue
    if r.status_code!=200 or len(r.text)<500: continue
    h=r.text; found={}
    for k,p in PAT.items():
      m=set(re.findall(p,h))
      if m: found[k.rstrip('2')]=sorted(m)[:5]
    txt=html.unescape(re.sub(r'<script.*?</script>|<style.*?</style>','',h,flags=re.S|re.I))
    hits=[' '.join(re.sub(r'<[^>]+>',' ',x).split()) for x in STU.findall(txt)]
    hits=[x for x in hits if not re.search(r'student loan|internal|international|interface|internet',x,re.I)][:8]
    sub=[urljoin(r.url,a) for a in re.findall(r'href=["\']([^"\']+)["\']',h) if re.search(r'career|jobs|positions|join|משרות|דרושים',a,re.I) and not re.search(r'linkedin|facebook|twitter|instagram',a,re.I)][:6]
    if not found and not hits and sub and depth<1:  # landed on a homepage or a shell page: follow its careers link once
      deeper=one((name,size,sub[:3]),depth+1)
      if not deeper.get('error'): return deeper
    return dict(company=name,size=size,url=r.url,ats=found,hits=hits,textlen=len(re.sub(r'<[^>]+>','',txt)),sub=sub)
  return dict(company=name,size=size,url=urls[0],error=True)
with ThreadPoolExecutor(24) as ex: res=list(ex.map(one,targets))
json.dump(res,open(S+'/sites.json','w'),ensure_ascii=False)
import collections
print(len(res),'errors',sum(1 for r in res if r.get('error')),collections.Counter(k for r in res for k in r.get('ats',{})),'with student hits',sum(1 for r in res if r.get('hits')),file=sys.stderr)
