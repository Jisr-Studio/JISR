const $=q=>document.querySelector(q), $$=q=>[...document.querySelectorAll(q)];
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=n=>`${String(Math.floor((+n||0)/60)).padStart(2,'0')}:${String(Math.floor((+n||0)%60)).padStart(2,'0')}`;
const video=$('#video');
const playbackStatus=document.createElement('div');playbackStatus.className='playback-status';playbackStatus.hidden=true;playbackStatus.setAttribute('role','status');
const playbackMessage=document.createElement('span'),playbackRetry=document.createElement('button');playbackRetry.type='button';playbackRetry.className='button secondary';playbackRetry.textContent='إعادة تحميل الفيديو';playbackRetry.hidden=true;
playbackStatus.append(playbackMessage,playbackRetry);$('#videoStage').append(playbackStatus);
video.preload='auto';
video.addEventListener('loadstart',()=>{playbackMessage.textContent='جارٍ تحميل وتجهيز معاينة الفيديو…';playbackRetry.hidden=true;playbackStatus.hidden=false});
video.addEventListener('loadeddata',()=>{playbackStatus.hidden=true});
video.addEventListener('canplay',()=>{playbackStatus.hidden=true});
video.addEventListener('error',()=>{playbackMessage.textContent='تعذر تشغيل معاينة الفيديو. أعد التحميل؛ وإذا استمرت المشكلة، جرّب نسخة MP4 بترميز H.264.';playbackRetry.hidden=false;playbackStatus.hidden=false});
playbackRetry.onclick=()=>video.load();

