import requests,re,html,json,time,sys,urllib.parse
UA={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
kws=sys.argv[2].split("|") or ["student","intern","internship","סטודנט","סטודנטית","student position","משרת סטודנט","junior student","working student","השמת סטודנטים"]
seen={}
for kw in kws:
  for start in range(0,int(__import__("os").environ.get("MAXS","1000")),25):
    u="https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?"+urllib.parse.urlencode({"keywords":kw,"location":"Israel","geoId":"101620260","f_TPR":"r2592000","start":start})
    for t in range(4):
      r=requests.get(u,headers=UA,timeout=30)
      if r.status_code==200: break
      time.sleep(5*(t+1))
    if r.status_code!=200: print(kw,start,r.status_code,file=sys.stderr); break
    cards=r.text.split('<li')
    n=0
    for c in cards:
      m=re.search(r'href="(https://[a-z]+\.linkedin\.com/jobs/view/[^"?]+)',c)
      if not m: continue
      n+=1
      url=m.group(1); jid=re.search(r'-(\d+)$',url) or re.search(r'(\d+)',url)
      g=lambda p:(html.unescape(re.search(p,c,re.S).group(1)).strip() if re.search(p,c,re.S) else '')
      d=dict(title=g(r'base-search-card__title">(.*?)</h3>'),company=g(r'base-search-card__subtitle">.*?>(.*?)</a>') or g(r'base-search-card__subtitle">(.*?)</h4>'),
        location=g(r'job-search-card__location">(.*?)</span>'),date=g(r'datetime="([^"]+)"'),url=url,kw=kw)
      seen.setdefault(jid.group(1),d)
    print(kw,start,n,len(seen),file=sys.stderr)
    json.dump(list(seen.values()),open(sys.argv[1],'w'),ensure_ascii=False)
    if n==0: break
    time.sleep(1.5)
json.dump(list(seen.values()),open(sys.argv[1],'w'),ensure_ascii=False,indent=0)
