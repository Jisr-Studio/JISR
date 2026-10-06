const $=q=>document.querySelector(q), $$=q=>[...document.querySelectorAll(q)];
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=n=>`${String(Math.floor((+n||0)/60)).padStart(2,'0')}:${String(Math.floor((+n||0)%60)).padStart(2,'0')}`;
const video=$('#video');
const subtitleImage=document.createElement('img');subtitleImage.id='subtitleImage';subtitleImage.className='subtitle-image';subtitleImage.alt='';subtitleImage.hidden=true;$('#subtitle').append(subtitleImage);
const subtitlePreview=JisrSubtitlePreview.create({image:subtitleImage,container:$('#subtitle'),onError:message=>toast(message)});
let previewAppearance='',previewKey='',previewWarmTimer;
window.addEventListener('pagehide',event=>{if(!event.persisted)subtitlePreview.destroy()});
video.addEventListener('loadedmetadata',()=>{if(video.videoWidth&&video.videoHeight)$('#videoStage').style.aspectRatio=`${video.videoWidth}/${video.videoHeight}`;video.style.objectFit='contain'});
function subtitlePreviewEntry(s){
  if(!project||!s)return null;
  const query=new URLSearchParams({font:style.font,size:style.size,color:style.color,backdrop:style.backdrop,bilingual:style.bilingual});
  return {key:JSON.stringify([project.id,s,style]),url:`/api/projects/${project.id}/subtitle/${s.id}?${query}`,headers:token?{'X-Edit-Token':token}:{}};
}
function updateSubtitleImage(s){
  const entry=subtitlePreviewEntry(s),key=entry?.key||'';
  const appearance=JSON.stringify([project?.id,style]),delay=appearance!==previewAppearance?120:0;
  previewAppearance=appearance;subtitlePreview.show(entry,delay);
  if(key===previewKey)return;
  previewKey=key;clearTimeout(previewWarmTimer);
  const upcoming=entry?segments[selected+1]:segments.find(cue=>cue.start>video.currentTime);
  const next=subtitlePreviewEntry(upcoming);
  if(next)previewWarmTimer=setTimeout(()=>subtitlePreview.warm(next),delay);
}
let project=null, token='', segments=[], filter='all', showArabic=true, selected=0, readOnly=false, poll=null, toastTimer;
const style={font:'plex',size:18,color:'#ffffff',backdrop:true,bilingual:true,position:'bottom'};
const demo=[
 {id:'d1',start:0,end:8,type:'speech',ar:'الطهارة ليست مجرد نظافة للجسد، بل استعداد للوقوف بين يدي الله.',en:'Purification is more than physical cleanliness. It prepares us to stand before Allah.'},
 {id:'d2',start:8,end:16,type:'quran',ar:'إِنَّ اللَّهَ يُحِبُّ التَّوَّابِينَ وَيُحِبُّ الْمُتَطَهِّرِينَ',en:'Indeed, Allah loves those who are constantly repentant and loves those who purify themselves.',source:{surah:2,ayah:222,title:'سورة البقرة · الآية ٢٢٢',url:'https://quranpedia.net/embed?surah=2&ayah=222',arabic:'إِنَّ اللَّهَ يُحِبُّ التَّوَّابِينَ وَيُحِبُّ الْمُتَطَهِّرِينَ',english:'Indeed, Allah loves those who are constantly repentant and loves those who purify themselves.',translator:'مثال توضيحي'}},
 {id:'d3',start:16,end:24,type:'speech',ar:'فالوضوء عبادة نؤديها بخشوع، ونستحضر فيها معنى الطهارة.',en:'We perform ablution with humility, mindful of the meaning of purification.'},
 {id:'d4',start:24,end:32,type:'hadith',ar:'الطُّهُورُ شَطْرُ الْإِيمَانِ',en:'Purification is half of faith.',source:{title:'الطهور شطر الإيمان',url:'https://hadeethenc.com/ar/browse/hadith/65004',grade:'صحيح',attribution:'صحيح مسلم ٢٢٣',narrator:'أبو مالك الأشعري'}},
 {id:'d5',start:32,end:40,type:'speech',ar:'ونحرص على [كلمة غير واضحة] عند غسل الأعضاء.',en:'We take care to [unclear word] when washing the limbs.',needs_review:true},
 {id:'d6',start:40,end:48,type:'speech',ar:'فلنجعل وضوءنا فرصة لتجديد النية والاستعداد للصلاة.',en:'Let our ablution be an opportunity to renew our intention and prepare for prayer.'}
];segments=demo.map(x=>({...x}));
function toast(s){$('#toast').textContent=s;$('#toast').classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').classList.remove('visible'),4500)}
async function api(path,opt={}){let r=await fetch(path,{...opt,headers:{...(opt.body instanceof FormData?{}:{'Content-Type':'application/json'}),...(token?{'X-Edit-Token':token}:{}),...opt.headers}});let d=await r.json().catch(()=>({error:'تعذر قراءة استجابة الخادم'}));if(!r.ok)throw Error(d.error||'تعذر الطلب');return d}
function setProject(p){
  const sameVideo=project?.id===p.id&&project.filename===p.filename;
  const keepAppearance=sameVideo&&(styleTimer||pendingStyleSaves.size);
  project=p;segments=p.segments||[];
  if(!keepAppearance)Object.assign(style,{font:'plex',size:18,color:'#ffffff',backdrop:true,bilingual:true,position:'bottom'},p.style||{},{position:'bottom'});
  $('#videoStage').classList.add('has-project');
  if(!sameVideo){subtitlePreview.reset();clearTimeout(previewWarmTimer);clearTimeout(styleTimer);styleTimer=null;previewKey='';video.src=p.video_url;selected=JisrSubtitlePreview.activeIndex(segments,0)}
  else selected=JisrSubtitlePreview.activeIndex(segments,video.currentTime);
  render();applyStyle();status();clearInterval(poll);
  if(p.status==='processing')poll=setInterval(async()=>{try{let next=await api('/api/projects/'+p.id);setProject(next);if(next.status==='ready')toast('اكتملت المعالجة؛ راجع النصوص والمراجع');if(next.status==='error')toast(next.error)}catch(e){clearInterval(poll);toast(e.message)}},2500);
}
function status(){$('#projectTitle').textContent=project?.title||'الطهارة.. بداية كل عبادة';$('#saveState').textContent=project?({uploaded:'تم الرفع',processing:project.stage,ready:'التعديلات محفوظة',error:project.error}[project.status]||''):'بيانات توضيحية';$('#durationLabel').textContent=project?fmt(project.duration||video.duration||0):'٤٨ ثانية';$('.demo-pill').textContent=project?'مشروع حقيقي':'نسخة تجريبية';$('.workflow-note').textContent=project?(project.stage||'جاهز للمعالجة'):'بيانات توضيحية · لا توجد معالجة آلية';$('.preview-note').textContent=project?'راجع النصوص والمصادر قبل النشر. المقاطع الطويلة تُصغّر تلقائيًا لتلائم الفيديو.':'الفيديو صامت والنصوص أمثلة مستقلة للتجربة.';$('.video-title').style.display=project?'none':'';$('.video-top').style.display=project?'none':'';$('#upload').style.display=readOnly?'none':'';$('#export').style.display=readOnly?'none':'';document.body.classList.toggle('viewer-mode',readOnly)}
function sourceLabel(s){let r=s.source;if(!r)return '';if(r.quotation_mode==='paraphrase')return 'نقل بالمعنى · مرجع مرتبط · '+(r.attribution||r.title||'حديث');return s.type==='quran'?r.title||'آية قرآنية':(r.attribution||r.title||'حديث')+' · '+(r.grade||'الحكم غير مذكور')+(s.needs_review?' · بانتظار المراجعة':'')}
function render(){let counts={all:segments.length,quran:segments.filter(x=>x.type==='quran').length,hadith:segments.filter(x=>x.type==='hadith').length,review:segments.filter(JisrCitationText.reviewPending).length};$$('[data-filter]').forEach(b=>{b.querySelector('span').textContent=counts[b.dataset.filter]});$('.transcript-panel .count').textContent=segments.length+' مقاطع';$('#reviewCount').textContent=counts.review;$('#reviewSummary').textContent=counts.review?counts.review+' مقطع يحتاج انتباهك':'لا توجد مقاطع تنتظر المراجعة';$('.topbar nav .count').textContent=counts.quran+counts.hadith;
let list=segments.map((s,i)=>({s,i})).filter(({s})=>filter==='all'||(filter==='review'?JisrCitationText.reviewPending(s):s.type===filter));
$('#segments').innerHTML=list.map(({s,i})=>`<div class="segment ${i===selected?'current':''}"><button class="segment-time" data-seek="${i}">${fmt(s.start)}<br><span>${fmt(s.end)}</span></button><div class="segment-body">${s.type==='quran'?'<span class="tag quran">قرآن كريم</span>':s.type==='hadith'?'<span class="tag hadith">حديث نبوي</span>':''}${JisrCitationText.reviewPending(s)?'<span class="tag review">يحتاج مراجعة</span>':''}${showArabic?`<p class="ar">${esc(JisrCitationText.presentation(s).arabic)}</p>${JisrCitationText.presentation(s).fromSource?'<span class="tag">نص المصدر</span>':''}`:''}<p class="en" dir="ltr">${esc(s.en||'الترجمة تحتاج مراجعة')}</p>${s.citation_lookup?`<p class="modal-note" role="status">${esc(s.citation_lookup.message||"تعذر ربط المصدر؛ يحتاج إلى مراجعة")}</p>`:""}${s.source?`<button class="text-button" data-ref="${i}">${esc(sourceLabel(s))} · عرض المصدر</button>`:''}</div>${readOnly?'':`<button class="edit" data-edit="${i}" aria-label="تعديل المقطع">✎</button>`}</div>`).join('')||'<p style="padding:20px;color:#75828d">لا توجد مقاطع في هذا العرض.</p>';
$$('[data-seek]').forEach(b=>b.onclick=()=>seek(+b.dataset.seek));$$('[data-edit]').forEach(b=>b.onclick=()=>edit(+b.dataset.edit));$$('[data-ref]').forEach(b=>b.onclick=()=>reference(+b.dataset.ref));renderCitationSuggestions();renderSources();updateSubtitle()}
function renderCitationSuggestions(){
  if(readOnly)return;
  $$('[data-edit]').forEach(button=>{
    const i=+button.dataset.edit;
    const choices=segments[i]?.citation_suggestions||[];
    const body=button.closest('.segment').querySelector('.segment-body');
    choices.forEach((source,j)=>{
      const action=document.createElement('button');
      action.className='text-button';
      action.textContent='مصدر محتمل · '+source.narrator+' · قارن واربط';
      action.onclick=()=>citationSuggestion(i,j);
      body.appendChild(action);
    });
  });
}
function citationSuggestion(i,j){
  const segment=segments[i],source=segment?.citation_suggestions?.[j];
  if(!source||!project||readOnly)return;
  const projectId=project.id,segmentId=segment.id;
  const paraphrase=source.quotation_mode==='paraphrase';
  const group=segment.citation_group?segments.filter(s=>s.citation_group===segment.citation_group):[segment];
  modal('مراجعة المصدر المقترح',`<p class="modal-note">${paraphrase?'هذا مصدر محتمل لعبارة مختصرة أو مختلفة. عند ربطه نحافظ على كلام المتحدث ونميزه كنقل بالمعنى؛ لا نستبدله بالرواية كاملة.':'قارن الاقتباس بالمصدر قبل الربط.'}</p><h3>التفريغ الأصلي</h3><p class="modal-verse">${esc(segment.ar)}</p><h3>نص المصدر</h3><p class="modal-verse">${esc(source.arabic)}</p><p dir="ltr">${esc(source.english)}</p><dl class="source-list"><dt>الراوي</dt><dd>${esc(source.narrator)}</dd><dt>الحكم</dt><dd>${esc(source.grade)}</dd><dt>التخريج</dt><dd>${esc(source.attribution)}</dd></dl><div class="modal-actions"><a class="button secondary" href="https://hadeethenc.com/ar/browse/hadith/${esc(source.id)}" target="_blank" rel="noopener noreferrer">قراءة المصدر ↗</a><button class="button" id="acceptCitationSuggestion">${paraphrase?'ربط كنقل بالمعنى':'ربط الاقتباس'}</button></div><p class="modal-note">الربط يبقى بانتظار تأكيد المراجعة.</p>`);
  $('#acceptCitationSuggestion').onclick=async event=>{
    event.target.disabled=true;
    try{
      const updated=await api(`/api/projects/${projectId}/hadith/${segmentId}`,{method:'POST',body:JSON.stringify({hadith_id:source.id,paraphrase,apply_to_group:!!$('#applyCitationGroup')?.checked})});
      setProject(updated);$('#modal').close();toast('تم ربط المصدر؛ راجع النص والترجمة قبل تأكيده');
    }catch(error){event.target.disabled=false;toast(error.message)}
  };
  if(group.length>1){
    $('#modalBody .modal-actions').insertAdjacentHTML('beforebegin',`<label class="check"><input id="applyCitationGroup" type="checkbox" checked> تطبيق المرجع على أجزاء الاقتباس المتصل (${group.length})</label><p class="modal-note">التفريغ المتصل: ${esc(group.map(s=>s.ar).join(' '))}</p>`);
  }
}
function renderSources(){let cards=segments.map((s,i)=>({s,i})).filter(({s})=>s.source&&['quran','hadith'].includes(s.type));$('#referencePanel').querySelectorAll('.reference-card,.source-disclaimer').forEach(x=>x.remove());$('#referencePanel').insertAdjacentHTML('beforeend',cards.map(({s,i})=>`<button class="reference-card" data-ref="${i}"><div><span class="tag ${s.type}">${s.type==='quran'?'قرآن كريم':'حديث نبوي'}</span><span class="ref-time">${fmt(s.start)}</span></div><h3>${esc(s.source.title||'مصدر الاقتباس')}</h3><p class="verse">${esc(JisrCitationText.presentation(s).arabic)}</p><footer>${esc(sourceLabel(s))}<span>عرض التفاصيل ‹</span></footer></button>`).join('')+(!cards.length?'<div class="source-disclaimer">لم تُوثَّق اقتباسات بعد. الاقتباسات المحتملة تنتظر المراجعة.</div>':''));$('#referencePanel').querySelectorAll('[data-ref]').forEach(b=>b.onclick=()=>reference(+b.dataset.ref))}
function seek(i){if(!segments[i])return;video.currentTime=segments[i].start;selected=i;render()}
function updateSubtitle(){let s=segments[selected];$('#subtitle').classList.toggle('no-cue',!s);$('#subtitleArabic').textContent=s&&style.bilingual&&['quran','hadith'].includes(s.type)?JisrCitationText.presentation(s).arabic:'';$('#subtitleEnglish').textContent=s?(s.en?.trim()||'[Translation unavailable]'):'';$('#subtitleRef').textContent=JisrCitationText.sourceCaption(s);$('#editSubtitleRef').hidden=readOnly||!s?.source;updateSubtitleImage(s)}
function updateTime(frameTime){let duration=Number.isFinite(video.duration)?video.duration:(project?.duration||48),time=typeof frameTime==='number'?frameTime:video.currentTime;$('#seek').max=duration;$('#seek').value=time;$('#time').textContent=fmt(time)+' / '+fmt(duration);let i=JisrSubtitlePreview.activeIndex(segments,time);if(i!==selected){selected=i;render()}}
let videoFrameRequest=null;
function followVideoFrames(){
  if(!video.requestVideoFrameCallback||videoFrameRequest!==null)return;
  videoFrameRequest=video.requestVideoFrameCallback((_,frame)=>{videoFrameRequest=null;updateTime(frame.mediaTime);if(!video.paused)followVideoFrames()});
}
video.addEventListener('play',followVideoFrames);
video.addEventListener('pause',()=>{if(videoFrameRequest!==null){video.cancelVideoFrameCallback(videoFrameRequest);videoFrameRequest=null}});
video.addEventListener('seeked',updateTime);
video.addEventListener('timeupdate',()=>{if(video.paused||!video.requestVideoFrameCallback)updateTime()});video.addEventListener('loadedmetadata',()=>{status();updateTime()});video.addEventListener('play',()=>{$('#play').textContent='Ⅱ';$('#play').setAttribute('aria-label','إيقاف الفيديو مؤقتًا')});video.addEventListener('pause',()=>{$('#play').textContent='▶';$('#play').setAttribute('aria-label','تشغيل الفيديو')});$('#play').onclick=()=>video.paused?video.play().catch(()=>toast('تعذر تشغيل الفيديو')):video.pause();$('#seek').oninput=e=>{video.currentTime=+e.target.value;updateTime()};$('#fullscreen').onclick=()=>$('#videoStage').requestFullscreen?.();
const volumeControl=$('#volume'),volumeOutput=$('#volumeValue'),muteButton=$('#mute');
let lastAudibleVolume=video.volume||1;
function syncVolume(){
  const level=video.muted?0:Math.round(video.volume*100);
  if(level>0)lastAudibleVolume=video.volume;
  volumeControl.value=level;volumeControl.setAttribute('aria-valuetext',level+'%');volumeOutput.value=level+'%';
  muteButton.setAttribute('aria-pressed',String(level===0));muteButton.setAttribute('aria-label',level===0?'إلغاء كتم الصوت':'كتم الصوت');
}
volumeControl.oninput=e=>{const level=Number(e.target.value)/100;video.volume=level;video.muted=level===0;if(level>0)lastAudibleVolume=level;syncVolume()};
muteButton.onclick=()=>{if(video.muted||video.volume===0){video.volume=lastAudibleVolume;video.muted=false}else{lastAudibleVolume=video.volume;video.muted=true}syncVolume()};
video.addEventListener('volumechange',syncVolume);syncVolume();
$$('[data-filter]').forEach(b=>b.onclick=()=>{filter=b.dataset.filter;$$('[data-filter]').forEach(x=>x.classList.toggle('active',x===b));render()});$('#toggleAll').onclick=()=>{showArabic=!showArabic;$('#toggleAll').textContent=showArabic?'إخفاء النص العربي':'عرض النص العربي';render()};$('#toggleAll').textContent='إخفاء النص العربي';
const subtitleFonts={plex:"'Jisr Plex',sans-serif",amiri:"'Jisr Amiri',serif",cairo:"'Jisr Cairo',sans-serif",tajawal:"'Jisr Tajawal',sans-serif",'noto-sans':"'Jisr Noto Sans Arabic',sans-serif",'noto-naskh':"'Jisr Noto Naskh Arabic',serif",system:'Arial,sans-serif'};
function applyStyle(){
  style.position='bottom';
  const e=$('#subtitle');
  e.style.fontSize=style.size+'px';e.style.setProperty('--chosen-size',style.size+'px');e.style.setProperty('--subcolor',style.color);
  e.style.fontFamily=subtitleFonts[style.font]||subtitleFonts.plex;
  $$('.subtitle>div').forEach(x=>x.style.background=style.backdrop?'#05141dbb':'transparent');
  e.style.bottom='7%';e.style.top='auto';
  $('#font').value=style.font;$('#fontSize').value=style.size;$('#fontSizeNumber').value=style.size;
  $('#backdrop').checked=style.backdrop;$('#bilingual').checked=style.bilingual;$('#customColor').value=style.color;
  $$('[data-color]').forEach(x=>{const chosen=x.dataset.color.toLowerCase()===style.color.toLowerCase();x.classList.toggle('selected',chosen);x.setAttribute('aria-pressed',String(chosen))});
  updateSubtitle();
}
let styleTimer,styleSaveQueue=Promise.resolve();
const pendingStyleSaves=new Set();
function saveStyle(){
  applyStyle();if(!project||readOnly)return;
  clearTimeout(styleTimer);
  const id=project.id,settings={...style};
  styleTimer=setTimeout(()=>{
    styleTimer=null;
    const request=styleSaveQueue.then(()=>api('/api/projects/'+id+'/style',{method:'POST',body:JSON.stringify(settings)}))
      .then(p=>{if(project?.id===p.id&&p.updated>=project.updated)Object.assign(project,{style:p.style,updated:p.updated})})
      .catch(e=>toast(e.message));
    styleSaveQueue=request;
    pendingStyleSaves.add(request);request.finally(()=>pendingStyleSaves.delete(request));
  },350);
}
$('#fontSizeNumber').oninput=e=>{const size=Number(e.target.value);if(Number.isInteger(size)&&size>=10&&size<=42){style.size=size;saveStyle()}};
$('#font').oninput=e=>{style.font=e.target.value;saveStyle()};$('#fontSize').oninput=e=>{style.size=+e.target.value;saveStyle()};$('#backdrop').onchange=e=>{style.backdrop=e.target.checked;saveStyle()};$('#bilingual').onchange=e=>{style.bilingual=e.target.checked;saveStyle()};$$('[data-color]').forEach(b=>b.onclick=()=>{style.color=b.dataset.color;saveStyle()});$('#fontSizeNumber').onchange=e=>{style.size=Math.min(42,Math.max(10,Math.round(Number(e.target.value)||18)));saveStyle()};$('#customColor').oninput=e=>{style.color=e.target.value;saveStyle()};$('#resetStyle').onclick=()=>{Object.assign(style,{font:'plex',size:18,color:'#ffffff',backdrop:true,bilingual:true,position:'bottom'});saveStyle();toast('أُعيد مظهر الترجمة الافتراضي')};
function modal(title,body){video.pause();$('#modalTitle').textContent=title;$('#modalBody').innerHTML=body;$('#modal').showModal()}$('#closeModal').onclick=()=>$('#modal').close();
const captionButton=document.createElement('button');captionButton.id='editSubtitleRef';captionButton.className='text-button';captionButton.textContent='تعديل سطر المصدر';captionButton.hidden=true;$('.player-panel .panel-heading').append(captionButton);
captionButton.onclick=()=>editCaption(selected);
function editCaption(i){
  const s=segments[i];if(readOnly||!s?.source)return;
  modal('تعديل سطر المصدر',`<label for="editCaption">سطر المصدر أسفل الترجمة</label><input id="editCaption" type="text" maxlength="200" value="${esc(JisrCitationText.sourceCaption(s))}"><p class="modal-note">اتركه فارغًا لإخفاء السطر. بيانات المرجع ورابطه تبقى محفوظة في قائمة المصادر.</p><div class="modal-actions"><button class="button primary" id="saveCaption">حفظ سطر المصدر</button><button class="button secondary" id="resetCaption">استعادة السطر الأصلي</button><button class="button secondary" id="cancelCaption">إلغاء</button></div>`);
  $('#cancelCaption').onclick=()=>$('#modal').close();
  async function saveCaption(value){try{
    if(project){const p=await api(`/api/projects/${project.id}/segments/${s.id}`,{method:'POST',body:JSON.stringify({source_caption:value})});setProject(p)}
    else{if(value===null)delete s.source_caption;else s.source_caption=value;render()}
    if(!project)seek(i);$('#modal').close();toast('تم حفظ سطر المصدر');
  }catch(e){toast(e.message)}}
  $('#saveCaption').onclick=()=>saveCaption($('#editCaption').value.trim());
  $('#resetCaption').onclick=()=>saveCaption(null);
}
$('#upload').onclick=()=>$('#fileInput').click();$('#fileInput').onchange=async e=>{let f=e.target.files[0];if(!f)return;if(!/\.(mp4|mov|webm|mkv|m4v)$/i.test(f.name))return toast('اختر ملف فيديو مدعوماً');if(f.size>250*1024*1024)return toast('الحد الأقصى 250 ميغابايت');let body=new FormData();body.append('video',f);toast('جارٍ رفع الفيديو...');try{let p=await api('/api/projects',{method:'POST',body});token=p.edit_token;localStorage.setItem('jisr-edit',JSON.stringify({id:p.id,token}));history.replaceState(null,'','/?project='+p.id);setProject(p);toast('تم رفع الفيديو');processDialog()}catch(err){toast(err.message)}e.target.value=''};
function processDialog(){modal('معالجة الفيديو',`<p>المقطع: <b>${esc(project.title)}</b></p><p>التفريغ: ElevenLabs Scribe v2. الترجمة والتصنيف: خدمة الذكاء الاصطناعي المضبوطة على الخادم. مطابقة الآيات: Quranpedia. الحديث المحتمل ينتظر التوثيق بمصدر محدد.</p><div class="modal-actions"><button class="button primary" id="runProcess">بدء المعالجة الآلية</button><button class="button secondary" id="manualProcess">إدخال نص وتوقيت يدوياً</button></div><p class="modal-note">المفاتيح تُضبط على الخادم، ولا تُكتب داخل المتصفح.</p>`);$('#runProcess').onclick=async()=>{try{await api('/api/projects/'+project.id+'/process',{method:'POST',body:'{}'});$('#modal').close();setProject({...project,status:'processing',stage:'بدأت المعالجة'});toast('بدأت المعالجة')}catch(e){toast(e.message)}};$('#manualProcess').onclick=manualDialog}
function manualDialog(){modal('إدخال مقاطع يدوياً','<p>كل سطر: البداية|النهاية|العربية|الإنجليزية. الوقت بالثواني. هذا المسار لتجربة التحرير والتصدير قبل إضافة المفاتيح.</p><textarea id="manualText" dir="ltr" style="min-height:160px" placeholder="0|5|بسم الله|In the name of Allah"></textarea><div class="modal-actions"><button class="button primary" id="saveManual">حفظ المقاطع</button></div>');$('#saveManual').onclick=async()=>{try{let entries=$('#manualText').value.trim().split(/\r?\n/).filter(Boolean).map(line=>{let [start,end,ar,en]=line.split('|');return {start:+start,end:+end,ar:ar||'',en:en||''}});let p=await api('/api/projects/'+project.id+'/manual',{method:'POST',body:JSON.stringify({segments:entries})});setProject(p);$('#modal').close();toast('تم حفظ المقاطع')}catch(e){toast(e.message)}}}
function edit(i){
  const s=segments[i];
  const arabicView=JisrCitationText.presentation(s);
  let selectedSpan=null;
  const partial=!!(project&&s.source?.partial&&s.source?.quotation_mode!=='paraphrase');
  modal('تعديل المقطع · '+fmt(s.start),`
    <label for="editStart">البداية (ثوانٍ)</label><input id="editStart" type="number" min="0" step="0.01" value="${s.start}">
    <label for="editEnd">النهاية (ثوانٍ)</label><input id="editEnd" type="number" min="0" step="0.01" value="${s.end}">
    <label for="editAr">${arabicView.fromSource?'النص العربي من المصدر':'النص العربي'}</label><textarea id="editAr">${esc(arabicView.arabic)}</textarea>
    ${arabicView.fromSource?`<p class="modal-note">${esc(sourceLabel(s))} · النص من المصدر، والمطابقة تحتاج مراجعتك قبل النشر.</p>`:''}
    ${arabicView.changed?`<details class="modal-note"><summary>التفريغ الأصلي</summary><p lang="ar">${esc(arabicView.originalArabic)}</p></details>`:''}
    <label for="editEn">الترجمة الإنجليزية</label><textarea id="editEn" dir="ltr">${esc(s.en)}</textarea>
    ${s.source?`<label for="editSourceCaption">سطر المصدر أسفل الترجمة</label><input id="editSourceCaption" type="text" maxlength="200" value="${esc(JisrCitationText.sourceCaption(s))}"><button class="text-button" id="resetSourceCaption">استعادة السطر الأصلي</button><p class="modal-note">يمكن تعديل السطر أو تركه فارغًا لإخفائه. بيانات المرجع ورابطه محفوظة.</p>`:''}
    ${partial?`<label for="sourceEnglish">${s.source.translation_status==='machine_draft'?'مسودة الترجمة الآلية المرتبطة بالمطابقة':'ترجمة المصدر الكاملة للاقتباس الجزئي'}</label><textarea id="sourceEnglish" dir="ltr" readonly>${esc(s.source.english)}</textarea><p class="modal-note">${s.source.translation_status==='machine_draft'?'لم تُسترجع ترجمة منشورة لهذا الحديث. اختيار جزء من هذه المسودة لا يجعلها ترجمة من المصدر؛ قارن مرجعًا مترجمًا أو راجع المعنى قبل النشر.':'حدد بالمؤشر الجزء الإنجليزي المقابل للكلام المسموع، ثم اضغط استخدام التحديد.'}</p><button class="button secondary" id="useSourceSpan">استخدام التحديد للترجمة</button>`:''}
    <label><input id="reviewed" type="checkbox" ${s.reviewed?'checked':''}> راجعت هذا المقطع</label>
    ${s.source?'<label><input id="rejectSource" type="checkbox"> رفض المطابقة وإزالة المرجع</label>':''}
    ${project?`<label for="surahId">سورة / آية من Quranpedia</label><div class="modal-actions"><input id="surahId" type="number" min="1" max="114" placeholder="رقم السورة"><input id="ayahId" type="number" min="1" placeholder="رقم الآية"><button class="button secondary" id="verifyQuran">توثيق الآية</button></div><label><input id="hadithParaphrase" type="checkbox" ${s.source?.quotation_mode==='paraphrase'?'checked':''}> نقل بالمعنى: أربط مرجعاً ذا صلة وأحتفظ بكلام المتحدث (ليس اقتباساً حرفياً)</label><label for="hadithId">معرّف الحديث في HadeethEnc</label><div class="modal-actions"><input id="hadithId" inputmode="numeric" placeholder="معرّف الحديث"><button class="button secondary" id="verifyHadith">توثيق الحديث</button></div>`:''}
    <div class="modal-actions"><button class="button primary" id="saveEdit">حفظ التعديلات</button><button class="button secondary" id="cancelEdit">إلغاء</button></div><p class="modal-note">تعديل اقتباس موثّق يلغي المرجع إلى أن يُعاد التحقق منه. اختيار جزء حرفي من المصدر يحافظ على التوثيق.</p>`);
  $('#cancelEdit').onclick=()=>$('#modal').close();
  let resetCaption=false;
  if(s.source){$('#resetSourceCaption').onclick=()=>{$('#editSourceCaption').value=JisrCitationText.sourceCaption(s,true);resetCaption=true};$('#editSourceCaption').oninput=()=>{resetCaption=false}}
  $('#editEn').oninput=()=>{selectedSpan=null};
  if(partial)$('#useSourceSpan').onclick=()=>{
    const field=$('#sourceEnglish'),start=field.selectionStart,end=field.selectionEnd;
    const excerpt=field.value.slice(start,end).trim();
    if(!excerpt)return toast('حدد الجزء الإنجليزي المقابل للاقتباس أولًا');
    const actualStart=start+field.value.slice(start,end).indexOf(excerpt);
    selectedSpan={start:Array.from(field.value.slice(0,actualStart)).length,end:Array.from(field.value.slice(0,actualStart+excerpt.length)).length};
    $('#editEn').value=excerpt;
    $('#reviewed').checked=false;
    toast('تم اختيار جزء من ترجمة المصدر؛ راجعه قبل التأكيد');
  };
  $('#saveEdit').onclick=async()=>{
    const changes={start:+$('#editStart').value,end:+$('#editEnd').value,ar:JisrCitationText.transcriptForSave(s,$('#editAr').value),en:$('#editEn').value.trim(),reviewed:$('#reviewed').checked,reject_source:!!$('#rejectSource')?.checked};
    if(s.source&&(resetCaption||$('#editSourceCaption').value.trim()!==JisrCitationText.sourceCaption(s)))changes.source_caption=resetCaption?null:$('#editSourceCaption').value.trim();
    if(selectedSpan)changes.source_english_span=selectedSpan;
    if(!changes.ar||!changes.en)return toast('أدخل العربية والإنجليزية');
    try{
      if(project)setProject(await api(`/api/projects/${project.id}/segments/${s.id}`,{method:'POST',body:JSON.stringify(changes)}));
      else{Object.assign(s,changes);if(changes.source_caption===null)delete s.source_caption;s.needs_review=!changes.reviewed;if(changes.reject_source){s.type='speech';s.source=null;delete s.source_caption}render()}
      $('#modal').close();toast('تم حفظ التعديل');
    }catch(e){toast(e.message)}
  };
  if($('#verifyQuran'))$('#verifyQuran').onclick=async()=>{
    try{const p=await api(`/api/projects/${project.id}/quran/${s.id}`,{method:'POST',body:JSON.stringify({surah:+$('#surahId').value,ayah:+$('#ayahId').value})});setProject(p);$('#modal').close();toast('تم توثيق الآية')}catch(e){toast(e.message)}
  };
  if($('#verifyHadith'))$('#verifyHadith').onclick=async()=>{
    try{const p=await api(`/api/projects/${project.id}/hadith/${s.id}`,{method:'POST',body:JSON.stringify({hadith_id:$('#hadithId').value.trim(),paraphrase:!!$('#hadithParaphrase')?.checked})});setProject(p);$('#modal').close();toast(p.segments.find(x=>x.id===s.id)?.source?.quotation_mode==='paraphrase'?'تم ربط المرجع كنقل بالمعنى؛ راجع الترجمة':'تم توثيق الحديث')}catch(e){toast(e.message)}
  };
}
function reference(i){
  const s=segments[i],r=s.source;if(!r)return;
  const paraphrase=r.quotation_mode==='paraphrase',arabic=r.arabic||s.ar,range=JisrCitationText.sourceExcerptRange(s);
  const sourceArabic=range?esc(arabic.slice(0,range.start))+`<mark class="source-excerpt">${esc(arabic.slice(range.start,range.end))}</mark>`+esc(arabic.slice(range.end)):esc(arabic);
  const url=JisrCitationLinks.safeUrl(r.url),host=url?new URL(url).hostname:'';
  const provider=({'quranpedia.net':'Quranpedia','dorar.net':'الدرر السنية','hadeethenc.com':'موسوعة الأحاديث النبوية · HadeethEnc'})[host]||host;
  const scope=paraphrase?'نقل بالمعنى':r.partial?(s.type==='quran'?'جزء من الآية':'جزء من الحديث'):(s.type==='quran'?'الآية كاملة':'الحديث كامل');
  modal(r.title||'تفاصيل المصدر',`<span class="tag ${s.type}">${s.type==='quran'?'قرآن كريم':'حديث نبوي'}</span><p class="modal-verse">${sourceArabic}</p>${range?'<p class="source-excerpt-hint">الجزء المميز هو الاقتباس المستخدم في الفيديو.</p>':''}${paraphrase?'<p class="modal-note">كلام المتحدث نقل بالمعنى؛ النص المعروض من المرجع، وترجمة الفيديو مسودة لكلام المتحدث.</p>':''}<p dir="ltr">${esc(r.english||s.en)}</p><h3>تفاصيل الاقتباس</h3><dl class="source-list">
    ${r.surah?`<dt>الموضع</dt><dd>${esc(r.title||`سورة ${r.surah}، الآية ${r.ayah}`)}</dd>`:''}
    <dt>الاقتباس</dt><dd>${esc(scope)}</dd><dt>التوقيت</dt><dd><span dir="ltr">${fmt(s.start)} – ${fmt(s.end)}</span></dd>
    <dt>المراجعة</dt><dd>${!project?'مثال توضيحي':JisrCitationText.reviewPending(s)?'بانتظار تأكيد المراجعة':'تمت مراجعته'}</dd>
    ${provider?`<dt>مصدر النص</dt><dd>${esc(provider)}</dd>`:''}${r.translator?`<dt>الترجمة</dt><dd>${esc(r.translator)}</dd>`:''}
    ${r.narrator||r.metadata_missing?.includes('narrator')?`<dt>الراوي</dt><dd>${esc(!r.narrator?.trim()||/^[-–—]+$/.test(r.narrator.trim())?'غير مذكور في هذا المرجع':r.narrator)}</dd>`:''}
    ${r.attribution?`<dt>التخريج</dt><dd>${esc(r.attribution)}</dd>`:''}${r.grade?`<dt>حكم المحدّث</dt><dd>${esc(r.grade)}</dd>`:''}
  </dl><div class="modal-actions source-actions">${JisrCitationLinks.links(r,s.type).map(link=>`<a class="button secondary" href="${esc(link.href)}" target="_blank" rel="noopener noreferrer" data-citation-link="${link.role}">${esc(link.label)} ↗</a>`).join('')}<button class="button secondary" id="jumpRef">تشغيل المقطع</button></div>`);
  $('#modal').scrollTop=0;
  $('#jumpRef').onclick=()=>{$('#modal').close();seek(i);video.play().catch(()=>toast('اضغط تشغيل الفيديو للاستماع إلى المقطع'))};
}
$('#sourcesNav').onclick=()=>$('#referencePanel').scrollIntoView({behavior:'smooth'});$('#editorNav').onclick=()=>window.scrollTo({top:0,behavior:'smooth'});$('#help').onclick=()=>modal('عن جسر','<p>ارفع فيديو، ثم فرّغه عبر ElevenLabs وترجمه عبر خدمة الذكاء الاصطناعي. راجع الاقتباسات والمصادر وعدّل النص والتوقيت، ثم صدّر الفيديو والترجمة وقائمة المصادر.</p><p class="modal-note">لا يوجد تسجيل دخول؛ احفظ رابط التحرير في متصفحك.</p>');
let activeExport=null;
const exportNames={srt:'ملف الترجمة',sources:'قائمة المصادر المؤكدة','sources-draft':'مسودة المصادر',mp4:'الفيديو'};
function renderExportWarnings(warnings=project?.export_warnings||[]){
  const panel=$('#exportWarnings');if(!panel)return;
  const messages=[...warnings];
  if(!project.exportable)messages.unshift('انتظر انتهاء المعالجة أو أضف نصوصًا قبل التصدير.');
  else if(!project.publishable)messages.unshift('تنبيه: يمكنك تصدير نسخة غير مراجعة. تحقّق من النصوص والمصادر قبل النشر.');
  panel.hidden=!messages.length;
  panel.innerHTML=messages.map(message=>`<p>${esc(message)}</p>`).join('');
  if($('#shareExport'))$('#shareExport').disabled=!project.publishable;
}
function renderExportState(){
  const panel=$('#exportStatus');
  if(!panel||!activeExport||panel.dataset.project!==activeExport.id)return;
  const run=activeExport,busy=run.phase==='working';
  renderExportWarnings(run.phase==='ready'?run.result.warnings:project.export_warnings);
  $('#exportGrid').setAttribute('aria-busy',String(busy));
  if($('#deleteProject'))$('#deleteProject').disabled=busy;
  [['srtExport','srt'],['sourcesExport','sources'],['draftSourcesExport','sources-draft'],['videoExport','mp4']].forEach(([id,kind])=>{
    $('#'+id).disabled=busy||(!['sources','sources-draft'].includes(kind)&&!project.exportable);
  });
  panel.hidden=false;panel.dataset.state=run.phase;panel.setAttribute('role',run.phase==='error'?'alert':'status');
  panel.replaceChildren();
  const message=document.createElement('p');
  message.textContent=busy?`جارٍ تجهيز ${exportNames[run.kind]}… ${run.kind==='mp4'?'قد يستغرق ذلك بعض الوقت حسب طول الفيديو.':''}`:run.phase==='error'?run.error:`${exportNames[run.kind]} جاهز. اضغط على زر التنزيل لحفظ الملف.`;
  panel.append(message);
  if(run.phase==='ready'){
    const link=document.createElement('a');
    link.className='button primary export-download';link.href=run.result.download_url;link.download=run.result.filename;
    link.textContent=`تنزيل ${exportNames[run.kind]} · ${['sources','sources-draft'].includes(run.kind)?'JSON':run.kind.toUpperCase()}`;
    link.onclick=e=>{
      if(run.expires<=Date.now()){
        e.preventDefault();run.phase='error';run.error='انتهت صلاحية رابط التنزيل؛ جهّز الملف مجدداً';renderExportState();
      }
    };
    panel.append(link);
    const note=document.createElement('small');
    note.textContent='الرابط متاح لمدة ١٠ دقائق. يمكنك تجهيز الملف مجدداً عند الحاجة.';
    panel.append(note);
  }
}
async function download(kind){
  const id=project.id,editToken=token,settings={...style};
  const options={headers:{'X-Edit-Token':editToken}};
  clearTimeout(styleTimer);styleTimer=null;
  await Promise.all([...pendingStyleSaves]);
  let latest=await api('/api/projects/'+id,options);
  const saved={font:'plex',size:18,color:'#ffffff',backdrop:true,bilingual:true,position:'bottom',...latest.style};
  if(Object.keys(settings).some(key=>settings[key]!==saved[key])){
    latest=await api('/api/projects/'+id+'/style',{...options,method:'POST',body:JSON.stringify(settings)});
  }
  if(project?.id===id)setProject(latest);
  const result=await api(`/api/projects/${id}/export/${kind}`,{...options,method:'POST',body:'{}'});
  if(!/^\/api\/downloads\/[A-Za-z0-9_-]{43}$/.test(result.download_url))throw Error('تعذر تجهيز رابط التنزيل');
  return result;
}
$('#export').onclick=()=>{
  if(!project){
    modal('تصدير فيديوك','<p>هذه مساحة تجريبية ببيانات توضيحية. ارفع فيديوك لتفريغه وترجمته، ثم صدّره مع الترجمة.</p><div class="modal-actions"><button class="button primary" id="demoUploadForExport">رفع فيديو للتصدير</button></div>');
    $('#demoUploadForExport').onclick=()=>{$('#modal').close();$('#upload').click()};
    return;
  }
  if(activeExport?.phase==='ready'&&(activeExport.id!==project.id||activeExport.result.project_updated!==project.updated||activeExport.settings!==JSON.stringify(style)||activeExport.expires<=Date.now()))activeExport=null;
  modal('تصدير المشروع',`<p class="modal-note">اختر الملف لتجهيزه، ثم اضغط على التنزيل. رابط المشاهدة عام لمن يملكه.</p><section id="exportWarnings" class="modal-note" role="status" hidden></section><section id="exportStatus" class="export-status" data-project="${project.id}" role="status" aria-live="polite" hidden></section><div class="export-grid" id="exportGrid" aria-busy="false"><button class="export-option" id="srtExport"><b>ملف الترجمة · SRT</b><span>الترجمة مع التوقيت</span></button><button class="export-option" id="sourcesExport"><b>قائمة المصادر المؤكدة · JSON</b><span>المراجع المراجعة فقط؛ تكون فارغة قبل التأكيد</span></button><button class="export-option" id="draftSourcesExport"><b>مسودة المصادر · JSON</b><span>المراجع المقترحة وحالة مراجعتها؛ للمراجع فقط</span></button><button class="export-option" id="videoExport"><b>الفيديو المترجم · MP4</b><span>ترجمة مدمجة، مع الصوت الأصلي</span></button><button class="export-option" id="shareExport"><b>رابط المشاهدة</b></button></div>`);
  [['srtExport','srt'],['sourcesExport','sources'],['draftSourcesExport','sources-draft'],['videoExport','mp4']].forEach(([id,kind])=>$('#'+id).onclick=async()=>{
    if(activeExport?.phase==='working'&&activeExport.id===project.id)return;
    const run={id:project.id,kind,phase:'working',settings:JSON.stringify(style)};
    activeExport=run;renderExportState();
    try{run.result=await download(kind);run.expires=Date.now()+run.result.expires_in*1000-5000;run.phase='ready'}
    catch(e){run.phase='error';run.error=e.message||'تعذر تجهيز الملف؛ حاول مجدداً'}
    if(activeExport===run){
      renderExportState();
      if(run.phase==='ready'&&$('#modal').open)$('#exportStatus .export-download')?.focus();
    }
  });
  $('#shareExport').onclick=async()=>{let url=new URL(project.share_url,location.origin).href;try{await navigator.clipboard.writeText(url);toast('تم نسخ رابط المشاهدة')}catch{toast(url)}$('#modal').close()};
  renderExportState();
};
async function boot(){try{const labels=await fetch('/source-caption-labels.json');if(labels.ok)JisrCitationText.configureCaptionLabels(await labels.json())}catch{}let share=location.pathname.match(/^\/view\/([0-9a-f]{32})$/);if(share){readOnly=true;try{setProject(await api('/api/share/'+share[1]))}catch(e){toast(e.message)}return}const query=new URLSearchParams(location.search),wanted=query.get('project');let saved=null;try{saved=JSON.parse(localStorage.getItem('jisr-edit')||'null')}catch{}if(saved&&!query.has('demo')&&(wanted===saved.id||query.get('studio')==='1')){token=saved.token;try{setProject(await api('/api/projects/'+saved.id));return}catch{localStorage.removeItem('jisr-edit');token=''}}status();render();applyStyle()}
const processButton=document.createElement('button');processButton.className='button secondary';processButton.textContent='متابعة المعالجة';processButton.onclick=()=>processDialog();$('#upload').after(processButton);
const originalStatus=status;status=function(){originalStatus();processButton.style.display=project&&!readOnly&&['uploaded','error'].includes(project.status)?'':'none';$('.eyebrow').innerHTML=project?'مساحة العمل <span>/</span> مشروع مرفوع':'مساحة العمل <span>/</span> مشروع تجريبي';$('.page-footer').lastElementChild.textContent=project?'تحرير دون تسجيل دخول':'نموذج واجهة توضيحي';video.setAttribute('aria-label',project?'فيديو المشروع':'فيديو تجريبي صامت');const steps=$$('.workflow .step'),active=project&&['uploaded','processing','error'].includes(project.status)?1:2;const progress=readOnly?3:active;$('.workflow').style.setProperty('--workflow-progress',String(progress/3));const indicator=$('#workflowProgress');indicator.setAttribute('aria-valuenow',String(progress));indicator.setAttribute('aria-valuetext',steps[progress].querySelector('span').textContent);steps.forEach((step,i)=>{step.classList.toggle('done',readOnly||i<active);step.classList.toggle('current',!readOnly&&i===active);step.querySelector('b').textContent=readOnly||i<active?'✓':String(i+1)})};
const originalRender=render;render=function(){originalRender();$$('#segments .segment').forEach(el=>{const i=+el.querySelector('[data-seek]').dataset.seek,s=segments[i];if(s?.review_issues?.length)el.querySelector('.segment-body').insertAdjacentHTML('beforeend',`<ul class="review-message">${s.review_issues.map(issue=>`<li>${esc(issue.message)}</li>`).join('')}</ul>`);if(s?.source?.translation_status==='machine_draft')el.querySelector('.segment-body').insertAdjacentHTML('beforeend','<p class="review-message">ترجمة الحديث الإنجليزية مسودة آلية؛ لم تُسترجع من مصدر ترجمة موثق.</p>');if(s?.unclear_words?.length&&!s.reviewed)el.querySelector('.segment-body').insertAdjacentHTML('beforeend',`<div class="review-message">△ كلمات غير واضحة: ${s.unclear_words.map(w=>esc(w.text)+' ('+fmt(w.start)+')').join('، ')}</div>`);})};
const originalExport=$('#export').onclick;
$('#export').onclick=()=>{
  originalExport();if(!project)return;
  $('#modalBody .export-grid').insertAdjacentHTML('beforeend','<button class="export-option" id="editLink"><b>رابط التحرير الخاص</b><span>احتفظ به لاستئناف المشروع دون حساب</span></button><button class="export-option" id="deleteProject"><b>حذف المشروع</b><span>يحذف الفيديو والملفات ورابط المشاهدة نهائياً</span></button>');
  if(!project.publishable){
    $('#exportGrid').insertAdjacentHTML('beforebegin',`<button class="button secondary" id="reviewForExport" ${project.status==='processing'?'disabled':''}>${['uploaded','error'].includes(project.status)?'متابعة المعالجة':'الانتقال إلى المراجعة'}</button>`);
    ['srtExport','videoExport'].forEach(id=>$('#'+id).disabled=!project.exportable);
    $('#shareExport').disabled=true;
    $('#reviewForExport').onclick=()=>{
      $('#modal').close();
      if(['uploaded','error'].includes(project.status)){processDialog();return}
      const first=segments.findIndex(JisrCitationText.reviewPending);
      if(first>=0){seek(first);edit(first)}else{filter='review';render();$('.transcript-panel').scrollIntoView({behavior:'smooth'})}
    };
  }
  renderExportWarnings();
  $('#editLink').onclick=async()=>{const url=new URL('/?project='+project.id+'#edit='+encodeURIComponent(token),location.origin).href;try{await navigator.clipboard.writeText(url);toast('تم نسخ رابط التحرير الخاص')}catch{toast(url)}};
  $('#deleteProject').onclick=async()=>{if(!confirm('سيُحذف الفيديو والمشروع نهائياً. هل تريد المتابعة؟'))return;try{await api('/api/projects/'+project.id,{method:'DELETE'});localStorage.removeItem('jisr-edit');location.href='/'}catch(e){toast(e.message)}};
  renderExportState();
};
async function bootLive(){const id=new URLSearchParams(location.search).get('project'),fromHash=new URLSearchParams(location.hash.slice(1)).get('edit');if(id&&fromHash)localStorage.setItem('jisr-edit',JSON.stringify({id,token:fromHash}));await boot();if(location.pathname.startsWith('/view/')&&!project){segments=[];video.removeAttribute('src');project={title:'المشروع قيد المراجعة',status:'error',stage:'المشاهدة غير متاحة حالياً',duration:0};status();render()}}
const baseEdit=edit;
edit=function(i){
  baseEdit(i);
  const choices=segments[i]?.source?.translation_candidates||[];
  const field=$('#hadithId');
  if(!project||!field||!choices.length)return;
  field.parentElement.insertAdjacentHTML('beforebegin',`<label for="hadithChoice">نتائج البحث عن ترجمة الحديث — اختر ثم اضغط توثيق الحديث</label><select id="hadithChoice"><option value="">اختيار رواية للمراجعة</option>${choices.map(c=>`<option value="${esc(c.id)}">${esc(c.id)} · ${esc(c.title)}</option>`).join('')}</select>`);
  $('#hadithChoice').onchange=e=>{field.value=e.target.value};
};
const baseReference=reference;
reference=function(i){
  baseReference(i);
  const source=segments[i]?.source;
  const list=$('#modalBody .source-list');
  if(!source||!list||segments[i].type!=='hadith')return;
  const sourced=source.translation_status==='sourced';
  const translationLabel=source.quotation_mode==='paraphrase'?'ترجمة المرجع من المصدر؛ ترجمة كلام المتحدث مسودة آلية':sourced?'ترجمة من المصدر؛ تحتاج تأكيد المحرر':'مسودة آلية تحتاج مراجعة';
  list.insertAdjacentHTML('beforeend',`<dt>حالة الترجمة</dt><dd>${translationLabel}</dd>${source.verification?`<dt>التحقق الإضافي</dt><dd>الدرر السنية · ${esc(source.verification.attribution)} · ${esc(source.verification.grade)}</dd>`:''}`);
};
const qualityStatus=status;
status=function(){
  qualityStatus();
  if(project?.status==='ready'&&project.retryable&&!readOnly){
    processButton.style.display='';processButton.textContent='إعادة فحص المعنى والمصادر';
  }else processButton.textContent='متابعة المعالجة';
};
bootLive();

