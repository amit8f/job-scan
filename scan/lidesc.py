import requests,re,html,json,sys,time
UA={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
def desc(url):
  jid=re.search(r'(\d{8,})',url).group(1)
  for t in range(4):
    r=requests.get(f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{jid}",headers=UA,timeout=30)
    if r.status_code==200: break
    time.sleep(4*(t+1))
  if r.status_code!=200: return dict(status=r.status_code)
  t=r.text
  closed=bool(re.search(r'No longer accepting applications',t))
  m=re.search(r'show-more-less-html__markup[^>]*>(.*?)</div>',t,re.S)
  d=m.group(1) if m else ''
  d=re.sub(r'<br\s*/?>|</p>|</li>|<li>','\n',d); d=html.unescape(re.sub(r'<[^>]+>','',d)); d=re.sub(r'\n\s*\n+','\n',d).strip()
  ap=re.search(r'"(https?://[^"]*?)"[^>]*>\s*Apply',t)
  return dict(status=200,closed=closed,desc=d,applyurl=re.search(r'code id="applyUrl"[^>]*>\s*<!--"(.*?)"',t,re.S).group(1) if re.search(r'code id="applyUrl"[^>]*>\s*<!--"(.*?)"',t,re.S) else '')
if __name__=='__main__':
  L=json.load(open(sys.argv[1]))
  for j in L:
    if 'desc' in j: continue
    j.update(desc(j['url'])); time.sleep(1.2)
    print(j['company'],j['title'],j.get('closed'),len(j.get('desc','')),file=sys.stderr)
  json.dump(L,open(sys.argv[2],'w'),ensure_ascii=False,indent=0)
