(() => {
  'use strict';
  const form=document.querySelector('#worksheet-editor'); if(!form) return;
  const schema=JSON.parse(document.querySelector('#worksheet-schema').textContent);
  let payload=JSON.parse(document.querySelector('#worksheet-data').textContent);
  const links=JSON.parse(document.querySelector('#worksheet-links').textContent),canEdit=form.dataset.canEdit==='true';
  let revision=Number(form.dataset.revision),eventRevision=Number(form.dataset.eventRevision),timer,inflight=false,paused=false,dirty=false,showArchived=false,sequence=0;
  const undo=[],status=document.querySelector('#worksheet-save'),copy=v=>JSON.parse(JSON.stringify(v));
  const el=(tag,text,attrs={})=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,v));return n;};
  function remember(){undo.push(copy(payload));if(undo.length>50)undo.shift();}
  function change(){dirty=true;sequence++;status.textContent='Unsaved changes';form.dispatchEvent(new CustomEvent('draftdirty'));clearTimeout(timer);if(canEdit&&!paused)timer=setTimeout(save,900);list();}
  function field(spec,value,id,onChange){
    const wrap=el('div',undefined,{class:'field'}),label=el('label',spec.label,{for:id});let input;
    if(spec.type==='select'){input=el('select',undefined,{id});input.append(el('option','Choose',{value:''}));spec.choices.forEach(v=>input.append(el('option',v,{value:v})));}
    else input=el(spec.type==='textarea'?'textarea':'input',undefined,{id,...(spec.type==='textarea'?{rows:'3'}:{type:spec.type==='number'?'number':'text',...(spec.type==='number'?{step:'any'}:{})})});
    input.value=value??'';if(!canEdit)input.disabled=true;
    input.addEventListener('focus',()=>{input.dataset.original=input.value;});
    input.addEventListener('input',()=>{remember();onChange(input.value);change();});
    wrap.append(label,input);return wrap;
  }
  function render(){
    const meta=document.querySelector('#worksheet-meta');meta.replaceChildren();schema.meta.forEach(s=>meta.append(field(s,payload.meta[s.key],'meta-'+s.key,v=>payload.meta[s.key]=v)));
    const root=document.querySelector('#worksheet-rows');root.replaceChildren();
    if(schema.key==='affinity'){
      const groups=[...new Set(['',...(payload.meta.groups||'').split('\n'),...payload.rows.map(r=>r.group||'')])];
      const board=el('div',undefined,{class:'profile-cards'});
      groups.forEach(group=>{const zone=el('section',undefined,{class:'panel','aria-label':`Affinity group ${group||'Ungrouped'}`});zone.append(el('h3',group||'Ungrouped'),el('p','Drop a card here, or type this group in the card field. Keyboard moves use the group field.'));zone.addEventListener('dragover',e=>e.preventDefault());zone.addEventListener('drop',e=>{e.preventDefault();if(!canEdit)return;const row=payload.rows.find(r=>r.id===e.dataTransfer.getData('text/plain'));if(!row)return;remember();row.group=group;change();render();});board.append(zone);});root.append(board);
    }
    payload.rows.forEach((row,index)=>{
      if(row.archived&&!showArchived)return;
      const card=el('section',undefined,{class:'tool-row panel', 'data-row':row.id,draggable:canEdit?'true':'false'});
      card.append(el('h3',`Row ${index+1}${row.archived?' · archived':''}`),el('p',`ID: ${row.id}`,{class:'small muted'}));
      const grid=el('div',undefined,{class:'field-grid'});schema.fields.forEach(s=>grid.append(field(s,row[s.key],`row-${row.id}-${s.key}`,v=>row[s.key]=v)));card.append(grid);
      const actions=el('div',undefined,{class:'filter-actions'});
      [['Move up',()=>move(index,-1)],['Move down',()=>move(index,1)],[row.archived?'Restore row':'Archive row',()=>{remember();row.archived=!row.archived;change();render();}],['Add child / branch',()=>{remember();const child={id:crypto.randomUUID(),archived:false,parent:row.id,branch:row.branch||'New branch',category:row.category||''};payload.rows.splice(index+1,0,child);change();render();}]].forEach(([name,fn])=>{const b=el('button',name,{type:'button',class:'secondary'});b.disabled=!canEdit;b.onclick=fn;actions.append(b);});card.append(actions);
      card.addEventListener('dragstart',e=>e.dataTransfer.setData('text/plain',row.id));card.addEventListener('dragover',e=>e.preventDefault());
      card.addEventListener('drop',e=>{e.preventDefault();const from=payload.rows.findIndex(r=>r.id===e.dataTransfer.getData('text/plain'));if(from<0||!canEdit)return;remember();const moving=payload.rows.splice(from,1)[0];if(schema.key==='affinity')moving.group=row.group||'';payload.rows.splice(payload.rows.findIndex(r=>r.id===row.id),0,moving);change();render();});
      root.append(card);
    });
    document.querySelector('#tool-conclusion').value=payload.conclusion||'';document.querySelector('#include-a3').checked=payload.include_in_a3!==false;list();
  }
  function move(i,offset){const target=i+offset;if(target<0||target>=payload.rows.length)return;remember();[payload.rows[i],payload.rows[target]]=[payload.rows[target],payload.rows[i]];change();render();}
  function list(){const root=document.querySelector('#tool-list');root.replaceChildren();payload.rows.forEach((row,i)=>{const item=el('section');item.append(el('h3',`Row ${i+1}${row.archived?' · archived':''}`));schema.fields.forEach(s=>item.append(el('p',`${s.label}: ${row[s.key]??''}`)));root.append(item);});}
  function linkFields(){const root=document.querySelector('#worksheet-link-fields');Object.entries(links).forEach(([name,options])=>{const label=el('label',`Linked ${name}`),select=el('select',undefined,{multiple:'multiple',size:'4','aria-label':`Linked ${name}`});select.disabled=!canEdit;options.forEach(o=>{const option=el('option',`#${o.id} ${o.title||o.description||`${o.measure}: ${o.value} ${o.unit}`}`,{value:o.id});option.selected=(payload.links?.[name]||[]).map(String).includes(String(o.id));select.append(option);});select.addEventListener('change',()=>{remember();payload.links??={};payload.links[name]=[...select.selectedOptions].map(o=>Number(o.value));change();});label.append(select);root.append(label);});}
  async function save(restore){
    if(!canEdit||inflight||paused)return;clearTimeout(timer);inflight=true;const sent=sequence;status.textContent='Saving…';
    try{const response=await fetch(form.dataset.url,{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':form.querySelector('[name=csrfmiddlewaretoken]').value},body:JSON.stringify({revision,event_revision:eventRevision,...(restore!==undefined?{restore}:{payload})})});const data=await response.json();
      if(!response.ok){if(response.status===409)paused=true;status.textContent=data.error||'Save failed. Entries retained.';status.setAttribute('role','alert');return;}
      revision=data.revision;eventRevision=data.event_revision;form.dataset.eventRevision=eventRevision;
      if(restore!==undefined||sent===sequence){payload=data.payload;dirty=false;render();}
      const analysis=document.querySelector('#tool-analysis');analysis.replaceChildren(...data.analysis.messages.map(v=>el('p',v,{class:'notice'})),el('p',data.analysis.formula));
      if(data.analysis.correlation!==undefined)analysis.append(el('p',`Correlation r: ${data.analysis.correlation??'undefined'}; no causal conclusion.`));
      document.querySelector('#tool-visual').innerHTML=data.svg; // SVG generated and escaped exclusively by server.
      status.textContent=`Saved revision ${revision} · event r${eventRevision}${dirty?' · further edits pending':''}`;if(!dirty)form.dispatchEvent(new CustomEvent('draftsaved',{detail:{message:status.textContent},bubbles:true}));
    }catch(error){status.textContent='Network error. Entries retained; use Save now to retry.';status.setAttribute('role','alert');}
    finally{inflight=false;if(dirty&&sent!==sequence&&!paused)timer=setTimeout(save,900);}
  }
  form.addEventListener('submit',e=>{e.preventDefault();save();});
  document.querySelector('#add-tool-row').onclick=()=>{remember();payload.rows.push({id:crypto.randomUUID(),archived:false,...(schema.key==='ishikawa'?{category:(payload.meta.categories||'').split('\n')[0],state:'hypothesis'}:{})});change();render();};
  document.querySelector('#undo-tool-row').onclick=()=>{if(!undo.length)return;payload=undo.pop();change();render();};
  document.querySelector('#show-archived').onclick=()=>{showArchived=!showArchived;render();};
  document.querySelector('#tool-conclusion').addEventListener('input',e=>{remember();payload.conclusion=e.target.value;change();});
  document.querySelector('#include-a3').addEventListener('change',e=>{remember();payload.include_in_a3=e.target.checked;change();});
  document.querySelectorAll('.restore-worksheet').forEach(f=>f.addEventListener('submit',e=>{e.preventDefault();save(Number(f.querySelector('[name=restore]').value));}));
  window.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue='';}});
  render();linkFields();
})();
