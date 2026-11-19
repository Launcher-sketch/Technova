/* Campus Portal demo: role-aware, interactive and intentionally sample-only. */
const roles={
 student:{label:"STUDENT WORKSPACE",name:"Good morning, Aarav",desc:"Your learning day, organised in one place.",avatar:"A",stats:[["Attendance","96%","Sample metric"],["Assignments","04","2 due soon"],["Average score","88%","Sample metric"],["Achievements","06","Portfolio items"]],title:"Today's timetable",items:[["08:00","Mathematics","Room 204 · Ms. Sharma"],["09:00","Physics","Lab 2 · Mr. Khan"],["10:15","English Literature","Room 108 · Ms. Das"],["11:15","Computer Science","Lab 1 · Mr. Mehta"]],quick:[["🗓️","My timetable"],["✓","Assignments"],["🏅","My achievements"],["🪪","Digital ID"]],suggest:["Show my assignments","Show upcoming events","Open my digital ID"],modules:[["Assignment Manager","✓","Track sample tasks, due dates and submission status."],["Digital Student ID","🪪","View a clearly marked sample student identity card."],["Achievement Portfolio","🏅","Explore sample certificates, projects and competition highlights."],["School Calendar","🗓️","Browse sample academic dates and campus events."]]},
 teacher:{label:"TEACHER WORKSPACE",name:"Welcome, Ms. Sharma",desc:"Your classes, tasks and teaching day at a glance.",avatar:"S",stats:[["Classes today","5","Sample schedule"],["Students","142","Demo figure"],["Assignments","12","Sample queue"],["Attendance","94%","Sample metric"]],title:"Today's teaching plan",items:[["08:00","Class 9A · Mathematics","Algebra · Room 204"],["09:00","Class 10B · Mathematics","Geometry · Room 210"],["10:30","Class 8C · Mathematics","Fractions · Room 105"],["12:00","Faculty planning","Staff room"]],quick:[["✓","Mark attendance"],["✎","Create assignment"],["📝","Class overview"],["📣","Class notice"]],suggest:["Show my classes today","Show assignments to review","Draft a class notice"],modules:[["Class Overview","👥","Review sample classes, sections and daily teaching schedule."],["Assignment Manager","✓","Create and review demonstration assignments."],["Lesson Planner","📚","Organise sample lesson topics and classroom resources."],["Notice Publisher","📣","Preview a notice before a real school-authorised publishing workflow."]]},
 parent:{label:"PARENT WORKSPACE",name:"Welcome, Mrs. Mehta",desc:"A clear view of your child's school journey.",avatar:"M",stats:[["Attendance","96%","Sample metric"],["Assignments","3 / 4","One pending"],["Recent score","88%","Sample metric"],["Next meeting","24 Nov","Sample date"]],title:"Aarav's weekly snapshot",items:[["MON","Mathematics","Homework submitted"],["TUE","Science","Class participation: Good"],["WED","English","Reading task completed"],["FRI","Mathematics","Quiz score: 18/20"]],quick:[["📊","Progress report"],["🗓️","School calendar"],["✉️","Teacher messages"],["📄","Circulars"]],suggest:["Summarise my child's week","Any pending assignments?","Show upcoming school dates"],modules:[["Student Updates","📊","Review fictional attendance, learning and activity summaries."],["School Calendar","🗓️","See sample holidays, meetings and event dates."],["Teacher Communication","✉️","Preview a secure school communication area."],["Reports & Circulars","📄","Browse sample report and circular entries."]]},
 admin:{label:"SCHOOL ADMIN WORKSPACE",name:"Welcome, Campus Admin",desc:"A sample operational overview for school teams.",avatar:"A",stats:[["Enrolled learners","2,480","Demo figure"],["Faculty","186","Demo figure"],["Attendance today","94.2%","Sample metric"],["Open notices","08","Sample figure"]],title:"Campus operations",items:[["08:00","Attendance snapshot","94.2% · Sample data"],["09:00","Notice approvals","3 awaiting review"],["10:30","Event coordination","TECHNOVA showcase"],["12:00","Academic operations","Weekly review"]],quick:[["👥","Manage users"],["📢","Publish notice"],["📅","School calendar"],["📊","Reports"]],suggest:["Show campus overview","What notices need approval?","How do roles work?"],modules:[["Event Management","🎪","Preview event listings, schedules and publishing status."],["Announcement Manager","📢","Draft a sample campus announcement."],["Gallery Management","🖼️","Preview sample gallery organisation and moderation."],["Campus Analytics","📊","Explore fictional overview metrics; no live records are connected."]]}
};
const $=id=>document.getElementById(id);
let activeRole="student";
const moduleInfo={
 "Assignment Manager":["Assignments","Your sample assignment workspace includes task title, subject, due date and status.","Mathematics practice · Due 21 Nov · In progress","Physics worksheet · Due 22 Nov · Not started","Computer Science project · Due 25 Nov · Submitted"],
 "Digital Student ID":["Sample Digital ID","DEMO ONLY — This is not an official CMS identity card and cannot be used for access or verification.","Name: Aarav Mehta","Class: IX · Section A","Campus: Sample campus record","QR: Demonstration placeholder"],
 "Achievement Portfolio":["My Achievement Portfolio","A sample showcase of projects, certificates and participation. Student-submitted records would need review before publication.","Robotics showcase · Participation","Inter-house quiz · Certificate","Science model · Project entry"],
 "School Calendar":["School Calendar","Illustrative dates only. Confirm actual dates through official school communication.","20 Nov · TECHNOVA competition day","24 Nov · Sample parent interaction","30 Nov · Sample academic review"],
 "Class Overview":["Class Overview","Sample class and section information for the teacher demonstration.","Class 9A · Mathematics · 36 learners","Class 10B · Mathematics · 34 learners","Class 8C · Mathematics · 32 learners"],
 "Lesson Planner":["Lesson Planner","A sample planning board for classroom topics and resources.","Algebra · Learning objectives","Geometry · Practice activity","Fractions · Revision exercise"],
 "Notice Publisher":["Notice Publisher","Draft-only demonstration. Publishing to real school users requires authorised accounts and server-side permissions.","Draft: Mathematics enrichment session","Status: Not published"],
 "Student Updates":["Student Updates","Fictional student information for demonstrating a parent view.","Attendance: 96% · sample","Assignments: 3 of 4 complete · sample","Recent activity: Science project · sample"],
 "Teacher Communication":["Teacher Communication","This preview does not send messages. A real service needs verified accounts and protected messaging.","Class teacher · Sample contact entry","School office · Sample contact entry"],
 "Reports & Circulars":["Reports & Circulars","Sample documents only; no real student reports are connected.","Term progress summary · Sample","Campus circular · Sample"],
 "Event Management":["Event Management","Preview event publishing tools. Official event data remains maintained in its existing source files.","TECHNOVA · Event page available","CELESTA · Event page available","CMSMUN · Event page available"],
 "Announcement Manager":["Announcement Manager","Create a local preview; this demo does not publish notices to the school.","Draft: Campus announcement","Visibility: Demo preview only"],
 "Gallery Management":["Gallery Management","Sample gallery workflow; uploaded files are not published by this demo.","Campus life · Sample collection","Innovation showcase · Sample collection"],
 "Campus Analytics":["Campus Analytics","All figures are fictional demonstration metrics, not live CMS statistics.","Events listed · 3 sample entries","Notices awaiting review · 4 sample entries"],
 "Mark attendance":["Attendance Demo","This is a non-persistent preview. It does not record, change or transmit attendance.","Class 9A · Sample class list","Attendance status · Preview only","No student records are connected"],
 "Reports":["Demo Reports","Illustrative campus-level summaries only; no live school data is connected.","Attendance overview · Sample","Event participation · Sample"],
 "Manage users":["User Management Preview","This is a visual workflow preview only. It cannot create accounts or change permissions.","Student accounts · Not connected","Teacher accounts · Not connected","Parent accounts · Not connected"]
};
function addText(parent,tag,text,className){const el=document.createElement(tag);el.textContent=text;if(className)el.className=className;parent.appendChild(el);return el}
function render(role){
 activeRole=role;const d=roles[role];
 document.querySelectorAll(".role").forEach(b=>{const selected=b.dataset.role===role;b.classList.toggle("active",selected);b.setAttribute("aria-selected",String(selected));b.tabIndex=selected?0:-1});
 $("workspacePanel").setAttribute("aria-labelledby","role-"+role);
 $("roleEyebrow").textContent=d.label;$("greeting").textContent=d.name;$("roleDesc").textContent=d.desc;$("avatar").textContent=d.avatar;$("mainTitle").textContent=d.title;
 const stats=$("stats");stats.replaceChildren();d.stats.forEach(s=>{const card=addText(stats,"article","","stat");addText(card,"span",s[0]);addText(card,"b",s[1]);addText(card,"small",s[2])});
 const schedule=$("mainContent");schedule.replaceChildren();const list=addText(schedule,"div","","schedule");
 d.items.forEach((it,i)=>{const row=addText(list,"div","","lesson");addText(row,"time",it[0]);addText(row,"i","");const body=addText(row,"div","");addText(body,"b",it[1]);addText(body,"small",it[2]);addText(row,"em",i===0?"NEXT":"")});
 const quick=$("quickLinks");quick.replaceChildren();d.quick.forEach(q=>{const b=addText(quick,"button","","quick-action");b.type="button";b.dataset.quick=q[1];addText(b,"span",q[0]);b.append(document.createTextNode(q[1]))});
 const suggestions=$("suggestions");suggestions.replaceChildren();d.suggest.forEach(s=>{const b=addText(suggestions,"button",s);b.type="button"});
 const log=$("chatLog");log.replaceChildren();addText(log,"div","Hi! I'm Campus Genie. This is fictional "+role+" demo information. What would you like to explore?","bubble bot");
 const modules=$("roleModules");modules.replaceChildren();d.modules.forEach(m=>{const b=addText(modules,"button","","module-card");b.type="button";b.dataset.module=m[0];addText(b,"span",m[1],"module-icon");addText(b,"b",m[0]);addText(b,"small",m[2])});
 $("moduleDetail").hidden=true;
}
function showModule(name){
 const info=moduleInfo[name];if(!info)return;
 const box=$("moduleDetail");box.replaceChildren();
 addText(box,"p","DEMO MODULE","eyebrow");
 addText(box,"h4",info[0]);
 addText(box,"p",info[1],"module-description");
 const ul=addText(box,"ul","");
 info.slice(2).forEach(item=>addText(ul,"li",item));
 const actions={
  "Assignment Manager":["Add a sample task","Task title","Add task","Added to this temporary preview. Nothing was submitted."],
  "Lesson Planner":["Add a lesson topic","Lesson topic","Add topic","Topic added to this temporary lesson-plan preview."],
  "Notice Publisher":["Prepare a notice draft","Notice title","Preview draft","Draft added locally. It has not been published or sent."],
  "Announcement Manager":["Prepare an announcement draft","Announcement title","Preview draft","Draft added locally. It has not been published or sent."],
  "Teacher Communication":["Prepare a message preview","Message subject","Preview message","Message preview created locally. Nothing was sent."],
  "Gallery Management":["Add a sample gallery caption","Image caption","Add caption","Caption added to this temporary gallery preview."],
  "Achievement Portfolio":["Add a project idea","Project or achievement","Add item","Item added to this temporary portfolio preview."]
 };
 const config=actions[name];
 if(config){
  const form=addText(box,"form","","module-demo-form");
  const field=addText(form,"input","");
  field.type="text";field.maxLength=120;field.required=true;field.placeholder=config[1];
  field.setAttribute("aria-label",config[1]);field.autocomplete="off";
  const submit=addText(form,"button",config[2]);submit.type="submit";
  const status=addText(box,"p","This is a temporary demo preview. Changes are not saved to a school system.","module-feedback");
  status.setAttribute("role","status");
  form.addEventListener("submit",event=>{
   event.preventDefault();const value=field.value.trim();if(!value)return;
   addText(ul,"li",value+" · DEMO PREVIEW");field.value="";status.textContent=config[3];
  });
 }
 box.hidden=false;box.scrollIntoView({behavior:"smooth",block:"nearest"});
}
function reply(q){
 const text=q.toLowerCase();let answer;let target="";
 if(/digital id|student id|identity card/.test(text)){target="Digital Student ID";answer="I opened the sample Digital Student ID module. It is a demonstration card, not an official school ID."}
 else if(/assignment|homework/.test(text)){target="Assignment Manager";answer="I opened the sample Assignment Manager. Its tasks and deadlines are fictional."}
 else if(/achievement|portfolio|certificate/.test(text)){target="Achievement Portfolio";answer="I opened the sample Achievement Portfolio. It contains fictional project and certificate entries."}
 else if(/calendar|upcoming date|event|technova|celesta|cmsmun/.test(text)){target="School Calendar";answer="The calendar preview contains sample dates. For official event details, use the event pages and confirm dates with the organisers."}
 else if(/class overview|my classes|overview/.test(text)){target=activeRole==="admin"?"Campus Analytics":"Class Overview";answer="I opened the sample overview. All figures and records are fictional."}
 else if(/timetable|class|schedule/.test(text)){answer="Your sample timetable is displayed in the overview panel. The entries are illustrative and are not a live school timetable."}
 else if(/attendance/.test(text)){target=activeRole==="teacher"?"Mark attendance":"";answer="Attendance figures and any attendance workflow here are demonstration-only. No real attendance is recorded."}
 else if(/notice|message|teacher|circular/.test(text)){target=activeRole==="admin"?"Announcement Manager":activeRole==="parent"?( /report|circular/.test(text)?"Reports & Circulars":"Teacher Communication"):"Notice Publisher";answer="I opened the relevant sample communication area. This demo does not send messages or publish notices."}
 else if(/lesson|plan/.test(text)){target="Lesson Planner";answer="I opened the sample Lesson Planner. Its topics are illustrative."}
 else if(/manage users|user accounts/.test(text)){target="Manage users";answer="I opened the user-management preview. This demo cannot create accounts or change permissions."}
 else if(/report|analytics/.test(text)){target=activeRole==="admin"?"Campus Analytics":activeRole==="parent"?"Reports & Circulars":"Reports";answer="I opened the sample reports view. No live school data is connected."}
 else answer="I can help you explore the "+activeRole+" demo, its timetable and role-based modules. This prototype does not access real CMS records.";
 if(target&&moduleInfo[target])showModule(target);
 const log=$("chatLog");addText(log,"div",q,"bubble user");addText(log,"div",answer,"bubble bot");log.scrollTop=log.scrollHeight
}
document.querySelectorAll(".role").forEach(b=>b.addEventListener("click",()=>render(b.dataset.role)));
document.querySelector(".role-list")?.addEventListener("keydown",event=>{
 if(!["ArrowRight","ArrowDown","ArrowLeft","ArrowUp","Home","End"].includes(event.key))return;
 event.preventDefault();
 const tabs=[...document.querySelectorAll(".role")];
 const current=tabs.indexOf(document.activeElement);
 const next=event.key==="Home"?0:event.key==="End"?tabs.length-1:(current+(["ArrowRight","ArrowDown"].includes(event.key)?1:-1)+tabs.length)%tabs.length;
 tabs[next].focus();render(tabs[next].dataset.role);
});
$("genieForm").addEventListener("submit",e=>{e.preventDefault();const input=$("genieInput");const q=input.value.trim();if(!q)return;reply(q);input.value=""});
$("suggestions").addEventListener("click",e=>{if(e.target.tagName==="BUTTON")reply(e.target.textContent)});
$("quickLinks").addEventListener("click",e=>{const b=e.target.closest("button");if(b)reply("Open "+b.dataset.quick)});
$("roleModules").addEventListener("click",e=>{const b=e.target.closest("button[data-module]");if(b)showModule(b.dataset.module)});
render("student");
