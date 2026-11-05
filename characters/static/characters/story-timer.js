(() => {
  const timers = document.querySelectorAll('[data-story-end]');
  const update = () => timers.forEach(timer => {
    const end = Date.parse(timer.dataset.storyEnd);
    if (!Number.isFinite(end)) return;
    const seconds = Math.max(0, Math.ceil((end - Date.now()) / 1000));
    timer.textContent = seconds ? `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}` : 'odczekano — odśwież dziennik';
  });
  update();
  if (timers.length) setInterval(update, 1000);
})();
