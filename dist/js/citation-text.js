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
  root.JisrCitationText = { presentation, transcriptForSave, sourceCaption };
  if (typeof module !== 'undefined') module.exports = root.JisrCitationText;
})(typeof window === 'undefined' ? globalThis : window);
