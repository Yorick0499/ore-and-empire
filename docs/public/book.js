'use strict';
(() => {
  document.documentElement.classList.replace('no-js', 'js');
  const search = document.querySelector('#book-search');
  const status = document.querySelector('#search-status');
  const sections = [...document.querySelectorAll('[data-doc-section]')];
  const links = [...document.querySelectorAll('.rail a[href^="#"]')];
  const rail = document.querySelector('.rail');
  const menu = document.querySelector('#menu-toggle');
  const normalize = value => value.toLocaleLowerCase('pl').normalize('NFD').replace(/\p{M}/gu, '').replace(/ł/g, 'l');
  const index = sections.map(section => ({ section, text: normalize(section.textContent) }));
  const announce = text => {
    const node = document.querySelector('#action-status');
    node.textContent = text;
    clearTimeout(announce.timer);
    announce.timer = setTimeout(() => { node.textContent = ''; }, 3000);
  };
  function filter() {
    const tokens = normalize(search.value.trim()).split(/\s+/).filter(Boolean);
    let count = 0;
    index.forEach(({ section, text }) => {
      const match = tokens.every(token => text.includes(token));
      section.hidden = !match;
      section.classList.toggle('search-match', match && tokens.length > 0);
      if (match) count++;
    });
    links.forEach(link => {
      const target = document.getElementById(link.hash.slice(1));
      link.closest('li')?.toggleAttribute('hidden', target ? target.hidden : false);
    });
    document.querySelectorAll('.rail details').forEach(group => {
      group.hidden = ![...group.querySelectorAll('li')].some(li => !li.hidden);
      if (tokens.length && !group.hidden) group.open = true;
    });
    document.querySelector('#no-results').hidden = count > 0;
    status.textContent = tokens.length ? `Pasujące rozdziały: ${count} z ${sections.length}.` : `${sections.length} rozdziałów i dodatków. Cała księga jest dostępna offline.`;
    document.querySelectorAll('.report').forEach(report => {
      if (tokens.length) report.open = tokens.every(token => normalize(report.textContent).includes(token));
      else report.open = false;
    });
  }
  let timer;
  search.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(filter, 180); });
  search.addEventListener('keydown', event => {
    if (event.key === 'Escape') { search.value = ''; clearTimeout(timer); filter(); }
    if (event.key === 'Enter') {
      clearTimeout(timer); filter();
      const first = sections.find(section => !section.hidden);
      if (first) { first.scrollIntoView(); first.focus({ preventScroll: true }); }
    }
  });
  function openAnchor(hash) {
    if (!hash || hash === '#') return;
    const id = decodeURIComponent(hash.slice(1));
    const target = document.getElementById(id);
    if (!target) return;
    if (search.value) { clearTimeout(timer); search.value = ''; filter(); }
    let parent = target;
    while (parent) { if (parent.tagName === 'DETAILS') parent.open = true; parent = parent.parentElement; }
    if (innerWidth <= 760) { rail.classList.remove('is-open'); menu.setAttribute('aria-expanded', 'false'); }
    requestAnimationFrame(() => target.scrollIntoView({ block: 'start' }));
  }
  document.addEventListener('click', event => {
    const anchor = event.target.closest('a[href^="#"]');
    if (anchor) openAnchor(anchor.hash);
  });
  window.addEventListener('hashchange', () => openAnchor(location.hash));
  menu.addEventListener('click', () => {
    const open = rail.classList.toggle('is-open');
    menu.setAttribute('aria-expanded', String(open));
    if (open) { rail.scrollIntoView({ block: 'start' }); search.focus({ preventScroll: true }); }
  });
  document.querySelectorAll('pre').forEach(pre => {
    const button = document.createElement('button');
    button.type = 'button'; button.className = 'copy-code'; button.textContent = 'Kopiuj';
    button.setAttribute('aria-label', 'Kopiuj treść tego bloku');
    button.addEventListener('click', async () => {
      const value = pre.querySelector('code')?.textContent || pre.textContent.replace(/Kopiuj$/, '');
      try {
        if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(value);
        else {
          const textarea = document.createElement('textarea');
          textarea.value = value; textarea.style.position = 'fixed'; textarea.style.opacity = '0';
          document.body.append(textarea); textarea.select();
          const success = document.execCommand('copy'); textarea.remove();
          if (!success) throw new Error('clipboard');
        }
        announce('Skopiowano do schowka.');
      } catch { announce('Zaznacz i skopiuj tekst ręcznie — przeglądarka nie udostępniła schowka.'); }
    });
    pre.prepend(button);
  });
  const dialog = document.querySelector('#screen-dialog');
  document.querySelectorAll('[data-zoom]').forEach(button => button.addEventListener('click', () => {
    const figure = button.closest('figure');
    dialog.querySelector('img').src = button.querySelector('img').src;
    dialog.querySelector('img').alt = button.querySelector('img').alt;
    dialog.querySelector('p').textContent = figure.querySelector('figcaption').textContent;
    dialog.showModal();
  }));
  dialog.querySelector('button').addEventListener('click', () => dialog.close());
  document.querySelectorAll('[data-report-download]').forEach(button => button.addEventListener('click', () => {
    const report = button.closest('.report');
    const blob = new Blob([report.querySelector('code').textContent], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob); const anchor = document.createElement('a');
    anchor.href = url; anchor.download = button.dataset.reportDownload; anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }));
  let printState = [];
  window.addEventListener('beforeprint', () => {
    printState = [...document.querySelectorAll('details')].map(node => [node, node.open]);
    printState.forEach(([node]) => { node.open = true; });
  });
  window.addEventListener('afterprint', () => printState.forEach(([node, open]) => { node.open = open; }));
  document.querySelector('#print-book').addEventListener('click', () => window.print());
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      links.forEach(link => link.removeAttribute('aria-current'));
      links.find(link => link.hash === '#' + entry.target.id)?.setAttribute('aria-current', 'location');
    }), { rootMargin: '-15% 0px -65% 0px' });
    sections.forEach(section => observer.observe(section));
  }
  filter();
  if (location.hash) openAnchor(location.hash);
})();
