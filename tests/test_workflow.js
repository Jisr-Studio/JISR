/* Preparing a private draft must never imply that human review is complete. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const app=fs.readFileSync(require('node:path').join(__dirname,'../dist/js/app.js'),'utf8');
const start=app.indexOf('function syncWorkflow(){'),end=app.indexOf('const originalStatus=status;',start);
function element(){return {dataset:{},style:{setProperty(){}},attributes:{},textContent:'',classList:{values:{},toggle(k,v){this.values[k]=v}},setAttribute(k,v){this.attributes[k]=v},removeAttribute(k){delete this.attributes[k]},querySelector(){return this.number}};}
const bar=element(),indicator=element(),note=element(),steps=Array.from({length:4},()=>{const e=element();e.number=element();return e;});
const context={readOnly:false,workflowUploading:false,project:{id:'fixture',status:'ready',publishable:false},
  segments:[{reviewed:false}],activeExport:{id:'fixture',kind:'mp4',phase:'ready'},exportNames:{mp4:'الفيديو'},
  JisrCitationText:{reviewPending:s=>!s.reviewed},$:s=>s==='.workflow'?bar:s==='#workflowProgress'?indicator:note,$$:()=>steps};
vm.createContext(context);vm.runInContext(app.slice(start,end),context);
context.syncWorkflow();assert.equal(steps[2].classList.values.done,false);assert.equal(bar.dataset.current,'2');assert.match(note.textContent,/المراجعة لم تكتمل/);
context.activeExport.phase='working';context.syncWorkflow();assert.equal(steps[2].classList.values.done,false);
context.project.publishable=true;context.segments[0].reviewed=true;context.activeExport.phase='ready';context.syncWorkflow();assert.equal(steps[2].classList.values.done,true);assert.equal(steps[3].classList.values.done,true);
context.readOnly=true;context.activeExport=null;context.syncWorkflow();assert.equal(bar.dataset.state,'complete');
console.log('Draft export and human-review workflow checks passed.');
