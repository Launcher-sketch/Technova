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
function reply(q){
 const text=normalizePortalQuery(q);
 const roleData=roles[activeRole];
 let answer="";
 let target="";
 const asksToOpen=/\b(open|go to|take me to|navigate to|launch|access|view|bring up|kholo|dikhao)\b/.test(text);
 const hasAny=function(list){return list.some(function(term){return text.includes(term);});};
 const roleModules=roleData.modules.map(function(item){return item[0];});
 const choose=function(map){for(let i=0;i<map.length;i++){if(hasAny(map[i].terms)){return map[i];}}return null;};
 const moduleMatch=choose([
  {terms:["digital id","student id","identity card","id card"],name:"Digital Student ID",roles:["student"]},
  {terms:["assignment","homework","task","submission","due date"],name:"Assignment Manager",roles:["student","teacher"]},
  {terms:["achievement","portfolio","certificate","project showcase"],name:"Achievement Portfolio",roles:["student"]},
  {terms:["calendar","school dates","upcoming dates","event dates"],name:"School Calendar",roles:["student","parent"]},
  {terms:["class overview","my classes","class list","sections"],name:"Class Overview",roles:["teacher"]},
  {terms:["lesson planner","lesson plan","plan a lesson","teaching plan"],name:"Lesson Planner",roles:["teacher"]},
  {terms:["notice publisher","publish notice","class notice"],name:"Notice Publisher",roles:["teacher"]},
  {terms:["student updates","child progress","my child","childs progress"],name:"Student Updates",roles:["parent"]},
  {terms:["teacher communication","message teacher","contact teacher"],name:"Teacher Communication",roles:["parent"]},
  {terms:["reports","report card","circular","school circular"],name:activeRole==="parent"?"Reports & Circulars":"Reports",roles:["parent","student","teacher"]},
  {terms:["event management"],name:"Event Management",roles:["admin"]},
  {terms:["announcement manager","publish announcement","campus announcement"],name:"Announcement Manager",roles:["admin"]},
  {terms:["gallery management","campus gallery"],name:"Gallery Management",roles:["admin"]},
  {terms:["analytics","campus overview","manage users","user accounts"],name:hasAny(["manage users","user accounts"])?"Manage users":"Campus Analytics",roles:["admin"]},
  {terms:["mark attendance","take attendance"],name:"Mark attendance",roles:["teacher"]}
 ]);
 if(hasAny(["help","what can you do","what can i do","how can you help","how do i use","guide me","help me","what is available","portal features","portal modules","what modules","show my tools","my options"])){
  answer="I can guide you around this "+activeRole+" demo, explain the sample dashboard, summarise the timetable and describe the available tools. Your available modules are: "+roleModules.join(", ")+". Everything shown here is illustrative demo content, not a live school record.";
 } else if(hasAny(["timetable","schedule","periods","classes today","my day","teaching plan"])){
  answer="Here is the sample "+(activeRole==="teacher"?"teaching plan":activeRole==="admin"?"campus operations schedule":"timetable")+": "+roleData.items.map(function(item){return item[0]+" — "+item[1]+" ("+item[2]+")";}).join("; ")+". These entries are fictional examples, not your actual school schedule.";
 } else if(hasAny(["attendance","present","absent","attendance percentage"])){
  const metric=roleData.stats.find(function(item){return item[0].toLowerCase().includes("attendance");});
  answer=metric?"The dashboard displays "+metric[1]+" for "+metric[0].toLowerCase()+" ("+metric[2]+"). This is sample data only; the demo does not check or change real attendance.":"This role view does not provide an attendance record. No real attendance system is connected."; if(asksToOpen&&activeRole==="teacher")target="Mark attendance";
 } else if(hasAny(["stats","statistics","overview","dashboard","numbers","figures","progress","performance"])){
  answer="Your "+activeRole+" dashboard currently shows these sample figures: "+roleData.stats.map(function(item){return item[0]+": "+item[1]+" ("+item[2]+")";}).join("; ")+". All figures are fictional demo metrics, not live CMS data.";
 } else if(hasAny(["assignment","homework","task","submission","due date"])){
  if(activeRole==="parent"){answer="The Parent workspace has a Student Updates panel for a fictional progress snapshot and a Reports & Circulars module. Its sample summary shows 3 of 4 assignments complete; this is not linked to a real student record.";}
  else if(activeRole==="teacher"){answer="The Teacher workspace includes an Assignment Manager for creating and reviewing demonstration assignments. Its queue shows 12 sample assignments; no real student submissions are connected.";}
  else{answer="The Student workspace includes an Assignment Manager. The sample panel lists Mathematics practice (due 21 Nov), a Physics worksheet (due 22 Nov) and a Computer Science project (due 25 Nov). These are fictional tasks, not actual homework.";} if(asksToOpen)target=activeRole==="parent"?"Student Updates":"Assignment Manager";
 } else if(hasAny(["event","technova","celesta","cmsmun","school calendar","upcoming"])){
  answer="The portal includes a School Calendar module with illustrative dates and an Event Management preview for admins. For verified event details, use the main CMS Events website; the portal calendar is sample-only."; if(asksToOpen)target=activeRole==="admin"?"Event Management":activeRole==="teacher"?"":"School Calendar";
 } else if(hasAny(["notice","announcement","message","circular","communicate"])){
  answer=activeRole==="parent"?"The Parent workspace has Teacher Communication and Reports & Circulars previews. They do not send messages or access real circulars.":activeRole==="teacher"?"The Teacher workspace has a Notice Publisher for local draft previews. It does not publish notices to school users.":"The portal shows role-specific communication previews. They are demonstrations only; no real message is sent or notice published."; if(asksToOpen)target=activeRole==="parent"?"Teacher Communication":activeRole==="admin"?"Announcement Manager":activeRole==="teacher"?"Notice Publisher":"";
 } else if(moduleMatch && moduleMatch.roles.includes(activeRole)){
  target=moduleMatch.name;
  answer="The "+moduleMatch.name+" is available in your "+activeRole+" workspace. "+(moduleInfo[moduleMatch.name]?moduleInfo[moduleMatch.name][1]:"It is a demonstration module.")+" "+(asksToOpen?"I have opened its sample preview below.":"Ask me to open it if you want to explore the module.") ;
  if(asksToOpen)showModule(target);
 } else if(hasAny(["real data","live data","actual records","official records","real account","login","password","secure"])){
  answer="This is a concept demonstration that uses fictional sample content. It is not connected to official CMS accounts, attendance, marks, messages or student records. Do not enter real passwords, IDs or private information here.";
 } else {
  answer="I can help with the "+activeRole+" workspace. Try asking about your timetable, assignments, attendance, achievements, school calendar, notices, reports or available modules. You can also say “open assignments” or “open my timetable”. This portal uses fictional demo data only.";
 }
 if(target && asksToOpen && moduleInfo[target] && !answer.includes("opened its sample preview"))showModule(target);
 const log=$("chatLog");addText(log,"div",q,"bubble user");addText(log,"div",answer,"bubble bot");log.scrollTop=log.scrollHeight;
}

$("genieForm").addEventListener("submit",e=>{e.preventDefault();const input=$("genieInput");const q=input.value.trim();if(!q)return;reply(q);input.value=""});
$("suggestions").addEventListener("click",e=>{if(e.target.tagName==="BUTTON")reply(e.target.textContent)});
$("quickLinks").addEventListener("click",e=>{const b=e.target.closest("button");if(b)reply("Open "+b.dataset.quick)});
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
