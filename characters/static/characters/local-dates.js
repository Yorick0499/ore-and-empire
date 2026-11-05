(() => {
  document.querySelectorAll('time[data-local-date]').forEach(node => {
    const date = new Date(node.dateTime);
    if (!Number.isNaN(date.getTime())) node.textContent = new Intl.DateTimeFormat(navigator.language || 'pl', {dateStyle:'medium',timeStyle:'medium'}).format(date) + ' (czas lokalny) · ' + node.title;
  });
})();
