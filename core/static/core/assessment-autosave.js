/* Save draft responses in place; the server revision is the concurrency authority. */
document.querySelectorAll('form[data-assessment-autosave]').forEach(form=>{
  const state=form.querySelector('.save-state');
  const revision=form.querySelector('input[name="revision"]');
  let timer=null,inFlight=false,pending=false,generation=0,queuedSubmit=null,conflict=false;
  const show=message=>{if(state){state.textContent=message;state.dataset.dirty='true';}};
  async function save(){
    if(inFlight){pending=true;return;}
    if(conflict)return;
    inFlight=true;pending=false;
    const sent=generation;
    show('Saving draft…');
    const data=new FormData(form);data.set('autosave','1');
    try{
      const response=await fetch(form.action||location.href,{method:'POST',body:data,credentials:'same-origin',headers:{'Accept':'application/json'}});
      const result=await response.json();
      if(response.ok&&result.saved){
        revision.value=String(result.revision);
        if(generation===sent){form.dispatchEvent(new CustomEvent('draftsaved',{detail:{message:'Draft saved.'}}));}
        else pending=true;
      }else{
        const first=Object.values(result.errors||{})[0];
        show(response.status===409?'Another edit was saved. Reload and review before continuing.':
          `Save failed — ${Array.isArray(first)?first[0]:(result.error||'review the required fields')}`);
        if(response.status===409)conflict=true;
      }
    }catch(_error){show('Save failed — connection unavailable. Your entries remain on this page.');}
    finally{
      inFlight=false;
      if(pending&&!conflict){pending=false;timer=setTimeout(save,350);}
      else if(queuedSubmit&&!conflict){const button=queuedSubmit;queuedSubmit=null;form.requestSubmit(button);}
    }
  }
  const changed=()=>{generation+=1;clearTimeout(timer);timer=setTimeout(save,850);};
  form.addEventListener('input',changed);form.addEventListener('change',changed);
  form.addEventListener('submit',event=>{
    clearTimeout(timer);
    if(inFlight||timer){
      if(inFlight){event.preventDefault();queuedSubmit=event.submitter;show('Finishing draft save…');}
    }
  },true);
});
