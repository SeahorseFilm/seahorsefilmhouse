(function () {
  var header = document.querySelector('.site-header');
  var toggle = document.querySelector('.nav-toggle');
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function onScroll() {
    header.classList.toggle('solid', window.scrollY > 40 || !document.querySelector('.hero, .film-hero'));
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  if (toggle) {
    var setMenu = function (open) {
      header.classList.toggle('open', open);
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    };
    toggle.addEventListener('click', function () { setMenu(!header.classList.contains('open')); });
    // Escape closes the phone menu and puts focus back on the menu button
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && header.classList.contains('open')) { setMenu(false); toggle.focus(); }
    });
  }

  // Hero: hovering a film title brings its image into focus
  var titles = document.querySelectorAll('.hero-title');
  if (titles.length) {
    var layers = document.querySelectorAll('.hero-bg');
    var notes = document.querySelectorAll('.hero-note');
    var current = 0;
    var timer;
    // Only the first film's image comes with the page; the others are fetched shortly after it has loaded
    // (well before the first change at 5.5 seconds), or straight away if their film is picked first
    var wake = function (layer) {
      layer.querySelectorAll('[data-srcset]').forEach(function (el) {
        el.setAttribute('srcset', el.getAttribute('data-srcset'));
        el.removeAttribute('data-srcset');
        if (el.hasAttribute('data-src')) { el.setAttribute('src', el.getAttribute('data-src')); el.removeAttribute('data-src'); }
      });
    };
    var wakeAll = function () { setTimeout(function () { layers.forEach(wake); }, 1500); };
    if (document.readyState === 'complete') wakeAll(); else window.addEventListener('load', wakeAll);
    var show = function (i) {
      current = (i + titles.length) % titles.length;
      wake(layers[current]);
      [titles, layers, notes].forEach(function (set) {
        set.forEach(function (el, n) { el.classList.toggle('active', n === current); });
      });
      // let the page know which film is showing, so its image can be given a lighter tint
      var m = layers[current].className.match(/bg-([a-z0-9-]+)/);
      if (m) layers[current].parentNode.setAttribute('data-film', m[1]);
    };
    var hero = document.getElementById('hero');
    var heroOnScreen = true;
    // The films change by themselves only while the hero is on screen, and never for visitors who ask for less motion
    var start = function () {
      clearInterval(timer);
      if (reduceMotion || !heroOnScreen || document.hidden) return;
      timer = setInterval(function () { show(current + 1); }, 5500);
    };
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) {
        heroOnScreen = entries[0].isIntersecting;
        if (heroOnScreen) start(); else clearInterval(timer);
      }).observe(hero);
    }
    document.addEventListener('visibilitychange', function () { if (document.hidden) clearInterval(timer); else start(); });
    var noHover = window.matchMedia('(hover: none)').matches;
    titles.forEach(function (t, n) {
      t.addEventListener('focus', function () { clearInterval(timer); show(n); });
      t.addEventListener('click', function (e) {
        // On touch screens the first tap focuses the film, the second opens it
        if (noHover && n !== current) { e.preventDefault(); show(n); start(); }
      });
    });
    // The pointer only has to be level with a title, anywhere across the hero, to select it.
    var list = document.querySelector('.hero-list');
    var lockedUntil = 0;
    hero.addEventListener('mousemove', function (e) {
      var box = list.getBoundingClientRect();
      if (e.clientY < box.top - 50 || e.clientY > box.bottom + 40) return;
      clearInterval(timer);
      if (Date.now() < lockedUntil) return; // let the titles finish resizing before judging again
      var best = current, bestDist = Infinity;
      titles.forEach(function (t, n) {
        var r = t.getBoundingClientRect();
        var d = e.clientY < r.top ? r.top - e.clientY : e.clientY > r.bottom ? e.clientY - r.bottom : 0;
        if (d < bestDist) { bestDist = d; best = n; }
      });
      if (best !== current) { show(best); lockedUntil = Date.now() + 380; }
    });
    hero.addEventListener('mouseleave', start);
    start();
  }

  // Arrival: sections resolve out of blur as they scroll into view
  if ('IntersectionObserver' in window && !reduceMotion) {
    var targets = document.querySelectorAll('.section-head, .grid > *, .statement, .signup > *, .page-head .wrap > *, .film-credits .wrap > *, .film-centre > *, .locations, .contact-layout > *, .about-stamp');
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
      });
    }, { threshold: 0.12 });
    targets.forEach(function (el) {
      el.classList.add('reveal');
      io.observe(el);
      // once in focus, the element no longer needs a filter at all, which saves the browser work while scrolling
      el.addEventListener('transitionend', function done(e) {
        if (e.target !== el || e.propertyName !== 'filter' || !el.classList.contains('in')) return;
        el.classList.remove('reveal', 'in');
        el.removeEventListener('transitionend', done);
      });
    });
  }

  // Shop: clicking a small picture shows it as the product's main picture
  document.querySelectorAll('.product .thumbs button').forEach(function (b) {
    b.addEventListener('click', function () {
      var card = b.closest('.product');
      var from = b.querySelectorAll('source, img'), to = card.querySelectorAll('.shot source, .shot img');
      // same formats in the same order in both pictures; only the files change, not the sizes
      to.forEach(function (el, i) {
        el.setAttribute('srcset', from[i].getAttribute('srcset'));
        if (el.tagName === 'IMG') el.setAttribute('src', from[i].getAttribute('src'));
      });
      card.querySelectorAll('.thumbs button').forEach(function (o) {
        o.classList.toggle('on', o === b);
        o.setAttribute('aria-pressed', o === b ? 'true' : 'false');
      });
    });
  });

  // Trailer modal
  var modal = document.getElementById('trailer-modal');
  if (modal) {
    var frame = modal.querySelector('iframe');
    var closeBtn = modal.querySelector('.close');
    var opener = null;
    var close = function () {
      if (!modal.classList.contains('open')) return;
      frame.src = ''; modal.classList.remove('open');
      // focus goes back to the play button that opened the trailer
      if (opener) { opener.focus(); opener = null; }
    };
    document.querySelectorAll('[data-trailer]').forEach(function (b) {
      b.addEventListener('click', function (e) {
        e.preventDefault();
        var id = b.getAttribute('data-trailer');
        frame.src = 'https://www.youtube.com/embed/' + id + '?autoplay=1&rel=0&playsinline=1';
        var link = modal.querySelector('.yt-link');
        if (link) link.href = 'https://www.youtube.com/watch?v=' + id;
        opener = b;
        modal.classList.add('open');
        closeBtn.focus();
      });
    });
    modal.addEventListener('click', function (e) {
      if (e.target === modal || e.target.classList.contains('close')) close();
    });
    document.addEventListener('keydown', function (e) {
      if (!modal.classList.contains('open')) return;
      if (e.key === 'Escape') { close(); return; }
      // keep Tab inside the overlay while it is open: close button, player, YouTube link
      if (e.key === 'Tab') {
        var items = [closeBtn, frame, modal.querySelector('.yt-link')].filter(Boolean);
        var first = items[0], last = items[items.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
        else if (items.indexOf(document.activeElement) < 0) { e.preventDefault(); first.focus(); }
      }
    });
  }
})();
