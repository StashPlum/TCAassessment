"""Browser walk-through of the guided auditor journey on V3 (UX-31, V3-03). Needs a running local demo with the
V3 source imported (prepare_demo with TCA_V3_SOURCE) and TCA_DEMO_PASSWORD. Compares on-screen wording with the
private source at run time; no source wording is stored in this file or its output."""
import json, os, re, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from playwright.sync_api import sync_playwright
from core.v3_source import read_and_reconcile

BASE = os.environ.get('TCA_BASE', 'http://127.0.0.1:8000'); PW = os.environ['TCA_DEMO_PASSWORD']
OUT = os.environ.get('V33_OUT', 'docs/v33/evidence'); os.makedirs(OUT, exist_ok=True)
_, records, _ = read_and_reconcile(os.environ['TCA_V3_SOURCE'])
SITES = {'fictional-stage-one': 'TCA_v3_GROUP_02', 'fictional-matrix-pilot': 'TCA_v3_GROUP_12'}
norm = lambda text: re.sub(r'\s+', ' ', text).strip()
results = []

def check(name, ok, detail=''):
    results.append({'check': name, 'ok': bool(ok), 'detail': detail}); print(('PASS ' if ok else 'FAIL ') + name, detail)

def login(page, user):
    page.goto(BASE + '/login/'); page.fill('input[name=username]', user); page.fill('input[name=password]', PW)
    page.click('form button'); page.wait_for_load_state('networkidle')

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH', '/opt/pw-browsers/chromium'))
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    login(page, 'auditor_demo')
    for site, group in SITES.items():
        page.goto(f'{BASE}/sites/{site}/assessment/?view=single&page=1'); page.wait_for_load_state('networkidle')
        if page.locator('text=Start new assessment').count():
            page.click('text=Start new assessment'); page.wait_for_load_state('networkidle')
            page.goto(f'{BASE}/sites/{site}/assessment/?view=single&page=1')
        source = next(r for r in records if r['question_id'] == '01.01.C' and group in r['groups'])
        shown = norm(page.inner_text('.req-text'))
        check(f'{site}: 01.01.C shows the {group} variant exactly', shown == norm(source['requirement']), f"source record {source['master_order']}")
        others = [r for r in records if r['question_id'] == '01.01.C' and group not in r['groups']]
        check(f'{site}: no other 01.01.C variant shown', all(norm(o['requirement']) != shown for o in others))
        check(f'{site}: QuestionID shown without variant suffix', page.inner_text('.qid').strip() == '01.01.C')
        page.click('summary:has-text("What evidence is expected?")')
        check(f'{site}: evidence statement on demand', norm(page.inner_text('details[open].qc-panel')).endswith(norm(source['evidence'])[-60:]))
    site = 'fictional-stage-one'
    page.goto(f'{BASE}/sites/{site}/assessment/?view=single&page=1'); page.wait_for_load_state('networkidle')
    page.screenshot(path=f'{OUT}/auditor-focus-1440.png', full_page=True)
    clicks = 0
    page.click('label.seg-yes'); clicks += 1
    page.wait_for_selector('.focus-form .save-state:has-text("Saved")')
    page.fill('textarea[name=conclusion]', 'FICTIONAL demo conclusion: PPE observed at the gate.')
    page.wait_for_timeout(1500)
    check('Y saved with one selection', page.locator('.focus-form .save-state').inner_text().strip().startswith('Saved'), f'{clicks} selection')
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as handle:
        handle.write('FICTIONAL evidence note for the demo.'); evidence_file = handle.name
    page.click('summary:has-text("Attach evidence")')
    page.set_input_files('input[type=file]', evidence_file)
    page.check('input[name=accept]'); page.fill('input[name=reason]', 'FICTIONAL: checked on site')
    page.click('button:has-text("Attach to 01.01.C")'); page.wait_for_load_state('networkidle')
    check('evidence attached without leaving the question', '/assessment/' in page.url and page.inner_text('.qid').strip() == '01.01.C')
    check('evidence shows as accepted', 'All' in page.inner_text('.ev-meter') or 'accepted' in page.inner_text('.ev-meter'), page.inner_text('.ev-meter'))
    check('answer kept after attaching', page.locator('label.seg-yes input').is_checked())
    check('rail marks 01.01.C as Yes', page.locator('.rail-map .cell.s-yes').count() >= 1)
    page.click('a:has-text("Next unanswered")'); page.wait_for_load_state('networkidle')
    check('next unanswered opens the next open question', page.inner_text('.qid').strip() == '01.02.C', page.inner_text('.qid'))
    page.click('label.seg-advisory'); page.wait_for_selector('.focus-form .save-state:has-text("Saved")')
    check('Advisory shows its follow-up field', page.locator('[data-show-when=A]').is_visible())
    page.goto(f'{BASE}/sites/{site}/assessment/?view=section&category=1'); page.wait_for_load_state('networkidle')
    check('Section view shows the same Y', page.locator('form[action*="01.01.C"] input[value=Y]').first.is_checked())
    page.goto(f'{BASE}/sites/{site}/assessment/?view=all'); page.wait_for_load_state('networkidle')
    check('All questions view shows the same Advisory', page.locator('form[action*="01.02.C"] input[value=A]').first.is_checked())
    page.screenshot(path=f'{OUT}/auditor-all-1440.png')
    page.click('button:has-text("Sign out")'); page.wait_for_load_state('networkidle')
    login(page, 'auditor_demo')
    page.goto(f'{BASE}/sites/{site}/assessment/'); page.wait_for_load_state('networkidle')
    check('resume after logout opens the next open question', page.inner_text('.qid').strip() == '01.03.C', page.inner_text('.qid'))
    check('progress survives logout', '2' in page.inner_text('.answer-progress'))
    for width in (1024, 768, 390):
        page.set_viewport_size({'width': width, 'height': 900}); page.reload(); page.wait_for_load_state('networkidle')
        overflow = page.evaluate('document.documentElement.scrollWidth') - width
        check(f'focus view has no page overflow at {width}px', overflow <= 0, f'{overflow}px')
        page.screenshot(path=f'{OUT}/auditor-focus-{width}.png', full_page=True)
    browser.close()
json.dump(results, open(f'{OUT}/auditor-e2e.json', 'w'), indent=1)
print(f"{sum(r['ok'] for r in results)}/{len(results)} checks passed")
sys.exit(0 if all(r['ok'] for r in results) else 1)
