const assert=require('node:assert/strict');
const {create}=require('../dist/js/subtitle-preview.js');
const settle=()=>new Promise(resolve=>setImmediate(resolve));
const success={ok:true,blob:async()=>({})};
function fixture(fetch,limit=2){
  let index=0;
  const image={hidden:true,complete:false,naturalWidth:0,removeAttribute(){this.src=''},fireLoad(){this.complete=true;this.naturalWidth=640;this.onload?.()}};
  Object.defineProperty(image,'src',{get(){return this.value},set(value){this.value=value;this.complete=false;this.naturalWidth=0}});
  const timers=new Map(),revoked=[],errors=[],classes=new Set();
  const player=create({image,limit,fetch,makeURL:()=>`blob:${++index}`,revokeURL:url=>revoked.push(url),onError:message=>errors.push(message),
    container:{classList:{toggle(name,on){on?classes.add(name):classes.delete(name)},remove(name){classes.delete(name)}}},
    schedule:(fn,ms)=>{const id=++index;timers.set(id,{fn,ms});return id},cancel:id=>timers.delete(id)});
  return {player,image,timers,revoked,errors,classes};
}
const entry=key=>({key,url:`/subtitle/${key}`,headers:{'X-Edit-Token':'local-test'}});
(async()=>{
  // A warmed next cue can be shown without another request or a debounce.
  let calls=0;
  const cached=fixture(async()=>{++calls;return success});
  cached.player.warm(entry('next'));await settle();cached.player.show(entry('next'));await settle();cached.image.fireLoad();
  assert.equal(calls,1);assert.equal(cached.image.hidden,false);
  const lateLoad=cached.image.onload;cached.player.show(null);lateLoad();
  assert.equal(cached.image.hidden,true);assert.equal(cached.classes.has('image-subtitle'),false);

  // Out-of-order responses may fill the cache, but cannot paint the old cue.
  const responses=new Map();
  const race=fixture(url=>new Promise(resolve=>responses.set(url,resolve)));
  race.player.show(entry('old'));race.player.show(entry('new'));
  responses.get('/subtitle/new')(success);await settle();race.image.fireLoad();const current=race.image.src;
  responses.get('/subtitle/old')(success);await settle();assert.equal(race.image.src,current);assert.equal(race.image.hidden,false);

  // Network failure is retried for the same cue rather than leaving it blank.
  calls=0;
  const retry=fixture(async()=>{if(!calls++)throw Error('temporary');return success});
  retry.player.show(entry('retry'));await settle();
  assert.equal(retry.timers.size,1);
  const task=[...retry.timers.values()][0];assert.equal(task.ms,400);retry.timers.clear();task.fn();await settle();retry.image.fireLoad();
  assert.equal(calls,2);assert.equal(retry.image.hidden,false);assert.deepEqual(retry.errors,[]);

  // Access denial is not retried automatically; a later user action can retry.
  calls=0;
  const denied=fixture(async()=>{++calls;return {ok:false,status:403,json:async()=>({error:'Access denied'})}});
  denied.player.show(entry('private'));await settle();assert.equal(calls,1);assert.equal(denied.timers.size,0);assert.deepEqual(denied.errors,['Access denied']);
  denied.player.show(entry('private'));await settle();assert.equal(calls,2);

  // Eviction releases old object URLs while preserving the current image.
  const bounded=fixture(async()=>success);
  for(const key of ['one','two','three']){bounded.player.show(entry(key));await settle();bounded.image.fireLoad()}
  assert.equal(bounded.revoked.length,1);assert.notEqual(bounded.revoked[0],bounded.image.src);
  bounded.player.destroy();assert.equal(bounded.revoked.length,3);assert.equal(bounded.image.hidden,true);

  // A response arriving after a project reset cannot create or display an URL.
  let finish;
  const reset=fixture(()=>new Promise(resolve=>{finish=resolve}));
  reset.player.show(entry('abandoned'));reset.player.reset();finish(success);await settle();
  assert.equal(reset.image.src,'');assert.equal(reset.image.hidden,true);assert.deepEqual(reset.revoked,[]);assert.deepEqual(reset.errors,[]);
  for(const test of [cached,race,retry,denied,reset])test.player.destroy();
  console.log('Subtitle preview cache, retry, race, gap, and cleanup checks passed.');
})().catch(error=>{console.error(error);process.exitCode=1});
