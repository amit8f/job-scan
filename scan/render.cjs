// Render careers pages in headless Chromium; record hiring-system requests/links and student mentions.
// usage: node render.cjs targets.json out.json
const { chromium } = require('playwright'); const fs=require('fs');
const T=JSON.parse(fs.readFileSync(process.argv[2])); const OUT=process.argv[3];
const ATS=/comeet\.co|greenhouse\.io|lever\.co|ashbyhq|smartrecruiters|workable|breezy\.hr|bamboohr|recruitee|myworkdayjobs|teamtailor|hibob|jobvite|icims|successfactors|niloosoft|hunterhrms|adamtotal|taleo|eightfold|phenom|avature|oracle.*hcm|polymer|pinpoint|personio|freshteam|jazzhr|rippling/i;
const STU=/[^\n]{0,80}(\bstudent\b|\bintern\b|internship|סטודנט)[^\n]{0,80}/ig;
(async()=>{
  const b=await chromium.launch(process.env.HTTPS_PROXY?{proxy:{server:process.env.HTTPS_PROXY}}:{});
  const res=[]; let i=0;
  async function worker(){
    while(i<T.length){
      const t=T[i++]; const ctx=await b.newContext({userAgent:'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'});
      const p=await ctx.newPage(); const ats=new Set();
      await ctx.route('**/*',r=>/\.(png|jpe?g|gif|webp|svg|woff2?|mp4|ico)(\?|$)/.test(r.request().url())?r.abort():r.continue());
      p.on('request',r=>{const u=r.url(); if(ATS.test(u)) ats.add(u.slice(0,200));});
      const out={company:t.company,size:t.size,url:t.url,ats:[],hits:[],links:[]};
      try{
        await p.goto(t.url,{waitUntil:'domcontentloaded',timeout:20000}); await p.waitForTimeout(4000);
        const txt=await p.evaluate(()=>document.body?document.body.innerText:'');
        const links=await p.evaluate(()=>[...document.querySelectorAll('a,iframe')].map(a=>(a.innerText||'').trim().replace(/\s+/g,' ').slice(0,100)+' => '+(a.href||a.src)));
        out.hits=[...new Set((txt.match(STU)||[]).map(s=>s.trim()))].slice(0,10);
        out.links=links.filter(l=>ATS.test(l)||/student|intern|סטודנט/i.test(l)).slice(0,30);
        out.textlen=txt.length;
      }catch(e){out.error=String(e).slice(0,100);}
      out.ats=[...ats].slice(0,20); res.push(out); await ctx.close().catch(()=>{});
      if(res.length%50==0){fs.writeFileSync(OUT,JSON.stringify(res));console.error(res.length);}
    }
  }
  await Promise.all(Array.from({length:+(process.env.CONC||12)},worker));
  fs.writeFileSync(OUT,JSON.stringify(res)); await b.close(); console.error('done',res.length);
})();
