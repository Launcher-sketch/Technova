// CMS / TECHNOVA site interactions
const search=document.getElementById('search');
const cards=[...document.querySelectorAll('.event-card')];
const dateFilter=document.getElementById('dateFilter');
let category='All';
function filterCards(){
  const q=(search?.value||'').toLowerCase().trim();
  const date=dateFilter?.value||'All';
  cards.forEach(card=>{
    const categoryMatch=category==='All'||card.dataset.category===category;
    const dateMatch=date==='All'||card.dataset.date===date;
    const searchMatch=(card.dataset.search||'').includes(q);
    card.hidden=!(categoryMatch&&dateMatch&&searchMatch);
  });
}
document.querySelectorAll('.filter').forEach(btn=>btn.addEventListener('click',()=>{
  document.querySelector('.filter.active')?.classList.remove('active');
  btn.classList.add('active');category=btn.dataset.filter;filterCards();
}));
search?.addEventListener('input',filterCards);
dateFilter?.addEventListener('change',filterCards);

// Event details dialog
const modal=document.getElementById('eventModal');
const closeModal=()=>{if(modal){modal.classList.remove('open');modal.setAttribute('aria-hidden','true');}};
document.querySelectorAll('.event-details').forEach(button=>button.addEventListener('click',()=>{
  if(!modal)return;
  const fields={modalTitle:'name',modalSummary:'summary',modalCategory:'category',modalDate:'date',modalVenue:'venue',modalTeacher:'teacher'};
  Object.entries(fields).forEach(([id,key])=>{const node=document.getElementById(id);if(node)node.textContent=button.dataset[key]||'To be announced';});
  modal.classList.add('open');modal.setAttribute('aria-hidden','false');
  modal.querySelector('.modal-close')?.focus();
}));
modal?.querySelectorAll('[data-modal-close]').forEach(node=>node.addEventListener('click',closeModal));
document.addEventListener('keydown',event=>{if(event.key==='Escape')closeModal();});

// Chatbot: restart, typing indicator, duplicate-submit prevention and readable tables
const chat=document.getElementById('chat');
const body=document.getElementById('chatBody');
const input=document.getElementById('chatInput');
const form=document.getElementById('chatForm');
const sendButton=form?.querySelector('button[type="submit"],button:not([type])');
const welcomeMessage="Jai Jagat! I’m the CMS AI Assistant. Ask me about CMS, TECHNOVA 2026, or CELESTA cultural events.";
document.getElementById('chatLaunch')?.addEventListener('click',()=>chat?.classList.toggle('open'));

document.getElementById('chatClose')?.addEventListener('click',()=>chat?.classList.remove('open'));

