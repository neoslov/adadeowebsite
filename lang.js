/* Secye — language helper for the legal pages (secye.html / secye-tr.html /
 * secye-pl.html). Serves the visitor the rules in their own language:
 *
 *   - each legal page is tagged <body data-page-lang="en|tr|pl">;
 *   - a visitor whose browser language is tr/pl is redirected to the matching
 *     page (the target still opens the same anchor section, e.g. #privacy);
 *   - choosing a language via the header switch (or the banner) stores a
 *     preference so we never bounce them again;
 *   - the banner offers the other language when the page language differs
 *     from the visitor's, with a way to dismiss it.
 *
 * The mapping here mirrors app/core config and the settings screen: one new
 * supported language = one new page (secye-XX.html) + one line below.
 */
(function () {
  'use strict';

  var PAGES = { en: 'secye.html', tr: 'secye-tr.html', pl: 'secye-pl.html' };
  var LABELS = { en: 'English', tr: 'Türkçe', pl: 'Polski' };
  var STORAGE_KEY = 'secye-lang';

  function supported() {
    return Object.keys(PAGES);
  }

  /** Match navigator.languages[0..1] against a supported code. */
  function detect() {
    var list = [];
    try {
      if (navigator.languages && navigator.languages.length) list = navigator.languages.slice(0, 2);
      if (!list.length && navigator.language) list = [navigator.language];
    } catch (e) { /* rely on the <html lang> default */ }
    var codes = supported();
    for (var i = 0; i < list.length; i++) {
      var tag = String(list[i] || '').toLowerCase();
      for (var j = 0; j < codes.length; j++) {
        if (tag === codes[j] || tag.indexOf(codes[j] + '-') === 0) return codes[j];
      }
    }
    return null;
  }

  function saved() {
    try { return window.localStorage.getItem(STORAGE_KEY); } catch (e) { return null; }
  }

  function save(code) {
    try { window.localStorage.setItem(STORAGE_KEY, code); } catch (e) { /* storage may be off */ }
  }

  function currentLang() {
    var el = document.body;
    return el && el.getAttribute ? el.getAttribute('data-page-lang') : null;
  }

  function init() {
    var current = currentLang();
    if (!current) return;

    // Chosen earlier? That is the truth; never switch someone away from a
    // language they picked. (Re-evaluate once per visit, not per navigation.)
    if (saved()) return;

    var detected = detect();
    if (!detected || detected === current) return;

    // Landpeople on the right page. Anchors are identical on every language
    // page (#privacy, #terms, #disclaimer, #delete-account, #support), so a
    // store or in-app deep link still opens the same section.
    var target = PAGES[detected];
    if (target) {
      var hash = window.location.hash || '';
      window.location.replace(target + hash);
      return;
    }

    // Fallback: offer the visitor the other language without moving them.
    var banner = document.getElementById('lang-banner');
    var link = document.getElementById('lang-banner-link');
    if (banner && link) {
      var text = document.getElementById('lang-banner-text');
      if (text) {
        text.textContent =
          detected === 'tr' ? 'Bu sayfayı Türkçe görüntüleyin.' :
          detected === 'pl' ? 'Zobacz tę stronę po polsku.' :
          'View this page in ' + (LABELS[detected] || detected) + '.';
      }
      link.href = target + (window.location.hash || '');
      banner.removeAttribute('hidden');
      banner.style.display = 'flex';
    }
  }

  // Header language switch: record the choice so auto-serving never overrides it.
  document.addEventListener('click', function (e) {
    var node = e.target && e.target.closest ? e.target.closest('[data-lang-link]') : null;
    if (node) save(node.getAttribute('data-lang-link'));
  });

  // Banner dismiss ("stay on this page"): remember the current page language.
  document.addEventListener('click', function (e) {
    var node = e.target && e.target.closest ? e.target.closest('[data-lang-dismiss]') : null;
    if (node) save(currentLang());
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();