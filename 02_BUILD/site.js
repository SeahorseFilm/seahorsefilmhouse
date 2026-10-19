(function () {
  var header = document.querySelector('.site-header');
  var toggle = document.querySelector('.nav-toggle');

  function onScroll() {
    header.classList.toggle('solid', window.scrollY > 40 || !document.querySelector('.hero, .film-hero'));
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  if (toggle) {
    toggle.addEventListener('click', function () {
      var open = header.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  // Hero: hovering a film title brings its image into focus
  var titles = document.querySelectorAll('.hero-title');
  if (titles.length) {
    var layers = document.querySelectorAll('.hero-bg');
    var notes = document.querySelectorAll('.hero-note');
    var current = 0;
    var timer;
    var show = function (i) {
      current = (i + titles.length) % titles.length;
      [titles, layers, notes].forEach(function (set) {
        set.forEach(function (el, n) { el.classList.toggle('active', n === current); });
      });
      // let the page know which film is showing, so its image can be given a lighter tint
      var m = layers[current].className.match(/bg-([a-z0-9-]+)/);
      if (m) layers[current].parentNode.setAttribute('data-film', m[1]);
    };
    var start = function () { clearInterval(timer); timer = setInterval(function () { show(current + 1); }, 5500); };
    var noHover = window.matchMedia('(hover: none)').matches;
    titles.forEach(function (t, n) {
      t.addEventListener('focus', function () { clearInterval(timer); show(n); });
      t.addEventListener('click', function (e) {
        // On touch screens the first tap focuses the film, the second opens it
        if (noHover && n !== current) { e.preventDefault(); show(n); start(); }
      });
    });
    // The pointer only has to be level with a title, anywhere across the hero, to select it.
    var hero = document.getElementById('hero');
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
  if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    var targets = document.querySelectorAll('.section-head, .grid > *, .statement, .signup > *, .page-head .wrap > *, .film-credits .wrap > *, .film-centre > *, .locations, .contact-layout > *, .about-stamp');
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
      });
    }, { threshold: 0.12 });
    targets.forEach(function (el) { el.classList.add('reveal'); io.observe(el); });
  }

  // Shop: clicking a small picture shows it as the product's main picture
  document.querySelectorAll('.product .thumbs button').forEach(function (b) {
    b.addEventListener('click', function () {
      var card = b.closest('.product');
      card.querySelector('.shot img').src = b.getAttribute('data-src');
      card.querySelectorAll('.thumbs button').forEach(function (o) { o.classList.toggle('on', o === b); });
    });
  });

  // Trailer modal
  var modal = document.getElementById('trailer-modal');
  if (modal) {
    var frame = modal.querySelector('iframe');
    var close = function () { frame.src = ''; modal.classList.remove('open'); };
    document.querySelectorAll('[data-trailer]').forEach(function (b) {
      b.addEventListener('click', function (e) {
        e.preventDefault();
        var id = b.getAttribute('data-trailer');
        frame.src = 'https://www.youtube.com/embed/' + id + '?autoplay=1&rel=0&playsinline=1';
        var link = modal.querySelector('.yt-link');
        if (link) link.href = 'https://www.youtube.com/watch?v=' + id;
        modal.classList.add('open');
      });
    });
    modal.addEventListener('click', function (e) {
      if (e.target === modal || e.target.classList.contains('close')) close();
    });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
  }
})();
