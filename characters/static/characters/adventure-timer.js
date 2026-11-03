(() => {
  const timers = document.querySelectorAll('[data-ends]');
  const update = () => timers.forEach(timer => {
    const remaining = Math.max(0, Math.ceil((Date.parse(timer.dataset.ends) - Date.now()) / 1000));
    timer.textContent = remaining ? `${Math.floor(remaining / 60)}:${String(remaining % 60).padStart(2, '0')}` : 'Gotowe do odbioru';
    if (!remaining) document.querySelectorAll('[data-ready-button]').forEach(button => { button.disabled = false; });
  });
  update();
  if (timers.length) setInterval(update, 1000);
})();
