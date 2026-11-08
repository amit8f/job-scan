# Amazon, Elbit, Google student roles in Israel -> extra_jobs.json
import requests,re,json,sys,time,html
S=sys.argv[1]; out=[]
UA={"User-Agent":"Mozilla/5.0"}
STU=re.compile(r'student|intern\b|internship|סטודנט',re.I)
for q in ["student","intern"]:
  r=requests.get("https://www.amazon.jobs/en/search.json",params={"base_query":q,"country":"ISR","result_limit":100},headers=UA,timeout=60).json()
  for j in r.get('jobs',[]):
    if STU.search(j['title']): out.append(dict(src='amazon',company='Amazon',title=j['title'],location=j['normalized_location'],url='https://www.amazon.jobs'+j['job_path'],updated=j['posted_date'],desc=re.sub('<[^>]+>',' ',j.get('description','')+'\n'+j.get('basic_qualifications','')+'\n'+j.get('preferred_qualifications',''))[:4000]))
for t in range(6):
  try: E=requests.get("https://elbitsystemscareer.com/cron/jobs.json",headers=UA,timeout=60).json(); break
  except Exception: time.sleep(5); E=[]
def clean(s): s=html.unescape(html.unescape(s or '')); s=re.sub(r'<br\s*/?>|</div>|</p>|</li>','\n',s); return re.sub(r'\n\s*\n+','\n',re.sub(r'<[^>]+>','',s)).strip()
for j in E:
  if STU.search(j['jobTitle']): out.append(dict(src='elbit',company='Elbit Systems',title=j['jobTitle'],location=j.get('area') or '',url=f"https://elbitsystemscareer.com/jobs/ (job code {j['jobCode']})",updated=j['updateDate'],desc=clean(j['description'])[:4000]))
for q in ["student","intern"]:
  t=requests.get(f"https://www.google.com/about/careers/applications/jobs/results/?location=Israel&q={q}",headers=UA,timeout=60).text
  for s in set(re.findall(r'jobs/results/(\d+-[a-z0-9-]+)',t)):
    out.append(dict(src='google',company='Google',title=s.split('-',1)[1].replace('-',' '),location='Israel',url='https://www.google.com/about/careers/applications/jobs/results/'+s,updated=''))
# Gav-Yam Negev park board (Be'er Sheva companies, includes Rafael)
try:
  g=requests.get("https://careers.gavyam-negev.co.il/",headers=UA,timeout=60).text
  for u,d,t,c in re.findall(r'<a href="(/jobs/detail/[^"]+)"[^>]*>.*?<span>(\d\d/\d\d/\d{4})</span>.*?<h3[^>]*>\s*<span>(.*?)</span>\s*</h3>\s*<span>(.*?)</span>',g,re.S):
    t=html.unescape(t).strip()
    if STU.search(t): out.append(dict(src='gavyam',company=html.unescape(c).strip(),title=t,location="Be'er Sheva",url='https://careers.gavyam-negev.co.il'+u,updated=d))
except Exception as e: print('gavyam failed',e,file=sys.stderr)
# SecretTLV job board RSS (search "student"; "intern" matches "internal")
try:
  for pg in range(1,4):
    x=requests.get(f"https://jobs.secrettelaviv.com/search/student/feed/rss2/?paged={pg}",headers={"User-Agent":"curl/8.5.0"},timeout=60).text
    its=re.findall(r'<item>(.*?)</item>',x,re.S)
    if not its: break
    for it in its:
      g=lambda t:(re.search(rf'<{t}>(.*?)</{t}>',it,re.S) or [None,''])[1]
      t=html.unescape(g('title')).strip()
      if STU.search(t): out.append(dict(src='secrettlv',company='(see posting)',title=t,location='',url=g('link').strip(),updated=g('pubDate')[:16]))
except Exception as e: print('secrettlv failed',e,file=sys.stderr)
json.dump(out,open(S+'/extra_jobs.json','w'),ensure_ascii=False)
print('extra',len(out),file=sys.stderr)
