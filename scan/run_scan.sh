#!/bin/bash
# Daily scan. Usage: run_scan.sh <workdir>   (writes <workdir>/new_candidates.json)
set -u; W=$1; D=$(cd "$(dirname "$0")" && pwd); mkdir -p "$W"; cd "$W"
[ -d techmap ] || git clone -q --depth 1 https://github.com/mluggy/techmap techmap
D="$D" python3 - <<'P'
import json,glob
out=[]
for f in glob.glob('techmap/companies/*.json'):
  d=json.load(open(f))
  if d.get('isActive'): out.append({k:d.get(k) for k in ('name','size','careersUrl','comeetId','greenhouseId','leverId','breezyId','linkedinId','isMultinational')})
import os; X=os.environ.get('D','')+'/extra_companies.json'
if os.path.exists(X): out+=[{k:d.get(k) for k in ('name','size','careersUrl','comeetId','greenhouseId','leverId','breezyId','linkedinId','isMultinational')} for d in json.load(open(X))]
json.dump(out,open('companies.json','w'))
P
python3 "$D/ats.py" "$W" 2>ats.log
python3 "$D/wd.py" "$W" 2>wd.log
python3 "$D/wd2.py" "$W" "intel.wd1/External nvidia.wd5/NVIDIAExternalCareerSite marvell.wd1/MarvellCareers amat.wd1/External kla.wd1/Search hpe.wd5/Jobsathpe ptc.wd1/PTC medtronic.wd1/MedtronicCareers motorolasolutions.wd5/Careers cisco.wd5/Cisco_Careers nxp.wd3/careers salesforce.wd12/External_Career_Site philips.wd3/jobs-and-careers micron.wd1/External" 2>>wd.log
python3 "$D/extra.py" "$W" 2>extra.log
python3 "$D/tg.py" "$W" 2>tg.log
python3 "$D/bigtech.py" "$W" 2>bigtech.log
python3 "$D/public.py" "$W" 2>public.log
python3 "$D/goozali.py" "$W" 2>goozali.log
python3 "$D/hmt.py" "$W" 14 2>hmt.log
# every company's own careers page (techmap careersUrl + website/careers for size m+)
python3 "$D/sites.py" "$W" 2>sites.log
python3 "$D/ats2.py" "$W" 2>>sites.log
python3 "$D/wd2.py" "$W" "$(cat workday_sites.txt)" 2>>wd.log
MAXS=500 python3 "$D/li.py" li_jobs.json "student|intern|internship|סטודנט|סטודנטית|student position|משרת סטודנט|student software|student data|student security|student AI|student algorithm|student developer" 2>li.log
python3 "$D/merge.py" "$W" --commit
