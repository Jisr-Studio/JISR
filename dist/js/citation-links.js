/* Source, translation, explanation, and search destinations stay distinct. */
(function (root) {
  function safeUrl(value) {
    try {
      const url = new URL(value);
      return url.protocol === 'https:' && !url.username && !url.password ? url.href : '';
    } catch { return ''; }
  }
  function isSearch(source) {
    const url = safeUrl(source.url);
    return source.link_status === 'search_only' || (url && new URL(url).hostname === 'dorar.net' && new URL(url).pathname === '/hadith/search');
  }
  function links(source, kind) {
    const result = [], seen = new Set();
    function add(value, label, role) {
      const href = safeUrl(value);
      if (href && !seen.has(href)) { seen.add(href); result.push({ href, label, role }); }
    }
    add(source.url || source.search_url, isSearch(source) ? 'البحث في المصدر' : kind === 'quran' ? 'قراءة مصدر الآية' : 'قراءة مصدر الحديث', 'source');
    if (source.translation_status === 'sourced') add(source.translation_url, 'قراءة ترجمة الحديث من المصدر', 'translation');
    if (source.verification) add(source.verification.url || source.verification.search_url,
      isSearch(source.verification) ? 'البحث عن التخريج في الدرر السنية' : 'قراءة التخريج في الدرر السنية', 'verification');
    add(source.origins_url || source.verification?.origins_url, 'قراءة أصول الحديث', 'origins');
    if (source.explanation_status === 'available') {
      add(source.explanation_url || source.url, kind === 'quran' ? 'قراءة تفسير الآية' : 'قراءة شرح الحديث', 'explanation');
    } else if (kind === 'quran') {
      // Older projects stored a surah index under explanation_url.
      add(source.explanation_index_url || source.explanation_url, 'تصفح تفاسير السورة', 'index');
    }
    return result;
  }
  root.JisrCitationLinks = { safeUrl, isSearch, links };
  if (typeof module !== 'undefined') module.exports = root.JisrCitationLinks;
})(typeof window === 'undefined' ? globalThis : window);
