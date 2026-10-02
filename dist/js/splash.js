(() => {
  const query = new URLSearchParams(location.search);
  if (location.pathname !== '/' || query.has('project') || query.has('demo') ||
      matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  try {
    if (sessionStorage.getItem('jisr-intro-seen')) return;
    sessionStorage.setItem('jisr-intro-seen', '1');
  } catch {
    // Storage restrictions must never stop access to the application.
    return;
  }
  const splash = document.createElement('div');
  splash.className = 'splash';
  splash.setAttribute('role', 'dialog');
  splash.setAttribute('aria-modal', 'true');
  splash.setAttribute('aria-label', 'مرحباً بك في جسر');
  splash.innerHTML = '<div class="splash-mark"><img src="/favicon.svg" alt=""><span class="splash-name">جسر</span><small>للمعنى طريق</small></div><button class="splash-skip" type="button">تخطي المقدمة ←</button>';
  const previousFocus = document.activeElement;
  const pageElements = [...document.body.children].filter(el => !['SCRIPT', 'STYLE'].includes(el.tagName));
  const previousInert = pageElements.map(el => el.inert);
  pageElements.forEach(el => { el.inert = true; });
  document.body.append(splash);
  const skip = splash.querySelector('button');
  skip.focus({preventScroll: true});
  let finished = false;
  let timer;
  function dismiss() {
    if (finished) return;
    finished = true;
    clearTimeout(timer);
    splash.remove();
    pageElements.forEach((el, i) => { el.inert = previousInert[i]; });
    document.removeEventListener('keydown', onKey);
    if (previousFocus && previousFocus !== document.body && previousFocus.isConnected) {
      previousFocus.focus({preventScroll: true});
    } else {
      document.querySelector('#startUpload')?.focus({preventScroll: true});
    }
  }
  function onKey(event) {
    if (event.key === 'Escape') dismiss();
    if (event.key === 'Tab') { event.preventDefault(); skip.focus(); }
  }
  skip.onclick = dismiss;
  document.addEventListener('keydown', onKey);
  timer = setTimeout(dismiss, 1100);
})();
