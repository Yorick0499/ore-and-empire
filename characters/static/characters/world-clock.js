(() => {
 const clock = document.querySelector('[data-world-phase-end]');
 if (!clock) return;
 const start = Date.parse(clock.dataset.serverNow), end = Date.parse(clock.dataset.worldPhaseEnd), tick = performance.now();
 const next = clock.textContent;
 const update = () => {
   const left = Math.max(0, Math.ceil((end - start - (performance.now() - tick))/1000));
   clock.textContent = left ? `${next} · za ${Math.floor(left/60)}:${String(left%60).padStart(2,'0')}` : 'Nadeszła kolejna pora dnia — odśwież widok, aby zobaczyć aktualne premie.';
 };
 update(); setInterval(update,1000);
})();
