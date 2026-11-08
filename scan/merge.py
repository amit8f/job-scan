# merge all scan outputs, keep tech-looking student titles, diff against seen.json -> new_candidates.json
import json,re,sys,os,glob
S=sys.argv[1]; D=os.path.dirname(os.path.abspath(__file__))
STU=re.compile(r'student|intern\b|internship|interns\b|סטודנט|co-?op|trainee',re.I)
BAD=re.compile(r'\bQA\b|quality|NOC\b|help ?desk|IT support|support|customer|sales|marketing|\bHR\b|human resources|recruit|financ|account|legal|lawyer|משפט|שיווק|מכירות|כספים|חשבונ|גיוס|משאבי אנוש|רכש|procure|logistic|לוגיסט|admin|אדמינ|office|design|content|operations|תפעול|mechanic|מכונות|electrical|חשמל|industrial|תעשי|planner|פלנר|economic|lab tech|PhD|Doctoral|purchas|supply chain|payroll|tax|audit|ביטוח|test automation|בדיקות|תפ"?י|EHS|יצוא|מראיינ|aeronaut|אווירונאוט|NDI|materials|aeromech|EMC|servo',re.I)
allj=[]
for f in ['li_jobs.json','ats_jobs.json','ats2_jobs.json','wd_jobs.json','extra_jobs.json','tg_jobs.json','bigtech_jobs.json','public_jobs.json','goozali_jobs.json','hmt_jobs.json']:
  p=os.path.join(S,f)
  if os.path.exists(p): allj+=json.load(open(p))
T=re.compile(r'software|develop|engineer|data|algorithm|cyber|security|research|backend|full ?stack|embedded|AI\b|machine|תוכנה|פיתוח|אלגורית|סייבר|דאטה|מפתח|R&D|firmware|devops|analyst',re.I)
sp=os.path.join(S,'sites.json')
if os.path.exists(sp):
  for r in json.load(open(sp)):
    for h in r.get('hits',[]):
      h=' '.join(h.split())[:160]
      if T.search(h) and not re.search(r'href=|data-|class=|alt=|src=',h): allj.append(dict(src='site-text',company=r['company'],title=h,location='',url=r['url']))
def key(j):
  m=re.search(r'linkedin\.com/jobs/view/.*?(\d{8,})',j['url'])
  return ('li:'+m.group(1)) if m else (j['company']+'|'+j['title']+'|'+j['url']).lower()
seenp=os.path.join(D,'seen.json'); seen=set(json.load(open(seenp))) if os.path.exists(seenp) else set()
new=[]; 
for j in allj:
  k=key(j)
  if k in seen: continue
  seen.add(k)
  if STU.search(j['title']) and not BAD.search(j['title']): j['key']=k; new.append(j)
json.dump(new,open(os.path.join(S,'new_candidates.json'),'w'),ensure_ascii=False,indent=0)
if '--commit' in sys.argv: json.dump(sorted(seen),open(seenp,'w'))
print('total',len(allj),'new tech-student candidates',len(new))
