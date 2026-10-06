/* Custom language menus keep native selects as the application's data source. */
(()=>{
  const controls=[];
  let opened=null;
  function close(focus=false){if(!opened)return;const c=opened;c.menu.hidden=true;c.button.setAttribute('aria-expanded','false');opened=null;if(focus)c.button.focus()}
  function position(c){const r=c.button.getBoundingClientRect();c.menu.style.width=Math.min(Math.max(r.width,220),innerWidth-24)+'px';c.menu.style.left=Math.max(12,Math.min(r.left,innerWidth-parseFloat(c.menu.style.width)-12))+'px';const height=Math.min(320,innerHeight-24);c.menu.style.maxHeight=height+'px';c.menu.style.top=(innerHeight-r.bottom>=Math.min(c.menu.scrollHeight,height)+8?r.bottom+8:Math.max(12,r.top-Math.min(c.menu.scrollHeight,height)-8))+'px'}
  function open(c,index){if(c.select.disabled)return;close();opened=c;c.menu.hidden=false;c.button.setAttribute('aria-expanded','true');position(c);const options=[...c.menu.children];(options[index??Math.max(0,c.select.selectedIndex)]).focus()}
  document.querySelectorAll('[data-upload-language],#projectLanguageChoice').forEach((select,n)=>{
    const label=select.closest('.language-picker');
    const wrapper=document.createElement('div');wrapper.className='language-control';
    const button=document.createElement('button');button.type='button';button.className='language-trigger';button.setAttribute('aria-haspopup','listbox');button.setAttribute('aria-expanded','false');
    const menu=document.createElement('div');menu.className='language-menu';menu.id='language-menu-'+n;menu.setAttribute('role','listbox');menu.hidden=true;button.setAttribute('aria-controls',menu.id);
    const labelText=label?label.firstChild.textContent.trim():document.querySelector('label[for="'+select.id+'"]').textContent;
    menu.setAttribute('aria-label',labelText);
    if(label){label.before(wrapper);select.remove();label.remove()}else select.before(wrapper);
    wrapper.append(button,select);select.hidden=true;
    document.body.append(menu);
    const c={select,button,menu};controls.push(c);
    [...select.options].forEach((option,index)=>{const item=document.createElement('button');item.type='button';item.className='language-menu-option';item.setAttribute('role','option');item.textContent=option.textContent;item.onclick=()=>{select.value=option.value;select.dispatchEvent(new Event('change',{bubbles:true}));sync();close(true)};item.onkeydown=e=>{const items=[...menu.children];let next;if(e.key==='ArrowDown')next=(index+1)%items.length;if(e.key==='ArrowUp')next=(index+items.length-1)%items.length;if(e.key==='Home')next=0;if(e.key==='End')next=items.length-1;if(next!==undefined){e.preventDefault();items[next].focus()}if(e.key==='Escape'){e.preventDefault();close(true)}if(e.key==='Tab')close()};menu.append(item)});
    button.onclick=()=>opened===c?close():open(c);
    button.onkeydown=e=>{if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();open(c,e.key==='ArrowUp'?select.options.length-1:undefined)}if(e.key==='Escape')close(true)};
    c.sync=()=>{button.replaceChildren();const caption=document.createElement('span');caption.className='language-trigger-label';caption.textContent=labelText;const value=document.createElement('span');value.className='language-trigger-value';value.textContent=select.selectedOptions[0]?.textContent||'';const arrow=document.createElement('span');arrow.className='language-trigger-arrow';arrow.setAttribute('aria-hidden','true');arrow.textContent='⌄';button.append(caption,value,arrow);button.disabled=select.disabled;[...menu.children].forEach((item,i)=>item.setAttribute('aria-selected',String(i===select.selectedIndex)));if(opened===c&&select.disabled)close()};
    select.addEventListener('change',sync);new MutationObserver(sync).observe(select,{attributes:true,attributeFilter:['disabled']});
  });
  function sync(){controls.forEach(c=>c.sync())}
  document.addEventListener('change',sync);
  document.addEventListener('jisr-language-sync',sync);
  document.addEventListener('pointerdown',e=>{if(opened&&!opened.button.contains(e.target)&&!opened.menu.contains(e.target))close()});
  document.addEventListener('focusin',e=>{if(opened&&!opened.button.contains(e.target)&&!opened.menu.contains(e.target))close()});
  window.addEventListener('resize',()=>close());window.addEventListener('scroll',()=>close(),true);
  sync();
})();
