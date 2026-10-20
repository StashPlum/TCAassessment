"""Browser walk of the auditor journey on a local demo: start, answer in Focus view, resume, Section/All views."""
import os, json
from playwright.sync_api import sync_playwright, expect
BASE='http://127.0.0.1:8000'; PW=os.environ['TCA_DEMO_PASSWORD']; OUT=os.environ.get('V3_OUT','output/v3-journey'); os.makedirs(OUT,exist_ok=True)
SITE='/sites/fictional-stage-one'
log=[];clicks=0
def step(msg):log.append(msg);print(msg)
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or None)
    for width,height in ((1440,900),(390,844)):
        ctx=b.new_context(viewport={'width':width,'height':height});page=ctx.new_page()
        page.goto(BASE+'/login/');page.fill('#id_username','auditor_demo');page.fill('#id_password',PW);page.click('form button')
        if width==1440:
            clicks=0
            page.goto(BASE+SITE+'/assessment/');clicks+=1  # Conduct assessment in the menu
            expect(page.get_by_role('heading',name='This version is approved and locked')).to_be_visible()
            page.screenshot(path=f'{OUT}/01-locked-{width}.png',full_page=True)
            page.get_by_role('button',name='Start new assessment').click();clicks+=1
            page.wait_for_load_state('networkidle')
            expect(page.locator('.focus-question')).to_be_visible()
            first=page.locator('.focus-meta .level-chip').inner_text();step(f'Focus view opened at {first}')
            page.screenshot(path=f'{OUT}/02-focus-empty-{width}.png',full_page=True)
            page.locator('.choice-yes span').click();clicks+=1
            expect(page.locator('.focus-form .save-state')).to_have_text('Saved',timeout=5000)
            step(f'Y saved with one selection; clicks from menu: {clicks}')
            page.screenshot(path=f'{OUT}/03-focus-yes-{width}.png',full_page=True)
            page.reload();expect(page.locator('.choice-yes input')).to_be_checked();step('Y retained after reload')
            page.get_by_role('link',name='Next question').click();page.wait_for_load_state('networkidle')
            page.locator('.choice-advisory span').click()
            expect(page.locator('[data-show-when=A]')).to_be_visible()
            page.fill('.focus-form textarea[name=advisory_follow_up]','FICTIONAL recheck label check next visit')
            page.wait_for_timeout(1500);expect(page.locator('.focus-form .save-state')).to_have_text('Saved',timeout=5000)
            step('Advisory with follow-up saved')
            page.get_by_role('link',name='Section').click();page.wait_for_load_state('networkidle')
            page.locator('.inline-answer').nth(2).locator('.choice-no span').click()
            expect(page.locator('.inline-answer').nth(2).locator('.save-state')).to_have_text('Saved',timeout=5000)
            page.locator('.inline-answer').nth(3).locator('.choice-yes span').click()
            expect(page.locator('.inline-answer').nth(3).locator('.save-state')).to_have_text('Saved',timeout=5000)
            step('Two inline answers in Section view saved in a row (shared revision)')
            page.screenshot(path=f'{OUT}/04-section-{width}.png',full_page=True)
            page.context.clear_cookies();page.goto(BASE+'/login/');page.fill('#id_username','auditor_demo');page.fill('#id_password',PW);page.click('form button')
            page.goto(BASE+SITE+'/assessment/');page.wait_for_load_state('networkidle')
            step('After logout/login Conduct resumes at '+page.locator('.focus-meta .level-chip').inner_text())
            page.get_by_role('link',name='All questions').click();page.wait_for_load_state('networkidle')
            checked=[page.locator('.inline-answer').nth(i).locator('input:checked').get_attribute('value') for i in range(4)]
            step(f'All questions view shows first four answers {checked}')
            page.screenshot(path=f'{OUT}/05-all-{width}.png',full_page=True)
        else:
            page.goto(BASE+SITE+'/assessment/?view=single');page.wait_for_load_state('networkidle')
            page.screenshot(path=f'{OUT}/06-focus-{width}.png',full_page=True)
            w=page.evaluate('document.documentElement.scrollWidth');step(f'390 px focus view document width {w}')
            page.get_by_role('link',name='Section').click();page.wait_for_load_state('networkidle')
            w=page.evaluate('document.documentElement.scrollWidth');step(f'390 px section view document width {w}')
            page.screenshot(path=f'{OUT}/07-section-{width}.png',full_page=True)
        ctx.close()
    b.close()
json.dump(log,open(f'{OUT}/journey.json','w'),indent=1)
