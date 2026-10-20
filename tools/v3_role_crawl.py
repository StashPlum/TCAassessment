"""Read-only role crawl of the local baseline demo: landing, navigation, screen metrics, screenshots."""
import json, re, sys
from playwright.sync_api import sync_playwright
BASE='http://127.0.0.1:8000'; PW=__import__('os').environ['TCA_DEMO_PASSWORD']
ROLES=__import__('os').environ.get('V3_ROLES','auditor_demo,manager_demo,sensei_demo,team_demo,team_demo2,admin_demo').split(',')
OUT=__import__('os').environ.get('V3_OUT','output/v3-crawl')
METRICS="""() => {const vis=e=>{const r=e.getBoundingClientRect();const s=getComputedStyle(e);return r.width>0&&r.height>0&&s.visibility!='hidden'&&s.display!='none'};
const q=s=>[...document.querySelectorAll(s)].filter(vis);
const main=document.querySelector('main')||document.body;
const words=(main.innerText||'').split(/\\s+/).filter(Boolean).length;
return {title:document.title,h1:(document.querySelector('h1')||{}).innerText||'',
buttons:q('button, input[type=submit], a.btn, .button').length, links:q('main a').length, inputs:q('main input:not([type=hidden]), main select, main textarea').length,
forms:q('main form').length, words, tables:q('main table').length, details:document.querySelectorAll('main details').length,
docWidth:document.documentElement.scrollWidth, primary:q('.btn-primary, .button.primary, button.primary, .primary').length}}"""
def login(page,u):
    page.goto(BASE+'/login/'); page.fill('input[name=username]',u); page.fill('input[name=password]',PW)
    page.click('form button'); page.wait_for_load_state('networkidle'); page.wait_for_load_state('networkidle')
res={}
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=__import__('os').environ.get('CHROMIUM_PATH') or None)
    for u in ROLES:
        ctx=b.new_context(viewport={'width':1440,'height':900}); page=ctx.new_page(); login(page,u)
        r={'landing':page.url.replace(BASE,''),'landing_metrics':page.evaluate(METRICS)}
        page.screenshot(path=f'{OUT}/shots/{u}-landing-1440.png',full_page=True)
        nav=page.eval_on_selector_all('nav a, aside a, header a',"els=>els.map(a=>({t:a.innerText.trim().replace(/\\s+/g,' '),h:a.getAttribute('href')}))")
        seen=[];r['nav']=[]
        for n in nav:
            h=n['h']
            if not h or h.startswith('#') or h in seen or 'logout' in h or h.startswith('http'): continue
            seen.append(h); resp=page.goto(BASE+h if h.startswith('/') else h); page.wait_for_load_state('networkidle')
            m=page.evaluate(METRICS); m.update(label=n['t'],href=h,status=resp.status if resp else None)
            slug=re.sub(r'[^a-z0-9]+','-',h.lower()).strip('-') or 'root'
            page.screenshot(path=f'{OUT}/shots/{u}-{slug}-1440.png')
            r['nav'].append(m)
        ctx.close()
        ctx=b.new_context(viewport={'width':390,'height':844}); page=ctx.new_page(); login(page,u)
        r['mobile']=[]
        for m in r['nav']:
            page.goto(BASE+m['href']); page.wait_for_load_state('networkidle')
            r['mobile'].append({'href':m['href'],'docWidth':page.evaluate('document.documentElement.scrollWidth')})
        page.goto(BASE+r['landing']); page.screenshot(path=f'{OUT}/shots/{u}-landing-390.png')
        ctx.close(); res[u]=r; print(u,'done',len(r['nav']),'nav targets',file=sys.stderr)
    b.close()
json.dump(res,open(f'{OUT}/crawl.json','w'),indent=1)
