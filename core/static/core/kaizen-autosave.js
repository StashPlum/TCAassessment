(() => {
  const form=document.querySelector('[data-autosave-url]');if(!form) return;
  let timer=null,inflight=false,sequence=0,paused=false;const changedFields=new Map();
  const state=form.querySelector('.save-state');
  const errors=document.createElement('div');errors.className='autosave-errors';errors.setAttribute('role','alert');form.prepend(errors);
  const clearErrors=()=>{errors.replaceChildren();form.querySelectorAll('[data-autosave-error]').forEach(node=>{const field=form.elements.namedItem(node.dataset.field);if(field){field.removeAttribute('aria-invalid');const ids=(field.getAttribute('aria-describedby')||'').split(' ').filter(id=>id!==node.id);field.setAttribute('aria-describedby',ids.join(' '));}node.remove();});};
  const save=async()=>{
    if(inflight||paused) return;inflight=true;const started=sequence;
    state.textContent='Saving draft…';const buttons=Array.from(form.querySelectorAll('button'));buttons.forEach(button=>button.disabled=true);
    const sentFields=new Map(changedFields),fullData=new FormData(form),payload=new FormData();
    ['csrfmiddlewaretoken','revision',...sentFields.keys()].forEach(key=>fullData.getAll(key).forEach(value=>payload.append(key,value)));
    try{
      const response=await fetch(form.dataset.autosaveUrl,{method:'POST',body:payload,credentials:'same-origin',headers:{'X-Requested-With':'XMLHttpRequest'}});
      const result=await response.json();clearErrors();
      if(!response.ok){
        if(response.status===409) paused=true;
        const message=result.message||'Save failed. Correct the highlighted fields, then retry. Your entries are retained.';
        errors.textContent=message;state.textContent='Not saved — entries retained.';
        Object.entries(result.errors||{}).forEach(([key,items])=>{const field=form.elements.namedItem(key);const text=items.map(item=>item.message).join(' ');if(field){const error=document.createElement('span');error.dataset.autosaveError='true';error.dataset.field=key;error.id=field.id+'-autosave-error';error.textContent=text;field.setAttribute('aria-invalid','true');field.setAttribute('aria-describedby',((field.getAttribute('aria-describedby')||'')+' '+error.id).trim());field.closest('.field')?.append(error);if(field.closest('details')) field.closest('details').open=true;}else{const p=document.createElement('p');p.textContent=text;errors.append(p);}});
        return;
      }
      document.querySelectorAll('input[name="revision"],input[name="event_revision"]').forEach(input=>input.value=result.revision);
      document.querySelectorAll('[data-revision-display]').forEach(node=>node.textContent='revision '+result.revision);
      document.querySelectorAll('[data-saved-display]').forEach(node=>node.textContent='saved '+new Date(result.saved_at).toLocaleString());
      document.querySelectorAll('[data-event-status]').forEach(node=>node.textContent=result.status);
      document.querySelectorAll('[data-local-status]').forEach(node=>node.textContent=result.local_status==='closed'?'Locally closed':'Open');
      sentFields.forEach((version,key)=>{if(changedFields.get(key)===version) changedFields.delete(key);});
      if(sequence===started) form.dispatchEvent(new CustomEvent('draftsaved',{detail:{message:'Draft saved at '+new Date(result.saved_at).toLocaleTimeString()}}));
      else {state.textContent='New edits pending…';timer=setTimeout(save,900);}
    }catch(error){errors.textContent='Connection or save failed. Your entries are retained. Use Save now to retry.';state.textContent='Not saved — retry required.';}
    finally{inflight=false;buttons.forEach(button=>button.disabled=false);}
  };
  const schedule=event=>{sequence++;if(event.target.name) changedFields.set(event.target.name,sequence);clearTimeout(timer);if(!paused) timer=setTimeout(save,900);};
  form.addEventListener('input',schedule);form.addEventListener('change',schedule);
  form.addEventListener('submit',event=>{clearTimeout(timer);if(inflight){event.preventDefault();state.textContent='Wait for the current draft save, then retry your action.';}},true);
})();
