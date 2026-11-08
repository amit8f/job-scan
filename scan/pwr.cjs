// browser load where every request is retried on 502 by fetching through Node
const { chromium } = require('playwright');
(async()=>{
  const b=await chromium.launch({proxy:{server:process.env.HTTPS_PROXY}});
  const ctx=await b.newContext({userAgent:'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'});
  const xhr=[];
  await ctx.route('**/*',async route=>{
    const req=route.request();
    if(/\.(png|jpg|jpeg|svg|woff2?|gif|webp|ico|mp4)(\?|$)/.test(req.url())||/google|facebook|clarity|hotjar|doubleclick/.test(req.url())) return route.abort();
    for(let i=0;i<5;i++){
      try{ const r=await route.fetch(); if(r.status()!==502&&r.status()!==503){ if(['xhr','fetch'].includes(req.resourceType())) xhr.push([req.method(),req.url(),req.postData(),(await r.text()).slice(0,+process.env.XL||300)]); return route.fulfill({response:r}); } }catch(e){}
      await new Promise(s=>setTimeout(s,1500));
    }
    return route.abort();
  });
  const p=await ctx.newPage();
  await p.goto(process.argv[2],{waitUntil:'networkidle',timeout:90000}).catch(e=>console.log('ERR',e.message));
  await p.waitForTimeout(+process.argv[3]||5000);
  if(process.env.SCROLL){for(let i=0;i<+process.env.SCROLL;i++){await p.mouse.wheel(0,4000);await p.waitForTimeout(1500);}}
  console.log(( await p.evaluate(()=>document.body.innerText)).slice(0,+process.argv[4]||3000));
  console.log('XHR'); xhr.forEach(x=>console.log(x.join(' | ')));
  if(process.env.LINKS){const links=await p.evaluate(()=>[...document.querySelectorAll('a')].map(a=>a.innerText.trim().replace(/\s+/g,' ')+' => '+a.href));console.log(links.join('\n'));}
  await b.close();
})();
