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
// Browser Back/Forward can restore this page from the back-forward cache without re-running
// the script. Normalize the embedded homepage chatbot whenever the homepage is restored.
function restoreHomepageGenie(){
  if(!isEventsHome||!chat)return;
  document.body.classList.remove('genie-mode');
  chat.classList.remove('fullscreen');
  chat.classList.add('open');
  pendingCommonQuestion='';
  if(body)body.replaceChildren();
  bubble(welcomeMessage,'bot');
  if(input)input.value='';
  if(sendButton)sendButton.disabled=false;
}
window.addEventListener('pageshow',restoreHomepageGenie);
window.addEventListener('popstate',()=>{
  if(window.location.pathname==='/'||window.location.pathname==='/index'){
    leaveGenie();
    restoreHomepageGenie();
  }
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
  const asksPersonalTimetable=/\b(my|our|personal)\b.{0,24}\b(timetable|schedule|class routine|periods)\b|\b(timetable|schedule)\b.{0,24}\b(for me|for my class)\b/.test(lowerMessage);
  const asksCommonDetail=commonQuestionTerms.some(term=>lowerMessage.includes(term))&&!eventContextTerms.some(term=>lowerMessage.includes(term))&&!hasActiveEventPage&&!asksPersonalTimetable;
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
  {terms:['digital campus','school portal','campus portal','student portal','portal'],url:'/portal',label:'Digital Campus'},
  {terms:['learning spaces','learning space','spaces built for curiosity','infrastructure','facilities','labs and library'],url:'/campus/infrastructure',label:'Learning Spaces & Infrastructure'},
  {terms:['student development','child development','student growth','holistic development'],url:'/campus/child-development',label:'Student Development'},
  {terms:['academic milestones','academic achievements','academic achievement','achievements','achievement','academic results','results','result','board results','icse','isc','jee','ap results'],url:'/academic-results',label:'Academic Achievements'},
  {terms:['education impact','impact of education','peace education'],url:'/campus/education-impact',label:'Education Impact'},
  {terms:['our founders','founders','founding vision'],url:'/campus/our-founders',label:'Our Founders'},
  {terms:['cms management','management','school management'],url:'/campus/management',label:'CMS Management'},
  {terms:['academic events','conference','conferences','mun','cmsmun','model united nations'],url:'/cmsmun',label:'CMSMUN'},
  {terms:['sports','sport','sports events','sporting events','spardha','concord','football','sports olympiad'],url:'/sports',label:'Sports'},
  {terms:['cultural','culture','cultural events','celesta','nazakat','arts','music','dance'],url:'/celesta',label:'Cultural Events / CELESTA'},
  {terms:['technova','tech nova','technology','innovation','robotics','artificial intelligence','ai event'],url:'/technova',label:'TECHNOVA'},
  {terms:['contact','contact us','phone','email'],url:'/contact',label:'Contact Us'},
  {terms:['about campus','about cms','about us','school information'],url:'/about',label:'About CMS'},
  {terms:['home','homepage','main page','all events'],url:'/?skipIntro=1',label:'CMS Events Homepage'}
];
function findCampusDestination(message){
  const q=message.toLowerCase().replace(/[^a-z0-9\s]/g,' ').replace(/\s+/g,' ').trim();

  // Mentioning a section is not the same as asking to navigate to it.
  // Informational questions must stay in chat and be answered by the chatbot API.
  const informationIntent=/^(what is|what are|tell me about|explain|describe|give me (?:information|details) about|show me information about|who is|when is|where is|how does|how do i know about)\b/.test(q);
  if(informationIntent)return null;

  // Recognise common natural-language requests to open a destination.
  const navigationIntent=/\b(go to|go|take me to|open|visit|navigate to|show me|where can i (?:see|find|open)|i want to (?:see|visit|open)|bring me to|redirect me to|let me see)\b/.test(q);
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


// Homepage-only event image previews. Images are reused from existing official event galleries.
(function initEventHoverPreviews(){
  const sources={
    celesta:{title:'CELESTA · EVENT PREVIEW',note:'Official CELESTA 2026 gallery',images:[
      'https://cmseducation.org/celesta/wp-content/uploads/sites/28/2026/04/ODYSSEY-02.webp',
      'https://cmseducation.org/celesta/wp-content/uploads/sites/28/elementor/thumbs/11-1-rlic3cn6dhuswbuspw00n1p3g1i7vet8jkyy17ngc0.webp',
      'https://cmseducation.org/celesta/wp-content/uploads/sites/28/elementor/thumbs/2-rlibteio1m8k0wazt375r22h48jdeqbi6cey6seg6o.webp',
      'https://cmseducation.org/celesta/wp-content/uploads/sites/28/elementor/thumbs/3-rlibtfgi8g9uci9mnllsbjtxpmeqmff8ih2fo2d20.webp'
    ]},
    cmsmun:{title:'CMSMUN · EVENT PREVIEW',note:'CMSMUN 2025 · previous edition',images:[
      'https://cmseducation.org/aliganj-campus-1/wp-content/uploads/sites/2/2025/08/SON08441.png',
      'https://cmseducation.org/aliganj-campus-1/wp-content/uploads/sites/2/2025/08/SON08505.png',
      'https://cmseducation.org/aliganj-campus-1/wp-content/uploads/sites/2/2025/08/DSC3624-1.png',
      'https://cmseducation.org/aliganj-campus-1/wp-content/uploads/sites/2/2025/08/DSC3688.png'
    ]}
  };
  if(!document.body.classList.contains('cms-homepage')||!window.matchMedia('(hover: hover) and (pointer: fine)').matches)return;
  let timer=null,index=0,activeCard=null,popup=null;
  const hide=()=>{if(timer)clearInterval(timer);timer=null;activeCard=null;if(popup){popup.classList.remove('is-visible');const old=popup;setTimeout(()=>old.remove(),190);popup=null;}};
  const show=card=>{
    const data=sources[card.dataset.preview];if(!data)return;
    if(activeCard===card)return;hide();activeCard=card;index=0;
    popup=document.createElement('div');popup.className='event-hover-preview';popup.setAttribute('role','status');
    const img=document.createElement('img');img.src=data.images[0];img.alt=data.title;img.loading='eager';
    const title=document.createElement('strong');title.textContent=data.title;
    const note=document.createElement('span');note.textContent=data.note+' · preview';
    popup.append(img,title,note);document.body.appendChild(popup);
    const rect=card.getBoundingClientRect(),width=Math.min(310,window.innerWidth-28);
    let left=Math.max(14,Math.min(window.innerWidth-width-14,rect.left+(rect.width-width)/2));
    let top=rect.top-190;if(top<12)top=Math.min(window.innerHeight-210,rect.bottom+12);
    popup.style.left=left+'px';popup.style.top=top+'px';requestAnimationFrame(()=>popup?.classList.add('is-visible'));
    timer=setInterval(()=>{if(!popup)return;index=(index+1)%data.images.length;img.src=data.images[index];},2400);
  };
  document.querySelectorAll('.home-event-card[data-preview]').forEach(card=>{
    card.addEventListener('mouseenter',()=>show(card));card.addEventListener('mouseleave',hide);
    card.addEventListener('focusin',()=>show(card));card.addEventListener('focusout',event=>{if(!card.contains(event.relatedTarget))hide();});
  });
  window.addEventListener('scroll',hide,{passive:true});window.addEventListener('resize',hide);
})();

// Interactive campus directory: switch the detail panel without pretending it is a geographic floor plan.
(function initCampusExplorer(){
  const descriptions={
    stem:'Explore hands-on learning through the Maker Space, Design & Technology Lab, Computer Lab and Studio Pod.',
    arts:'Discover creative and quiet spaces including the Music Room, Art Room and Library.',
    sport:'Explore the campus sports and wellbeing facilities: Basketball Court, Ground and Swimming Pool.',
    community:'Find shared campus spaces including Shux Courtyard, Reception Area, Waiting Lounge and inner corridors.'
  };
  const detail=document.getElementById('campusSpaceDetail');if(!detail)return;
  document.querySelectorAll('[data-space]').forEach(button=>button.addEventListener('click',()=>{
    document.querySelectorAll('[data-space]').forEach(item=>item.classList.toggle('is-active',item===button));
    detail.textContent=descriptions[button.dataset.space]||'';
  }));
})();



// Interactive homepage calendar: event dates open their published event details.
(function initHomepageEventCalendar(){
 const root=document.getElementById('homeEventCalendar');if(!root)return;
 const eventRanges=[
  {start:'2026-04-24',end:'2026-04-25',title:'CMSMUN · 5th Edition',dateLabel:'24–25 April 2026',category:'Academic Events & Conferences',description:'A Model United Nations experience focused on diplomacy, global affairs, committee discussions and policy. Explore the conference archive and its learning experience at CMS Aliganj Campus I.',href:'/cmsmun',venue:'CMS Aliganj Campus I'},
  {start:'2026-08-21',end:'2026-08-25',title:'CELESTA International 2026',dateLabel:'21–25 August 2026',category:'Arts, Culture & Creativity',description:'A cultural festival celebrating creativity and expression through art, music, dance and performance. Explore the CELESTA experience and its published festival highlights.',href:'/celesta',venue:'CMS Aliganj Campus I'},
  {start:'2026-10-24',end:'2026-10-27',title:'SPARDHA 2026',dateLabel:'24–27 October 2026',category:'Sports',description:'The International Sports Olympiad brings sporting disciplines and competition together, celebrating teamwork, participation and athletic achievement.',href:'/sports#spardha',venue:'CMS Aliganj Campus I'},
  {start:'2026-11-02',end:'2026-11-06',title:'CONCORD 2026',dateLabel:'2–6 November 2026',category:'Sports',description:'An international football tournament featuring boys’ and girls’ football, bringing teams together for competition and sporting exchange.',href:'/sports#concord',venue:'CMS Aliganj Campus I'},
  {start:'2026-11-19',end:'2026-11-20',title:'TECHNOVA 2026',dateLabel:'19–20 November 2026',category:'Technology & Innovation',description:'A technology and innovation event exploring robotics, artificial intelligence and computing through student creativity, experimentation and problem-solving.',href:'/technova',venue:'CMS Aliganj Campus I'}
 ];
 const monthLabel=document.getElementById('homeCalendarMonth'),daysNode=document.getElementById('homeCalendarDays'),details=document.getElementById('homeCalendarEventDetails');
 const today=new Date();today.setHours(0,0,0,0);let shownMonth=new Date(today.getFullYear(),today.getMonth(),1);
 const parseDate=value=>{const p=value.split('-').map(Number);return new Date(p[0],p[1]-1,p[2]);};
 const keyDate=date=>[date.getFullYear(),String(date.getMonth()+1).padStart(2,'0'),String(date.getDate()).padStart(2,'0')].join('-');
 const eventsFor=date=>{const selected=parseDate(date);return eventRanges.filter(event=>selected>=parseDate(event.start)&&selected<=parseDate(event.end));};
 function showDetails(date,button){
  const events=eventsFor(date);
  if(!events.length)return;
  const existing=root.querySelector('.home-calendar-event-popup');
  if(existing)existing.remove();
  const popup=document.createElement('div');popup.className='home-calendar-event-popup';popup.setAttribute('role','status');popup.textContent=events.map(event=>event.title).join(' · ');
  button.insertAdjacentElement('afterend',popup);
 }

 function render(){
  const year=shownMonth.getFullYear(),month=shownMonth.getMonth();
  monthLabel.textContent=shownMonth.toLocaleDateString('en-IN',{month:'long',year:'numeric'});
  const offset=new Date(year,month,1).getDay(),count=new Date(year,month+1,0).getDate(),cells=Math.ceil((offset+count)/7)*7;
  daysNode.replaceChildren();
  for(let i=0;i<cells;i++){
   const date=new Date(year,month,1-offset+i),inMonth=date.getMonth()===month,marked=eventsFor(keyDate(date)).length>0,button=document.createElement('button');
   button.type='button';button.className='home-calendar-day'+(!inMonth?' is-outside':'')+(date.getTime()===today.getTime()?' is-today':'')+(marked?' has-event':'');
   button.textContent=String(date.getDate());
   button.setAttribute('aria-label',date.toLocaleDateString('en-IN',{weekday:'long',day:'numeric',month:'long',year:'numeric'})+(marked?', event scheduled':''));
   button.setAttribute('aria-pressed','false');
   if(marked)button.title='Select to view event details';
   button.addEventListener('click',()=>{
    daysNode.querySelectorAll('.home-calendar-day').forEach(day=>day.setAttribute('aria-pressed','false'));
    button.setAttribute('aria-pressed','true');showDetails(keyDate(date),button);
   });
   daysNode.appendChild(button);
  }
 }
 document.getElementById('homeCalendarPrev').addEventListener('click',()=>{shownMonth=new Date(shownMonth.getFullYear(),shownMonth.getMonth()-1,1);root.querySelector('.home-calendar-event-popup')?.remove();render();});
 document.getElementById('homeCalendarNext').addEventListener('click',()=>{shownMonth=new Date(shownMonth.getFullYear(),shownMonth.getMonth()+1,1);details.hidden=true;render();});
 render();
})();
