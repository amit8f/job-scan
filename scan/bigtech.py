# Big employers whose careers sites our other scanners miss: Microsoft (Eightfold), Apple,
# Check Point and Wix (SmartRecruiters), Oracle (HCM). Writes bigtech_jobs.json; merge.py filters titles.
import requests,json,re,sys,time
S=sys.argv[1]; out=[]
UA={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36","Accept":"application/json"}
def get(u,**kw):
  for k in range(3):
    try: return requests.get(u,headers=UA,timeout=40,**kw)
    except Exception as e: time.sleep(3)
  return None
try:  # Microsoft
  for st in range(0,200,10):
    r=get("https://apply.careers.microsoft.com/api/pcsx/search",params={"domain":"microsoft.com","query":"","location":"Israel","start":st})
    d=(r.json().get('data') or {}) if r else {}; ps=d.get('positions') or []
    for p in ps: out.append(dict(src='microsoft',company='Microsoft',title=p['name'],location='; '.join(p.get('locations',[])[:3]),url=f"https://apply.careers.microsoft.com/careers/job/{p['id']}",updated=time.strftime('%Y-%m-%d',time.gmtime(p.get('postedTs') or 0))))
    if len(ps)<10: break
except Exception as e: print('microsoft failed',e,file=sys.stderr)
try:  # Apple
  seen=set()
  for q in ('student','intern'):
    for pg in range(1,4):
      r=get("https://jobs.apple.com/en-il/search",params={"location":"israel-ISR","search":q,"page":pg})
      m=re.search(r'__staticRouterHydrationData\s*=\s*JSON\.parse\((".*?")\);',r.text if r else '',re.S)
      if not m: break
      acc=[]
      def walk(o):
        if isinstance(o,dict):
          if 'postingTitle' in o: acc.append(o)
          for v in o.values(): walk(v)
        elif isinstance(o,list):
          for v in o: walk(v)
      walk(json.loads(json.loads(m.group(1))))
      new=[p for p in acc if p.get('positionId') not in seen]
      for p in new:
        seen.add(p.get('positionId'))
        out.append(dict(src='apple',company='Apple',title=p['postingTitle'],location=', '.join(l.get('name','') for l in p.get('locations',[])),url=f"https://jobs.apple.com/en-il/details/{p['positionId']}/{p.get('transformedPostingTitle','')}",updated=(p.get('postDateInGMT') or '')[:10]))
      if not new: break
except Exception as e: print('apple failed',e,file=sys.stderr)
for slug,name in (('CheckPointSoftwareTechnologies2','Check Point'),('Wix2','Wix')):  # SmartRecruiters
  try:
    off=0
    while True:
      r=get(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings",params={"limit":100,"offset":off})
      d=r.json() if r else {}; c=d.get('content') or []
      for p in c:
        loc=p.get('location') or {}
        if (loc.get('country') or '').lower() in ('il','israel'): out.append(dict(src='smartrecruiters',company=name,title=p['name'],location=loc.get('city',''),url=f"https://jobs.smartrecruiters.com/{slug}/{p['id']}",updated=(p.get('releasedDate') or '')[:10]))
      off+=100
      if not c or off>=d.get('totalFound',0): break
  except Exception as e: print(name,'failed',e,file=sys.stderr)
try:  # Oracle
  r=get("https://eeho.fa.us2.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true&expand=requisitionList&finder=findReqs;siteNumber=CX_45001,limit=200,location=Israel")
  for x in (r.json()['items'][0]['requisitionList'] if r else []):
    out.append(dict(src='oracle',company='Oracle',title=x['Title'],location=x.get('PrimaryLocation',''),url=f"https://careers.oracle.com/jobs/#en/sites/jobsearch/job/{x['Id']}",updated=x.get('PostedDate','')))
except Exception as e: print('oracle failed',e,file=sys.stderr)
json.dump(out,open(S+'/bigtech_jobs.json','w'),ensure_ascii=False)
from collections import Counter
print('bigtech',len(out),dict(Counter(o['company'] for o in out)),file=sys.stderr)
