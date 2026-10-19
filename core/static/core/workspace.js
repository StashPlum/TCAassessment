/* Native controls remain usable without JavaScript. No external services. */
document.body.classList.add('js');
const menu=document.getElementById('menu-toggle');
if(menu) menu.addEventListener('click',()=>{const expanded=menu.getAttribute('aria-expanded')!=='true';menu.setAttribute('aria-expanded',String(expanded));document.getElementById('main-navigation').classList.toggle('expanded',expanded);});
document.querySelectorAll('.nav-group').forEach(group=>group.addEventListener('toggle',()=>{if(group.open) document.querySelectorAll('.nav-group').forEach(other=>{if(other!==group) other.open=false;});}));
const country=document.getElementById('country-selector'),site=document.getElementById('site-selector');
if(country&&site){const filter=()=>{let first=null;Array.from(site.options).forEach(option=>{const matches=option.dataset.country===country.value;option.hidden=!matches;option.disabled=!matches;if(matches&&!first) first=option;});if(site.selectedOptions[0]?.disabled&&first) site.value=first.value;};country.addEventListener('change',filter);filter();}
const dirtyForms=new Set();
document.querySelectorAll('main form[method="post"]:not([data-no-dirty])').forEach(form=>{const state=document.createElement('div');state.className='save-state';state.setAttribute('role','status');state.textContent='No unsaved changes.';form.prepend(state);const dirty=()=>{dirtyForms.add(form);state.dataset.dirty='true';state.textContent='Unsaved changes — save before leaving this page.';};if(form.querySelector('.errorlist')){dirty();state.textContent='Save failed — entries retained. Correct the highlighted fields.';}form.addEventListener('input',dirty);form.addEventListener('change',dirty);form.addEventListener('draftdirty',dirty);form.addEventListener('draftsaved',event=>{dirtyForms.delete(form);state.dataset.dirty='false';state.textContent=event.detail?.message||'Draft saved.';});form.addEventListener('submit',event=>{if(event.defaultPrevented||form.hasAttribute('data-async-save')) return;dirtyForms.delete(form);state.dataset.dirty='false';state.textContent='Saving…';});});
document.querySelectorAll('[data-filter-form]').forEach(form=>form.addEventListener('submit',()=>{const button=form.querySelector('button:not(.secondary)');if(button) button.textContent='Applying…';}));
const leaveDialog=document.getElementById('leave-confirm');let pendingLeave=null;
const requestLeave=action=>{pendingLeave=action;leaveDialog.showModal();};
leaveDialog.querySelector('[data-keep-work]').addEventListener('click',()=>{pendingLeave=null;leaveDialog.close();});
leaveDialog.querySelector('[data-discard-work]').addEventListener('click',()=>{const action=pendingLeave;pendingLeave=null;dirtyForms.clear();leaveDialog.close();if(action) action();});
leaveDialog.addEventListener('cancel',()=>{pendingLeave=null;});
document.addEventListener('click',event=>{const link=event.target.closest('a[href]');if(!link||link.getAttribute('href').startsWith('#')||!dirtyForms.size) return;event.preventDefault();event.stopImmediatePropagation();requestLeave(()=>window.location.assign(link.href));},true);
document.querySelectorAll('[data-location-form],header form').forEach(form=>form.addEventListener('submit',event=>{if(dirtyForms.size){event.preventDefault();const submitter=event.submitter;requestLeave(()=>form.requestSubmit(submitter));}}));
window.addEventListener('beforeunload',event=>{if(dirtyForms.size){event.preventDefault();event.returnValue='';}});
