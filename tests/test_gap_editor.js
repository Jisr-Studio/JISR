/* A non-speech gap can be dismissed only through an explicit editor decision. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const app=fs.readFileSync(require('node:path').join(__dirname,'../dist/js/app.js'),'utf8');
const start=app.indexOf('function edit(i){'),end=app.indexOf('function reference(i){',start);
let fields,requested=[],accepted=false,closed=false,saved=false;
const context={segments:[{id:'gap',ar:'',translation:'',type:'speech',audio_gap:true,start:1,end:2}],project:{id:'test'},
  JisrCitationText:{presentation:s=>({arabic:s.ar,fromSource:false})},esc:String,fmt:String,targetLanguage:()=> 'en',targetInfo:()=>({direction:'ltr'}),
  modal:(title,markup)=>{fields={'#modal':{close(){closed=true}}};for(const id of markup.matchAll(/id="([^"]+)"/g))fields['#'+id[1]]={};},
  $:selector=>fields[selector]||null,confirm:()=>accepted,toast(){},setProject(){saved=true},
  api:async(path,options)=>{requested.push({path,body:JSON.parse(options.body)});return {};}};
vm.createContext(context);vm.runInContext(app.slice(start,end),context);
(async()=>{
  context.edit(0);assert.ok(fields['#dismissGap']);
  await fields['#dismissGap'].onclick();assert.equal(requested.length,0);assert.equal(closed,false);
  accepted=true;await fields['#dismissGap'].onclick();assert.deepEqual(requested,[{path:'/api/projects/test/segments/gap',body:{dismiss_gap:true}}]);assert.equal(saved,true);assert.equal(closed,true);
  context.segments[0].audio_gap=false;context.edit(0);assert.equal(fields['#dismissGap'],undefined);
  console.log('Non-speech gap editor confirmation and save checks passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
