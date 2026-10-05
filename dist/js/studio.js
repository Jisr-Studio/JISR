// Presentation enhancements share the editor's existing project state.
const reviewAction = document.createElement('button');
reviewAction.className = 'review-action';
reviewAction.textContent = 'الانتقال إلى المراجعة ←';
$('.review-summary').append(reviewAction);
reviewAction.onclick = () => {
  filter = 'review';
  $$('[data-filter]').forEach(button => button.classList.toggle('active', button.dataset.filter === filter));
  render();
  $('.transcript-panel').scrollIntoView({behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'start'});
};
const reviewMeter = document.createElement('div');
reviewMeter.className = 'review-meter';
$('.transcript-panel .panel-heading').after(reviewMeter);
const studioRender = render;
const timeline = document.createElement('div');
timeline.className = 'clip-timeline';
timeline.setAttribute('aria-label', 'مقاطع الفيديو');
$('.video-controls').after(timeline);
render = function () {
  studioRender();
  timeline.replaceChildren();
  segments.forEach((segment, index) => {
    const clip = document.createElement('button');
    clip.className = 'timeline-clip ' + segment.type;
    clip.classList.toggle('selected', index === selected);
    clip.style.flexGrow = Math.max(.1, segment.end - segment.start);
    clip.textContent = String(index + 1).padStart(2, '0');
    clip.setAttribute('aria-label', `المقطع ${index + 1} · ${fmt(segment.start)}`);
    clip.setAttribute('aria-pressed', String(index === selected));
    clip.title = `${fmt(segment.start)} — ${segment.type === 'quran' ? 'آية قرآنية' : segment.type === 'hadith' ? 'حديث نبوي' : 'كلام'}`;
    clip.onclick = () => seek(index);
    timeline.append(clip);
  });
  const pending = segments.filter(JisrCitationText.reviewPending).length;
  reviewMeter.replaceChildren();
  const label = document.createElement('span');
  label.textContent = pending ? `${pending} مقطع يحتاج مراجعة` : 'لا توجد تنبيهات مراجعة';
  const context = document.createElement('small');
  context.textContent = project ? (project.publishable ? 'جاهز للتصدير والمشاركة' : project.exportable ? 'يمكن تصدير مسودة الآن؛ راجع النصوص والمصادر قبل النشر' : 'انتظر انتهاء المعالجة قبل التصدير') : 'مثال توضيحي · جرّب التحرير والمصادر';
  reviewMeter.append(label, context);
  reviewMeter.classList.toggle('clear', !pending);
  reviewAction.disabled = !pending;
  $$('.filters button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.filter === filter)));
};
$('#toggleAll').textContent = showArabic ? 'إخفاء النص العربي' : 'عرض النص العربي';
const toggleArabic = $('#toggleAll').onclick;
$('#toggleAll').onclick = function (event) {
  toggleArabic.call(this, event);
  this.textContent = showArabic ? 'إخفاء النص العربي' : 'عرض النص العربي';
};
render();

// Start and studio are two views of the same connected application.
const studioMain = $('main');
const welcome = $('#landing');
let demoOpened = new URLSearchParams(location.search).get('demo') === '1';
function syncView() {
  const inStudio = !!project || demoOpened || location.pathname.startsWith('/view/');
  welcome.hidden = inStudio;
  document.title = inStudio ? 'جسر | استوديو الترجمة' : 'جسر | للمعنى طريق';
  $('.skip-link').href = inStudio ? '#studioMain' : '#landing';
  studioMain.hidden = !inStudio;
  document.body.classList.toggle('start-view', !inStudio);
}


const sidebar = $('.workspace aside');
const tabs = document.createElement('div');
tabs.className = 'studio-tabs';
tabs.setAttribute('role', 'tablist');
tabs.setAttribute('aria-label', 'أدوات الاستوديو');
const reviewPanel = document.createElement('section');
reviewPanel.className = 'review-tools';
reviewPanel.innerHTML = '<h2>قبل النشر</h2><p>يمكنك تصدير مسودة، وراجع النصوص وأكّد مصادر الاقتباسات قبل نشرها.</p>';
reviewPanel.append($('.review-summary'));
sidebar.prepend(reviewPanel);
sidebar.prepend(tabs);
const toolPanels = [reviewPanel, $('#referencePanel'), $('.appearance-panel')];
const toolNames = ['المراجعة', 'المصادر', 'المظهر'];
const subtitleSizeNote = document.createElement('p');
subtitleSizeNote.textContent = 'الحجم يتناسب مع الفيديو. يُصغّر النص الطويل عند الحاجة، ويظهر بالشكل نفسه في المعاينة والتصدير.';
$('#fontSize').after(subtitleSizeNote);
function selectTool(index) {
  toolPanels.forEach((panel, i) => {
    panel.hidden = i !== index;
    panel.id ||= 'tool-panel-' + i;
    panel.setAttribute('role', 'tabpanel');
    panel.setAttribute('aria-labelledby', 'tool-tab-' + i);
    tabs.children[i].setAttribute('aria-selected', String(i === index));
    tabs.children[i].tabIndex = i === index ? 0 : -1;
  });
  if(index === 2) $('.appearance-panel').open = true;
}
for(let index=0;index<toolNames.length;index++) {
  const button = document.createElement('button');
  button.textContent = toolNames[index];
  button.id = 'tool-tab-' + index;
  button.setAttribute('role', 'tab');
  button.setAttribute('aria-controls', toolPanels[index].id || 'tool-panel-' + index);
  button.onclick = () => selectTool(index);
  button.onkeydown = event => {
    if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return;
    event.preventDefault();
    const next = event.key === 'Home' ? 0 : event.key === 'End' ? 2 : (index + (event.key === 'ArrowLeft' ? 1 : 2)) % 3;
    selectTool(next);
    tabs.children[next].focus();
  };
  tabs.append(button);
}
selectTool(0);
$('#sourcesNav').onclick = () => { demoOpened = true; syncView(); selectTool(1); sidebar.scrollIntoView({block:'start'}); };
$('#editorNav').onclick = () => { demoOpened = true; syncView(); window.scrollTo({top:0}); };
const stagePanel = document.createElement('section');
stagePanel.className = 'stage-panel';
stagePanel.setAttribute('role','status');
$('.workflow').after(stagePanel);
let processingStarted = null;
let processingProject = null;
function updateProcessingTime() {
  const clock = stagePanel.querySelector('.processing-time');
  if(clock && processingStarted) clock.textContent = 'الوقت المنقضي ' + fmt((Date.now() - processingStarted) / 1000);
}
setInterval(updateProcessingTime, 1000);
const viewStatus = status;
status = function () {
  viewStatus();
  syncView();
  if(readOnly) selectTool(1);
  const processing = project && ['uploaded','processing','error','ready'].includes(project.status) && !readOnly;
  stagePanel.hidden = !processing;
  if(!processing) {
    $('.workflow').classList.remove('is-processing');
    $('.workflow-note').hidden = false;
  }
  if(processing) {
    const running = project.status === 'processing';
    const ready = project.status === 'ready';
    const failed = project.status === 'error';
    if(running && (!processingStarted || processingProject !== project.id)) {
      processingStarted = Date.now();
      processingProject = project.id;
    }
    if(!running) processingStarted = null;
    const stage = project.stage || '';
    $('.workflow').classList.toggle('is-processing', running);
    $('.workflow-note').hidden = true;
    stagePanel.classList.toggle('is-running', running);
    stagePanel.classList.toggle('is-ready', ready);
    stagePanel.classList.toggle('is-error', failed);
    stagePanel.replaceChildren();
    const heading = document.createElement('b');
    heading.textContent = running ? 'جارٍ تحليل الفيديو' : ready ? 'اكتملت المعالجة — دورك في المراجعة' : failed ? 'توقفت المعالجة' : 'الفيديو مرفوع — الخطوة التالية: المعالجة';
    const detail = document.createElement('p');
    detail.textContent = failed ? project.error : ready ? 'راجع الترجمة والمصادر، ثم صدّر الفيديو عندما تكون جاهزاً.' : running ? stage || 'جارٍ بدء المعالجة…' : 'اضغط «معالجة الفيديو» لبدء التفريغ والترجمة.';
    stagePanel.append(heading, detail);
    if(running) {
      const timing = document.createElement('div');
      timing.className = 'processing-meta';
      timing.innerHTML = '<span class="processing-time"></span><span>قد يستغرق ذلك عدة دقائق حسب طول الفيديو واستجابة الخدمات.</span>';
      stagePanel.append(timing);
      updateProcessingTime();
    }
  }
};
status();
if(readOnly) selectTool(1);
