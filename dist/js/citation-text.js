/* Display source text without overwriting the speech-recognition transcript. */
(function (root) {
  function presentation(segment) {
    const originalArabic = segment?.ar || '';
    const source = segment?.source;
    const literal = source && ['quran', 'hadith'].includes(segment.type) && source.quotation_mode !== 'paraphrase';
    const arabic = literal ? (source.subtitle_arabic || (!source.partial ? source.arabic : '') || originalArabic) : originalArabic;
    const fromSource = !!(literal && (source.subtitle_arabic || (!source.partial && source.arabic)));
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
    if(source.quotation_mode==='paraphrase')return 'نقل بالمعنى · مرجع مرتبط · '+(source.attribution||source.title||'حديث')+(segment.translation_origin!=='human'&&segment.reviewed!==true?' · English: machine draft':'');
    if(segment.type==='quran')return (source.title||'آية قرآنية')+' · ترجمة معاني القرآن الكريم'+(source.translator?' · '+source.translator:'');
    return (source.attribution||source.title||'حديث')+' · '+(source.grade||'الحكم غير مذكور')+(source.translation_status!=='sourced'?' · English: machine draft':'');
  }
  function reviewPending(segment) {
    if(!segment)return false;
    const source=segment.source||{};
    const aligned=['matched','selected'].includes(source.alignment_status);
    const paraphrase=source.kind==='hadith'&&source.quotation_mode==='paraphrase'&&source.relation_method==='editor_selected'&&source.alignment_status==='paraphrase';
    const partialReady=!source.partial||((aligned||paraphrase)&&source.subtitle_arabic&&source.subtitle_english);
    return !!(segment.reviewed!==true||!segment.en?.trim()||segment.needs_review||['quran','hadith'].includes(segment.candidate?.kind)
      ||(['quran','hadith'].includes(segment.type)&&(!segment.source||segment.reviewed!==true))||!partialReady);
  }
  function sourceExcerptRange(segment) {
    const source = segment?.source;
    if (!source?.arabic || source.quotation_mode === 'paraphrase' || !source.partial) return null;
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
  root.JisrCitationText = { presentation, transcriptForSave, sourceCaption, reviewPending, sourceExcerptRange };
  if (typeof module !== 'undefined') module.exports = root.JisrCitationText;
})(typeof window === 'undefined' ? globalThis : window);
