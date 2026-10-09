// Ayurwiki — home page category rows (sampada.net-style).
// For each category, renders a heading + a horizontally scrolling strip of
// summary cards drawn from the same card JSON used by the category feeds.
(function () {
  'use strict';

  var CATEGORIES = [
    { cat: 'herbs',      label: 'Herbs',      desc: 'Medicinal plants — names, properties, uses and identification.' },
    { cat: 'medicines',  label: 'Medicines',  desc: 'Ayurvedic formulations, proprietary medicines and preparations.' },
    { cat: 'yoga',       label: 'Yoga',       desc: 'Asanas, pranayama techniques and mudras.' },
    { cat: 'physiology', label: 'Physiology', desc: 'Doshas, dhatus, srotas and agni — the body in Ayurveda.' },
    { cat: 'concepts',   label: 'Concepts',   desc: 'Core ideas — prakriti, rasa, guna and veerya.' },
    { cat: 'traditions', label: 'Traditions', desc: 'Schools of thought, classical texts and lineages.' },
    { cat: 'practices',  label: 'Practices',  desc: 'Clinical and therapeutic practices of Ayurveda.' }
  ];
  var PER_ROW = 12;

  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }
  function esc(s) {
    return (s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  function fmt(n) { return n.toLocaleString('en-US'); }

  // Fisher–Yates shuffle for a rotating "discover" selection each visit.
  function shuffle(arr) {
    for (var i = arr.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = arr[i]; arr[i] = arr[j]; arr[j] = t;
    }
    return arr;
  }

  function basePath() {
    var b = location.pathname.replace(/[^/]*\.html?$/, '');
    if (b.charAt(b.length - 1) !== '/') b += '/';
    return b;
  }

  function ok(r) { return r.ok ? r.json() : Promise.reject(r.status); }

  function init() {
    var host = document.getElementById('aw-home-feed');
    if (!host || host.dataset.built === '1') return;
    host.dataset.built = '1';
    host.innerHTML = '';
    var base = basePath();
    var toc = buildHomeToc();

    function addSection(id, title) {
      var s = el('section', 'aw-home-row');
      s.id = id;
      host.appendChild(s);
      if (toc) toc.add(id, title);
      return s;
    }
    function fail(id, s) { s.remove(); if (toc) toc.remove(id); }

    // Herb of the day — a date-seeded daily spotlight (a reason to return).
    var hotd = addSection('row-hotd', 'Herb of the day');
    fetch(base + 'assets/cards/herbs.json').then(ok)
      .then(function (cards) {
        var pool = cards.filter(function (c) { return c.i && c.d; });
        if (!pool.length) { fail('row-hotd', hotd); return; }
        renderHerbOfDay(hotd, pool[dateIndex(pool.length)], base);
      })
      .catch(function () { fail('row-hotd', hotd); });

    // Recently updated (wisdomlib-style "latest text").
    var recent = addSection('row-recent', 'Recently updated');
    fetch(base + 'assets/cards/_recent.json').then(ok)
      .then(function (cards) {
        if (!cards || !cards.length) { fail('row-recent', recent); return; }
        renderRecent(recent, cards, base);
      })
      .catch(function () { fail('row-recent', recent); });

    // Latest images (wisdomlib-style "latest images").
    var imgs = addSection('row-images', 'Latest images');
    fetch(base + 'assets/cards/_latest_images.json').then(ok)
      .then(function (cards) {
        if (!cards || !cards.length) { fail('row-images', imgs); return; }
        renderLatestImages(imgs, cards, base);
      })
      .catch(function () { fail('row-images', imgs); });

    CATEGORIES.forEach(function (c) {
      var section = addSection('row-' + c.cat, c.label);
      section.dataset.cat = c.cat;
      fetch(base + 'assets/cards/' + c.cat + '.json').then(ok)
        .then(function (cards) { renderRow(section, c, cards, base); })
        .catch(function () { fail('row-' + c.cat, section); });
    });
  }

  // Build a "On this page" list in the right sidebar reflecting the rows.
  function buildHomeToc() {
    var sidebar = document.querySelector('.md-sidebar--secondary .md-sidebar__scrollwrap');
    if (!sidebar) return null;
    var mtoc = sidebar.querySelector('.md-nav--secondary');
    if (mtoc) mtoc.style.display = 'none';
    var hostEl = sidebar.querySelector('.aw-home-toc');
    if (!hostEl) {
      hostEl = el('div', 'aw-home-toc');
      hostEl.appendChild(el('div', 'aw-home-toc-title', 'On this page'));
      hostEl.appendChild(el('nav', 'aw-home-toc-list'));
      sidebar.appendChild(hostEl);
    }
    var list = hostEl.querySelector('.aw-home-toc-list');
    list.innerHTML = '';
    return {
      add: function (id, title) {
        var a = el('a', 'aw-home-toc-link', esc(title));
        a.href = '#' + id;
        a.setAttribute('data-for', id);
        a.addEventListener('click', function (e) {
          e.preventDefault();
          var t = document.getElementById(id);
          if (t) t.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
        list.appendChild(a);
      },
      remove: function (id) {
        var a = list.querySelector('[data-for="' + id + '"]');
        if (a) a.remove();
      }
    };
  }

  // "Latest images" — image-forward gallery of recently illustrated pages.
  function renderLatestImages(section, cards, base) {
    var head = el('div', 'aw-home-rowhead');
    var left = el('div', 'aw-home-rowhead-l');
    left.appendChild(el('span', 'aw-home-rowtitle-plain', 'Latest images'));
    left.appendChild(el('span', 'aw-home-rowdesc', 'Pages that recently gained photos.'));
    head.appendChild(left);
    section.appendChild(head);

    var strip = el('div', 'aw-home-strip');
    cards.forEach(function (card) {
      var a = cardEl(base + encodeURI(card.s) + '/', card, base);
      if (card.c) {
        var tag = el('div', 'aw-hc-tag', esc(cap(card.c)));
        a.insertBefore(tag, a.querySelector('.aw-hc-title'));
      }
      strip.appendChild(a);
    });
    section.appendChild(strip);
  }

  function renderRow(section, c, cards, base) {
    var total = cards.length;
    var catUrl = base + c.cat + '/';

    // Header: title + description on the left, "Browse all N →" on the right.
    var head = el('div', 'aw-home-rowhead');
    var left = el('div', 'aw-home-rowhead-l');
    var h = el('a', 'aw-home-rowtitle', esc(c.label));
    h.href = catUrl;
    left.appendChild(h);
    left.appendChild(el('span', 'aw-home-rowdesc', esc(c.desc)));
    head.appendChild(left);

    var right = el('div', 'aw-home-rowhead-r');
    // Per-row search — submits to the category feed page (?q=…)
    var form = el('form', 'aw-home-search');
    var si = el('input', 'aw-home-search-input');
    si.type = 'search';
    si.placeholder = 'Search ' + c.label.toLowerCase() + '…';
    si.setAttribute('aria-label', 'Search ' + c.label);
    form.appendChild(si);
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var q = si.value.trim();
      location.href = catUrl + (q ? '?q=' + encodeURIComponent(q) : '');
    });
    right.appendChild(form);
    var more = el('a', 'aw-home-more', 'Browse all ' + fmt(total) + ' &rarr;');
    more.href = catUrl;
    right.appendChild(more);
    head.appendChild(right);
    section.appendChild(head);

    // Strip of cards — a fresh random pick each visit, preferring images.
    var withImg = cards.filter(function (x) { return x.i; });
    var pool = (withImg.length >= PER_ROW ? withImg : cards).slice();
    var chosen = shuffle(pool).slice(0, PER_ROW);

    var strip = el('div', 'aw-home-strip');

    // Leading "section cover" tile (sampada-style).
    var cover = el('a', 'aw-hc aw-hc-cover');
    cover.href = catUrl;
    cover.innerHTML =
      '<div class="aw-hc-cover-inner">' +
      '<div class="aw-hc-cover-label">' + esc(c.label) + '</div>' +
      '<div class="aw-hc-cover-count">' + fmt(total) + ' pages</div>' +
      '<div class="aw-hc-cover-cta">Browse all &rarr;</div>' +
      '</div>';
    strip.appendChild(cover);

    chosen.forEach(function (card) {
      strip.appendChild(cardEl(base + c.cat + '/' + encodeURI(card.s) + '/', card, base));
    });

    section.appendChild(strip);
  }

  // Build a home card <a> from a card record.
  function cardEl(href, card, base) {
    var a = el('a', 'aw-hc');
    a.href = href;
    var thumb = el('div', 'aw-hc-thumb');
    if (card.i) {
      var img = el('img');
      img.loading = 'lazy';
      img.alt = '';
      img.src = 'https://img.ayurwiki.org/' + encodeURI(card.i);
      img.onerror = function () { thumb.classList.add('aw-hc-thumb--empty'); img.remove(); };
      thumb.appendChild(img);
    } else {
      thumb.classList.add('aw-hc-thumb--empty');
    }
    a.appendChild(thumb);
    a.appendChild(el('div', 'aw-hc-title', esc(card.t)));
    if (card.d) a.appendChild(el('div', 'aw-hc-desc', esc(card.d)));
    return a;
  }

  function cap(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : s; }

  // "Recently updated" row (newest content first).
  function renderRecent(section, cards, base) {
    var head = el('div', 'aw-home-rowhead');
    var left = el('div', 'aw-home-rowhead-l');
    var h = el('a', 'aw-home-rowtitle', 'Recently updated');
    h.href = base + 'recent-changes/';
    left.appendChild(h);
    left.appendChild(el('span', 'aw-home-rowdesc', 'Freshly edited and newly added pages.'));
    head.appendChild(left);
    var right = el('div', 'aw-home-rowhead-r');
    var more = el('a', 'aw-home-more', 'All recent changes &rarr;');
    more.href = base + 'recent-changes/';
    right.appendChild(more);
    head.appendChild(right);
    section.appendChild(head);

    var strip = el('div', 'aw-home-strip');
    cards.forEach(function (card) {
      var a = cardEl(base + encodeURI(card.s) + '/', card, base);
      if (card.c) {
        var tag = el('div', 'aw-hc-tag', esc(cap(card.c)));
        a.insertBefore(tag, a.querySelector('.aw-hc-title'));
      }
      strip.appendChild(a);
    });
    section.appendChild(strip);
  }

  // Deterministic index for "today" — same pick all day, changes daily.
  function dateIndex(n) {
    var d = new Date();
    var key = d.getFullYear() * 10000 + (d.getMonth() + 1) * 100 + d.getDate();
    return ((key * 2654435761) % 4294967296 % n + n) % n;
  }

  // "Herb of the day" spotlight banner.
  function renderHerbOfDay(section, card, base) {
    var head = el('div', 'aw-home-rowhead');
    var left = el('div', 'aw-home-rowhead-l');
    left.appendChild(el('span', 'aw-home-rowtitle-plain', 'Herb of the day'));
    left.appendChild(el('span', 'aw-home-rowdesc', 'A plant to explore today.'));
    head.appendChild(left);
    section.appendChild(head);

    var href = base + 'herbs/' + encodeURI(card.s) + '/';
    var banner = el('a', 'aw-hotd');
    banner.href = href;
    var thumb = el('div', 'aw-hotd-thumb');
    var img = el('img');
    img.loading = 'lazy';
    img.alt = '';
    img.src = 'https://img.ayurwiki.org/' + encodeURI(card.i);
    img.onerror = function () { thumb.classList.add('aw-hc-thumb--empty'); img.remove(); };
    thumb.appendChild(img);
    banner.appendChild(thumb);
    var body = el('div', 'aw-hotd-body');
    body.appendChild(el('div', 'aw-hotd-title', esc(card.t)));
    if (card.d) body.appendChild(el('div', 'aw-hotd-desc', esc(card.d)));
    body.appendChild(el('span', 'aw-hotd-cta', 'Read more →'));
    banner.appendChild(body);
    section.appendChild(banner);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
  if (typeof document$ !== 'undefined') {
    document$.subscribe(init);
  }
})();
