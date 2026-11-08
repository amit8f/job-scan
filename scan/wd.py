import requests,json,sys,re
from concurrent.futures import ThreadPoolExecutor
S=sys.argv[1]
T="""intel.wd1/External nvidia.wd5/NVIDIAExternalCareerSite dell.wd1/External marvell.wd1/MarvellCareers amat.wd1/External analogdevices.wd1/External broadcom.wd1/External_Career kla.wd1/Search qualcomm.wd5/External hp.wd5/ExternalCareerSite salesforce.wd12/External_Career_Site nokia.wd3/Nokia hpe.wd5/Jobsathpe motorolasolutions.wd5/Careers cadence.wd1/External_Careers mastercard.wd1/CorporateCareers medtronic.wd1/MedtronicCareers philips.wd3/jobs-and-careers ptc.wd1/PTC cyberark.wd1/CyberArk_Careers synopsys.wd1/Careers wd.wd5/WD_External micron.wd1/External tevapharm.wd3/TEVA abbvie.wd1/AbbVie_External_Careers jnj.wd5/JnJ nice.wd3/NICE_Careers citi.wd5/2 visa.wd5/Visa_Careers paypal.wd1/jobs ebay.wd5/apply autodesk.wd1/Ext Workday.wd5/Workday thermofisher.wd5/ThermoFisherCareers bmc.wd1/BMC_Careers zoominfo.wd1/ZoomInfo akamai.wd1/akamai_careers servicenow.wd1/ServiceNow_Careers adobe.wd5/external_experienced zebra.wd1/Zebra_External equifax.wd5/External sandisk.wd1/sandisk-careers hpe.wd5/ACJobSite agilent.wd5/Agilent_Careers keysight.wd5/Keysight cisco.wd5/Cisco_Careers redhat.wd5/jobs elbit.wd3/Elbit gm.wd5/Careers_GM stellantis.wd3/Stellantis lseg.wd3/Careers sap.wd3/SAP sonyglobal.wd1/SonyGlobalCareers gehc.wd5/GEHC_ExternalSite nxp.wd3/careers""".split()
UA={"User-Agent":"Mozilla/5.0","Content-Type":"application/json","Accept":"application/json"}
IL=re.compile(r'israel|tel[- ]?aviv|haifa|jerusalem|herzliya|herzlia|petah|petach|ra.?anana|be.?er|yokneam|yoqneam|kiryat|qiryat|ramat|hod|modiin|netanya|rehovot|caesarea|jerusalem|ISR|IL\b|Migdal|Or Akiva|Hadera|Kfar|Rosh|Holon|Airport City|Lod|Matam|Ra\'anana|Beersheba|Petah',re.I)
STU=re.compile(r'student|intern\b|internship|סטודנט',re.I)
out=[]
def one(t):
  ten,site=t.split('/'); tenant=ten.split('.')[0]
  base=f"https://{ten}.myworkdayjobs.com"
  api=f"{base}/wday/cxs/{tenant}/{site}/jobs"
  got=0
  for q in ("student israel","intern israel","student","סטודנט"):
    off=0
    while off<400:
      try: r=requests.post(api,json={"appliedFacets":{},"limit":20,"offset":off,"searchText":q},headers=UA,timeout=30)
      except Exception as e: print(t,'ERR',e,file=sys.stderr); return
      if r.status_code!=200: print(t,r.status_code,file=sys.stderr); return
      js=r.json(); posts=js.get('jobPostings',[])
      for p in posts:
        if not STU.search(p.get('title','')): continue
        loc=p.get('locationsText','')
        url=base+'/'+site+p.get('externalPath','')
        if not IL.search(loc):
          if 'Locations' in loc:
            try:
              d=requests.get(f"{base}/wday/cxs/{tenant}/{site}{p['externalPath']}",headers=UA,timeout=30).json()
              jp=d.get('jobPostingInfo',{})
              loc=jp.get('location','')+' '+' '.join(jp.get('additionalLocations',[]) or [])+' '+str(jp.get('country',{}).get('descriptor',''))
            except Exception: pass
          if not IL.search(loc): continue
        out.append(dict(src='workday',company=tenant,title=p['title'],location=loc,url=url,updated=p.get('postedOn','')))
        got+=1
      off+=20
      if len(posts)<20 or off>=js.get('total',0): break
  print(t,'ok',got,file=sys.stderr)
with ThreadPoolExecutor(8) as ex: list(ex.map(one,T))
d={}
for o in out: d[o['url']]=o
json.dump(list(d.values()),open(S+'/wd_jobs.json','w'),ensure_ascii=False,indent=0)
print(len(d),file=sys.stderr)
