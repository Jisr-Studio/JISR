/* Display source text without overwriting the speech-recognition transcript. */
(function (root) {
  let captionLabels = {surahs:{}, labels:{}};
  function configureCaptionLabels(labels) { captionLabels = labels; }
  function translationCaptionText(value) {
    value=String(value||'').trim().replace(/[٠-٩]/g,c=>String('٠١٢٣٤٥٦٧٨٩'.indexOf(c)));
    if(!/[\u0600-\u06ff]/.test(value))return value;
    for(const [arabic,translation] of Object.entries(captionLabels.labels))value=value.split(arabic).join(translation);
    return /[\u0600-\u06ff]/.test(value)?'':value;
  }
  function presentation(segment) {
    const originalArabic = segment?.ar || '';
    const source = segment?.source;
    const sourceWording = source?.subtitle_mode === 'source_excerpt';
    const literal = source && ['quran', 'hadith'].includes(segment.type) && (source.quotation_mode !== 'paraphrase' || sourceWording);
    const excerpt = literal ? (source.subtitle_arabic || (!source.partial ? source.arabic : '')) : '';
    const validExcerpt = !!(excerpt && (!sourceWording || source.arabic?.includes(excerpt)));
    const arabic = sourceWording ? (validExcerpt ? excerpt : '[Source excerpt unavailable]') : excerpt || originalArabic;
    const fromSource = !!(literal && validExcerpt);
    return { arabic, originalArabic, fromSource, changed: fromSource && arabic !== originalArabic };
  }
  function transcriptForSave(segment, editedArabic) {
    const view = presentation(segment);
    const edited = editedArabic.trim();
    // Saving or confirming the displayed reference unchanged must retain its
    // link and the original transcript, not appear to be a transcript edit.
    return view.fromSource && edited === view.arabic.trim() ? view.originalArabic : edited;
  }
  function sourceCaption(segment, useDefault=false) {
    const source=segment?.source;
    if(!source || !['quran','hadith'].includes(segment.type))return '';
    if(!useDefault && typeof segment.source_caption==='string')return segment.source_caption;
    if(root.JisrLanguages && root.JisrLanguages.code(segment)!=='en'){
      const label=key=>root.JisrLanguages.label(key,segment);
      let text;
      if(segment.type==='quran'){
        text=`${label('quran')} ${source.surah||''}:${source.ayah||''} · ${label('meanings')}`;
        text+=' · '+(source.translation_status==='sourced'?source.translator||'':label('unavailable'));
      }else{
        text=`${source.source_name||'Dorar'} · ${label('hadith')} ${source.id||''} · ${source.grade_translated||label('grading')}`;
        if(source.quotation_mode==='paraphrase')text=label(source.subtitle_mode==='source_excerpt'?'source_wording':'paraphrase')+' · '+label('related')+' · '+text;
      }
      if(source.translation_status!=='sourced'||!alignmentReady(source)||(source.quotation_mode==='paraphrase'&&source.subtitle_mode!=='source_excerpt'))text+=' · '+label(segment.translation_origin==='human'?'editor_translation':'draft');
      return text;
    }
    if(segment.type==='quran'){
      let query=new URLSearchParams();try{query=new URL(source.url).searchParams}catch{}
      const location=String(source.url||'').match(/\/surah\/(\d+)\/(\d+)/);
      const surah=String(source.surah||query.get('surah')||location?.[1]||''),ayah=String(source.ayah||query.get('ayah')||location?.[2]||'');
      const name=captionLabels.surahs[surah];
      const reference=name&&/^\d+$/.test(ayah)?`Surah ${name} (${surah}:${ayah})`:name?`Surah ${name} (${surah})`:'Quran';
      const translator=translationCaptionText(source.translator_translated||source.translator);
      let text=reference+' · Translation of Quranic meanings'+(translator?' · '+translator:'');
      if(source.translation_status==='unavailable')text+=' · '+(root.JisrLanguages?root.JisrLanguages.label('unavailable',segment):'Documented translation unavailable')+' · '+(segment.translation_origin==='human'?'Editor translation':'Machine draft · Review required');
      else if(source.partial&&!['matched','selected'].includes(source.alignment_status))text+=' · Machine draft · Review required';
      return text;
    }
    let attribution=translationCaptionText(source.attribution_translated||source.attribution);
    if(!attribution){
      const dorar=String(source.url||'').match(/dorar\.net\/h\/([A-Za-z0-9]+)/),record=String(source.url||'').match(/hadeethenc\.com\/(?:ar|en)\/browse\/hadith\/(\d+)/);
      attribution=dorar?`Dorar · Hadith ${dorar[1]}`:record?`HadeethEnc · Hadith ${record[1]}`:'Hadith · See source for details';
    }
    if(source.quotation_mode==='paraphrase'){
      if(source.subtitle_mode==='source_excerpt')return 'Source wording · Related narration · '+attribution+(sourceWordingReady(source)?'':' · Machine draft · Review required');
      return 'Paraphrased quotation · Related source · '+attribution+(segment.translation_origin!=='human'&&segment.reviewed!==true?' · Machine draft · Review required':'');
    }
    return attribution+' · '+(translationCaptionText(source.grade_translated||source.grade)||'See source for grading')+(source.translation_status!=='sourced'||(source.partial&&!['matched','selected'].includes(source.alignment_status))?' · '+(segment.translation_origin==='human'?'Editor translation':'Machine draft · Review required'):'');
  }
  function sourceWordingReady(source) {
    return !!(source.translation_status==='sourced'&&['full','matched','selected'].includes(source.alignment_status)
      &&source.subtitle_arabic&&source.arabic?.includes(source.subtitle_arabic)
      &&source.subtitle_translation&&source.translation?.includes(source.subtitle_translation));
  }
  function alignmentReady(source) {
    if(source.subtitle_mode==='source_excerpt')return sourceWordingReady(source);
    if(['unavailable','machine_draft'].includes(source.translation_status))return false;
    if(!source.partial)return true;
    const aligned=['matched','selected'].includes(source.alignment_status);
    const paraphrase=source.kind==='hadith'&&source.quotation_mode==='paraphrase'&&source.relation_method==='editor_selected'&&source.alignment_status==='paraphrase';
    return !!((aligned||paraphrase)&&source.subtitle_translation&&source.subtitle_arabic);
  }
  function reviewPending(segment) {
    if(!segment)return false;
    const source=segment.source||{};
    const aligned=['matched','selected'].includes(source.alignment_status);
    const paraphrase=source.kind==='hadith'&&source.quotation_mode==='paraphrase'&&source.relation_method==='editor_selected'&&source.alignment_status==='paraphrase';
    const partialReady=source.translation_status==='unavailable'&&source.subtitle_mode!=='source_excerpt'?!!(segment.translation?.trim()&&source.arabic&&(source.quotation_mode==='paraphrase'||source.subtitle_arabic)):source.translation_status==='machine_draft'?false:source.subtitle_mode==='source_excerpt'?sourceWordingReady(source):!source.partial||((aligned||paraphrase)&&source.subtitle_arabic&&source.subtitle_translation);
    return !!(segment.reviewed!==true||!segment.translation?.trim()||segment.needs_review||['quran','hadith'].includes(segment.candidate?.kind)
      ||(['quran','hadith'].includes(segment.type)&&(!segment.source||segment.reviewed!==true))||!partialReady);
  }
  function sourceExcerptRange(segment) {
    const source = segment?.source;
    if (!source?.arabic || (source.quotation_mode === 'paraphrase' && source.subtitle_mode !== 'source_excerpt') || !source.partial) return null;
    const normalize = text => text.replace(/[\u064b-\u065f\u0670\u06d6-\u06ed\u0640]/g, '')
      .replace(/[أإآٱىة]/g, c => ({أ:'ا',إ:'ا',آ:'ا',ٱ:'ا',ى:'ي',ة:'ه'}[c]))
      .replace(/[^\u0621-\u064a]+/g, ' ').trim();
    const words = [];
    for (const match of source.arabic.matchAll(/\S+/g)) {
      for (const word of normalize(match[0]).split(' ').filter(Boolean)) {
        words.push({word, start:match.index, end:match.index + match[0].length});
      }
    }
    const excerpt = normalize(source.subtitle_arabic || segment.ar || '').split(' ').filter(Boolean);
    if (!excerpt.length) return null;
    const matches = [];
    for (let i = 0; i <= words.length - excerpt.length; i++) {
      if (excerpt.every((word, j) => words[i+j].word === word)) matches.push(i);
    }
    if (matches.length !== 1) return null;
    const first = matches[0];
    return {start:words[first].start, end:words[first+excerpt.length-1].end};
  }
  root.JisrCitationText = { presentation, transcriptForSave, sourceCaption, reviewPending, sourceExcerptRange, configureCaptionLabels };
  if (typeof module !== 'undefined') module.exports = root.JisrCitationText;
})(typeof window === 'undefined' ? globalThis : window);