const subtitleImage=document.createElement('img');subtitleImage.id='subtitleImage';subtitleImage.className='subtitle-image';subtitleImage.alt='';subtitleImage.hidden=true;$('#subtitle').append(subtitleImage);
const subtitlePreview=JisrSubtitlePreview.create({image:subtitleImage,container:$('#subtitle'),onError:message=>toast(message)});
let previewAppearance='',previewKey='',previewWarmTimer;
window.addEventListener('pagehide',event=>{if(!event.persisted)subtitlePreview.destroy()});
video.addEventListener('loadedmetadata',()=>{if(video.videoWidth&&video.videoHeight)$('#videoStage').style.aspectRatio=`${video.videoWidth}/${video.videoHeight}`;video.style.objectFit='contain'});
function subtitlePreviewEntry(s){
  if(!project||!s)return null;
  const query=new URLSearchParams({font:style.font,size:style.size,color:style.color,backdrop:style.backdrop,bilingual:style.bilingual});
  return {key:JSON.stringify([project.id,project.target_language,s,style]),url:`/api/projects/${project.id}/subtitle/${s.id}?${query}`,headers:token?{'X-Edit-Token':token}:{}};
}
function updateSubtitleImage(s){
  const entry=subtitlePreviewEntry(s),key=entry?.key||'';
  const appearance=JSON.stringify([project?.id,project?.target_language,style]),delay=appearance!==previewAppearance?120:0;
  previewAppearance=appearance;subtitlePreview.show(entry,delay);
  if(key===previewKey)return;
  previewKey=key;clearTimeout(previewWarmTimer);
  const upcoming=entry?segments[selected+1]:segments.find(cue=>cue.start>video.currentTime);
  const next=subtitlePreviewEntry(upcoming);
  if(next)previewWarmTimer=setTimeout(()=>subtitlePreview.warm(next),delay);
}
let project=null, token='', segments=[], filter='all', showArabic=true, selected=0, readOnly=false, poll=null, toastTimer, workflowUploading=false;
const style={font:'plex',size:18,color:'#ffffff',backdrop:true,bilingual:true,position:'bottom'};
const pendingReviews=new Set();
const demo=[
 {id:'d1',start:0,end:8,type:'speech',ar:'الطهارة ليست مجرد نظافة للجسد، بل استعداد للوقوف بين يدي الله.',translation:'Purification is more than physical cleanliness. It prepares us to stand before Allah.'},
 {id:'d2',start:8,end:16,type:'quran',ar:'إِنَّ اللَّهَ يُحِبُّ التَّوَّابِينَ وَيُحِبُّ الْمُتَطَهِّرِينَ',translation:'Indeed, Allah loves those who are constantly repentant and loves those who purify themselves.',source:{surah:2,ayah:222,title:'سورة البقرة · الآية ٢٢٢',url:'https://quranpedia.net/embed?surah=2&ayah=222',arabic:'إِنَّ اللَّهَ يُحِبُّ التَّوَّابِينَ وَيُحِبُّ الْمُتَطَهِّرِينَ',translation:'Indeed, Allah loves those who are constantly repentant and loves those who purify themselves.',translator:'مثال توضيحي'}},
 {id:'d3',start:16,end:24,type:'speech',ar:'فالوضوء عبادة نؤديها بخشوع، ونستحضر فيها معنى الطهارة.',translation:'We perform ablution with humility, mindful of the meaning of purification.'},
 {id:'d4',start:24,end:32,type:'hadith',ar:'الطُّهُورُ شَطْرُ الْإِيمَانِ',translation:'Purification is half of faith.',source:{title:'الطهور شطر الإيمان',url:'https://hadeethenc.com/ar/browse/hadith/65004',grade:'صحيح',attribution:'صحيح مسلم ٢٢٣',narrator:'أبو مالك الأشعري'}},
 {id:'d5',start:32,end:40,type:'speech',ar:'ونحرص على [كلمة غير واضحة] عند غسل الأعضاء.',translation:'We take care to [unclear word] when washing the limbs.',needs_review:true},
 {id:'d6',start:40,end:48,type:'speech',ar:'فلنجعل وضوءنا فرصة لتجديد النية والاستعداد للصلاة.',translation:'Let our ablution be an opportunity to renew our intention and prepare for prayer.'}
];segments=demo.map(x=>({...x}));
function toast(s){$('#toast').textContent=s;$('#toast').classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').classList.remove('visible'),4500)}
async function api(path,opt={}){let r=await fetch(path,{...opt,headers:{...(opt.body instanceof FormData?{}:{'Content-Type':'application/json'}),...(token?{'X-Edit-Token':token}:{}),...opt.headers}});let d=await r.json().catch(()=>({error:'تعذر قراءة استجابة الخادم'}));if(!r.ok)throw Error(d.error||'تعذر الطلب');return d}
function setProject(p){
  const sameVideo=project?.id===p.id&&project.filename===p.filename;
  const keepAppearance=sameVideo&&(styleTimer||pendingStyleSaves.size);
  const previousLanguage=project?.target_language||'en';
  project={target_language:'en',...p};segments=(p.segments||[]).map(s=>({target_language:project.target_language,...s}));
  if(previousLanguage!==project.target_language){subtitlePreview.reset();previewKey='';previewAppearance='';clearTimeout(previewWarmTimer)}
  syncLanguageControls();
  if(!keepAppearance)Object.assign(style,{font:'plex',size:18,color:'#ffffff',backdrop:true,bilingual:true,position:'bottom'},p.style||{},{position:'bottom'});
  $('#videoStage').classList.add('has-project');
  if(!sameVideo){subtitlePreview.reset();clearTimeout(previewWarmTimer);clearTimeout(styleTimer);styleTimer=null;previewKey='';video.src=p.video_url;selected=JisrSubtitlePreview.activeIndex(segments,0)}
  else selected=JisrSubtitlePreview.activeIndex(segments,video.currentTime);
  render();applyStyle();status();clearInterval(poll);
  if(p.status==='processing')poll=setInterval(async()=>{try{let next=await api('/api/projects/'+p.id);setProject(next);if(next.status==='ready')toast('اكتملت المعالجة؛ راجع النصوص والمراجع');if(next.status==='error')toast(next.error)}catch(e){clearInterval(poll);toast(e.message)}},2500);
}
function status(){$('#projectTitle').textContent=project?.title||'الطهارة.. بداية كل عبادة';$('#saveState').textContent=project?({uploaded:'تم الرفع',processing:project.stage,ready:'التعديلات محفوظة',error:project.error}[project.status]||''):'بيانات توضيحية';$('#durationLabel').textContent=project?fmt(project.duration||video.duration||0):'٤٨ ثانية';$('.demo-pill').textContent=project?'مشروع حقيقي':'نسخة تجريبية';$('.workflow-note').textContent=project?(project.stage||'جاهز للمعالجة'):'بيانات توضيحية · لا توجد معالجة آلية';$('.preview-note').textContent=project?'راجع النصوص والمصادر قبل النشر. المقاطع الطويلة تُصغّر تلقائيًا لتلائم الفيديو.':'الفيديو صامت والنصوص أمثلة مستقلة للتجربة.';$('.video-title').style.display=project?'none':'';$('.video-top').style.display=project?'none':'';$('#upload').style.display=readOnly?'none':'';$('#export').style.display=readOnly?'none':'';document.body.classList.toggle('viewer-mode',readOnly)}
function sourceLabel(s){let r=s.source;if(!r)return '';if(r.quotation_mode==='paraphrase')return (r.subtitle_mode==='source_excerpt'?'صياغة المرجع · رواية مرتبطة · ':'نقل بالمعنى · مرجع مرتبط · ')+(r.attribution||r.title||'حديث');return s.type==='quran'?r.title||'آية قرآنية':(r.attribution||r.title||'حديث')+' · '+(r.grade||'الحكم غير مذكور')+(s.needs_review?' · بانتظار المراجعة':'')}
function render(){let counts={all:segments.length,quran:segments.filter(x=>x.type==='quran').length,hadith:segments.filter(x=>x.type==='hadith').length,review:segments.filter(JisrCitationText.reviewPending).length};$$('[data-filter]').forEach(b=>{b.querySelector('span').textContent=counts[b.dataset.filter]});$('.transcript-panel .count').textContent=segments.length+' مقاطع';$('#reviewCount').textContent=counts.review;$('#reviewSummary').textContent=counts.review?counts.review+' مقطع يحتاج انتباهك':'لا توجد مقاطع تنتظر المراجعة';$('.topbar nav .count').textContent=counts.quran+counts.hadith;
let list=segments.map((s,i)=>({s,i})).filter(({s})=>filter==='all'||(filter==='review'?JisrCitationText.reviewPending(s):s.type===filter));
$('#segments').innerHTML=list.map(({s,i})=>`<div class="segment ${i===selected?'current':''}"><button class="segment-time" data-seek="${i}">${fmt(s.start)}<br><span>${fmt(s.end)}</span></button><div class="segment-body">${s.type==='quran'?'<span class="tag quran">قرآن كريم</span>':s.type==='hadith'?'<span class="tag hadith">حديث نبوي</span>':''}${JisrCitationText.reviewPending(s)?'<span class="tag review">يحتاج مراجعة</span>':''}${showArabic?`<p class="ar">${esc(JisrCitationText.presentation(s).arabic)}</p>${JisrCitationText.presentation(s).fromSource?'<span class="tag">نص المصدر</span>':''}`:''}<p class="en translation" lang="${targetLanguage()}" dir="${targetInfo().direction}" style="font-family:${esc(targetInfo().font_family)}">${esc(s.translation||'الترجمة تحتاج مراجعة')}</p>${s.citation_lookup?`<p class="modal-note" role="status">${esc(s.citation_lookup.message||"تعذر ربط المصدر؛ يحتاج إلى مراجعة")}</p>`:""}${s.source?`<button class="text-button" data-ref="${i}">${esc(sourceLabel(s))} · عرض المصدر</button>`:''}</div>${readOnly?'':`<button class="edit" data-edit="${i}" aria-label="تعديل المقطع">✎</button><div class="segment-review-footer"><button type="button" class="segment-review-button" data-review="${i}" aria-pressed="${s.reviewed===true}" ${pendingReviews.size||project?.status==='processing'||!s.translation?.trim()?'disabled':''}><span aria-hidden="true">${s.reviewed===true?'✓':''}</span> ${pendingReviews.has(s.id)?'جارٍ حفظ المراجعة…':'راجعت هذا المقطع'}</button></div>`}</div>`).join('')||'<p style="padding:20px;color:#75828d">لا توجد مقاطع في هذا العرض.</p>';
$$('[data-seek]').forEach(b=>b.onclick=()=>seek(+b.dataset.seek));$$('[data-edit]').forEach(b=>b.onclick=()=>edit(+b.dataset.edit));$$('[data-ref]').forEach(b=>b.onclick=()=>reference(+b.dataset.ref));$$('[data-review]').forEach(b=>b.onclick=()=>toggleSegmentReview(+b.dataset.review));renderCitationSuggestions();renderSources();updateSubtitle()}
async function toggleSegmentReview(index){
  const segment=segments[index];
  if(readOnly||!segment||pendingReviews.size||project?.status==='processing')return;
  if(!segment.translation?.trim())return toast('أضف الترجمة قبل تأكيد المراجعة');
  const reviewed=segment.reviewed!==true,projectId=project?.id;
  pendingReviews.add(segment.id);render();
  try{
    if(projectId){
      const updated=await api(`/api/projects/${projectId}/segments/${segment.id}`,{method:'POST',body:JSON.stringify({reviewed})});
      if(project?.id===projectId)setProject(updated);
    }else{
      segment.reviewed=reviewed;segment.needs_review=!reviewed;
      if(reviewed)segment.unclear_words=[];
    }
    if(project?.id===projectId)toast(reviewed?'تم تأكيد مراجعة المقطع':'أُعيد المقطع للمراجعة');
  }catch(error){toast(error.message)}
  finally{pendingReviews.delete(segment.id);render()}
}
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
  modal('مراجعة المصدر المقترح',`<p class="modal-note">${paraphrase?'هذا مصدر محتمل لعبارة مختصرة أو مختلفة. عند ربطه نحافظ على كلام المتحدث ونميزه كنقل بالمعنى؛ لا نستبدله بالرواية كاملة.':'قارن الاقتباس بالمصدر قبل الربط.'}</p><h3>التفريغ الأصلي</h3><p class="modal-verse">${esc(segment.ar)}</p><h3>نص المصدر</h3><p class="modal-verse">${esc(source.arabic)}</p><p class="translation" lang="${targetLanguage()}" dir="${targetInfo().direction}">${esc(source.translation||'لا تتوفر ترجمة موثقة بهذه اللغة')}</p><dl class="source-list"><dt>الراوي</dt><dd>${esc(source.narrator)}</dd><dt>الحكم</dt><dd>${esc(source.grade)}</dd><dt>التخريج</dt><dd>${esc(source.attribution)}</dd></dl><div class="modal-actions"><a class="button secondary" href="https://hadeethenc.com/ar/browse/hadith/${esc(source.id)}" target="_blank" rel="noopener noreferrer">قراءة المصدر ↗</a><button class="button" id="acceptCitationSuggestion">${paraphrase?'ربط كنقل بالمعنى':'ربط الاقتباس'}</button></div><p class="modal-note">الربط يبقى بانتظار تأكيد المراجعة.</p>`);
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
function updateSubtitle(){let s=segments[selected];$('#subtitle').classList.toggle('no-cue',!s);$('#subtitleArabic').textContent=s&&style.bilingual&&['quran','hadith'].includes(s.type)?JisrCitationText.presentation(s).arabic:'';$('#subtitleTranslation').textContent=s?(s.translation?.trim()||'['+JisrLanguages.label('unavailable',s)+']'):'';$('#subtitleRef').textContent=JisrCitationText.sourceCaption(s);$('#editSubtitleRef').hidden=readOnly||!s?.source;updateSubtitleImage(s)}
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
  $('#subtitleTranslation').style.fontFamily=targetInfo().font_family;$('#subtitleRef').style.fontFamily=targetInfo().font_family;
  ['subtitleTranslation','subtitleRef'].forEach(id=>{const el=$('#'+id);el.dir=targetInfo().direction;el.lang=targetLanguage()});
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
function modal(title,body){$('#modal').classList.remove('export-dialog');video.pause();$('#modalTitle').textContent=title;$('#modalBody').innerHTML=body;$('#modal').showModal()}$('#closeModal').onclick=()=>$('#modal').close();
const captionButton=document.createElement('button');captionButton.id='editSubtitleRef';captionButton.className='text-button';captionButton.textContent='تعديل سطر المصدر';captionButton.hidden=true;$('.player-panel .panel-heading').append(captionButton);
captionButton.onclick=()=>editCaption(selected);
function editCaption(i){
  const s=segments[i];if(readOnly||!s?.source)return;
  modal('تعديل سطر المصدر',`<label for="editCaption">سطر المصدر أسفل الترجمة</label><input id="editCaption" class="translation" lang="${targetLanguage()}" dir="${targetInfo().direction}" type="text" maxlength="200" value="${esc(JisrCitationText.sourceCaption(s))}"><p class="modal-note">اتركه فارغًا لإخفاء السطر. بيانات المرجع ورابطه تبقى محفوظة في قائمة المصادر.</p><div class="modal-actions"><button class="button primary" id="saveCaption">حفظ سطر المصدر</button><button class="button secondary" id="resetCaption">استعادة السطر الأصلي</button><button class="button secondary" id="cancelCaption">إلغاء</button></div>`);
  $('#cancelCaption').onclick=()=>$('#modal').close();
  async function saveCaption(value){try{
    if(project){const p=await api(`/api/projects/${project.id}/segments/${s.id}`,{method:'POST',body:JSON.stringify({source_caption:value})});setProject(p)}
    else{if(value===null)delete s.source_caption;else s.source_caption=value;render()}
    if(!project)seek(i);$('#modal').close();toast('تم حفظ سطر المصدر');
  }catch(e){toast(e.message)}}
  $('#saveCaption').onclick=()=>saveCaption($('#editCaption').value.trim());
  $('#resetCaption').onclick=()=>saveCaption(null);
}
function requireUploadLanguage(){
  if(uploadLanguage)return true;
  toast('اختر لغة الترجمة أولاً');
  const visible=$$('[data-upload-language]').find(el=>el.parentElement.getBoundingClientRect().width>0);
  const trigger=visible?.parentElement.querySelector('.language-trigger');
  if(trigger){trigger.focus();trigger.click()}else visible?.focus();
  return false;
}
function chooseUploadVideo(){if(requireUploadLanguage())$('#fileInput').click()}
$('#upload').onclick=chooseUploadVideo;$('#fileInput').onchange=async e=>{let f=e.target.files[0];if(!f)return;if(!requireUploadLanguage()){e.target.value='';return;}if(!/\.(mp4|mov|webm|mkv|m4v)$/i.test(f.name))return toast('اختر ملف فيديو مدعوماً');if(f.size>250*1024*1024)return toast('الحد الأقصى 250 ميغابايت');let body=new FormData();body.append('target_language',uploadLanguage);body.append('video',f);toast('جارٍ رفع الفيديو...');workflowUploading=true;syncWorkflow();try{let p=await api('/api/projects',{method:'POST',body});token=p.edit_token;localStorage.setItem('jisr-edit',JSON.stringify({id:p.id,token}));history.replaceState(null,'','/?project='+p.id);setProject(p);toast('تم رفع الفيديو');processDialog()}catch(err){toast(err.message)}finally{workflowUploading=false;status()}e.target.value=''};
function processDialog(){modal('معالجة الفيديو',`<p>المقطع: <b>${esc(project.title)}</b></p><p>التفريغ: ElevenLabs Scribe v2. الترجمة والتصنيف: خدمة الذكاء الاصطناعي المضبوطة على الخادم. مطابقة الآيات: Quranpedia. الحديث المحتمل ينتظر التوثيق بمصدر محدد.</p><div class="modal-actions"><button class="button primary" id="runProcess">بدء المعالجة الآلية</button><button class="button secondary" id="manualProcess">إدخال نص وتوقيت يدوياً</button></div><p class="modal-note">المفاتيح تُضبط على الخادم، ولا تُكتب داخل المتصفح.</p>`);$('#runProcess').onclick=async()=>{try{await api('/api/projects/'+project.id+'/process',{method:'POST',body:'{}'});$('#modal').close();setProject({...project,status:'processing',stage:'بدأت المعالجة'});toast('بدأت المعالجة')}catch(e){toast(e.message)}};$('#manualProcess').onclick=manualDialog}
function manualDialog(){modal('إدخال مقاطع يدوياً','<p>كل سطر: البداية|النهاية|العربية|الترجمة. الوقت بالثواني. هذا المسار لتجربة التحرير والتصدير قبل إضافة المفاتيح.</p><textarea id="manualText" dir="ltr" style="min-height:160px" placeholder="0|5|بسم الله|In the name of Allah"></textarea><div class="modal-actions"><button class="button primary" id="saveManual">حفظ المقاطع</button></div>');$('#saveManual').onclick=async()=>{try{let entries=$('#manualText').value.trim().split(/\r?\n/).filter(Boolean).map(line=>{let [start,end,ar,translation]=line.split('|');return {start:+start,end:+end,ar:ar||'',translation:translation||''}});let p=await api('/api/projects/'+project.id+'/manual',{method:'POST',body:JSON.stringify({segments:entries})});setProject(p);$('#modal').close();toast('تم حفظ المقاطع')}catch(e){toast(e.message)}}}
function edit(i){
  const s=segments[i];
  const arabicView=JisrCitationText.presentation(s);
  let selectedSpan=null;
  const relatedHadith=s.type==='hadith'&&s.source?.quotation_mode==='paraphrase';
  const sourceWording=s.source?.subtitle_mode==='source_excerpt';
  const partial=!!(project&&s.source?.partial&&s.source.translation_status==='sourced'&&s.source.translation);
  modal('تعديل المقطع · '+fmt(s.start),`
    <label for="editStart">البداية (ثوانٍ)</label><input id="editStart" type="number" min="0" step="0.01" value="${s.start}">
    <label for="editEnd">النهاية (ثوانٍ)</label><input id="editEnd" type="number" min="0" step="0.01" value="${s.end}">
    <label for="editAr">${arabicView.fromSource?'النص العربي من المصدر':'النص العربي'}</label><textarea id="editAr">${esc(arabicView.arabic)}</textarea>
    ${arabicView.fromSource?`<p class="modal-note">${esc(sourceLabel(s))} · النص من المصدر، والمطابقة تحتاج مراجعتك قبل النشر.</p>`:''}
    ${arabicView.changed?`<details class="modal-note"><summary>التفريغ الأصلي</summary><p lang="ar">${esc(arabicView.originalArabic)}</p></details>`:''}
    <label for="editTranslation">الترجمة باللغة المختارة</label><textarea id="editTranslation" class="translation" lang="${targetLanguage()}" dir="${targetInfo().direction}">${esc(s.translation)}</textarea>
    ${project&&relatedHadith&&(s.source.translation_status==='sourced'||sourceWording)?`<label><input id="useSourceWording" type="checkbox" ${sourceWording?'checked':''}> استخدام نص المرجع وترجمته في الفيديو</label><p class="modal-note">يعرض الجزء المقابل من الرواية المرتبطة، مع الاحتفاظ بالتفريغ الأصلي. صياغة المرجع قد تختلف عن كلام المتحدث؛ حدد ترجمتها باللغة المختارة أدناه وراجعها قبل النشر.</p>`:''}
    ${s.source?`<label for="editSourceCaption">سطر المصدر أسفل الترجمة</label><input id="editSourceCaption" class="translation" lang="${targetLanguage()}" dir="${targetInfo().direction}" type="text" maxlength="200" value="${esc(JisrCitationText.sourceCaption(s))}"><button class="text-button" id="resetSourceCaption">استعادة السطر الأصلي</button><p class="modal-note">يمكن تعديل السطر أو تركه فارغًا لإخفائه. بيانات المرجع ورابطه محفوظة.</p>`:''}
    ${partial?`<label for="sourceTranslation">${s.source.translation_status==='machine_draft'?'مسودة الترجمة الآلية المرتبطة بالمطابقة':'ترجمة المصدر الكاملة للاقتباس الجزئي'}</label><textarea id="sourceTranslation" class="translation" lang="${targetLanguage()}" dir="${targetInfo().direction}" readonly>${esc(s.source.translation)}</textarea><p class="modal-note">${s.source.translation_status==='machine_draft'?'لم تُسترجع ترجمة منشورة لهذا الحديث. اختيار جزء من هذه المسودة لا يجعلها ترجمة من المصدر؛ قارن مرجعًا مترجمًا أو راجع المعنى قبل النشر.':'حدد بالمؤشر جزء الترجمة المقابل للكلام المسموع، ثم اضغط استخدام التحديد.'}</p><button class="button secondary" id="useSourceSpan">استخدام التحديد للترجمة</button>`:''}
    ${s.source?'<label><input id="rejectSource" type="checkbox"> رفض المطابقة وإزالة المرجع</label>':''}
    ${project?`<label for="surahId">سورة / آية من Quranpedia</label><div class="modal-actions"><input id="surahId" type="number" min="1" max="114" placeholder="رقم السورة"><input id="ayahId" type="number" min="1" placeholder="رقم الآية"><button class="button secondary" id="verifyQuran">توثيق الآية</button></div><label><input id="hadithParaphrase" type="checkbox" ${s.source?.quotation_mode==='paraphrase'?'checked':''}> نقل بالمعنى: أربط مرجعاً ذا صلة وأحتفظ بكلام المتحدث (ليس اقتباساً حرفياً)</label><label for="hadithId">معرّف الحديث في HadeethEnc</label><div class="modal-actions"><input id="hadithId" inputmode="numeric" placeholder="معرّف الحديث"><button class="button secondary" id="verifyHadith">توثيق الحديث</button></div>`:''}
    ${project&&s.audio_gap?'<p class="modal-note">استمع أولاً: اكتب الكلام وترجمته إن وجد. إذا كان صوتاً غير كلامي، يمكنك تجاهل تنبيه التفريغ.</p><button class="button secondary" id="dismissGap">تجاهل التنبيه: الصوت ليس كلاماً</button>':''}
    <div class="modal-actions"><button class="button primary" id="saveEdit">حفظ التعديلات</button><button class="button secondary" id="cancelEdit">إلغاء</button></div><p class="modal-note">تعديل اقتباس موثّق يلغي المرجع إلى أن يُعاد التحقق منه. اختيار جزء حرفي من المصدر يحافظ على التوثيق.</p>`);
  $('#cancelEdit').onclick=()=>$('#modal').close();
  if($('#dismissGap'))$('#dismissGap').onclick=async()=>{
    if(!confirm('هل استمعت وتأكدت أن الصوت ليس كلاماً يحتاج تفريغاً؟'))return;
    try{setProject(await api(`/api/projects/${project.id}/segments/${s.id}`,{method:'POST',body:JSON.stringify({dismiss_gap:true})}));$('#modal').close();toast('تم تجاهل التنبيه بعد تأكيدك')}catch(e){toast(e.message)}
  };
  let resetCaption=false;
  if(s.source){$('#resetSourceCaption').onclick=()=>{$('#editSourceCaption').value=JisrCitationText.sourceCaption(s,true);resetCaption=true};$('#editSourceCaption').oninput=()=>{resetCaption=false}}
  $('#editTranslation').oninput=()=>{selectedSpan=null};
  if($('#useSourceWording'))$('#useSourceWording').onchange=event=>{
    selectedSpan=null;
    if(!event.target.checked)$('#editTranslation').value=s.source.speech_translation||s.translation;
  };
  if(partial)$('#useSourceSpan').onclick=()=>{
    const field=$('#sourceTranslation'),start=field.selectionStart,end=field.selectionEnd;
    const excerpt=field.value.slice(start,end).trim();
    if(!excerpt)return toast('حدد جزء الترجمة المقابل للاقتباس أولًا');
    const actualStart=start+field.value.slice(start,end).indexOf(excerpt);
    selectedSpan={start:Array.from(field.value.slice(0,actualStart)).length,end:Array.from(field.value.slice(0,actualStart+excerpt.length)).length};
    if($('#useSourceWording'))$('#useSourceWording').checked=true;
    $('#editTranslation').value=excerpt;
    toast('تم اختيار جزء من ترجمة المصدر؛ راجعه قبل التأكيد');
  };
  $('#saveEdit').onclick=async()=>{
    const changes={start:+$('#editStart').value,end:+$('#editEnd').value,ar:JisrCitationText.transcriptForSave(s,$('#editAr').value),translation:$('#editTranslation').value.trim(),reject_source:!!$('#rejectSource')?.checked};
    const wordingChanged=!!$('#useSourceWording')&&$('#useSourceWording').checked!==sourceWording;
    if($('#useSourceWording')&&(wordingChanged||selectedSpan))changes.use_source_wording=$('#useSourceWording').checked;
    const contentChanged=changes.ar!==s.ar||changes.translation!==s.translation||changes.start!==s.start||changes.end!==s.end||changes.reject_source||!!selectedSpan||wordingChanged;
    changes.reviewed=contentChanged?false:s.reviewed===true;
    if(s.source&&(resetCaption||$('#editSourceCaption').value.trim()!==JisrCitationText.sourceCaption(s)))changes.source_caption=resetCaption?null:$('#editSourceCaption').value.trim();
    if(selectedSpan)changes.source_translation_span=selectedSpan;
    if(!changes.ar||!changes.translation)return toast('أدخل العربية والترجمة');
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
  const paraphrase=r.quotation_mode==='paraphrase',sourceWording=r.subtitle_mode==='source_excerpt',arabic=r.arabic||s.ar,range=JisrCitationText.sourceExcerptRange(s);
  const sourceArabic=range?esc(arabic.slice(0,range.start))+`<mark class="source-excerpt">${esc(arabic.slice(range.start,range.end))}</mark>`+esc(arabic.slice(range.end)):esc(arabic);
  const url=JisrCitationLinks.safeUrl(r.url),host=url?new URL(url).hostname:'';
  const provider=({'quranpedia.net':'Quranpedia','dorar.net':'الدرر السنية','hadeethenc.com':'موسوعة الأحاديث النبوية · HadeethEnc'})[host]||host;
  const scope=paraphrase?(sourceWording?'صياغة المرجع · رواية مرتبطة':'نقل بالمعنى'):r.partial?(s.type==='quran'?'جزء من الآية':'جزء من الحديث'):(s.type==='quran'?'الآية كاملة':'الحديث كامل');
  modal(r.title||'تفاصيل المصدر',`<span class="tag ${s.type}">${s.type==='quran'?'قرآن كريم':'حديث نبوي'}</span><p class="modal-verse">${sourceArabic}</p>${range?'<p class="source-excerpt-hint">الجزء المميز هو الاقتباس المستخدم في الفيديو.</p>':''}${paraphrase?`<p class="modal-note">${sourceWording?'الفيديو يعرض صياغة المرجع المرتبط. قد تختلف هذه الرواية عن كلام المتحدث؛ راجع الجزء العربي وترجمته قبل النشر.':'كلام المتحدث نقل بالمعنى؛ النص المعروض من المرجع، وترجمة الفيديو مسودة لكلام المتحدث.'}</p>`:''}<p class="translation" lang="${targetLanguage()}" dir="${targetInfo().direction}">${esc(r.translation||'لا تتوفر ترجمة موثقة بهذه اللغة')}</p><h3>تفاصيل الاقتباس</h3><dl class="source-list">
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
let activeExport=null,exportClock=null;
$('#modal').addEventListener('close',()=>{clearInterval(exportClock);exportClock=null});
function updateExportClock(){
  const clock=$('#exportElapsed');
  if(clock&&activeExport?.phase==='working')clock.textContent='الوقت المنقضي '+fmt((Date.now()-activeExport.started)/1000);
}
function exportFileSize(bytes){
  return bytes>=1024*1024?(bytes/(1024*1024)).toFixed(1)+' MB':Math.max(1,Math.ceil(bytes/1024))+' KB';
}
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
  syncWorkflow();
  clearInterval(exportClock);exportClock=null;
  const panel=$('#exportStatus');
  if(!panel||!activeExport||project?.id!==activeExport.id||panel.dataset.project!==activeExport.id)return;
  const run=activeExport,busy=run.phase==='working';
  renderExportWarnings(run.phase==='ready'?run.result.warnings:project.export_warnings);
  $('#exportGrid').setAttribute('aria-busy',String(busy));
  if($('#deleteProject'))$('#deleteProject').disabled=busy;
  [['srtExport','srt'],['sourcesExport','sources'],['draftSourcesExport','sources-draft'],['videoExport','mp4']].forEach(([id,kind])=>{
    const button=$('#'+id);
    button.disabled=busy||(!['sources','sources-draft'].includes(kind)&&!project.exportable);
    button.setAttribute('aria-pressed',String(run.kind===kind));
  });
  panel.hidden=false;panel.dataset.state=run.phase;panel.setAttribute('role',run.phase==='error'?'alert':'status');
  panel.replaceChildren();
  const icon=document.createElement('span');icon.className='export-state-icon';icon.setAttribute('aria-hidden','true');
  icon.textContent=busy?'':run.phase==='error'?'!':'✓';panel.append(icon);
  const heading=document.createElement('h3');
  heading.textContent=busy?`جارٍ تجهيز ${exportNames[run.kind]}…`:run.phase==='error'?'تعذر تجهيز الملف':run.downloadRequested?'الملف جاهز · تم طلب التنزيل':'ملفك جاهز للتنزيل';panel.append(heading);
  const message=document.createElement('p');
  message.textContent=busy?(run.kind==='mp4'?'نُجهّز الفيديو بالترجمة المدمجة والصوت الأصلي. يمكنك متابعة التجهيز عند إعادة فتح هذه النافذة.':'نُجهّز الملف بالتعديلات المحفوظة. انتظر ظهور زر التنزيل.'):run.phase==='error'?run.error:run.downloadRequested?'تابع التنزيل في متصفحك. إذا لم يبدأ، اضغط زر التنزيل مرة أخرى.':'اضغط على الزر أدناه لحفظ الملف على جهازك.';panel.append(message);
  const steps=document.createElement('div');steps.className='export-phases';steps.setAttribute('aria-label','مراحل التصدير');
  ['اختيار الصيغة','تجهيز الملف','التنزيل'].forEach((label,i)=>{
    const item=document.createElement('span');item.textContent=(i===0||i===1&&run.phase==='ready'?'✓ ':'')+label;
    if(i===(busy||run.phase==='error'?1:2))item.setAttribute('aria-current','step');
    steps.append(item);
  });panel.append(steps);
  if(busy){
    const activity=document.createElement('div');activity.className='export-activity';activity.setAttribute('role','progressbar');activity.setAttribute('aria-label','تجهيز الملف قيد التنفيذ');panel.append(activity);
    const clock=document.createElement('small');clock.id='exportElapsed';clock.setAttribute('aria-live','off');panel.append(clock);
    updateExportClock();exportClock=setInterval(updateExportClock,1000);
  }else if(run.phase==='ready'){
    const file=document.createElement('div');file.className='export-file-summary';
    const name=document.createElement('span');name.dir='ltr';name.textContent=run.result.filename;
    const size=document.createElement('span');size.dir='ltr';size.textContent=exportFileSize(run.result.size);
    file.append(name,size);panel.append(file);
    const link=document.createElement('a');
    link.className='button primary export-download';link.href=run.result.download_url;link.download=run.result.filename;
    link.textContent=`↓ تنزيل ${exportNames[run.kind]} · ${['sources','sources-draft'].includes(run.kind)?'JSON':run.kind.toUpperCase()}`;
    link.onclick=e=>{
      if(run.expires<=Date.now()){
        e.preventDefault();run.phase='error';run.error='انتهت صلاحية رابط التنزيل؛ جهّز الملف مجدداً';renderExportState();return;
      }
      run.downloadRequested=true;
      heading.textContent='الملف جاهز · تم طلب التنزيل';
      message.textContent='تابع التنزيل في متصفحك. إذا لم يبدأ، اضغط زر التنزيل مرة أخرى.';
      link.textContent='↓ تنزيل الملف مرة أخرى';
    };
    panel.append(link);
    const note=document.createElement('small');note.textContent='رابط التنزيل مؤقت. يمكنك تجهيز الملف مجدداً إذا انتهت صلاحيته.';panel.append(note);
  }else{
    const retry=document.createElement('button');retry.className='button primary';retry.textContent='إعادة المحاولة';
    retry.onclick=()=>$('#'+({mp4:'videoExport',srt:'srtExport',sources:'sourcesExport','sources-draft':'draftSourcesExport'}[run.kind])).click();panel.append(retry);
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
  if(activeExport&&(activeExport.id!==project.id||(activeExport.phase==='ready'&&(activeExport.result.project_updated!==project.updated||activeExport.settings!==JSON.stringify(style)||activeExport.expires<=Date.now()))))activeExport=null;
  modal('تصدير وتنزيل',`<p class="export-intro">اختر ما تريد تنزيله. نُجهّز الملف أولاً، ثم يظهر زر حفظه على جهازك.</p>
    <section id="exportStatus" class="export-status" data-project="${project.id}" role="status" aria-live="polite" hidden></section>
    <section id="exportWarnings" class="modal-note export-warnings" role="status" hidden></section>
    <div class="export-grid" id="exportGrid" aria-busy="false">
      <button class="export-option export-video" id="videoExport"><span class="export-format">MP4</span><b>تنزيل الفيديو المترجم</b><span>الفيديو مع الترجمة المدمجة والصوت الأصلي، حسب المظهر الذي اخترته.</span><strong>تجهيز الفيديو ←</strong></button>
      <h3 class="export-section-title">ملفات إضافية</h3>
      <div class="export-secondary"><button class="export-option" id="srtExport"><span class="export-format">SRT</span><b>ملف الترجمة</b><span>نص الترجمة وتوقيتها للاستخدام في برامج المونتاج.</span></button><button class="export-option" id="sourcesExport"><span class="export-format">JSON</span><b>المصادر المؤكدة</b><span>المراجع التي أكّدت مراجعتها؛ تكون القائمة فارغة قبل التأكيد.</span></button></div>
      <details class="export-extra"><summary>مسودة المصادر للمراجعة</summary><button class="export-option" id="draftSourcesExport"><b>تنزيل مسودة المصادر · JSON</b><span>المراجع المقترحة وحالة مراجعتها، بما فيها المراجع غير المؤكدة.</span></button></details>
      <section class="export-sharing"><h3 class="export-section-title">مشاركة المشروع</h3><button class="export-option" id="shareExport"><b>نسخ رابط المشاهدة</b><span>${project.publishable?'رابط عام للمشاهدة، دون أدوات تحرير.':'أكمل مراجعة المقاطع والمصادر لتفعيل رابط المشاهدة.'}</span></button></section>
      <details class="export-extra" id="projectExportTools"><summary>رابط التحرير وإدارة المشروع</summary><div id="exportProjectTools"></div></details>
    </div>`);
  $('#modal').classList.add('export-dialog');
  renderExportWarnings();
  [['srtExport','srt'],['sourcesExport','sources'],['draftSourcesExport','sources-draft'],['videoExport','mp4']].forEach(([id,kind])=>$('#'+id).disabled=!['sources','sources-draft'].includes(kind)&&!project.exportable);
  [['srtExport','srt'],['sourcesExport','sources'],['draftSourcesExport','sources-draft'],['videoExport','mp4']].forEach(([id,kind])=>$('#'+id).onclick=async()=>{
    if(activeExport?.phase==='working'&&activeExport.id===project.id)return;
    const run={id:project.id,kind,phase:'working',started:Date.now(),settings:JSON.stringify(style)};
    activeExport=run;renderExportState();$('#exportStatus').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'nearest'});
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
async function boot(){const languageResponse=await fetch('/languages.json');if(!languageResponse.ok)throw Error('تعذر تحميل قائمة اللغات');JisrLanguages.configure(await languageResponse.json());syncLanguageControls();try{const labels=await fetch('/source-caption-labels.json');if(labels.ok)JisrCitationText.configureCaptionLabels(await labels.json())}catch{}let share=location.pathname.match(/^\/view\/([0-9a-f]{32})$/);if(share){readOnly=true;try{setProject(await api('/api/share/'+share[1]))}catch(e){toast(e.message)}return}const query=new URLSearchParams(location.search),wanted=query.get('project');let saved=null;try{saved=JSON.parse(localStorage.getItem('jisr-edit')||'null')}catch{}if(saved&&!query.has('demo')&&(wanted===saved.id||query.get('studio')==='1')){token=saved.token;try{setProject(await api('/api/projects/'+saved.id));return}catch{localStorage.removeItem('jisr-edit');token=''}}status();render();applyStyle()}
const processButton=document.createElement('button');processButton.className='button secondary';processButton.textContent='متابعة المعالجة';processButton.onclick=()=>processDialog();$('#upload').after(processButton);
function syncWorkflow(){
  const bar=$('.workflow'),steps=$$('.workflow .step');
  const exporting=project&&activeExport?.id===project.id?activeExport:null;
  let current=2,state='idle',progress=2/3,note='مثال توضيحي · جرّب التحرير والمصادر';
  if(readOnly){current=3;progress=1;state='complete';note='اكتملت المراجعة · رابط مشاهدة';}
  else if(workflowUploading){current=0;progress=0;state='busy';note='جارٍ رفع الفيديو… انتظر اكتمال الرفع';}
  else if(project){
    if(project.status==='uploaded'){current=1;progress=1/3;note='تم رفع الفيديو · ابدأ المعالجة الآلية أو أدخل النص يدوياً';}
    else if(project.status==='processing'){
      current=1;state='busy';
      const stage=project.stage||'';
      progress=stage.includes('مطابقة')||stage.includes('المراجع')?0.6:stage.includes('ترجم')||stage.includes('المعنى')?0.48:1/3;
      note=stage||'جارٍ تحليل الفيديو';
    }else if(project.status==='error'){current=1;progress=1/3;state='error';note='توقفت المعالجة · يمكنك إعادة المحاولة';}
    else{
      const remaining=segments.filter(JisrCitationText.reviewPending).length;
      note=remaining?`${remaining} مقطع يحتاج مراجعة · يمكنك تصدير مسودة`:'المعالجة مكتملة · راجع النتيجة أو صدّر المشروع';
    }
    if(exporting&&project.status!=='processing'&&project.status!=='error'){
      current=3;progress=1;
      state=exporting.phase==='working'?'busy':exporting.phase==='error'?'error':'complete';
      note=exporting.phase==='working'?`جارٍ تجهيز ${exportNames[exporting.kind]}…`:exporting.phase==='error'?'تعذر التصدير · حاول مجدداً':`${exportNames[exporting.kind]} جاهز للتنزيل`;
      if(exporting.phase==='ready'&&!project.publishable){
        current=2;progress=2/3;state='idle';
        note=`مسودة ${exportNames[exporting.kind]} جاهزة للتنزيل · المراجعة لم تكتمل`;
      }
    }
  }
  bar.dataset.state=state;
  bar.dataset.current=String(current);
  bar.style.setProperty('--workflow-progress',String(progress));
  bar.setAttribute('aria-busy',String(state==='busy'));
  const indicator=$('#workflowProgress');
  indicator.setAttribute('aria-valuenow',String(current));
  indicator.setAttribute('aria-valuetext',note);
  const label=$('.workflow-note');
  if(label.textContent!==note)label.textContent=note;
  steps.forEach((step,i)=>{
    const done=(i<current||(state==='complete'&&i===current))&&!(i===2&&project&&!project.publishable&&!readOnly);
    step.classList.toggle('done',done);
    step.classList.toggle('current',i===current&&state!=='complete');
    if(i===current)step.setAttribute('aria-current','step');else step.removeAttribute('aria-current');
    const value=done?'✓':String(i+1);
    if(step.querySelector('b').textContent!==value)step.querySelector('b').textContent=value;
  });
}
const originalStatus=status;status=function(){originalStatus();processButton.style.display=project&&!readOnly&&['uploaded','error'].includes(project.status)?'':'none';$('.eyebrow').innerHTML=project?'مساحة العمل <span>/</span> مشروع مرفوع':'مساحة العمل <span>/</span> مشروع تجريبي';$('.page-footer').lastElementChild.textContent=project?'تحرير دون تسجيل دخول':'نموذج واجهة توضيحي';video.setAttribute('aria-label',project?'فيديو المشروع':'فيديو تجريبي صامت');syncWorkflow()};
const workflowActivity=document.createElement('span');workflowActivity.className='workflow-activity';workflowActivity.setAttribute('aria-hidden','true');$('.workflow').append(workflowActivity);
video.addEventListener('play',()=>{$('.workflow').dataset.playing='true'});
video.addEventListener('pause',()=>{$('.workflow').dataset.playing='false'});

const originalRender=render;render=function(){originalRender();syncWorkflow();$$('#segments .segment').forEach(el=>{const i=+el.querySelector('[data-seek]').dataset.seek,s=segments[i];if(s?.review_issues?.length)el.querySelector('.segment-body').insertAdjacentHTML('beforeend',`<ul class="review-message">${s.review_issues.map(issue=>`<li>${esc(issue.message)}</li>`).join('')}</ul>`);if(s?.source&&s.source.translation_status!=='sourced')el.querySelector('.segment-body').insertAdjacentHTML('beforeend','<p class="review-message">لا تتوفر ترجمة موثقة بهذه اللغة. الترجمة الظاهرة مسودة آلية لكلام المتحدث تحتاج مراجعة، ولا تنسب إلى المصدر.</p>');if(s?.unclear_words?.length&&!s.reviewed)el.querySelector('.segment-body').insertAdjacentHTML('beforeend',`<div class="review-message">△ كلمات غير واضحة: ${s.unclear_words.map(w=>esc(w.text)+' ('+fmt(w.start)+')').join('، ')}</div>`);})};
const originalExport=$('#export').onclick;
$('#export').onclick=()=>{
  originalExport();if(!project)return;
  $('#exportProjectTools').insertAdjacentHTML('beforeend','<button class="export-option" id="editLink"><b>رابط التحرير الخاص</b><span>احتفظ به لاستئناف المشروع دون حساب</span></button><button class="export-option" id="deleteProject"><b>حذف المشروع</b><span>يحذف الفيديو والملفات ورابط المشاهدة نهائياً</span></button>');
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
  const translationLabel=source.translation_status==='unavailable'?'لا تتوفر ترجمة موثقة بهذه اللغة':source.subtitle_mode==='source_excerpt'?'ترجمة الجزء المختار من المرجع؛ تحتاج تأكيد المحرر':source.quotation_mode==='paraphrase'?'ترجمة المرجع من المصدر؛ ترجمة كلام المتحدث مسودة آلية':sourced?'ترجمة من المصدر؛ تحتاج تأكيد المحرر':'مسودة آلية تحتاج مراجعة';
  list.insertAdjacentHTML('beforeend',`<dt>حالة الترجمة</dt><dd>${translationLabel}</dd>${source.verification?`<dt>التحقق الإضافي</dt><dd>الدرر السنية · ${esc(source.verification.attribution)} · ${esc(source.verification.grade)}</dd>`:''}`);
};
const qualityStatus=status;
status=function(){
  qualityStatus();
  if(project?.status==='ready'&&project.retryable&&!readOnly){
    processButton.style.display='';processButton.textContent='إعادة فحص المعنى والمصادر';
  }else processButton.textContent='متابعة المعالجة';
};

let uploadLanguage='';
function targetLanguage(){return project?.target_language||'en'}
function targetInfo(){return JisrLanguages.info(targetLanguage())}
function syncLanguageControls(){
  $$('[data-upload-language]').forEach(el=>{el.value=uploadLanguage;el.disabled=workflowUploading;el.onchange=event=>{uploadLanguage=event.target.value;syncLanguageControls()}});
  $('#currentLanguage').textContent=targetInfo().name_ar;
  $('#projectLanguageControls').hidden=readOnly||!project||!['ready','error'].includes(project.status)||!segments.length;
  $('#projectLanguageChoice').value=targetLanguage();
  $('#retranslateLanguage').disabled=project?.status==='processing';
  document.documentElement.style.setProperty('--translation-font',targetInfo().font_family);
  document.dispatchEvent(new Event('jisr-language-sync'));
}
$('#retranslateLanguage').onclick=()=>{
  if(!project||readOnly||pendingReviews.size||project.status==='processing')return;
  const language=$('#projectLanguageChoice').value;
  if(language===targetLanguage())return toast('اختر لغة أخرى لإعادة الترجمة');
  const id=project.id;
  modal('إعادة الترجمة إلى '+JisrLanguages.info(language).name_ar,`<p>سيبقى التفريغ العربي وتوقيت الكلمات والمراجع العربية محفوظة. ستُعاد الترجمة وفحص مصادرها باللغة الجديدة، ويُلغى اعتماد الترجمة وتحديد أجزائها وسطر المصدر المخصص. تُحفظ نسخة من التعديلات السابقة داخليًا.</p><p class="modal-note">هذا الإجراء يستخدم خدمة الترجمة وقد يحتسب طلبات API.</p><div class="modal-actions"><button class="button primary" id="confirmRetranslate">تأكيد إعادة الترجمة</button><button class="button secondary" id="cancelRetranslate">إلغاء</button></div>`);
  $('#cancelRetranslate').onclick=()=>$('#modal').close();
  $('#confirmRetranslate').onclick=async event=>{
    event.target.disabled=true;
    try{clearTimeout(styleTimer);styleTimer=null;await Promise.allSettled([...pendingStyleSaves]);
      const updated=await api('/api/projects/'+id+'/retranslate',{method:'POST',body:JSON.stringify({target_language:language,confirm:true})});
      setProject(updated);$('#modal').close();toast('بدأت إعادة الترجمة دون تفريغ جديد');
    }catch(error){event.target.disabled=false;toast(error.message)}
  };
};

bootLive();

