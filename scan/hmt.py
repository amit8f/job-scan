# HireMe (hiremetech.com / juniors.hiremetech.com): Israeli aggregator that copies LinkedIn, ATS boards and
# defense sites (Rafael, IAI, Elbit) with full text. Public JSON, no login:
#   /api/jobs/search?job_level=student&israeli=true&posted_days=N&limit=100&page=P   (mixes juniors in; keep "Student / Intern")
#   /api/jobs/{id}  full description + requirements
# Employer names are hidden, so we infer them from the text (Rafael job numbers, Elta, Elbit...). Writes hmt_jobs.json.
import requests,json,re,sys,html,time,concurrent.futures as cf
S=sys.argv[1]; DAYS=int(sys.argv[2]) if len(sys.argv)>2 else 14
H={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) Chrome/126 Safari/537.36'}
API='https://hiremetech.com/api/jobs'
def get(u,**p):
  for k in range(3):
    try:
      r=requests.get(u,params=p,headers=H,timeout=40)
      if r.status_code==200: return r.json()
    except Exception: pass
    time.sleep(3)
  return None
jobs={}
for page in range(1,40):
  r=get(API+'/search',job_level='student',israeli='true',posted_days=DAYS,limit=100,page=page)
  if not r: break
  n=0
  for j in r['jobs']:
    if j['id'] not in jobs and j.get('job_level')=='Student / Intern': jobs[j['id']]=j; n+=1
  if not r['pagination'].get('has_more') or not r['jobs']: break
txt=lambda s: re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',html.unescape(s or '')))).strip()
COS=[(r'רפאל|rafael',"Rafael"),(r'אלתא|elta\b',"IAI (Elta)"),(r'התעשייה האווירית|\bIAI\b',"IAI"),(r'elbit|אלביט|Land & IMI|Aerospace division',"Elbit Systems"),
     (r'taboola|performance-driven advertising company',"Taboola"),(r'intuit',"Intuit"),(r'mobileye',"Mobileye"),(r'annapurna|amazon|\bAWS\b',"Amazon"),
     (r'microsoft',"Microsoft"),(r'nvidia',"NVIDIA"),(r'intel\b',"Intel"),(r'qualcomm',"Qualcomm"),(r'samsung',"Samsung"),(r'gong\b',"Gong")]
def detail(j):
  d=get(f"{API}/{j['id']}"); d=(d or {}).get('job') or j
  body=txt(d.get('description'))+' '+txt(d.get('requirements'))
  co=d.get('company_name') or next((c for p,c in COS if re.search(p,body,re.I)),'(hidden on HireMe)')
  url=f"https://hiremetech.com/job/{j['id']}"
  m=re.search(r'מספר משרה:?\s*(\d{4,6})',body)
  if co=='Rafael' and m: url=f'https://career.rafael.co.il/job/{m.group(1)}/'
  t=d['title'] if re.search(r'student|intern|סטודנט',d['title'],re.I) else d['title']+' (student)'
  loc=(d.get('location') or {}).get('basic',{}).get('city') or ''
  return dict(src='hiremetech',company=co,title=t,location=loc,url=url,hmt=f"https://hiremetech.com/job/{j['id']}",posted=d.get('posted_date'),desc=body[:4000])
with cf.ThreadPoolExecutor(6) as ex: out=list(ex.map(detail,jobs.values()))
json.dump(out,open(S+'/hmt_jobs.json','w'),ensure_ascii=False)
from collections import Counter
print('hiremetech',len(out),Counter(o['company'] for o in out).most_common(8),file=sys.stderr)
