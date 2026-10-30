// Irminsul glow (15 Oct 2026). Loaded into VS Code by the "Custom CSS and JS Loader" extension
// (setting vscode_custom_css.imports). It adds a soft glow to function names (Geo) and keywords (Electro), and a gold glow
// to the cursor. It only touches Irminsul's own colours, so other themes look as they always did.
// Switch off: Ctrl+Shift+P, "Disable Custom CSS and JS", then restart VS Code.
(function () {
  'use strict';
  // colour (lower case, no #) -> glow strength. Geo functions glow most; keywords a little less.
  var GLOW = {
    f2c463: 0.55,                // Geo: functions (Night and Abyss)
    b18bec: 0.45, d7a6ff: 0.45,  // Electro: keywords that steer (Night, Abyss)
    '9479d9': 0.4, a97fe0: 0.4   // Electro, deeper: def, class, const (Night, Abyss)
  };
  var MARK = '/* irminsul-glow */';
  var rx = new RegExp('color:\\s*#(' + Object.keys(GLOW).join('|') + ')\\s*;', 'gi');

  function alpha(a) { return ('0' + Math.round(a * 255).toString(16)).slice(-2); }

  function patch() {
    var el = document.querySelector('.vscode-tokens-styles');
    if (!el) return;
    var css = el.textContent;
    if (css.indexOf(MARK) !== -1 || !rx.test(css)) return;
    rx.lastIndex = 0;
    el.textContent = MARK + css.replace(rx, function (m, hex) {
      var h = hex.toLowerCase();
      return 'color: #' + hex + '; text-shadow: 0 0 7px #' + h + alpha(GLOW[h]) + ';';
    });
  }

  // the gold cursor glow, only while an Irminsul theme is active (its cursor colour is the tell)
  var cursor = document.createElement('style');
  cursor.textContent = '.irminsul-on .monaco-editor .cursor { box-shadow: 0 0 8px 1px rgba(243, 215, 156, .55); border-radius: 1px; }';
  document.head.appendChild(cursor);
  function markTheme() {
    var css = (document.querySelector('.vscode-tokens-styles') || {}).textContent || '';
    document.body.classList.toggle('irminsul-on', /#f2c463/i.test(css) && /#(b18bec|d7a6ff)/i.test(css));
  }

  // VS Code rewrites the colour list whenever the theme changes, so watch for that and patch again.
  function run() { patch(); markTheme(); }
  new MutationObserver(run).observe(document.head, { childList: true, subtree: true, characterData: true });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run); else run();
})();
