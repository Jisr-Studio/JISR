(()=>{
  const root=()=>document.documentElement;
  let theme='dark';
  try{if(localStorage.getItem('jisr-theme')==='light')theme='light'}catch{}
  root().dataset.theme=theme;
  document.addEventListener('DOMContentLoaded',()=>{
    const button=document.querySelector('#themeToggle');
    function update(){
      const light=root().dataset.theme==='light';
      button.setAttribute('aria-pressed',String(light));
      button.setAttribute('aria-label',light?'تفعيل المظهر الداكن':'تفعيل المظهر الفاتح');
      button.title=light?'المظهر الداكن':'المظهر الفاتح';
      button.textContent=light?'☾':'☀';
    }
    button.onclick=()=>{root().dataset.theme=root().dataset.theme==='light'?'dark':'light';try{localStorage.setItem('jisr-theme',root().dataset.theme)}catch{}update()};
    update();
  });
})();
