# Goozali's public Airtable of open Israeli tech jobs (~34K rows, read like the browser does, no login) -> goozali_jobs.json
# Keeps student/intern/part-time rows discovered in the last 60 days, skipping fields you exclude.
import json,sys,subprocess,os,re,datetime
S=sys.argv[1]; D=os.path.dirname(os.path.abspath(__file__)); raw=S+'/goozali_raw.json'
subprocess.run([sys.executable,'-I',D+'/airtable_view.py','shrQBuWjXd0YgPqV6',raw],check=True,stdout=subprocess.DEVNULL)
t=json.load(open(raw))['data']['table']
col={c['name']:c for c in t['columns']}; cid={n:c['id'] for n,c in col.items()}
def ch(name,v):
  opts=col[name].get('typeOptions',{}).get('choices',{})
  return [opts[x]['name'] for x in (v if isinstance(v,list) else [v]) if x in opts] if v else []
SKIP={'Marketing','Customer Success','Finance','Sales','Business Development','QA','IT and System Administration','Operations','HR & Recruitment','Natural Science','Compliance, Legal & Policy','C-Level','UI/UX, Design & Content','Mechanical Engineering','Project Management'}
cut=(datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)-datetime.timedelta(days=60)).isoformat()
STU=re.compile(r'student|intern\b|internship|סטודנט',re.I); out=[]
for r in t['rows']:
  v={n:r['cellValuesByColumnId'].get(i) for n,i in cid.items()}
  scope=ch('Scope',v['Scope']); field=ch('Field',v['Field'])
  title=(v['Job Title'] or '').strip()
  if (v['Discovered'] or '')<cut or set(field)&SKIP: continue
  if not (set(scope)&{'Student','Internship'} or STU.search(title)): continue
  if not STU.search(title): title+=' (Student)'
  contact=', '.join(x for x in (v['Point of Contact'],v['Email'],v['Linkedin']) if x)
  out.append(dict(src='goozali',company=v['Company'] or '',title=title,location=', '.join(ch('Location',v['Location'])),url=v['Position Link'] or '',updated=(v['Posted'] or '')[:10],field=', '.join(field),contact=contact))
json.dump(out,open(S+'/goozali_jobs.json','w'),ensure_ascii=False); os.remove(raw)
print('goozali',len(out),file=sys.stderr)
