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
const welcomeMessage="Jai Jagat! I’m Campus Genie, your virtual guide to City Montessori School. Where would you like to go today? Try Academic Achievements, Sports, Cultural Events, CMSMUN, CELESTA, TECHNOVA or Contact Us.";
let pendingCommonQuestion="";
const commonQuestionTerms=["schedule","timetable","date","dates","timing","timings","venue","venues","location","locations","registration","register","deadline","last date"];
const eventContextTerms=["technova","celesta","cmsmun","mun","spardha","concord","icse","isc","jee","ap examination","quiz","robotics","football"];
const isEventsHome=document.body.classList.contains('cms-homepage');
document.getElementById('chatLaunch')?.addEventListener('click',()=>{
  chat?.classList.toggle('open');
  if(chat?.classList.contains('open'))input?.focus();
});

const leaveGenie=()=>{
  chat?.classList.remove('open','fullscreen');
};
document.getElementById('chatClose')?.addEventListener('click',leaveGenie);
// Returning from a destination with the browser Back button should show the homepage, not the open chat.
window.addEventListener('popstate',()=>{
  if(window.location.pathname==='/'||window.location.pathname==='/index')leaveGenie();
});

// Campus Genie is a fixed, full-screen experience; its header is not draggable.
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
  pendingCommonQuestion='';
  bubble(welcomeMessage,'bot');
  if(input)input.value='';
  if(sendButton)sendButton.disabled=false;
});
form?.addEventListener('submit',async event=>{
  event.preventDefault();const message=input?.value.trim();if(!message||!body)return;
  bubble(message,'user');input.value='';if(sendButton)sendButton.disabled=true;
  const lowerMessage=message.toLowerCase();
  if(pendingCommonQuestion){
    const contextualMessage=pendingCommonQuestion+' for '+message;
    pendingCommonQuestion='';
    await askCampusGenie(contextualMessage);
    return;
  }
  const hasActiveEventPage=["/technova","/celesta","/cmsmun"].includes(window.location.pathname);
  const asksCommonDetail=commonQuestionTerms.some(term=>lowerMessage.includes(term))&&!eventContextTerms.some(term=>lowerMessage.includes(term))&&!hasActiveEventPage;
  if(asksCommonDetail){
    pendingCommonQuestion=message;
    bubble('Which event are you asking about? Choose TECHNOVA, CELESTA, CMSMUN, SPARDHA, CONCORD, or Academic Achievements.','bot');
    if(sendButton)sendButton.disabled=false;
    input?.focus();
    return;
  }
  const destination=findCampusDestination(message);
  if(destination){
    bubble('Taking you to '+destination.label+'…','bot');
    setTimeout(()=>{leaveGenie();window.location.href=destination.url;},650);
    return;
  }
  await askCampusGenie(message);
});
async function askCampusGenie(message){
  const typing=showTyping();
  try{
    const response=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message,page_context:window.location.pathname})});
    if(!response.ok)throw new Error('Request failed');
    const data=await response.json();typing.remove();bubble(data.reply||'I could not prepare a response.', 'bot',data.table);
  }catch{typing.remove();bubble('The assistant is temporarily unavailable. Please try again.','bot');}
  finally{if(sendButton)sendButton.disabled=false;input?.focus();}
}
document.querySelectorAll('[data-prompt]').forEach(button=>button.addEventListener('click',()=>{
  if(input){input.value=button.dataset.prompt||'';form?.requestSubmit();}
}));

// Finish the CMS welcome animation without automatically opening the chatbot.
const intro=document.getElementById('cmsIntro');
if(intro){
  const skipIntro=new URLSearchParams(window.location.search).has('skipIntro');
  if(skipIntro){
    intro.remove();
  }else{
    const finishIntro=()=>{
      if(!intro.classList.contains('is-leaving')){
        intro.classList.add('is-leaving');
        setTimeout(()=>intro.remove(),750);
      }
    };
    document.getElementById('introSkip')?.addEventListener('click',finishIntro);
    if(window.matchMedia('(prefers-reduced-motion: reduce)').matches)setTimeout(finishIntro,500);
    else setTimeout(finishIntro,4600);
  }
}

// Campus Genie destination shortcuts: send visitors to real sections/pages in this site.
const campusDestinations=[
  {terms:['academic achievements','academic achievement','achievements','achievement','academic results','results','result','board results','icse','isc','jee','ap results'],url:'/academic-results',label:'Academic Achievements'},
  {terms:['academic events','conference','conferences','mun','cmsmun'],url:'/cmsmun',label:'CMSMUN'},
  {terms:['sports','sport','spardha','concord','football'],url:'/sports',label:'Sports'},
  {terms:['cultural','culture','celesta','arts','music','dance'],url:'/celesta',label:'Cultural Events / CELESTA'},
  {terms:['technova','technology','innovation','robotics','artificial intelligence'],url:'/technova',label:'TECHNOVA'},
  {terms:['contact','contact us','phone','email'],url:'/contact',label:'Contact Us'},
  {terms:['about','about us','school information'],url:'/about',label:'About CMS'},
  {terms:['home','homepage','main page','all events'],url:'/?skipIntro=1',label:'CMS Events Homepage'}
];
function findCampusDestination(message){
  const q=message.toLowerCase().replace(/[^a-z0-9\s]/g,' ').replace(/\s+/g,' ').trim();

  // Mentioning a section is not the same as asking to navigate to it.
  // Informational questions must stay in chat and be answered by the chatbot API.
  const informationIntent=/^(what is|what are|tell me about|explain|describe|give me (?:information|details) about|show me information about|who is|when is|where is|how does|how do i know about)\b/.test(q);
  if(informationIntent)return null;

  // Navigate only when the visitor clearly asks to open, visit, go to, or take
  // them to a section/page. This applies consistently to every destination below.
  const navigationIntent=/\b(go to|take me to|open|visit|navigate to|show me the page for|bring me to|redirect me to)\b/.test(q);
  if(!navigationIntent)return null;

  return campusDestinations.find(destination=>
    destination.terms.some(term=>q===term||q.includes(term))
  )||null;
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


// Homepage Campus Genie is embedded directly in the hero; other pages retain the floating globe launcher.
