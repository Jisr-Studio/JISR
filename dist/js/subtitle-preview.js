/* Shared-image preview: bounded cache, next-cue warming, and stale-load guards. */
(function(root) {
  function create(options) {
    const {image, container, onError=()=>{}} = options;
    const request = options.fetch || root.fetch.bind(root);
    const makeURL = options.makeURL || (blob => URL.createObjectURL(blob));
    const revokeURL = options.revokeURL || (url => URL.revokeObjectURL(url));
    const schedule = options.schedule || setTimeout, cancel = options.cancel || clearTimeout;
    const cache = new Map(), pending = new Map(), limit = options.limit || 16;
    let current='', sequence=0, epoch=0, timer=null, destroyed=false;

    function trim() {
      while(cache.size > limit) {
        const oldest = [...cache.keys()].find(key => key !== current);
        if(oldest === undefined)break;
        revokeURL(cache.get(oldest));cache.delete(oldest);
      }
    }
    function load(entry) {
      if(cache.has(entry.key)) {
        const url=cache.get(entry.key);cache.delete(entry.key);cache.set(entry.key,url);
        return Promise.resolve(url);
      }
      if(pending.has(entry.key))return pending.get(entry.key).promise;
      const controller=new AbortController(), started=epoch;
      const job={controller};
      job.promise=(async()=>{
        const response=await request(entry.url,{headers:entry.headers||{},signal:controller.signal});
        if(!response.ok) {
          const message=await response.json().catch(()=>({}));
          const error=Error(message.error||'تعذر رسم معاينة الترجمة');
          error.retryable=response.status>=500||response.status===429;throw error;
        }
        const blob=await response.blob();
        if(destroyed||started!==epoch)throw Object.assign(Error('Preview cancelled'),{name:'AbortError'});
        const url=makeURL(blob);cache.set(entry.key,url);trim();return url;
      })().finally(()=>{if(pending.get(entry.key)===job)pending.delete(entry.key)});
      pending.set(entry.key,job);return job.promise;
    }
    function paint(key,url,expected) {
      if(destroyed||key!==current||expected!==sequence)return;
      image.onload=()=>{
        if(key===current&&expected===sequence&&image.src===url)image.hidden=false;
      };
      image.src=url;
      if(image.complete&&image.naturalWidth>0)image.hidden=false;
    }
    function show(entry,delay=0) {
      const key=entry?.key||'';
      if(key===current&&(!key||!image.hidden||pending.has(key)||timer!==null))return;
      current=key;const expected=++sequence;cancel(timer);timer=null;
      image.hidden=true;container.classList.toggle('image-subtitle',!!key);
      if(!key||destroyed)return;
      if(cache.has(key)){paint(key,cache.get(key),expected);return}
      async function run(attempt=0) {
        timer=null;
        try {paint(key,await load(entry),expected)}
        catch(error) {
          if(destroyed||key!==current||expected!==sequence||error.name==='AbortError')return;
          if(!attempt&&error.retryable!==false)timer=schedule(()=>run(1),400);
          else onError(error.message||'تعذر رسم معاينة الترجمة');
        }
      }
      if(delay)timer=schedule(run,delay);else run();
    }
    function warm(entry) {
      if(entry&&!destroyed)load(entry).catch(()=>{});
    }
    function reset() {
      ++epoch;++sequence;current='';cancel(timer);timer=null;
      image.hidden=true;image.onload=null;container.classList.remove('image-subtitle');
      for(const job of pending.values())job.controller.abort();pending.clear();
      for(const url of cache.values())revokeURL(url);cache.clear();
      image.removeAttribute('src');
    }
    return {show,warm,reset,destroy(){reset();destroyed=true}};
  }
  root.JisrSubtitlePreview={create};
  if(typeof module!=='undefined')module.exports=root.JisrSubtitlePreview;
})(typeof window==='undefined'?globalThis:window);
