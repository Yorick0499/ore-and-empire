/* Native details works without JavaScript; narrow screens start compact. */
(() => {
  const narrow = window.matchMedia('(max-width: 700px)');
  document.querySelectorAll('.profile-details').forEach(card => {
    card.open = !narrow.matches;
    narrow.addEventListener('change', event => { card.open = !event.matches; });
  });
})();