// Drag the chatbot anywhere by its title bar; keep the whole panel in view.
const chatHead=chat?.querySelector('.chat-head');
if(chat&&chatHead){
  let drag=null;
  chatHead.addEventListener('pointerdown',event=>{
    if(event.target.closest('button')||event.button!==0)return;
    const rect=chat.getBoundingClientRect();
    drag={x:event.clientX,y:event.clientY,left:rect.left,top:rect.top};
    chat.style.left=rect.left+'px';
    chat.style.top=rect.top+'px';
    chat.style.right='auto';
    chat.style.bottom='auto';
    chatHead.setPointerCapture(event.pointerId);
    chat.classList.add('is-dragging');
    event.preventDefault();
  });
  chatHead.addEventListener('pointermove',event=>{
    if(!drag)return;
    const maxLeft=Math.max(0,window.innerWidth-chat.offsetWidth);
    const maxTop=Math.max(0,window.innerHeight-chat.offsetHeight);
    const left=Math.min(maxLeft,Math.max(0,drag.left+event.clientX-drag.x));
    const top=Math.min(maxTop,Math.max(0,drag.top+event.clientY-drag.y));
    chat.style.left=left+'px';
    chat.style.top=top+'px';
  });
  const stopDragging=event=>{
    if(!drag)return;
    drag=null;
    chat.classList.remove('is-dragging');
    if(chatHead.hasPointerCapture(event.pointerId))chatHead.releasePointerCapture(event.pointerId);
  };
  chatHead.addEventListener('pointerup',stopDragging);
  chatHead.addEventListener('pointercancel',stopDragging);
  window.addEventListener('resize',()=>{
    if(!chat.style.left||!chat.style.top)return;
    const rect=chat.getBoundingClientRect();
    chat.style.left=Math.min(Math.max(0,window.innerWidth-chat.offsetWidth),rect.left)+'px';
    chat.style.top=Math.min(Math.max(0,window.innerHeight-chat.offsetHeight),rect.top)+'px';
  });
}
function bubble(text,kind,tableData){
  const p=document.createElement('p');p.className=kind;p.textContent=text;body?.appendChild(p);
  if(tableData&&Array.isArray(tableData.headers)&&Array.isArray(tableData.rows)){
    const wrap=document.createElement('div');wrap.className='chat-table-wrap';
    const table=document.createElement('table');table.className='chat-table';
    const thead=document.createElement('thead');const hr=document.createElement('tr');
    tableData.headers.forEach(value=>{const th=document.createElement('th');th.textContent=value;hr.appendChild(th);});
    thead.appendChild(hr);table.appendChild(thead);
    const tbody=document.createElement('tbody');
    tableData.rows.forEach(row=>{const tr=document.createElement('tr');row.forEach(value=>{const td=document.createElement('td');td.textContent=value;tr.appendChild(td);});tbody.appendChild(tr);});
    table.appendChild(tbody);wrap.appendChild(table);body.appendChild(wrap);
  }
  if(body)body.scrollTop=body.scrollHeight;
}
function showTyping(){
  const node=document.createElement('div');node.className='chat-typing';node.setAttribute('role','status');node.setAttribute('aria-label','Assistant is typing');
  for(let i=0;i<3;i++)node.appendChild(document.createElement('span'));
  body?.appendChild(node);if(body)body.scrollTop=body.scrollHeight;return node;
}
document.getElementById('chatRestart')?.addEventListener('click',()=>{
  if(body)body.replaceChildren();
  bubble(welcomeMessage,'bot');
  if(input)input.value='';
  if(sendButton)sendButton.disabled=false;
});
form?.addEventListener('submit',async event=>{
  event.preventDefault();const message=input?.value.trim();if(!message||!body)return;
  bubble(message,'user');input.value='';if(sendButton)sendButton.disabled=true;
  const typing=showTyping();
  try{
    const response=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message})});
    if(!response.ok)throw new Error('Request failed');
    const data=await response.json();typing.remove();bubble(data.reply||'I could not prepare a response.', 'bot',data.table);
  }catch{typing.remove();bubble('The assistant is temporarily unavailable. Please try again.','bot');}
  finally{if(sendButton)sendButton.disabled=false;input?.focus();}
});
document.querySelectorAll('[data-prompt]').forEach(button=>button.addEventListener('click',()=>{
  if(input){input.value=button.dataset.prompt||'';form?.requestSubmit();}
}));

// CMS intro is present only on the homepage
const intro=document.getElementById('cmsIntro');
if(intro){
  const finishIntro=()=>{if(!intro.classList.contains('is-leaving')){intro.classList.add('is-leaving');setTimeout(()=>intro.remove(),750);}};
  document.getElementById('introSkip')?.addEventListener('click',finishIntro);
  if(window.matchMedia('(prefers-reduced-motion: reduce)').matches)setTimeout(finishIntro,500);
  else setTimeout(finishIntro,4600);
}

// Live TECHNOVA countdown based on the published local start date
const countdown=document.getElementById('eventCountdown');
if(countdown){
  const start=new Date(countdown.dataset.start).getTime();
  const fields={days:document.getElementById('countDays'),hours:document.getElementById('countHours'),minutes:document.getElementById('countMinutes'),seconds:document.getElementById('countSeconds')};
  const pad=n=>String(n).padStart(2,'0');
  const tick=()=>{
    const remaining=start-Date.now();
    if(remaining<=0){countdown.innerHTML='<p class="countdown-live">TECHNOVA 2026 IS UNDERWAY</p>';return false;}
    const values={days:Math.floor(remaining/86400000),hours:Math.floor(remaining%86400000/3600000),minutes:Math.floor(remaining%3600000/60000),seconds:Math.floor(remaining%60000/1000)};
    Object.keys(values).forEach(key=>{if(fields[key])fields[key].textContent=pad(values[key]);});
    return true;
  };
  if(tick()){const timer=setInterval(()=>{if(!tick())clearInterval(timer);},1000);}
}
