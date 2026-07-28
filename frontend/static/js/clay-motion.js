(function () {
  'use strict';

  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var SWEEP_TARGETS = '.rate-card, .live-metal-card, .lg-card, .idx-card';
  var TILT_TARGETS = '.b-card, .why-card, .gold-type-card, .live-metal-card, .lg-card, .idx-card, .crude-card, .result-card';
  var POP_ZONES = '.live-strip, .live-gold-row, .index-cards-row, .results-grid, .material-summary, .karats-grid';

  function stagger() {
    var groups = {};
    document.querySelectorAll(SWEEP_TARGETS).forEach(function (el) {
      var parentKey = el.parentNode ? (el.parentNode.className || 'root') : 'root';
      groups[parentKey] = groups[parentKey] || 0;
      el.style.setProperty('--clay-delay', (groups[parentKey] * 0.45) + 's');
      groups[parentKey]++;
    });
  }

  function pop(el) {
    if (!el || reduce) return;
    el.classList.remove('clay-pop');
    void el.offsetWidth;
    el.classList.add('clay-pop');
    setTimeout(function () { el.classList.remove('clay-pop'); }, 600);
  }

  function watchValues() {
    if (reduce || !('MutationObserver' in window)) return;

    var zones = document.querySelectorAll(POP_ZONES);
    if (!zones.length) return;

    var observer = new MutationObserver(function (mutations) {
      var touched = [];

      mutations.forEach(function (m) {
        var node = m.type === 'characterData' ? m.target.parentNode : m.target;
        if (!node || node.nodeType !== 1) return;
        if (node.classList && node.classList.contains('clay-pop')) return;
        if (touched.indexOf(node) === -1) touched.push(node);
      });

      touched.slice(0, 12).forEach(pop);
    });

    zones.forEach(function (zone) {
      observer.observe(zone, { childList: true, characterData: true, subtree: true });
    });
  }

  function tilt() {
    if (reduce || window.matchMedia('(hover: none)').matches) return;

    document.querySelectorAll(TILT_TARGETS).forEach(function (card) {
      card.addEventListener('mousemove', function (e) {
        var r = card.getBoundingClientRect();
        var rx = ((e.clientY - r.top) / r.height - 0.5) * -7;
        var ry = ((e.clientX - r.left) / r.width - 0.5) * 7;
        card.style.setProperty(
          'transform',
          'translateY(-8px) scale(1.025) perspective(850px) rotateX(' + rx + 'deg) rotateY(' + ry + 'deg)',
          'important'
        );
      });

      card.addEventListener('mouseleave', function () {
        card.style.removeProperty('transform');
      });
    });
  }

  function parallaxBlobs() {
    if (reduce) return;
    var ticking = false;

    window.addEventListener('scroll', function () {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () {
        var y = window.scrollY * 0.02;
        document.body.style.setProperty('--clay-scroll', y.toFixed(2) + 'px');
        ticking = false;
      });
    }, { passive: true });
  }

  var lastRates = {};

  function inr(n, whole) {
    var d = whole ? 0 : 2;
    return Number(n).toLocaleString('en-IN', {
      minimumFractionDigits: d,
      maximumFractionDigits: d
    });
  }

  function numNode(el) {
    var num = el.querySelector('.chr-num');
    if (!num) {
      el.textContent = '';
      var cur = document.createElement('span');
      cur.className = 'chr-cur';
      cur.textContent = '\u20B9';
      num = document.createElement('span');
      num.className = 'chr-num';
      el.appendChild(cur);
      el.appendChild(num);
    }
    return num;
  }

  function countTo(el, to) {
    if (!el) return;
    var from = typeof lastRates[el.id] === 'number' ? lastRates[el.id] : 0;
    lastRates[el.id] = to;

    var whole = Math.abs(to % 1) < 0.005;
    var num = numNode(el);

    if (reduce || from === to) {
      num.textContent = inr(to, whole);
      return;
    }

    if (el._raf) cancelAnimationFrame(el._raf);
    var start = null;
    var dur = 850;

    function step(ts) {
      if (start === null) start = ts;
      var p = Math.min((ts - start) / dur, 1);
      var eased = p === 1 ? 1 : 1 - Math.pow(2, -10 * p);
      num.textContent = inr(from + (to - from) * eased, whole);
      if (p < 1) { el._raf = requestAnimationFrame(step); } else { el._raf = null; }
    }
    el._raf = requestAnimationFrame(step);
  }

  function setChip(el, pct) {
    if (!el) return;
    el.classList.remove('up', 'dn');
    if (typeof pct !== 'number' || isNaN(pct)) {
      el.classList.add('chr-empty');
      el.textContent = '';
      return;
    }
    el.classList.remove('chr-empty');
    var up = pct >= 0;
    el.classList.add(up ? 'up' : 'dn');
    el.textContent = (up ? '\u25B2 +' : '\u25BC ') + Math.abs(pct).toFixed(2) + '%';
  }

  function setRate(valueId, chipId, value, pct) {
    var valueEl = document.getElementById(valueId);
    if (!valueEl) return;

    if (typeof value !== 'number' || isNaN(value)) {
      valueEl.textContent = '—';
      lastRates[valueId] = 0;
    } else {
      countTo(valueEl, value);
      pop(valueEl.parentNode);
    }
    setChip(document.getElementById(chipId), pct);
  }

  window.updateHeroRates = function (data) {
    if (!data || !document.getElementById('heroRates')) return;

    var g = data.gold || {};
    var goldPct = data.gold_usd ? data.gold_usd.change_pct : null;

    var pick = function (block) {
      if (!block) return null;
      var v = block.per_gram != null ? block.per_gram : block.per_1g;
      return typeof v === 'number' ? v : null;
    };

    setRate('heroGold24', 'heroGold24Chg', pick(g['24K']), goldPct);
    setRate('heroGold22', 'heroGold22Chg', pick(g['22K']), goldPct);
    setRate('heroGold18', 'heroGold18Chg', pick(g['18K']), goldPct);
    setRate('heroSilver', 'heroSilverChg',
      data.silver ? data.silver.price_per_gram : null,
      data.silver ? data.silver.change_pct : null);
    setRate('heroPlatinum', 'heroPlatinumChg',
      data.platinum ? data.platinum.price_per_gram : null,
      data.platinum ? data.platinum.change_pct : null);

    var foot = document.getElementById('heroRatesFoot');
    if (foot) {
      if (data.has_rates === false) {
        foot.textContent = 'Rates not published yet';
      } else if (data.rates_updated_at) {
        foot.textContent = 'Updated ' + data.rates_updated_at;
      } else if (data.timestamp) {
        foot.textContent = 'Refreshed at ' + data.timestamp;
      }
    }
  };

  function boot() {
    stagger();
    tilt();
    watchValues();
    parallaxBlobs();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
