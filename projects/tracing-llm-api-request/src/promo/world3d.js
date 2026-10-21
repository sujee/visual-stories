/* The 3D journey for promo3d.html: from the send to the end of decode (story time 4..22), seen by a chase camera.
   Uses the page's shared constants and helpers (C, P, W, H, TOKENS, OUT, TOKCOL, T_DEC, STEP, step, seg, lerp, easings, rnd)
   and window.THREE (node_modules/three, a classic script). The world is laid out along -z, one place per stage:
     network tunnel z 10..-95 · gateway z -100 · tokenizer z -160 · router, replicas at z -200
     GPU batch around z -300 · prefill + decode on a GPU around z -380 (the client's screen sits beside it, off the chip)
   world3d(t) positions everything for story time t and renders one frame. Deterministic: no clocks, seeded layout. */
function makeWorld3d(glCanvas) {
  const T = window.THREE;
  const R3 = new T.WebGLRenderer({ canvas: glCanvas, antialias: true, preserveDrawingBuffer: true });
  R3.setPixelRatio(1);
  const S = new T.Scene(); S.background = new T.Color(C.bg); S.fog = new T.Fog(C.bg, 28, 120);
  const cam = new T.PerspectiveCamera(P ? 64 : 46, W / H, .1, 400);
  S.add(new T.AmbientLight(0xaabbee, 1.2));
  const sun = new T.DirectionalLight(0xffffff, 1.6); sun.position.set(8, 30, 20); S.add(sun);
  const DF = P ? 1.55 : 1;                                  // vertical: pull the camera back to fit the narrow frame

  const col = c => new T.Color(c);
  const mat = (c, e = .35, o = {}) => new T.MeshStandardMaterial({ color: col(c), emissive: col(c), emissiveIntensity: e, roughness: .5, metalness: .1, ...o });
  const box = (w, h, d, m) => new T.Mesh(new T.BoxGeometry(w, h, d), m);
  const add = (o, x = 0, y = 0, z = 0) => { o.position.set(x, y, z); S.add(o); return o; };
  const GLOW = (() => { const c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d'); const r = g.createRadialGradient(64, 64, 0, 64, 64, 64); r.addColorStop(0, 'rgba(255,255,255,1)'); r.addColorStop(.2, 'rgba(255,255,255,.55)'); r.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = r; g.fillRect(0, 0, 128, 128); return new T.CanvasTexture(c); })();
  const halo = (c, s) => { const sp = new T.Sprite(new T.SpriteMaterial({ map: GLOW, color: col(c), blending: T.AdditiveBlending, depthWrite: false, transparent: true, fog: false })); sp.scale.set(s, s, 1); return sp; };
  function label(str, color, h = 1, o = {}) {               // a camera-facing text sprite, h = world height
    const fs = 96, c = document.createElement('canvas'), g = c.getContext('2d'), font = `${o.w || 700} ${fs}px JBM`;
    g.font = font; c.width = Math.ceil(g.measureText(str).width) + (o.chip ? 90 : 30); c.height = Math.round(fs * (o.chip ? 1.55 : 1.3));
    g.font = font; g.textBaseline = 'middle'; g.textAlign = 'center';
    if (o.chip) { g.fillStyle = '#0D1628'; g.strokeStyle = color; g.lineWidth = 8; g.beginPath(); g.roundRect(5, 5, c.width - 10, c.height - 10, 34); g.fill(); g.stroke(); }
    g.fillStyle = o.ink || color; g.fillText(str, c.width / 2, c.height / 2 + 5);
    const tex = new T.CanvasTexture(c); tex.colorSpace = T.SRGBColorSpace; tex.anisotropy = 8;
    const sp = new T.Sprite(new T.SpriteMaterial({ map: tex, transparent: true, depthWrite: false, fog: false }));
    sp.scale.set(h * c.width / c.height, h, 1); sp.renderOrder = 10; return sp;
  }
  const show = (o, a) => { o.visible = a > .01; o.material.opacity = a; };
  function tube(points, r, m) { return new T.Mesh(new T.TubeGeometry(new T.CatmullRomCurve3(points), 48, r, 6), m); }
  function chipSlab(w, d, x, z, y = -.25) {                 // a GPU: dark slab, glowing edges, pins, a label
    const g = new T.Group();
    g.add(box(w, .5, d, mat('#0D1628', .25)));
    const edge = new T.LineSegments(new T.EdgesGeometry(new T.BoxGeometry(w, .5, d)), new T.LineBasicMaterial({ color: col(C.dim), transparent: true }));
    g.add(edge);
    const pm = mat(C.dim, .4);
    for (let k = -w / 2 + 1; k <= w / 2 - 1; k += 1.4) for (const s of [-1, 1]) { const p = box(.25, .15, .8, pm); p.position.set(k, 0, s * (d / 2 + .4)); g.add(p); }
    for (let k = -d / 2 + 1; k <= d / 2 - 1; k += 1.4) for (const s of [-1, 1]) { const p = box(.8, .15, .25, pm); p.position.set(s * (w / 2 + .4), 0, k); g.add(p); }
    const lab = label('GPU', C.muted, 1.1); lab.position.set(-w / 2 + 2, 1, d / 2 - 1.2); g.add(lab);
    add(g, x, y, z); return { g, edge };
  }

  // ---------------------------------------------------------------- network tunnel
  const ringM = new T.MeshBasicMaterial({ color: col('#1E3A66'), transparent: true, opacity: .9 });
  for (let z = 10; z > -96; z -= 7) { const r = new T.Mesh(new T.TorusGeometry(6, .04, 6, 48), ringM); add(r, 0, 1, z); }
  const streakM = [C.cyan, C.violet].map(c => new T.MeshBasicMaterial({ color: col(c), transparent: true, opacity: .35 }));
  for (let k = 0; k < 70; k++) {
    const a = rnd() * Math.PI * 2, r = 3 + rnd() * 2.6, len = 2 + rnd() * 6;
    add(box(.04, .04, len, streakM[k % 3 ? 0 : 1]), Math.cos(a) * r, 1 + Math.sin(a) * r, 8 - rnd() * 100);
  }
  const httpLab = label('HTTPS  POST /v1/messages', C.cyan, .26, { chip: true }); S.add(httpLab);

  // ---------------------------------------------------------------- the request (a glowing packet with a trail)
  const pkt = add(new T.Mesh(new T.SphereGeometry(.38, 24, 16), new T.MeshBasicMaterial({ color: 0xf4fdff })));
  const pktHalo = halo(C.cyan, 3); S.add(pktHalo);
  const trail = Array.from({ length: 14 }, (_, k) => { const h = halo(C.cyan, 1.6 * (1 - k / 16)); S.add(h); return h; });

  // ---------------------------------------------------------------- gateway (z -100)
  const GZ = -100, gateM = mat(C.dim, .3), gate = [];
  for (const x of [-10.5, -3.5, 3.5, 10.5]) gate.push(add(box(.6, 7, .6, gateM), x, 3.5, GZ));
  gate.push(add(box(21.6, .6, .6, gateM), 0, 7.2, GZ));
  const scanner = add(box(21, .08, .4, new T.MeshBasicMaterial({ color: col(C.cyan) })), 0, 0, GZ);
  const others = [[-7, C.amber], [7, C.pink]].map(([x, c]) => { const m = add(new T.Mesh(new T.SphereGeometry(.3, 16, 12), new T.MeshBasicMaterial({ color: col(c), transparent: true })), x, 1, 0); const h = halo(c, 3); S.add(h); return { m, h, x, c }; });
  const lab429 = label('✕ 429', C.red, .8); S.add(lab429);
  const labAuth = label('auth ✓', C.green, .6, { chip: true }), labRate = label('rate limit ✓', C.green, .6, { chip: true }); S.add(labAuth); S.add(labRate);

  // ---------------------------------------------------------------- tokens: six cubes that travel on as the request
  const toks = TOKENS.map(([s, id], i) => {
    const m = mat(TOKCOL[i], .45, { transparent: true });
    const cube = add(box(1.6, 1, 1, m));
    const lab = label(s, C.ink, .75, { chip: true, ink: C.ink }); S.add(lab);
    const idl = label(String(id), C.muted, .4, { w: 400 }); S.add(idl);
    return { cube, m, lab, idl };
  });
  const burst = halo(C.cyan, 1); S.add(burst);

  // ---------------------------------------------------------------- router (replicas at z -200)
  const RZ = -200, RX = [-15, -5, 5, 15], HIT = 2, R0 = new T.Vector3(0, 1, -163);
  const reps = RX.map((x, i) => {
    const m = mat('#16233D', .2), b = add(box(6, 4, 3, m), x, 2, RZ);
    const edge = new T.LineSegments(new T.EdgesGeometry(new T.BoxGeometry(6, 4, 3)), new T.LineBasicMaterial({ color: col(C.dim) })); b.add(edge);
    const cells = Array.from({ length: 10 }, (_, j) => {
      const hitCell = i === HIT && j < 6, v = rnd(), c = hitCell ? '#24406A' : v < .25 ? '#111C30' : ['#3A3360', '#4A3A28', '#28483A', '#4A2A44'][Math.floor(v * 4) % 4];
      const cm = mat(c, .3); const cb = box(.42, .7, .1, cm); cb.position.set(-2.45 + j * .54, -.4, 1.56); b.add(cb); return { cm, hitCell };
    });
    const lab = label(`replica ${i + 1}`, C.muted, .55, { w: 400 }); lab.position.set(0, 2.7, 0); b.add(lab);
    const curve = new T.CatmullRomCurve3([R0, new T.Vector3(x * .35, 1, -180), new T.Vector3(x, 1, RZ + 1.6)]);
    const lm = new T.MeshBasicMaterial({ color: col(C.dim), transparent: true });
    add(new T.Mesh(new T.TubeGeometry(curve, 48, .06, 6), lm));
    return { b, m, edge, cells, curve, lm };
  });
  const labHit = label('cache hit', C.green, .7, { chip: true, ink: C.green }); S.add(labHit);

  // ---------------------------------------------------------------- GPU batch (z -300)
  const BZ = -300, LANEZ = i => BZ + (i - 3.5) * 2, OURS = 3;
  const batchChip = chipSlab(24, 18, 0, BZ);
  const rows = Array.from({ length: 8 }, (_, i) => i === OURS ? null : { n: 3 + Math.floor(rnd() * 8), c: [C.amber, C.pink, C.green, C.violet][i % 4], d: rnd() * .5 }).map((r, i) => {
    if (!r) return null;
    r.cubes = Array.from({ length: r.n }, () => add(box(.85, .55, .85, mat(r.c, .35)))); r.z = LANEZ(i); return r;
  });
  const labBatch = label('8 requests · 1 GPU · 1 batch', C.muted, .8, { w: 400 }); labBatch.position.set(0, .8, BZ + 11); S.add(labBatch);

  // ---------------------------------------------------------------- prefill + decode on a GPU (z -380)
  const PZ = -380, TX = i => (i - 2.5) * 2.4;
  const pgpu = chipSlab(30, 16, 0, PZ - 1);
  const kv = TOKENS.map((_, i) => Array.from({ length: 4 }, (_, k) => add(box(1.2, .55, .55, mat(TOKCOL[i], .5, { transparent: true })), TX(i), .45 + k * .7, PZ - 2.2)));
  const kvOut = Array.from({ length: OUT.length }, (_, j) => Array.from({ length: 4 }, (_, k) => add(box(.9, .55, .55, mat(C.violet, .5, { transparent: true })), -11 + j * 1.2, .45 + k * .7, PZ - 4.6)));
  const labKV = label('KV cache', C.muted, .6, { w: 400 }); labKV.position.set(-7.6, 3.5, PZ - 2.2); S.add(labKV);
  const outCube = add(box(1.6, .8, .8, mat(C.violet, .5)), 0, .8, PZ + 5);
  const outLabs = OUT.map(s => { const l = label(s, C.ink, .6, { chip: true }); S.add(l); return l; });
  const wave = add(box(16, 3.2, .05, new T.MeshBasicMaterial({ color: col(C.cyan), transparent: true, blending: T.AdditiveBlending, depthWrite: false })), 0, 1.4, PZ);
  // the developer's screen, off the GPU: streamed text arrives here
  const SCRP = P ? new T.Vector3(0, 11, PZ - 6) : new T.Vector3(21, 4, PZ - 1);
  const sc = document.createElement('canvas'); sc.width = 1024; sc.height = 640; const sg = sc.getContext('2d');
  const stex = new T.CanvasTexture(sc); stex.colorSpace = T.SRGBColorSpace; stex.anisotropy = 8;
  const screen = add(new T.Mesh(new T.PlaneGeometry(12, 7.5), new T.MeshBasicMaterial({ map: stex, fog: false })), SCRP.x, SCRP.y, SCRP.z);
  if (!P) screen.rotation.y = -.45;
  const SSE0 = new T.Vector3(P ? 0 : 2, P ? 3.2 : 1.6, PZ + (P ? -3 : 5)), SSE1 = P ? new T.Vector3(0, 7, PZ - 6) : new T.Vector3(15.8, 3.6, PZ + 1.2);
  add(tube([SSE0, SSE0.clone().lerp(SSE1, .5).add(new T.Vector3(0, .6, 0)), SSE1], .04, new T.MeshBasicMaterial({ color: col(C.dim) })));
  const sseLab = label('SSE stream', C.muted, .55, { w: 400 }); sseLab.position.copy(SSE0.clone().lerp(SSE1, .5).add(new T.Vector3(P ? 2.4 : 0, 1.4, 0))); S.add(sseLab);
  const flyers = Array.from({ length: 4 }, () => { const m = add(new T.Mesh(new T.SphereGeometry(.2, 12, 8), new T.MeshBasicMaterial({ color: col(C.violet) }))); const h = halo(C.violet, 1.8); S.add(h); return { m, h }; });
  let lastScreen = '';
  function drawScreen(shown, cursor) {
    const key = shown + '/' + cursor; if (key === lastScreen) return; lastScreen = key;
    sg.fillStyle = '#0A1222'; sg.fillRect(0, 0, 1024, 640); sg.strokeStyle = '#2A3A5E'; sg.lineWidth = 6; sg.strokeRect(3, 3, 1018, 634);
    [C.red, C.amber, C.green].forEach((c, i) => { sg.fillStyle = c; sg.beginPath(); sg.arc(40 + i * 34, 38, 10, 0, 7); sg.fill(); });
    sg.font = '400 34px JBM'; sg.fillStyle = C.muted; sg.textBaseline = 'middle'; sg.fillText('> ' + PROMPT, 40, 100);
    sg.font = '400 46px JBM'; sg.fillStyle = C.ink;
    const lines = [''];
    for (const w of OUT.slice(0, shown)) { const s = lines.at(-1) ? lines.at(-1) + (w === '.' ? '' : ' ') + w : w; if (sg.measureText(s).width > 940) lines.push(w); else lines[lines.length - 1] = s; }
    lines.forEach((s, i) => sg.fillText(s, 40, 180 + i * 64));
    if (cursor) { sg.fillStyle = C.violet; sg.fillRect(40 + sg.measureText(lines.at(-1)).width + 10, 180 + (lines.length - 1) * 64 - 24, 24, 48); }
    stex.needsUpdate = true;
  }

  // ---------------------------------------------------------------- motion
  const V = (x, y, z) => new T.Vector3(x, y, z);
  const pk = t => {                                         // the packet, 4..8.4
    if (t < 6) return V(.3 * Math.sin(t * 3), 1 + .15 * Math.sin(t * 4), -92 * (t - 4) / 2);
    if (t < 8) return V(0, 1, t < 7.3 ? lerp(-92, GZ + 3, eOC(seg(t, 6.0, 6.65))) : lerp(GZ + 3, -150, eIn(seg(t, 7.3, 8.0))));
    return V(0, 1, lerp(-150, -160, eOC(seg(t, 8.0, 8.35))));
  };
  const trainAt = t => reps[HIT].curve.getPoint(eIO(seg(t, 11.15, 11.85)));
  function tokPlace(i, t) {                                 // where token i is: {x, y, z, s, lab}
    if (t < 10) {
      const u = eOB(seg(t, 8.42 + i * .04, 8.85 + i * .04)), m = eIO(seg(t, 9.45, 9.9));
      return { x: lerp(lerp(0, (i - 2.5) * 2.1, u), (i - 2.5) * 1.75, m), y: 1, z: -160, s: lerp(.3, 1, clamp(u, 0, 1.2)), lab: (1 - m) * seg(t, 8.5, 8.7), id: seg(t, 8.95, 9.2) * (1 - seg(t, 9.3, 9.45)) };
    }
    if (t < 12) { const c = t < 10.95 ? R0 : trainAt(t), s = lerp(1, .5, eIO(seg(t, 11.15, 11.85))); return { x: c.x + (i - 2.5) * 1.75 * s, y: c.y, z: c.z, s, lab: 0, id: 0 }; }
    if (t < 14) { const u = eOC(seg(t, 12.85, 13.35)); return { x: lerp(-26, -10, u) + i * 1.1, y: .45, z: LANEZ(OURS), s: .53, lab: 0, id: 0 }; }
    const dx = -32 * (1 - eOC(seg(t, 14.0, 14.45)));         // enters the GPU from the left
    return { x: TX(i) + dx, y: 1, z: PZ, s: 1, lab: seg(t, 14.3, 14.5), id: 0 };
  }
  const look = (pos, at) => ({ pos, at });
  const mixCam = (a, b, u) => ({ pos: a.pos.clone().lerp(b.pos, u), at: a.at.clone().lerp(b.at, u) });
  const chase = (p, back = 7, up = 2.4) => look(p.clone().add(V(0, up, back)), p.clone().add(V(0, .4, -4)));
  function camAt(t) {
    if (t < 6) return chase(V(0, 1, pk(t).z), 6, 1.8);
    if (t < 8) return mixCam(chase(pk(t)), look(V(0, 10, GZ + 24), V(0, 2.5, GZ)), eIO(seg(t, 6.3, 6.75)) * (1 - eIO(seg(t, 7.3, 7.65))));
    if (t < 10) {
      const front = look(V(0, 4.5, -146), V(0, 1, -160));
      return mixCam(mixCam(chase(pk(Math.min(t, 8.35))), front, eIO(seg(t, 8.35, 8.8))), chase(V(0, 1, -160), 8, 3), eIO(seg(t, 9.5, 10)));
    }
    if (t < 12) {
      let c = mixCam(chase(R0.clone().setZ(-160), 8, 3), look(V(0, 11, -168), V(0, 1, -196)), eIO(seg(t, 10.05, 10.6)));
      const tp = trainAt(t); c = mixCam(c, look(tp.clone().add(V(0, 3.5, 9)), tp.clone().add(V(0, .5, -6))), eIO(seg(t, 11.0, 11.5)));
      return mixCam(c, look(V(RX[HIT], 1.6, RZ + 3.2), V(RX[HIT], 1.2, RZ)), eIn(seg(t, 11.75, 12.0)));   // into the replica
    }
    if (t < 14) {
      const lz = LANEZ(OURS), u = eOC(seg(t, 12.85, 13.35)), ox = lerp(-26, -10, u) + 2.75;
      let c = mixCam(look(V(ox, 2.5, lz + 7), V(ox, .4, lz)), look(V(-3, 21, BZ + 17), V(-3, 0, BZ)), eIO(seg(t, 12.1, 12.8)));
      return mixCam(c, look(V(-7.25, 1.1, lz + 2.2), V(-7.25, .5, lz)), eIn(seg(t, 13.55, 14.0)));        // into our lane
    }
    if (t < 17) return mixCam(look(V(-4, 7, PZ + 18), V(0, 1, PZ)), look(V(0, 5, PZ + 14), V(0, 1.5, PZ + 1)), eIO(seg(t, 15.8, 17.0)));
    const wide = P ? look(V(0, 9, PZ + 20), V(0, 5, PZ - 2)) : look(V(10, 9, PZ + 26), V(10, 2.5, PZ));
    return mixCam(look(V(0, 5, PZ + 14), V(0, 1.5, PZ + 1)), wide, eIO(seg(t, 17.0, 17.8)));
  }

  function smoothCam(t) {                                   // the camera trails its target a little: a weighted average of the
    const lo = t >= 14 ? 14 : t >= 12 ? 12 : 4, n = 8;      // last ~0.25 story s (restarting at the zoom-through cuts)
    const out = { pos: V(0, 0, 0), at: V(0, 0, 0) }; let w = 0;
    for (let k = 0; k < n; k++) { const c = camAt(Math.max(lo, t - k * .035)), wk = n - k; out.pos.addScaledVector(c.pos, wk); out.at.addScaledVector(c.at, wk); w += wk; }
    out.pos.divideScalar(w); out.at.divideScalar(w); return out;
  }

  function frame(t) {
    // packet + trail
    const live = t < 8.4, p = pk(t);
    pkt.visible = pktHalo.visible = live; pkt.position.copy(p); pktHalo.position.copy(p);
    pktHalo.scale.setScalar(3 + 6 * seg(t, 8.25, 8.4));
    trail.forEach((h, k) => { const q = pk(Math.max(4, t - (k + 1) * .03)); h.position.copy(q); h.visible = live && t - (k + 1) * .03 > 4; h.material.opacity = .5 * (1 - k / 14); });
    show(httpLab, eOC(seg(t, 4.2, 4.5)) * (1 - seg(t, 5.5, 5.7))); httpLab.position.copy(p).add(V(0, .75, 0));
    // gateway
    const ok = seg(t, 7.15, 7.3); gateM.color.set(ok ? C.green : C.dim); gateM.emissive.set(ok ? C.green : C.dim); gateM.emissiveIntensity = .3 + .7 * ok;
    scanner.visible = t > 6.6 && t < 7.1; scanner.position.y = lerp(7, 0, eIO(seg(t, 6.6, 7.05)));
    const [am, pi] = others;
    am.m.position.set(am.x, 1, t < 7.35 ? lerp(-80, GZ + 3, eOC(seg(t, 6.15, 6.8))) : lerp(GZ + 3, -140, eIn(seg(t, 7.4, 8.0))));
    const rej = seg(t, 7.0, 7.1);
    pi.m.position.set(pi.x, 1, t < 7.0 ? lerp(-78, GZ + 3, eOC(seg(t, 6.1, 6.8))) : lerp(GZ + 3, -82, eOC(seg(t, 7.0, 7.7))));
    pi.m.material.color.set(rej ? C.red : C.pink); pi.h.material.color.set(rej ? C.red : C.pink);
    for (const o of others) { o.h.position.copy(o.m.position); const a = t > 5.5 && t < 8.4 ? 1 - (o === pi ? seg(t, 7.5, 7.9) : seg(t, 7.7, 8.0)) : 0; o.m.visible = o.h.visible = a > .01; o.m.material.opacity = a; o.h.material.opacity = a; }
    show(lab429, rej * (1 - seg(t, 7.6, 7.95))); lab429.position.copy(pi.m.position).add(V(0, 1.3, 0));
    const ga = 1 - seg(t, 7.6, 7.85);
    show(labAuth, seg(t, 6.95, 7.0) * ga); labAuth.position.set(0, 2.3 + .3 * (1 - eOB(seg(t, 6.95, 7.2))), GZ + 3);
    show(labRate, seg(t, 7.15, 7.2) * ga); labRate.position.set(0, 3.2 + .3 * (1 - eOB(seg(t, 7.15, 7.4))), GZ + 3);
    // tokens
    burst.visible = t > 8.4 && t < 8.9; burst.position.set(0, 1, -160); burst.scale.setScalar(2 + 22 * eOC(seg(t, 8.4, 8.9))); burst.material.opacity = 1 - seg(t, 8.4, 8.9);
    toks.forEach(({ cube, m, lab, idl }, i) => {
      const q = tokPlace(i, t), vis = t >= 8.42 + i * .04;
      cube.visible = vis; cube.position.set(q.x, q.y, q.z); cube.scale.setScalar(q.s);
      m.emissiveIntensity = .45 + 1.2 * bump(t, 8.42 + i * .04, 9.1) + 1.4 * bump(t, 14.5, 14.85) - .25 * (t > 14 && t < 14.5);
      show(lab, vis ? q.lab : 0); lab.position.set(q.x, q.y + 1.15, q.z);
      show(idl, vis ? q.id : 0); idl.position.set(q.x, q.y - .95, q.z + .6);
    });
    // router
    const scan = seg(t, 10.45, 11.0), hit = seg(t, 11.0, 11.1), cur = t > 10.45 && t < 11 ? Math.floor(scan * 4) % 4 : -1;
    reps.forEach((r, i) => {
      const won = i === HIT && hit;
      r.m.emissive.set(won ? C.green : cur === i ? '#5a6a90' : '#16233D'); r.m.emissiveIntensity = won ? .5 : cur === i ? .8 : .2;
      r.edge.material.color.set(won ? C.green : C.dim);
      r.lm.color.set(won ? C.cyan : C.dim);
      r.cells.forEach((c, j) => { if (c.hitCell) { c.cm.color.set(won ? TOKCOL[j] : '#24406A'); c.cm.emissive.set(won ? TOKCOL[j] : '#24406A'); c.cm.emissiveIntensity = won ? 1 : .3; } });
    });
    show(labHit, hit); labHit.position.set(RX[HIT], 5.2 + .3 * (1 - eOB(seg(t, 11.0, 11.3))), RZ);
    // batch
    rows.forEach(r => { if (!r) return; const u = eOC(seg(t, 12.0 + r.d, 12.55 + r.d)); r.cubes.forEach((c, j) => c.position.set(lerp(-34, -10, u) + j * 1.1, .45, r.z)); });
    const pulse = bump(t, 13.45, 13.95); batchChip.edge.material.color.set(pulse > .05 ? C.cyan : C.dim);
    show(labBatch, seg(t, 12.6, 12.9) * (1 - seg(t, 13.45, 13.65)));
    // prefill: the GPU lights up as the request enters; one pass fills every KV column at once
    const enter = bump(t, 14.15, 14.75); pgpu.edge.material.color.set(enter > .05 ? C.cyan : C.dim);
    show(wave, .55 * bump(t, 14.45, 14.85)); wave.scale.y = 1 + .3 * bump(t, 14.45, 14.85);
    kv.forEach((colm, i) => colm.forEach((b, k) => { const f = seg(t, 14.6 + k * .1, 14.75 + k * .1); b.visible = f > 0; b.scale.y = Math.max(.01, eOB(f)); b.material.emissiveIntensity = .5 + 1.2 * (1 - seg(t, 15.0, 15.6)); }));
    show(labKV, seg(t, 15.0, 15.3));
    // the first token, then decode: one token per pass, each adding a KV column, streamed to the screen
    const k = t < 17 ? 0 : step(t), since = t < 17 ? t - 15.75 : t - (T_DEC + (k - 1) * STEP);
    const fu = t < 17 ? eOB(seg(t, 15.75, 16.15)) : .75 + .25 * eOB(seg(since, 0, .16));
    outCube.visible = t > 15.75; outCube.scale.setScalar(Math.max(.01, fu)); outCube.material.emissiveIntensity = .5 + 1.5 * (1 - seg(since, 0, .3));
    outLabs.forEach((l, j) => { show(l, j === k && t > 15.75 ? 1 : 0); l.position.set(0, 1.85, PZ + 5); l.scale.setScalar(1); const s0 = l.material.map.image; l.scale.set(.6 * s0.width / s0.height * Math.max(.3, fu), .6 * Math.max(.3, fu), 1); });
    kvOut.forEach((colm, j) => colm.forEach(b => { const f = t < 17 ? 0 : seg(t, T_DEC + (j - 1) * STEP + .1, T_DEC + (j - 1) * STEP + .2); b.visible = j >= 1 && j <= k && f > 0; b.scale.y = Math.max(.01, f); }));
    flyers.forEach((f, n) => {
      const j = k - n, u = j >= 1 && t >= 17 ? seg(t, T_DEC + (j - 1) * STEP + .05, T_DEC + (j - 1) * STEP + .3) : 0;
      f.m.visible = f.h.visible = u > 0 && u < 1; const q = SSE0.clone().lerp(SSE1, u).add(V(0, .6 * Math.sin(Math.PI * u), 0)); f.m.position.copy(q); f.h.position.copy(q);
    });
    const shown = t < 17 ? 0 : Math.min(OUT.length, 1 + Math.max(0, Math.floor((t - T_DEC - .3) / STEP) + 1));
    screen.visible = sseLab.visible = t > 17;
    if (screen.visible) drawScreen(shown, Math.floor(t * 4) % 2 === 0);
    // camera
    const c = smoothCam(t), pos = c.at.clone().add(c.pos.clone().sub(c.at).multiplyScalar(DF));
    cam.position.copy(pos); cam.lookAt(c.at);
    R3.render(S, cam);
  }
  return { frame, resize: (w, h) => { R3.setSize(w, h, false); cam.aspect = W / H; cam.updateProjectionMatrix(); } };
}
