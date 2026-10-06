/* One catalog supplies both the Python renderer and the Arabic editor. */
(function(root){
  let catalog = {en:{name_ar:'الإنجليزية',name:'English',direction:'ltr',font:'noto-latin',font_family:'Noto Sans',labels:{unavailable:'Documented translation unavailable'}}};
  function configure(value){catalog=value;}
  function info(code='en'){if(!catalog[code])throw Error('لغة الترجمة غير مدعومة');return catalog[code];}
  function code(segment){return segment?.target_language||'en';}
  function label(key,segment){return info(code(segment)).labels[key];}
  function options(selected='en'){return Object.entries(catalog).map(([value,item])=>({value,text:item.name_ar,selected:value===selected}));}
  function attributes(code='en'){const item=info(code);return {lang:code,dir:item.direction,fontFamily:`'${item.font_family}',sans-serif`};}
  root.JisrLanguages={configure,info,code,label,options,attributes};
  if(typeof module!=='undefined')module.exports=root.JisrLanguages;
})(typeof window==='undefined'?globalThis:window);
