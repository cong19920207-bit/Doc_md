/* Local, dependency-free ion field. Authentication works independently of this canvas. */
(function () {
  'use strict';
  const scene = document.getElementById('ionScene');
  const canvas = document.getElementById('ionCanvas');
  if (!scene || !canvas) return;
  const toolbar = document.getElementById('sceneToolbar');
  const motionButton = document.getElementById('motionToggle');
  const shapeButton = document.getElementById('shapeNext');
  const paletteButtons = Array.from(document.querySelectorAll('[data-palette]'));
  const rain = document.getElementById('codeRain');
  const trail = document.getElementById('cursorTrail');
  const rainCtx = rain.getContext('2d');
  const trailCtx = trail.getContext('2d');
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const coarsePointer = matchMedia('(pointer: coarse)');
  const names = ['离子涡环', '引力扭结', '星核脉动', '流光薄膜', 'H · 共振'];
  const palettes = [
    [[.28, .85, 1], [.56, .43, 1]],
    [[.68, .42, 1], [.35, .65, 1]],
    [[.34, 1, .72], [.22, .70, 1]]
  ];
  const colorA = palettes[0][0].slice(), colorB = palettes[0][1].slice();
  let gl, program, pointBuffer, lineBuffer, uniforms, attrs;
  let pointCount = 0, lineCount = 0, available = false;
  let width = 1, height = 1, dpr = 1, rainW = 1, rainH = 1;
  let paused = reducedMotion.matches, sceneVisible = true, focused = false;
  let raf = 0, lastFrame = 0, clock = 0, shapeAge = 0, shape = 0;
  let queuedShapes = 0, manualTransition = false;
  let palette = 'auto', zoom = 1, zoomTarget = 1, yaw = 0, pitch = 0;
  let yawTarget = 0, pitchTarget = 0, dragging = false, dragX = 0, dragY = 0;
  const pointer = { x: 8, y: 8, strength: 0, target: 0 };
  let trailPoints = [], lastRain = -1;
  const TAU = Math.PI * 2;

  const vertexSource = `
    precision highp float;
    attribute vec4 aParam;
    attribute vec3 aMark;
    uniform float uTime, uFrom, uTo, uMorph, uDpr, uFit, uZoom, uGlow, uOffset;
    uniform vec2 uResolution, uRotation;
    uniform vec3 uPointer, uColorA, uColorB;
    varying vec3 vColor;
    varying float vAlpha, vKind;
    const float PI = 3.14159265359;
    mat2 rotate(float a) { return mat2(cos(a), -sin(a), sin(a), cos(a)); }
    vec3 field(float state, float u, float v) {
      float t = uTime * .23;
      vec3 p;
      if (state < .5) {
        float major = 1.30 + .13 * sin(3. * u + t);
        float tube = .39 + .13 * sin(2. * u - t);
        float wave = v + .30 * sin(u * 3. + t);
        p = vec3((major + tube * cos(wave)) * cos(u), (major + tube * cos(wave)) * sin(u), tube * sin(wave));
        p.z += .33 * sin(2. * u + t);
        p.yz = rotate(.65) * p.yz;
        p.xy = rotate(-.35) * p.xy;
      } else if (state < 1.5) {
        float r = 1.1 + .39 * cos(3. * u + t * .3);
        p = vec3(r * cos(2. * u), r * sin(2. * u), .62 * sin(3. * u + t * .3));
        p += .18 * vec3(cos(v) * cos(2. * u), cos(v) * sin(2. * u), sin(v));
        p.xz = rotate(.36) * p.xz;
      } else if (state < 2.5) {
        float lat = v * .5;
        float r = 1.35 + .15 * sin(5. * u + t) * sin(3. * lat - t) + .09 * cos(7. * lat + t);
        p = r * vec3(sin(lat) * cos(u), cos(lat), sin(lat) * sin(u));
        p.xz = rotate(t * .17) * p.xz;
      } else if (state < 3.5) {
        float x = (u / PI - 1.) * 1.8;
        float y = (v / PI - 1.) * 1.2;
        p = vec3(x, y, .4 * sin(x * 2.4 + t) + .3 * cos(y * 2.5 - t));
        p.yz = rotate(x * .62 + .3 * sin(t)) * p.yz;
        p.xy = rotate(-.5) * p.xy;
      } else {
        p = aMark;
        p.z += .07 * sin(u * 6. + t);
      }
      // Organic turbulence is continuous through all shape transitions.
      float amount = state > 3.5 ? .012 : .09;
      p += amount * vec3(sin(p.y * 4. + t * 2. + v), cos(p.z * 5. - t + u), sin(p.x * 4. - t * 2.));
      return p;
    }
    void main() {
      float u = aParam.x, v = aParam.y, seed = aParam.z;
      vKind = aParam.w;
      vec3 p = mix(field(uFrom, u, v), field(uTo, u, v), uMorph);
      float turbulence = sin(uMorph * PI);
      p += turbulence * .16 * vec3(sin(u * 5. + uTime), cos(v * 3. - uTime), sin(v + u));
      if (vKind > 1.5) {
        p = aMark;
        p.xy = rotate(uTime * .007) * p.xy;
      } else {
        p.xz = rotate(uRotation.x + .13 * sin(uTime * .13)) * p.xz;
        p.yz = rotate(uRotation.y) * p.yz;
      }
      float perspective = 4.8 / (6.2 - p.z);
      vec2 screen = p.xy * uFit * perspective * uZoom;
      vec2 normalized = screen / (uResolution * .5) + vec2(0., uOffset);
      vec2 delta = normalized - uPointer.xy;
      float influence = exp(-dot(delta, delta) * 8.) * uPointer.z;
      normalized += delta * influence * .30;
      normalized += vec2(-delta.y, delta.x) * influence * .13;
      gl_Position = vec4(normalized, 0., 1.);
      float bright = pow(seed, 10.);
      gl_PointSize = (1. + bright * 2.4) * uDpr * perspective;
      float tint = .5 + .5 * sin(u * 1.8 + v * .7 + uTime * .13);
      vColor = mix(uColorA, uColorB, tint);
      float stream = pow(.5 + .5 * sin(v * 3. + u * 2. + .3 * sin(u * 4.) + uTime * .2), 6.);
      vColor = mix(vColor, vec3(.8, .94, 1.), bright * .5 + stream * .35);
      vAlpha = (.36 + bright * .7 + stream * .6) * (.55 + perspective * .35);
      if (vKind > .5 && vKind < 1.5) vAlpha = .24 + stream * .4;
      if (vKind > 1.5) { vAlpha = .1 + bright * .18; gl_PointSize = (1. + bright * 1.4) * uDpr; }
      if (vKind < 1.5) vAlpha *= clamp(pow(uFit / 190., 1.2), .17, 1.);
      if (uGlow > .5) { gl_PointSize *= 7.; vAlpha *= .105; }
    }
  `;
  const fragmentSource = `
    precision mediump float;
    varying vec3 vColor;
    varying float vAlpha, vKind;
    void main() {
      float alpha = vAlpha;
      if (vKind < .5 || vKind > 1.5) {
        float dist = length(gl_PointCoord - .5) * 2.;
        if (dist > 1.) discard;
        alpha *= pow(1. - dist, 1.35);
      }
      gl_FragColor = vec4(vColor, alpha);
    }
  `;

  // Sample the same H + hexagon as the platform's core icon.
  const segments = [
    [12,2,20.5,7], [20.5,7,20.5,17], [20.5,17,12,22],
    [12,22,3.5,17], [3.5,17,3.5,7], [3.5,7,12,2],
    [8,7,8,17], [16,7,16,17], [8,12,16,12], [3.5,7,8,9], [16,15,20.5,17]
  ];
  function markPoint(u, v, seed) {
    const position = u / TAU * segments.length;
    const segment = segments[Math.min(segments.length - 1, Math.floor(position))];
    const part = position % 1;
    return [(segment[0] + (segment[2] - segment[0]) * part - 12) * .14 + Math.cos(v) * .028,
      -(segment[1] + (segment[3] - segment[1]) * part - 12) * .14 + Math.sin(v) * .028,
      (seed - .5) * .12];
  }
  function shader(type, source) {
    const item = gl.createShader(type);
    gl.shaderSource(item, source); gl.compileShader(item);
    if (!gl.getShaderParameter(item, gl.COMPILE_STATUS)) {
      const error = gl.getShaderInfoLog(item); gl.deleteShader(item); throw new Error(error);
    }
    return item;
  }
  function makeBuffer(data) {
    const buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(data), gl.STATIC_DRAW);
    return buffer;
  }
  function buildGeometry() {
    const points = [], lines = [];
    const count = coarsePointer.matches ? 15000 : 34000;
    for (let i = 0; i < count; i++) {
      const u = Math.random() * TAU, v = Math.random() * TAU, seed = Math.random();
      points.push(u, v, seed, 0, ...markPoint(u, v, seed));
    }
    for (let i = 0; i < 800; i++) {
      points.push(Math.random() * TAU, Math.random() * TAU, Math.random(), 2,
        (Math.random() - .5) * 11, (Math.random() - .5) * 9, -2 - Math.random() * 4);
    }
    const strands = coarsePointer.matches ? 38 : 68, steps = 200;
    for (let j = 0; j < strands; j++) {
      const v = j / strands * TAU;
      for (let i = 0; i < steps; i++) {
        // Don't connect separate strokes when the field becomes the H icon.
        const start = i / steps * TAU, end = (i + 1) / steps * TAU;
        if (Math.floor(start / TAU * segments.length) !== Math.floor(end / TAU * segments.length)) continue;
        for (const u of [start, end]) lines.push(u, v, .4, 1, ...markPoint(u, v, .4));
      }
    }
    pointCount = points.length / 7; lineCount = lines.length / 7;
    pointBuffer = makeBuffer(points); lineBuffer = makeBuffer(lines);
  }
  function bind(buffer) {
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.enableVertexAttribArray(attrs.param); gl.vertexAttribPointer(attrs.param, 4, gl.FLOAT, false, 28, 0);
    gl.enableVertexAttribArray(attrs.mark); gl.vertexAttribPointer(attrs.mark, 3, gl.FLOAT, false, 28, 16);
  }
  function initialize() {
    try {
      gl = canvas.getContext('webgl', { alpha: false, antialias: false, depth: false, powerPreference: 'low-power' });
      if (!gl) throw new Error('WebGL unavailable');
      const vertex = shader(gl.VERTEX_SHADER, vertexSource), fragment = shader(gl.FRAGMENT_SHADER, fragmentSource);
      program = gl.createProgram(); gl.attachShader(program, vertex); gl.attachShader(program, fragment); gl.linkProgram(program);
      gl.deleteShader(vertex); gl.deleteShader(fragment);
      if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program));
      attrs = { param: gl.getAttribLocation(program, 'aParam'), mark: gl.getAttribLocation(program, 'aMark') };
      uniforms = {};
      ['Time','From','To','Morph','Dpr','Fit','Zoom','Glow','Offset','Resolution','Rotation','Pointer','ColorA','ColorB'].forEach(key => { uniforms[key] = gl.getUniformLocation(program, 'u' + key); });
      buildGeometry();
      gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE); gl.disable(gl.DEPTH_TEST);
      available = true; scene.dataset.render = 'webgl'; toolbar.hidden = false;
      resize(); updateMotionButton(); schedule();
    } catch (error) {
      fallback();
      console.warn('Hayyo ion scene is using its static fallback.', error.message);
    }
  }
  function fallback() {
    available = false; scene.dataset.render = 'fallback'; toolbar.hidden = true;
    stop(); clearTrail();
  }
  function setLabel(index) {
    document.getElementById('shapeNumber').textContent = String(index + 1).padStart(2, '0');
    document.getElementById('shapeName').textContent = names[index];
  }
  function draw() {
    if (!available || gl.isContextLost()) return;
    const fraction = Math.max(0, Math.min(1, (shapeAge - 4) / 5));
    const morph = fraction * fraction * (3 - 2 * fraction);
    gl.viewport(0, 0, canvas.width, canvas.height); gl.clearColor(4 / 255, 9 / 255, 15 / 255, 1); gl.clear(gl.COLOR_BUFFER_BIT); gl.useProgram(program);
    gl.uniform1f(uniforms.Time, clock); gl.uniform1f(uniforms.From, shape); gl.uniform1f(uniforms.To, (shape + 1) % names.length);
    const compact = innerWidth <= 820;
    gl.uniform1f(uniforms.Morph, morph); gl.uniform1f(uniforms.Dpr, dpr);
    gl.uniform1f(uniforms.Fit, Math.min(width * .25, height * (compact ? .19 : .31)));
    gl.uniform1f(uniforms.Offset, compact ? -.05 : .12);
    gl.uniform1f(uniforms.Zoom, zoom); gl.uniform2f(uniforms.Resolution, width, height);
    gl.uniform2f(uniforms.Rotation, yaw, pitch); gl.uniform3f(uniforms.Pointer, pointer.x, pointer.y, pointer.strength);
    gl.uniform3fv(uniforms.ColorA, colorA); gl.uniform3fv(uniforms.ColorB, colorB);
    gl.uniform1f(uniforms.Glow, 1); bind(pointBuffer); gl.drawArrays(gl.POINTS, 0, pointCount - 800);
    gl.uniform1f(uniforms.Glow, 0); bind(lineBuffer); gl.drawArrays(gl.LINES, 0, lineCount);
    bind(pointBuffer); gl.drawArrays(gl.POINTS, 0, pointCount);
    setLabel(morph >= .5 ? (shape + 1) % names.length : shape);
  }
  function resize2D(target, context, w, h) {
    if (!context) return;
    const ratio = Math.min(devicePixelRatio || 1, 1.5);
    target.width = Math.max(1, Math.round(w * ratio)); target.height = Math.max(1, Math.round(h * ratio));
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
  }
  function resize() {
    const rect = scene.getBoundingClientRect();
    width = Math.max(1, rect.width); height = Math.max(1, rect.height);
    dpr = Math.min(devicePixelRatio || 1, coarsePointer.matches ? 1.25 : 1.6);
    canvas.width = Math.round(width * dpr); canvas.height = Math.round(height * dpr);
    const rainRect = rain.getBoundingClientRect(); rainW = rainRect.width; rainH = rainRect.height;
    resize2D(rain, rainCtx, rainW, rainH); resize2D(trail, trailCtx, innerWidth, innerHeight);
    draw(); drawRain();
  }
  function updateColors(dt) {
    const colorPhase = clock / 16;
    const index = palette === 'auto' ? Math.floor(colorPhase) % palettes.length : Number(palette);
    const next = palette === 'auto' ? (index + 1) % palettes.length : index;
    const mix = palette === 'auto' ? (1 - Math.cos((colorPhase % 1) * Math.PI)) / 2 : 0;
    const smoothing = 1 - Math.exp(-dt * 3);
    for (let i = 0; i < 3; i++) {
      colorA[i] += (palettes[index][0][i] * (1 - mix) + palettes[next][0][i] * mix - colorA[i]) * smoothing;
      colorB[i] += (palettes[index][1][i] * (1 - mix) + palettes[next][1][i] * mix - colorB[i]) * smoothing;
    }
  }
  function drawRain() {
    if (!rainCtx) return;
    rainCtx.clearRect(0, 0, rainW, rainH);
    rainCtx.font = '10px ui-monospace, SFMono-Regular, monospace';
    const glyphs = '01アイウエカキサシツヌネハミムメモラリルレヲ{}<>:+=HAYYO';
    for (let col = 0; col < Math.ceil(rainW / 18); col++) {
      const head = (clock * (12 + col % 9) + col * 43) % (rainH + 200) - 30;
      for (let row = 0; row < 17; row++) {
        const y = head - row * 14;
        if (y < 0 || y > rainH) continue;
        const alpha = row === 0 ? .65 : (1 - row / 17) * .28;
        rainCtx.fillStyle = 'rgba(98,203,167,' + alpha + ')';
        const character = (col * 7 + row * 13 + Math.floor(clock * 1.6)) % glyphs.length;
        rainCtx.fillText(glyphs[character], col * 18 + 4, y);
      }
    }
  }
  function clearTrail() {
    trailPoints = [];
    if (trailCtx) trailCtx.clearRect(0, 0, innerWidth, innerHeight);
  }
  function drawTrail(dt) {
    if (!trailCtx) return;
    trailCtx.clearRect(0, 0, innerWidth, innerHeight);
    trailPoints = trailPoints.filter(point => { point.life -= dt; return point.life > 0; });
    const rgb = colorA.map(value => Math.round(value * 255)).join(',');
    for (let i = 1; i < trailPoints.length; i++) {
      const point = trailPoints[i], previous = trailPoints[i - 1];
      if (Math.hypot(point.x - previous.x, point.y - previous.y) > 120) continue;
      const strength = point.life / .65;
      trailCtx.strokeStyle = 'rgba(' + rgb + ',' + (strength * .32 * point.dim) + ')';
      trailCtx.lineWidth = Math.max(.2, strength * 1.4);
      trailCtx.beginPath(); trailCtx.moveTo(previous.x, previous.y);
      trailCtx.lineTo(point.x, point.y); trailCtx.stroke();
      if (i % 3 === 0) {
        trailCtx.fillStyle = 'rgba(' + rgb + ',' + (strength * .48 * point.dim) + ')';
        trailCtx.fillRect(point.x + Math.sin(i * 2) * 4, point.y + Math.cos(i * 3) * 4, 1.1, 1.1);
      }
    }
  }
  function shouldAnimate() { return available && !paused && !document.hidden && sceneVisible; }
  function stop() { if (raf) cancelAnimationFrame(raf); raf = 0; lastFrame = 0; }
  function schedule() { if (!raf && shouldAnimate()) raf = requestAnimationFrame(frame); }
  function frame(now) {
    raf = 0;
    if (!shouldAnimate()) { lastFrame = 0; return; }
    const interval = coarsePointer.matches ? 1000 / 30 : 1000 / 45;
    if (lastFrame && now - lastFrame < interval) { schedule(); return; }
    const dt = lastFrame ? Math.min((now - lastFrame) / 1000, .06) : 1 / 45;
    lastFrame = now;
    const ambientDt = dt * (focused ? .3 : 1);
    clock += ambientDt; shapeAge += manualTransition ? dt * 3 : ambientDt;
    if (shapeAge >= 9) {
      shapeAge -= 9; shape = (shape + 1) % names.length;
      if (queuedShapes > 0) { queuedShapes--; shapeAge += 4; }
      else manualTransition = false;
    }
    const ease = 1 - Math.exp(-dt * 5);
    yaw += (yawTarget - yaw) * ease; pitch += (pitchTarget - pitch) * ease;
    zoom += (zoomTarget - zoom) * ease;
    pointer.strength += (pointer.target - pointer.strength) * ease;
    updateColors(dt); draw(); drawTrail(dt);
    if (clock - lastRain > .085) { drawRain(); lastRain = clock; }
    schedule();
  }
  function updateMotionButton() {
    motionButton.setAttribute('aria-pressed', String(paused));
    motionButton.setAttribute('aria-label', paused ? '播放动效' : '暂停动效');
    motionButton.title = paused ? '播放动效' : '暂停动效';
  }
  function setPaused(value) {
    paused = value; updateMotionButton(); clearTrail();
    if (paused) stop(); else schedule();
  }
  motionButton.addEventListener('click', () => setPaused(!paused));
  shapeButton.addEventListener('click', () => {
    if (paused) {
      shape = (shape + (shapeAge >= 6.5 ? 2 : 1)) % names.length;
      shapeAge = 0; queuedShapes = 0; manualTransition = false; draw();
    } else {
      if (shapeAge < 4) shapeAge = 4;
      else queuedShapes++;
      manualTransition = true;
    }
  });
  paletteButtons.forEach(button => button.addEventListener('click', () => {
    palette = button.dataset.palette;
    paletteButtons.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    if (paused) { updateColors(10); draw(); }
  }));
  canvas.addEventListener('pointerdown', event => {
    if (paused || event.button !== 0) return;
    dragging = true; dragX = event.clientX; dragY = event.clientY;
    canvas.setPointerCapture(event.pointerId);
  });
  function releaseDrag() { dragging = false; }
  canvas.addEventListener('pointerup', releaseDrag);
  canvas.addEventListener('pointercancel', releaseDrag);
  canvas.addEventListener('lostpointercapture', releaseDrag);
  canvas.addEventListener('pointermove', event => {
    if (paused) return;
    const rect = canvas.getBoundingClientRect();
    pointer.x = (event.clientX - rect.left) / width * 2 - 1;
    pointer.y = 1 - (event.clientY - rect.top) / height * 2;
    pointer.target = event.pointerType === 'touch' ? .45 : 1;
    if (dragging) {
      yawTarget += (event.clientX - dragX) * .005;
      pitchTarget = Math.max(-.85, Math.min(.85, pitchTarget + (event.clientY - dragY) * .004));
      dragX = event.clientX; dragY = event.clientY;
    }
  });
  canvas.addEventListener('pointerleave', () => { pointer.target = 0; });
  canvas.addEventListener('wheel', event => {
    if (!paused) zoomTarget = Math.max(.78, Math.min(1.2, zoomTarget - event.deltaY * .0004));
  }, { passive: true });
  document.addEventListener('pointermove', event => {
    if (paused || !shouldAnimate() || event.pointerType !== 'mouse' || reducedMotion.matches) return;
    const previous = trailPoints[trailPoints.length - 1];
    if (previous && Math.hypot(previous.x - event.clientX, previous.y - event.clientY) < 3) return;
    // Keep the trace faint over the form and never read field values.
    const inForm = event.target.closest && event.target.closest('.login-panel');
    trailPoints.push({ x: event.clientX, y: event.clientY, life: .65, dim: inForm ? .26 : 1 });
    if (trailPoints.length > 38) trailPoints.shift();
  }, { passive: true });
  document.addEventListener('focusin', event => { focused = event.target.matches('input'); });
  document.addEventListener('focusout', () => { focused = false; });
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) { stop(); clearTrail(); } else schedule();
  });
  window.addEventListener('pagehide', () => { stop(); clearTrail(); });
  window.addEventListener('pageshow', schedule);
  window.addEventListener('resize', resize, { passive: true });
  reducedMotion.addEventListener('change', () => { setPaused(reducedMotion.matches); draw(); });
  canvas.addEventListener('webglcontextlost', event => { event.preventDefault(); fallback(); });
  canvas.addEventListener('webglcontextrestored', initialize);
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(entries => {
      sceneVisible = entries[0].isIntersecting;
      if (sceneVisible) schedule(); else { stop(); clearTrail(); }
    }, { threshold: .01 }).observe(scene);
  }
  initialize();
})();
