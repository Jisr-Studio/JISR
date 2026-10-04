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
    if(source.quotation_mode==='paraphrase')return 'نقل بالمعنى · مرجع مرتبط · '+(source.attribution||source.title||'حديث');
    return segment.type==='quran' ? source.title||'آية قرآنية' : (source.attribution||source.title||'حديث')+' · '+(source.grade||'الحكم غير مذكور');
  }
  function reviewPending(segment) {
    if(!segment)return false;
    const source=segment.source||{};
    const aligned=['matched','selected'].includes(source.alignment_status);
    const paraphrase=source.kind==='hadith'&&source.quotation_mode==='paraphrase'&&source.relation_method==='editor_selected'&&source.alignment_status==='paraphrase';
    const partialReady=!source.partial||((aligned||paraphrase)&&source.subtitle_arabic&&source.subtitle_english);
    return !!(!segment.en?.trim()||segment.needs_review||['quran','hadith'].includes(segment.candidate?.kind)
      ||(['quran','hadith'].includes(segment.type)&&(!segment.source||segment.reviewed!==true))||!partialReady);
  }
  root.JisrCitationText = { presentation, transcriptForSave, sourceCaption, reviewPending };
  if (typeof module !== 'undefined') module.exports = root.JisrCitationText;
})(typeof window === 'undefined' ? globalThis : window);
