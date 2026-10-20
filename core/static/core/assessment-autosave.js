/* Save draft responses in place; the server revision is the concurrency authority.
   One assessment revision is shared by every answer form on the page. */
const answerForms=[...document.querySelectorAll('form[data-assessment-autosave]')];
const unsaved=new Set();
window.addEventListener('beforeunload',event=>{if(unsaved.size){event.preventDefault();event.returnValue='';}});
const syncRevision=value=>answerForms.forEach(f=>{const input=f.querySelector('input[name="revision"]');if(input)input.value=value;});
const toggleConditional=form=>{
  const code=(form.querySelector('input[name="code"]:checked')||form.querySelector('select[name="code"]')||{}).value||'';
  form.querySelectorAll('[data-show-when]').forEach(el=>{el.hidden=el.dataset.showWhen!==code;});
};
answerForms.forEach(form=>{
  const state=form.querySelector('.save-state');
  let timer=null,inFlight=false,pending=false,generation=0,queuedSubmit=null,conflict=false;
  const show=(message,kind)=>{
    if(kind==='saved')unsaved.delete(form);else unsaved.add(form);
    if(state){state.textContent=message;state.dataset.dirty=kind==='dirty'?'true':'false';state.dataset.state=kind||'';}};
  toggleConditional(form);
  async function save(){
    if(inFlight){pending=true;return;}
    if(conflict)return;
    inFlight=true;pending=false;
    const sent=generation;
    show('Saving…','dirty');
    const data=new FormData(form);data.set('autosave','1');
    try{
      const response=await fetch(form.action||location.href,{method:'POST',body:data,credentials:'same-origin',headers:{'Accept':'application/json'}});
      const result=await response.json();
      if(response.ok&&result.saved){
        syncRevision(String(result.revision));
        if(generation===sent){show('Saved','saved');form.dispatchEvent(new CustomEvent('draftsaved',{detail:{message:'Saved.'}}));}
        else pending=true;
      }else{
        const first=Object.values(result.errors||{})[0];
        if(response.status===409){conflict=true;show('Someone else saved a change to this assessment. Your answer is still on screen — reload the page, check the latest answer and choose again.','error');}
        else show(`Not saved — ${Array.isArray(first)?first[0]:(result.error||'check the fields above')}. Your entry stays on screen; change it or try again.`,'error');
      }
    }catch(_error){show('Not saved — no connection. Your entry stays on screen and will be sent when you change it again.','error');}
    finally{
      inFlight=false;
      if(pending&&!conflict){pending=false;timer=setTimeout(save,350);}
      else if(queuedSubmit&&!conflict){const button=queuedSubmit;queuedSubmit=null;form.requestSubmit(button);}
    }
  }
  const changed=event=>{
    toggleConditional(form);generation+=1;clearTimeout(timer);
    // A choice saves at once; typing waits for a pause.
    timer=setTimeout(save,event.target.type==='radio'?0:850);
  };
  form.addEventListener('input',changed);form.addEventListener('change',event=>{if(event.target.type!=='radio')changed(event);});
  form.addEventListener('submit',event=>{
    clearTimeout(timer);
    if(inFlight){event.preventDefault();queuedSubmit=event.submitter;show('Finishing save…','dirty');}
  },true);
});
/* Keep the open question in the address so refresh returns to it instead of jumping ahead. */
const focusQuestion=document.querySelector('.focus-question[data-page]');
if(focusQuestion){const url=new URL(location.href);if(!url.searchParams.get('page')){url.searchParams.set('view','single');url.searchParams.set('page',focusQuestion.dataset.page);history.replaceState(null,'',url);}}
