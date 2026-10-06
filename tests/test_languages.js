const assert=require('node:assert/strict');
const fs=require('node:fs');
const languages=require('../dist/js/languages.js');
const citations=require('../dist/js/citation-text.js');
const catalog=JSON.parse(fs.readFileSync(require.resolve('../dist/languages.json'),'utf8'));
languages.configure(catalog);
assert.equal(languages.options().length,7);
assert.equal(languages.options().find(x=>x.selected).value,'en');
assert.throws(()=>languages.info('fr'));
for(const [code,info] of Object.entries(catalog)){
  assert.equal(languages.attributes(code).dir,code==='ur'?'rtl':'ltr');
  assert.equal(languages.attributes(code).lang,code);
  assert.ok(languages.attributes(code).fontFamily.includes(info.font_family));
  const segment={target_language:code,type:'quran',translation:'TEST',translation_origin:'machine',reviewed:false,
    source:{arabic:'بسم الله',subtitle_arabic:'بسم الله',kind:'quran',surah:1,ayah:1,translation:'',translation_language:code,translation_status:'unavailable'}};
  assert.ok(citations.reviewPending(segment));
  if(code!=='en'){
    assert.ok(citations.sourceCaption(segment).includes(info.labels.unavailable));
    assert.ok(citations.sourceCaption(segment).includes(info.labels.draft));
    assert.ok(!citations.sourceCaption(segment).includes('Translation of Quranic meanings'));
  }
  segment.reviewed=true;segment.needs_review=false;
  assert.equal(citations.reviewPending(segment),false);
  assert.equal(segment.source.translation_status,'unavailable');
}
console.log('Seven-language direction, font, unavailable-source and review checks passed.');
