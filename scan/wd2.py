import requests,json,sys,re
S=sys.argv[1]
T=sys.argv[2].split()
UA={"User-Agent":"Mozilla/5.0","Content-Type":"application/json","Accept":"application/json"}
STU=re.compile(r'student|intern\b|internship|סטודנט',re.I)
IL=re.compile(r'israel|tel[- ]?aviv|haifa|jerusalem|herzliya|herzlia|petah|petach|ra.?anana|be.?er|yokneam|yoqneam|kiryat|qiryat|ramat|hod|modiin|netanya|rehovot|caesarea|ISR|IL\b|Migdal|Or Akiva|Hadera|Kfar|Rosh|Holon|Airport City|Lod|Matam|Beersheba',re.I)
out=json.load(open(S+'/wd_jobs.json'))  # wd.py output, already Israel-filtered
def facets_find(fs):
  res=[]
  for f in fs:
    for v in f.get('values',[]):
      if 'values' in v:  # nested
        for vv in v['values']:
          if re.search('israel',vv.get('descriptor',''),re.I): res.append((v.get('facetParameter') or f['facetParameter'],vv['id']))
      elif re.search('israel',v.get('descriptor',''),re.I): res.append((f['facetParameter'],v['id']))
  return res
for t in T:
  try:
    ten,site=t.split('/'); tenant=ten.split('.')[0]; base=f"https://{ten}.myworkdayjobs.com"; api=f"{base}/wday/cxs/{tenant}/{site}/jobs"
    r=requests.post(api,json={"appliedFacets":{},"limit":20,"offset":0,"searchText":""},headers=UA,timeout=30)
    fl=facets_find(r.json().get('facets',[]))
    if not fl: print(t,'no israel facet',file=sys.stderr); continue
    # prefer a country facet; otherwise apply every Israel value of the first facet (city-level facets list each site)
    fp=next((p for p,_ in fl if 'country' in p.lower()),fl[0][0]); ids=[i for p,i in fl if p==fp]
    n=0;off=0;tot=None
    while True:
      r=requests.post(api,json={"appliedFacets":{fp:ids},"limit":20,"offset":off,"searchText":""},headers=UA,timeout=30).json()
      if tot is None: tot=r.get('total',0)
      ps=r.get('jobPostings',[])
      for p in ps:
        if STU.search(p.get('title','')):
          out.append(dict(src='workday',company=tenant,title=p['title'],location=p.get('locationsText',''),url=base+'/'+site+p['externalPath'],updated=p.get('postedOn',''),il=True)); n+=1
      off+=20
      if not ps or off>=tot: break
    print(t,fp,len(ids),'israel total',tot,'students',n,file=sys.stderr)
  except Exception as e: print(t,'ERR',e,file=sys.stderr)
# facet results can leak other countries when a tenant ignores the facet, so still require an Israeli place or a multi-location tag
d={o['url']:o for o in out if IL.search(o['location']) or (o.get('il') and re.search(r'\d+ Locations',o['location']))}
json.dump(list(d.values()),open(S+'/wd_jobs.json','w'),ensure_ascii=False,indent=0)
print(len(d),file=sys.stderr)
