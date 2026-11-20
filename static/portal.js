/* Campus Portal demo: role-aware, interactive and intentionally sample-only. */
const roles={
 student:{label:"STUDENT WORKSPACE",name:"Welcome, student",desc:"Your learning day, organised in one place.",avatar:"A",stats:[["Attendance","96%","Sample metric"],["Assignments","04","2 due soon"],["Average score","88%","Sample metric"],["Achievements","06","Portfolio items"]],title:"Today's timetable",items:[["08:00","Mathematics","Room 204 · Ms. Sharma"],["09:00","Physics","Lab 2 · Mr. Khan"],["10:15","English Literature","Room 108 · Ms. Das"],["11:15","Computer Science","Lab 1 · Mr. Mehta"]],quick:[["🗓️","My timetable"],["✓","Assignments"],["🏅","My achievements"],["🪪","Digital ID"]],suggest:["Show my assignments","Show upcoming events","Open my digital ID"],modules:[["Assignment Manager","✓","Track sample tasks, due dates and submission status."],["Digital Student ID","🪪","View a clearly marked sample student identity card."],["Achievement Portfolio","🏅","Explore sample certificates, projects and competition highlights."],["School Calendar","🗓️","Browse sample academic dates and campus events."]]},
 teacher:{label:"TEACHER WORKSPACE",name:"Welcome, Ms. Sharma",desc:"Your classes, tasks and teaching day at a glance.",avatar:"S",stats:[["Classes today","5","Sample schedule"],["Students","142","Demo figure"],["Assignments","12","Sample queue"],["Attendance","94%","Sample metric"]],title:"Today's teaching plan",items:[["08:00","Class 9A · Mathematics","Algebra · Room 204"],["09:00","Class 10B · Mathematics","Geometry · Room 210"],["10:30","Class 8C · Mathematics","Fractions · Room 105"],["12:00","Faculty planning","Staff room"]],quick:[["✓","Mark attendance"],["✎","Create assignment"],["📝","Class overview"],["📣","Class notice"]],suggest:["Show my classes today","Show assignments to review","Draft a class notice"],modules:[["Class Overview","👥","Review sample classes, sections and daily teaching schedule."],["Assignment Manager","✓","Create and review demonstration assignments."],["Lesson Planner","📚","Organise sample lesson topics and classroom resources."],["Notice Publisher","📣","Preview a notice before a real school-authorised publishing workflow."]]},
 parent:{label:"PARENT WORKSPACE",name:"Welcome, Mrs. Mehta",desc:"A clear view of your child's school journey.",avatar:"M",stats:[["Attendance","96%","Sample metric"],["Assignments","3 / 4","One pending"],["Recent score","88%","Sample metric"],["Next meeting","24 Nov","Sample date"]],title:"Aarav's weekly snapshot",items:[["MON","Mathematics","Homework submitted"],["TUE","Science","Class participation: Good"],["WED","English","Reading task completed"],["FRI","Mathematics","Quiz score: 18/20"]],quick:[["📊","Progress report"],["🗓️","School calendar"],["✉️","Teacher messages"],["📄","Circulars"]],suggest:["Summarise my child's week","Any pending assignments?","Show upcoming school dates"],modules:[["Student Updates","📊","Review fictional attendance, learning and activity summaries."],["School Calendar","🗓️","See sample holidays, meetings and event dates."],["Teacher Communication","✉️","Preview a secure school communication area."],["Reports & Circulars","📄","Browse sample report and circular entries."]]},
 admin:{label:"SCHOOL ADMIN WORKSPACE",name:"Welcome, Campus Admin",desc:"A sample operational overview for school teams.",avatar:"A",stats:[["Enrolled learners","2,480","Demo figure"],["Faculty","186","Demo figure"],["Attendance today","94.2%","Sample metric"],["Open notices","08","Sample figure"]],title:"Campus operations",items:[["08:00","Attendance snapshot","94.2% · Sample data"],["09:00","Notice approvals","3 awaiting review"],["10:30","Event coordination","TECHNOVA showcase"],["12:00","Academic operations","Weekly review"]],quick:[["👥","Manage users"],["📢","Publish notice"],["📅","School calendar"],["📊","Reports"]],suggest:["Show campus overview","What notices need approval?","How do roles work?"],modules:[["Event Management","🎪","Preview event listings, schedules and publishing status."],["Announcement Manager","📢","Draft a sample campus announcement."],["Gallery Management","🖼️","Preview sample gallery organisation and moderation."],["Campus Analytics","📊","Explore fictional overview metrics; no live records are connected."]]}
};
const $=id=>document.getElementById(id);
let activeRole="student";
let activeStudentName="Student";
let activeTeacherName="Teacher";
let activeParentStudentName="Student";
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
function appendInlineMarkdown(parent,text){
 const pattern=/(\*\*|__)(.+?)\1|(?<!\*)\*([^*\n]+)\*(?!\*)|`([^`]+)`/g;
 let last=0,match;while((match=pattern.exec(text))){
  if(match.index>last)parent.appendChild(document.createTextNode(text.slice(last,match.index)));
  if(match[1])addText(parent,'strong',match[2]);else if(match[3])addText(parent,'em',match[3]);else addText(parent,'code',match[4]);last=pattern.lastIndex;
 }if(last<text.length)parent.appendChild(document.createTextNode(text.slice(last)));
}
function renderAssistantMessage(parent,text){
 const source=String(text||'').replace(/\r\n?/g,'\n').trim();if(!source){addText(parent,'p','No response available. Please try again.');return;}
 const lines=source.split('\n');let paragraph=[],list=null,listType='';
 const flushParagraph=()=>{if(!paragraph.length)return;const p=addText(parent,'p','');appendInlineMarkdown(p,paragraph.join(' ').trim());paragraph=[];};
 const closeList=()=>{list=null;listType='';};
 for(const raw of lines){const line=raw.trim();if(!line){flushParagraph();closeList();continue;}
  const heading=line.match(/^#{1,6}\s+(.+)$/);if(heading){flushParagraph();closeList();const h=addText(parent,'h4','');appendInlineMarkdown(h,heading[1].replace(/\s+#+$/,''));continue;}
  const bullet=line.match(/^\s*[-*+]\s+(.+)$/),ordered=line.match(/^\s*\d+[.)]\s+(.+)$/);
  if(bullet||ordered){flushParagraph();const type=bullet?'ul':'ol';if(!list||listType!==type){closeList();list=addText(parent,type,'');listType=type;}const item=addText(list,'li','');appendInlineMarkdown(item,(bullet||ordered)[1]);continue;}
  closeList();paragraph.push(line);
 }flushParagraph();
}
function render(role){
 activeRole=role;const d={...roles[role]};
 if(role==="student"){d.name="Welcome, "+activeStudentName;d.avatar=activeStudentName.split(" ").map(x=>x[0]).join("").slice(0,2).toUpperCase()}
 if(role==="teacher"){d.name="Welcome, "+activeTeacherName;d.avatar=activeTeacherName.split(" ").map(x=>x[0]).join("").slice(0,2).toUpperCase()}
 if(role==="parent"){d.name="Welcome, Parent of "+activeParentStudentName;d.title=activeParentStudentName+"’s weekly snapshot";d.avatar=activeParentStudentName.split(" ").map(x=>x[0]).join("").slice(0,2).toUpperCase()}
 $("workspacePanel").setAttribute("aria-label",d.label);
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
function normalizePortalQuery(value){
 let q=String(value||"").toLowerCase().normalize("NFKD").replace(/[\u0300-\u036f]/g,"").replace(/[^a-z0-9\s]/g," ").replace(/\s+/g," ").trim();
 const fixes={"ttable":"timetable","time table":"timetable","time-table":"timetable","assigment":"assignment","assignmnt":"assignment","homewrk":"homework","attendence":"attendance","attandance":"attendance","achievment":"achievement","calender":"calendar","circluar":"circular","anouncement":"announcement","announcment":"announcement","analytcs":"analytics","digi id":"digital id","idcard":"id card","clas":"class","schedul":"schedule","techer":"teacher","studnt":"student","parant":"parent"};
 Object.keys(fixes).forEach(function(key){q=q.replace(new RegExp("\\b"+key+"\\b","g"),fixes[key]);});
 return q;
}
async function reply(q){
 const log=$("chatLog");
 addText(log,"div",q,"bubble user");
 const typing=addText(log,"div","Campus Genie is thinking…","bubble bot");
 log.scrollTop=log.scrollHeight;
 const send=$("genieForm").querySelector('button[type="submit"],button:not([type])');
 if(send)send.disabled=true;
 try{
  const response=await fetch("/api/portal-chat",{
   method:"POST",
   headers:{"Content-Type":"application/json"},
   body:JSON.stringify({message:q,role:activeRole})
  });
  const data=await response.json();
  typing.remove();
  const answer=addText(log,"div","","bubble bot");
  renderAssistantMessage(answer,data.reply||"No response available. Please try again.");
 }catch(error){
  typing.remove();
  addText(log,"div","Campus Genie is temporarily unavailable. Please try again.","bubble bot");
 }finally{
  if(send)send.disabled=false;
  log.scrollTop=log.scrollHeight;
 }
}

$("genieForm").addEventListener("submit",e=>{
 e.preventDefault();
 const input=$("genieInput");
 const q=input.value.trim();
 if(!q)return;
 input.value="";
 reply(q);
});
$("suggestions").addEventListener("click",e=>{
 if(e.target.tagName==="BUTTON")reply(e.target.textContent);
});

$("roleModules").addEventListener("click",e=>{const b=e.target.closest("button[data-module]");if(b)showModule(b.dataset.module)});
render("student");
const demoStudents={"CMS-DEMO-001":"Shashwat Pandey","CMS-DEMO-002":"Virat Pandey"};
const demoTeachers={"CMS-TEACHER-001":"Divyansh Mishra","CMS-TEACHER-002":"Ansh Yadav"};
const demoParents={"CMS-PARENT-001":"Shashwat Pandey","CMS-PARENT-002":"Virat Pandey"};
document.querySelectorAll("[data-entry-role]").forEach(button=>button.addEventListener("click",()=>{
 const role=button.dataset.entryRole;
 const form=$("studentIdForm");
 const teacherForm=$("teacherIdForm");
 const parentForm=$("parentIdForm");
 $("idFeedback").textContent="";$("teacherIdFeedback").textContent="";$("parentIdFeedback").textContent="";
 form.hidden=role!=="student";teacherForm.hidden=role!=="teacher";parentForm.hidden=role!=="parent";
 if(role==="student"){$("studentDemoId").focus();return;}
 if(role==="teacher"){$("teacherDemoId").focus();return;}
 if(role==="parent"){$("parentDemoId").focus();return;}
 if(role==="admin"){window.location.href="/admin/login";return;}
 activeStudentName=roles[role].name.replace(/^Welcome,?\s*/,"");
 render(role);
 $("entryOverlay").hidden=true;
}));
$("switchRole").addEventListener("click",()=>{
 $("entryOverlay").hidden=false;
 $("studentIdForm").hidden=true;$("teacherIdForm").hidden=true;$("parentIdForm").hidden=true;
 $("idFeedback").textContent="";$("teacherIdFeedback").textContent="";$("parentIdFeedback").textContent="";
 document.querySelector("[data-entry-role=student]").focus();
});
$("studentIdForm").addEventListener("submit",event=>{
 event.preventDefault();
 const id=$("studentDemoId").value.trim().toUpperCase();
 const name=demoStudents[id];
 if(!name){$("idFeedback").textContent="ID not recognised. Use CMS-DEMO-001 or CMS-DEMO-002.";return;}
 activeStudentName=name;render("student");$("entryOverlay").hidden=true;
});
$("teacherIdForm").addEventListener("submit",event=>{
 event.preventDefault();
 const id=$("teacherDemoId").value.trim().toUpperCase();
 const name=demoTeachers[id];
 if(!name){$("teacherIdFeedback").textContent="ID not recognised. Use CMS-TEACHER-001 or CMS-TEACHER-002.";return;}
 activeTeacherName=name;render("teacher");$("entryOverlay").hidden=true;
});

$("parentIdForm").addEventListener("submit",event=>{
 event.preventDefault();
 const id=$("parentDemoId").value.trim().toUpperCase();
 const studentName=demoParents[id];
 if(!studentName){$("parentIdFeedback").textContent="ID not recognised. Use CMS-PARENT-001 or CMS-PARENT-002.";return;}
 activeParentStudentName=studentName;render("parent");$("entryOverlay").hidden=true;
});
