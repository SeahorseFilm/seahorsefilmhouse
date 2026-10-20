// Home hero, WebGL version (trial): changing films works like a focus pull on a camera lens.
// The current film drifts out of focus (with a lens's slight 'breathing'), the next one takes over
// while both are soft, then pulls sharp. No grain, no ripple.
// site.js keeps choosing the film; this script only draws it. If anything fails, or the device
// is slow, it removes itself and the ordinary CSS hero is left showing.
(function () {
  var hero = document.getElementById('hero');
  if (!hero || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  if (navigator.deviceMemory && navigator.deviceMemory < 4) return;
  var layers = Array.prototype.slice.call(hero.querySelectorAll('.hero-bg'));
  if (!layers.length) return;

  var canvas = document.createElement('canvas');
  canvas.className = 'hero-gl';
  canvas.setAttribute('aria-hidden', 'true');
  var debug = /gldebug/.test(location.search);
  var freeze = debug && (location.search.match(/freeze=(\d),(\d),([\d.]+)/) || 0);
  if (freeze) freeze = [+freeze[1], +freeze[2], +freeze[3]];   // ?gldebug keeps the canvas readable and never falls back, for testing
  var opts = { antialias: false, alpha: false, powerPreference: 'low-power', preserveDrawingBuffer: debug };
  var gl = canvas.getContext('webgl2', opts), gl2 = !!gl;
  if (!gl) gl = canvas.getContext('webgl', opts);
  if (!gl) return;

  var VS = 'attribute vec2 p; varying vec2 v; void main(){ v = p * 0.5 + 0.5; gl_Position = vec4(p, 0.0, 1.0); }';
  var FS = [
    'precision highp float;',
    'varying vec2 v;',
    'uniform sampler2D tA, tB;',
    'uniform vec2 rA, rB;',       // cover scale for each image
    'uniform vec2 oA, oB;',       // cover offset (CSS background-position)
    'uniform float prog, aspect;',
    // lens blur: 40 samples on a golden-angle spiral fill a disc evenly; bright points weigh more, like bokeh
    'vec3 lens(sampler2D t, vec2 c, float r){',
    '  vec3 sum = vec3(0.0); float wsum = 0.0;',
    '  for (int i = 0; i < 40; i++) {',
    '    float k = float(i) + 0.5, rad = sqrt(k / 40.0) * r, ang = k * 2.39996;',
    '    vec3 s = texture2D(t, c + vec2(cos(ang) / aspect, sin(ang)) * rad).rgb;',
    '    float w = 1.0 + 3.0 * pow(dot(s, vec3(0.299, 0.587, 0.114)), 4.0);',
    '    sum += s * w; wsum += w; }',
    '  return sum / wsum; }',
    'vec3 shot(sampler2D t, vec2 r, vec2 o, vec2 uv, float f){',   // f: 0 sharp, 1 fully out of focus
    '  uv = (uv - 0.5) / (1.0 + 0.012 * f) + 0.5;',                 // focus breathing: the frame eases in a touch as focus slides
    '  vec2 c = uv * r + o;',
    '  if (f < 0.002) return texture2D(t, c).rgb;',
    '  return lens(t, c, 0.02 * f); }',
    'void main(){',
    '  vec2 uv = v;',
    '  if (prog <= 0.0) { gl_FragColor = vec4(shot(tA, rA, oA, uv, 0.0), 1.0); return; }',
    '  float fOut = smoothstep(0.0, 0.42, prog);',                 // old film: focus slides away
    '  float fIn = pow(1.0 - smoothstep(0.42, 1.0, prog), 2.2);',            // new film: focus pulls in
    '  float m = smoothstep(0.34, 0.5, prog);',                    // hand-over happens while both are soft
    '  vec3 a = m < 1.0 ? shot(tA, rA, oA, uv, fOut) : vec3(0.0);',
    '  vec3 b = m > 0.0 ? shot(tB, rB, oB, uv, fIn) : vec3(0.0);',
    '  gl_FragColor = vec4(mix(a, b, m), 1.0);',
    '}'
  ].join('\n');

  function sh(type, src) {
    var s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
    return s;
  }
  var prog;
  try {
    prog = gl.createProgram();
    gl.attachShader(prog, sh(gl.VERTEX_SHADER, VS));
    gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FS));
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) return;
  } catch (e) { return; }
  gl.useProgram(prog);
  var buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
  var loc = gl.getAttribLocation(prog, 'p');
  gl.enableVertexAttribArray(loc);
  gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
  var U = {};
  ['tA', 'tB', 'rA', 'rB', 'oA', 'oB', 'prog', 'aspect'].forEach(function (k) { U[k] = gl.getUniformLocation(prog, k); });
  gl.uniform1i(U.tA, 0); gl.uniform1i(U.tB, 1);
  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
  var maxTex = gl.getParameter(gl.MAX_TEXTURE_SIZE);

  // Each film's picture comes from the page itself: site.js fetches the images (right size, format and,
  // on tall phone screens, the phone version of Tokyo); this script waits until they are in, then uses
  // the same pixels and the same framing (CSS object-position).
  var films = layers.map(function (el) {
    var img = el.querySelector('img');
    var pos = getComputedStyle(img).objectPosition.split(' ').map(function (s) { return s.indexOf('%') > -1 ? parseFloat(s) / 100 : 0.5; });
    return { img: img, px: pos[0], py: pos[1] === undefined ? 0.5 : pos[1], tex: null, w: 1, h: 1 };
  });

  function ready(f) {
    return new Promise(function (ok, bad) {
      var im = f.img, tries = 0;
      (function check() {
        var real = im.currentSrc && im.currentSrc.indexOf('data:') !== 0;
        if (real && im.complete && im.naturalWidth > 1) {
          (im.decode ? im.decode() : Promise.resolve()).then(function () { upload(f); ok(); }, bad);
        } else if (++tries > 150) bad();                       // nothing after 30 s: keep the CSS hero
        else setTimeout(check, 200);
      })();
    });
  }
  function upload(f) {
    var im = f.img, src = im;
    if (im.naturalWidth > maxTex || im.naturalHeight > maxTex) {   // shrink only if the GPU can't take it
      var k = maxTex / Math.max(im.naturalWidth, im.naturalHeight), c = document.createElement('canvas');
      c.width = Math.floor(im.naturalWidth * k); c.height = Math.floor(im.naturalHeight * k);
      c.getContext('2d').drawImage(im, 0, 0, c.width, c.height); src = c;
    }
    f.tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, f.tex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, src);
    if (gl2) gl.generateMipmap(gl.TEXTURE_2D);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl2 ? gl.LINEAR_MIPMAP_LINEAR : gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    f.w = im.naturalWidth; f.h = im.naturalHeight;
  }

  function activeIndex() {
    for (var i = 0; i < layers.length; i++) if (layers[i].classList.contains('active')) return i;
    return 0;
  }
  var from = activeIndex(), to = from, t0 = 0, DUR = 600, running = false, visible = true;
  var slowFrames = 0, frames = 0, last = 0;

  function cover(f, aspect) {
    var ia = f.w / f.h, r = [Math.min(aspect / ia, 1), Math.min(ia / aspect, 1)];
    return { r: r, o: [(1 - r[0]) * f.px, (1 - r[1]) * (1 - f.py)] };
  }
  function resize() {
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var w = canvas.clientWidth, h = canvas.clientHeight;
    canvas.width = Math.max(1, Math.round(w * dpr)); canvas.height = Math.max(1, Math.round(h * dpr));
    gl.viewport(0, 0, canvas.width, canvas.height);
  }
  function giveUp() {
    running = false; hero.classList.remove('gl-on'); canvas.remove();
  }
  function frame(now) {
    if (!running) return;
    if (visible && !document.hidden) {
      if (last && now - last > 45) { if (++slowFrames > 40 && !debug) return giveUp(); }  // too slow here: back to CSS
      frames++; last = now;
      var p = to === from ? 1 : Math.min((now - t0) / DUR, 1);
      if (freeze) { from = freeze[0]; to = freeze[1]; p = freeze[2]; }   // test only: hold one moment of a hand-over
      if (p >= 1) from = to;
      var aspect = canvas.width / canvas.height, A = cover(films[from], aspect), B = cover(films[to], aspect);
      gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, films[from].tex);
      gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, films[to].tex);
      gl.uniform2fv(U.rA, A.r); gl.uniform2fv(U.oA, A.o);
      gl.uniform2fv(U.rB, B.r); gl.uniform2fv(U.oB, B.o);
      gl.uniform1f(U.prog, from === to ? 0 : p);
      gl.uniform1f(U.aspect, aspect);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    } else { last = 0; }
    requestAnimationFrame(frame);
  }

  Promise.all(films.map(ready)).then(function () {
    hero.insertBefore(canvas, hero.querySelector('.hero-shade'));
    resize();
    hero.classList.add('gl-on');
    running = true;
    requestAnimationFrame(frame);
    if (debug) window.__heroGL = function () { return { frames: frames, slow: slowFrames, running: running, visible: visible, from: from, to: to }; };
    new MutationObserver(function () {
      var i = activeIndex();
      if (i === to) return;
      if (from !== to) from = to;         // a new choice mid hand-over starts from the film being revealed
      to = i; t0 = performance.now();
    }).observe(hero, { subtree: true, attributes: true, attributeFilter: ['class'] });
    if ('ResizeObserver' in window) new ResizeObserver(resize).observe(canvas); else window.addEventListener('resize', resize);
    if ('IntersectionObserver' in window) new IntersectionObserver(function (en) { visible = en[0].isIntersecting; }).observe(hero);
    canvas.addEventListener('webglcontextlost', function (ev) { ev.preventDefault(); giveUp(); });
  }).catch(function () { /* an image failed: keep the CSS hero */ });
})();
