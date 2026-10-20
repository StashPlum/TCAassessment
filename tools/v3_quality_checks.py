"""Phase 6 browser checks on a local demo: induced autosave failure and recovery, and page width per role at 1024/768/390."""
import os, json
from playwright.sync_api import sync_playwright, expect
BASE='http://127.0.0.1:8000'; PW=os.environ['TCA_DEMO_PASSWORD']; OUT=os.environ.get('V3_OUT','output/v3-quality'); os.makedirs(OUT,exist_ok=True)
SITE='/sites/fictional-stage-one'
ROLES=('auditor_demo','manager_demo','sensei_demo','team_demo','admin_demo')
result={'autosave':[],'widths':{}}
def login(page,user):
    page.goto(BASE+'/login/');page.fill('#id_username',user);page.fill('#id_password',PW);page.click('form button');page.wait_for_load_state('networkidle')
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or None)
    ctx=b.new_context(viewport={'width':1440,'height':900});page=ctx.new_page();login(page,'auditor_demo')
    page.goto(BASE+SITE+'/assessment/');page.wait_for_load_state('networkidle')
    if page.get_by_role('button',name='Start new assessment').count():
        page.get_by_role('button',name='Start new assessment').click();page.wait_for_load_state('networkidle')
    page.goto(BASE+SITE+'/assessment/?view=single');page.wait_for_load_state('networkidle')
    code=page.locator('.focus-meta .level-chip').inner_text()
    # Cut the connection for answer saves only.
    page.route('**/assessment/respond/**',lambda route:route.abort())
    page.locator('.choice-no span').click()
    state=page.locator('.focus-form .save-state')
    expect(state).to_contain_text('Not saved',timeout=5000)
    kept=page.locator('.choice-no input').is_checked()
    result['autosave'].append({'question':code,'offline_message':state.inner_text(),'answer_kept_on_screen':kept})
    page.screenshot(path=f'{OUT}/autosave-offline.png')
    page.unroute('**/assessment/respond/**')
    page.locator('.choice-yes span').click()
    expect(state).to_have_text('Saved',timeout=5000)
    page.reload();page.wait_for_load_state('networkidle')
    result['autosave'].append({'after_reconnect':state.inner_text() if state.count() else '','saved_answer_after_reload':'Y' if page.locator('.choice-yes input').is_checked() else 'other'})
    page.screenshot(path=f'{OUT}/autosave-recovered.png')
    ctx.close()
    for user in ROLES:
        for width in (1024,768,390):
            ctx=b.new_context(viewport={'width':width,'height':900});page=ctx.new_page();login(page,user)
            links=page.eval_on_selector_all('#main-navigation a',"els=>[...new Set(els.map(a=>a.getAttribute('href')))]")
            wide=[]
            for href in ['/']+[l for l in links if l and l.startswith('/') and 'logout' not in l]:
                page.goto(BASE+href);page.wait_for_load_state('networkidle')
                w=page.evaluate('document.documentElement.scrollWidth')
                if w>width: wide.append({'href':href,'width':w})
            result['widths'][f'{user}@{width}']={'pages':len(links)+1,'overflow':wide}
            ctx.close()
json.dump(result,open(f'{OUT}/quality.json','w'),indent=1)
print(json.dumps(result['autosave'],indent=1))
print({k:v for k,v in result['widths'].items() if v['overflow']} or 'no horizontal page overflow')
