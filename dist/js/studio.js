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
  const pending = segments.filter(s => s.needs_review && !s.reviewed).length;
  reviewMeter.replaceChildren();
  const label = document.createElement('span');
  label.textContent = pending ? `${pending} مقطع يحتاج مراجعة` : 'لا توجد تنبيهات مراجعة';
  const context = document.createElement('small');
  context.textContent = project ? (project.publishable ? 'جاهز للتصدير' : 'أكمل الترجمة وتأكيد الاقتباسات قبل التصدير') : 'مثال توضيحي · جرّب التحرير والمصادر';
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
const welcome = document.createElement('section');
welcome.className = 'welcome';
welcome.innerHTML = `<div class="welcome-copy"><span class="studio-kicker">جسر / من العربية إلى العالم</span><h1>المعنى يستحق<br>أن يصل.</h1><p>حوّل الفيديو العربي إلى ترجمة إنجليزية، مع مصادر واضحة للآيات والأحاديث ومراجعة بشرية قبل النشر.</p><div class="welcome-actions"><button class="button primary" id="startUpload">ارفع فيديوك ←</button><button class="button secondary" id="startDemo">جرّب مثالاً</button></div><small>MP4، MOV، WebM · حتى 250 ميغابايت</small></div><div class="welcome-preview"><span class="preview-label">من الكلام إلى المعرفة</span><div class="welcome-arch"><img src="/favicon.svg" alt="شعار جسر — المحراب"></div><div class="sample-translation"><span class="tag quran">اقتباس قرآني · مثال توضيحي</span><p lang="ar">إِنَّ اللَّهَ يُحِبُّ التَّوَّابِينَ</p><p lang="en" dir="ltr">Indeed, Allah loves those who are constantly repentant.</p><small>البقرة · ٢٢٢ / الترجمة: Saheeh International</small></div></div><div class="welcome-steps"><article><b>01 / ارفع</b><p>ابدأ بمقطع فيديو عربي.</p></article><article><b>02 / ترجم</b><p>تفريغ وترجمة مع مطابقة الاقتباسات.</p></article><article><b>03 / راجع</b><p>حرّر النص وتحقق من المصادر.</p></article><article><b>04 / شارك</b><p>صدّر الفيديو والترجمة وقائمة المصادر.</p></article></div><p class="welcome-note">جسر يساعد المحرر. الاقتباسات والترجمات تحتاج مراجعتك وتأكيدك قبل التصدير.</p>`;
studioMain.before(welcome);
let demoOpened = new URLSearchParams(location.search).get('demo') === '1';
function syncView() {
  const inStudio = !!project || demoOpened || location.pathname.startsWith('/view/');
  welcome.hidden = inStudio;
  studioMain.hidden = !inStudio;
  document.body.classList.toggle('start-view', !inStudio);
}
$('#startUpload').onclick = () => $('#fileInput').click();
$('#startDemo').onclick = () => {
  demoOpened = true;
  history.replaceState(null, '', '/?demo=1');
  syncView();
  window.scrollTo({top:0});
};

const sidebar = $('.workspace aside');
const tabs = document.createElement('div');
tabs.className = 'studio-tabs';
tabs.setAttribute('role', 'tablist');
tabs.setAttribute('aria-label', 'أدوات الاستوديو');
const reviewPanel = document.createElement('section');
reviewPanel.className = 'review-tools';
reviewPanel.innerHTML = '<h2>قبل التصدير</h2><p>أكمل الترجمة، وراجع المقاطع، وأكّد مصادر الاقتباسات.</p>';
reviewPanel.append($('.review-summary'));
sidebar.prepend(reviewPanel);
sidebar.prepend(tabs);
const toolPanels = [reviewPanel, $('#referencePanel'), $('.appearance-panel')];
const toolNames = ['المراجعة', 'المصادر', 'المظهر'];
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
const viewStatus = status;
status = function () {
  viewStatus();
  syncView();
  if(readOnly) selectTool(1);
  const processing = project && ['uploaded','processing','error'].includes(project.status) && !readOnly;
  stagePanel.hidden = !processing;
  if(processing) {
    stagePanel.replaceChildren();
    const heading = document.createElement('b');
    heading.textContent = project.status === 'processing' ? 'جارٍ تجهيز مساحة التحرير' : project.status === 'error' ? 'المعالجة تحتاج انتباهك' : 'الفيديو مرفوع — الخطوة التالية: المعالجة';
    const detail = document.createElement('p');
    detail.textContent = project.error || project.stage || 'ابدأ التفريغ والترجمة، أو أدخل نصاً وتوقيتاً يدوياً.';
    stagePanel.append(heading, detail);
  }
};
status();
if(readOnly) selectTool(1);
