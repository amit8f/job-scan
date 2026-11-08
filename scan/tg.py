# Goozali public Telegram channels (read via t.me/s, no login) -> tg_jobs.json
import requests,re,html,json,sys,time
S=sys.argv[1]; UA={"User-Agent":"Mozilla/5.0"}; out=[]
CH=['hitechjobsisrael','hitechjobsdatascience','hitechjobsdata','hitechjobsjunior']
# other public channels with free-form posts: each post becomes one entry, title = its first lines
GEN=['secretjuniordevelopers','hitech_jobs_in_israel','TheMisrot','hightechforolims','israjobs','hitechjobsJerusalem']
CH+=GEN
def txt(m): return html.unescape(re.sub(r'<[^>]+>','',re.sub(r'<br\s*/?>','\n',m)))
for ch in CH:
  before=None
  for page in range(4):
    u=f'https://t.me/s/{ch}'+(f'?before={before}' if before else '')
    s=None
    for k in range(3):
      try: s=requests.get(u,headers=UA,timeout=40).text; break
      except Exception as e: time.sleep(4)
    if s is None: print('tg fail',ch,file=sys.stderr); break
    posts=re.findall(r'data-post="[^/]+/(\d+)"(.*?)(?=data-post="|\Z)',s,re.S)
    if not posts: break
    for pid,body in posts:
      dm=re.search(r'<time datetime="([^"]+)"',body); d=dm.group(1)[:10] if dm else ''
      for m in re.findall(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>',body,re.S):
        links=[html.unescape(l) for l in re.findall(r'href="([^"]+)"',m) if not l.startswith('https://t.me')]
        t=txt(m)
        chunks=m.split('•')[1:]
        if ch in GEN:
          one=' '.join(l.strip() for l in t.split('\n') if l.strip())[:220]
          if one: out.append(dict(src='tg:'+ch,title=one,company='(telegram '+ch+')',location='',url=links[0] if links else f'https://t.me/{ch}/{pid}',updated=d))
        elif chunks:
          for c in chunks:
            l=txt(c).split('\n')[0].strip(); hl=[html.unescape(x) for x in re.findall(r'href="([^"]+)"',c) if not x.startswith('https://t.me')]
            mm=re.match(r'(.+?)\s+—\s+(.+?)(?:\s+·\s+(.+))?$',l)
            if mm: out.append(dict(src='tg:'+ch,title=mm.group(1),company=mm.group(2),location=mm.group(3) or '',url=hl[0] if hl else f'https://t.me/{ch}/{pid}',updated=d))
        else:
          lines=[l.strip() for l in t.split('\n') if l.strip()]
          co=re.search(r'Company:\s*(.+)',t); lo=re.search(r'Location:\s*(.+)',t)
          if lines and co: out.append(dict(src='tg:'+ch,title=re.sub(r'^\W+','',lines[0]),company=co.group(1).strip(),location=(lo.group(1).strip() if lo else ''),url=links[0] if links else f'https://t.me/{ch}/{pid}',updated=d))
    before=min(int(p) for p,_ in posts); time.sleep(1)
json.dump(out,open(S+'/tg_jobs.json','w'),ensure_ascii=False)
print('tg',len(out),file=sys.stderr)
