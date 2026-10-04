(() => {
  const tour = document.querySelector('#onboarding');
  const slides = [...tour.querySelectorAll('.onboarding-slide')];
  const tabs = [...tour.querySelectorAll('[role="tab"]')];
  const next = document.querySelector('#journeyNext');
  const back = document.querySelector('#journeyBack');
  const toggle = document.querySelector('#motionToggle');
  const replay = document.querySelector('#motionReplay');
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  const labels = ['الفكرة', 'ارفع فيديوك', 'فرّغ وترجم', 'راجع المصادر', 'صدّر وشارك'];
  const nextLabels = ['ابدأ الجولة', 'كيف تتم الترجمة؟', 'كيف أراجع المصادر؟', 'وماذا بعد المراجعة؟', 'ابدأ بفيديوك'];
  let current = 0;
  let paused = motion.matches;
  let touchStart = null;

  function updateMotion() {
    tour.classList.toggle('motion-paused', paused || document.hidden || document.querySelector('#landing').hidden);
    tour.classList.toggle('motion-reduced', motion.matches);
    toggle.setAttribute('aria-pressed', String(paused));
    toggle.innerHTML = paused ? '<span aria-hidden="true">▷</span> تشغيل الحركة' : '<span aria-hidden="true">Ⅱ</span> إيقاف الحركة';
    toggle.disabled = motion.matches;
    replay.disabled = motion.matches;
    if (motion.matches) toggle.innerHTML = '<span aria-hidden="true">◇</span> حركة مخففة';
  }

  function resetReview() {
    document.querySelector('#confirmExample').setAttribute('aria-pressed', 'false');
    document.querySelector('#confirmExample').innerHTML = '<span aria-hidden="true">□</span> جرّب تأكيد المراجعة';
    document.querySelector('#reviewFeedback').textContent = 'المطابقة تقترح المرجع. أنت تؤكّد صحته.';
    tour.querySelector('.scene-review').classList.remove('example-confirmed');
  }

  function restartScene() {
    const scene = slides[current].querySelector('.motion-scene');
    scene.classList.remove('scene-running');
    void scene.offsetWidth;
    scene.classList.add('scene-running');
    if (current === 3) resetReview();
  }

  function showStep(index, focus = true) {
    if (index < 0 || index >= slides.length) return;
    const previous = current;
    current = index;
    tour.dataset.direction = index < previous ? 'back' : 'next';
    slides.forEach((slide, i) => {
      slide.hidden = i !== current;
      slide.querySelector('.motion-scene').classList.toggle('scene-running', i === current);
      tabs[i].setAttribute('aria-selected', String(i === current));
      tabs[i].tabIndex = i === current ? 0 : -1;
      tabs[i].classList.toggle('step-visited', i < current);
    });
    back.disabled = current === 0;
    next.innerHTML = `${nextLabels[current]} <span aria-hidden="true">←</span>`;
    document.querySelector('#journeyCounter').innerHTML = `${String(current + 1).padStart(2, '0')} <span>/ 05</span>`;
    document.querySelector('#journeyAnnouncement').textContent = `المحطة ${current + 1} من ${slides.length}: ${labels[current]}`;
    if (current === 3) resetReview();
    if (previous === current) restartScene();
    if (focus) slides[current].querySelector('.journey-title').focus({preventScroll: true});
    if (tour.getBoundingClientRect().top < 0) {
      tour.scrollIntoView({behavior: motion.matches ? 'instant' : 'smooth', block: 'start'});
    }
  }

  next.onclick = () => {
    if (current === slides.length - 1) document.querySelector('#fileInput').click();
    else showStep(current + 1);
  };
  back.onclick = () => showStep(current - 1);
  tabs.forEach((tab, index) => {
    tab.onclick = () => showStep(index, false);
    tab.onkeydown = event => {
      const destination = event.key === 'Home' ? 0 : event.key === 'End' ? slides.length - 1
        : event.key === 'ArrowLeft' ? (index + 1) % slides.length
        : event.key === 'ArrowRight' ? (index + slides.length - 1) % slides.length : null;
      if (destination === null) return;
      event.preventDefault();
      showStep(destination, false);
      tabs[destination].focus();
    };
  });
  toggle.onclick = () => { paused = !paused; updateMotion(); };
  replay.onclick = restartScene;
  motion.addEventListener('change', () => { paused = motion.matches; updateMotion(); });
  document.addEventListener('visibilitychange', updateMotion);
  new MutationObserver(updateMotion).observe(document.querySelector('#landing'), {attributes: true, attributeFilter: ['hidden']});

  // Horizontal touch gestures leave vertical scrolling and scene buttons alone.
  document.querySelector('#journeyStage').addEventListener('touchstart', event => {
    if (event.touches.length !== 1 || event.target.closest('button, a')) { touchStart = null; return; }
    touchStart = {x: event.touches[0].clientX, y: event.touches[0].clientY};
  }, {passive: true});
  document.querySelector('#journeyStage').addEventListener('touchend', event => {
    if (!touchStart || !event.changedTouches.length) return;
    const dx = event.changedTouches[0].clientX - touchStart.x;
    const dy = event.changedTouches[0].clientY - touchStart.y;
    touchStart = null;
    if (Math.abs(dx) > 65 && Math.abs(dx) > Math.abs(dy) * 1.5) showStep(current + (dx > 0 ? 1 : -1));
  }, {passive: true});
  document.querySelector('#journeyStage').addEventListener('touchcancel', () => { touchStart = null; }, {passive: true});

  document.querySelector('#confirmExample').onclick = () => {
    const button = document.querySelector('#confirmExample');
    const confirmed = button.getAttribute('aria-pressed') !== 'true';
    button.setAttribute('aria-pressed', String(confirmed));
    button.innerHTML = confirmed ? '<span aria-hidden="true">✓</span> تم تأكيد المثال' : '<span aria-hidden="true">□</span> جرّب تأكيد المراجعة';
    tour.querySelector('.scene-review').classList.toggle('example-confirmed', confirmed);
    document.querySelector('#reviewFeedback').textContent = confirmed
      ? 'هكذا تكون المراجعة بقرارك، قبل التصدير.' : 'المطابقة تقترح المرجع. أنت تؤكّد صحته.';
  };
  document.querySelectorAll('[data-faq]').forEach(button => {
    button.onclick = () => {
      const faq = document.querySelector('#questions');
      faq.hidden = false;
      faq.scrollIntoView({behavior: motion.matches ? 'instant' : 'smooth', block: 'start'});
      faq.querySelector('h2').focus({preventScroll: true});
    };
  });
  document.querySelector('[data-tour]').onclick = () => {
    showStep(0, false);
    tour.scrollIntoView({behavior: motion.matches ? 'instant' : 'smooth', block: 'start'});
  };
  document.querySelector('#closeFaq').onclick = () => {
    document.querySelector('#questions').hidden = true;
    tour.scrollIntoView({behavior: motion.matches ? 'instant' : 'smooth', block: 'start'});
    next.focus({preventScroll: true});
  };
  try {
    const saved = JSON.parse(localStorage.getItem('jisr-edit') || 'null');
    if (saved?.id && saved?.token) document.querySelector('#resumeProject').hidden = false;
  } catch {
    // Storage availability does not affect the tour or the studio links.
  }
  showStep(0, false);
  updateMotion();
})();
