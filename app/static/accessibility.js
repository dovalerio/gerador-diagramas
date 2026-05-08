/**
 * Screen reader announcement helpers.
 */
const A11y = (() => {
  let _liveRegion = null;

  function _ensureRegion() {
    if (_liveRegion) return;
    _liveRegion = document.createElement('div');
    _liveRegion.setAttribute('aria-live', 'polite');
    _liveRegion.setAttribute('aria-atomic', 'true');
    _liveRegion.className = 'sr-only';
    document.body.appendChild(_liveRegion);
  }

  return {
    announce(message, priority = 'polite') {
      _ensureRegion();
      _liveRegion.setAttribute('aria-live', priority);
      // Clear then set forces re-announcement even for same text
      _liveRegion.textContent = '';
      requestAnimationFrame(() => { _liveRegion.textContent = message; });
    },
  };
})();
