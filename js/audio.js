/* ============================================================
   Delete Me Not. — procedural audio engine (WebAudio)
   雨・環境音・ドローンBGM・SEをすべてコードで合成（外部素材不要）
   ============================================================ */
'use strict';

const AudioEngine = (() => {
  let ctx = null, master = null, bgmBus = null, ambBus = null, seBus = null;
  let current = { bgm: null, amb: null };
  let bgmNodes = [], ambNodes = [];
  let detuneAmt = 0; // 違和感によるピッチ低下

  // 音量設定（0〜1）。ensure()前に設定されても保持し、初期化時に反映する
  const volumes = { master: 0.55, bgm: 0.5, amb: 0.6, se: 0.8, muted: false };

  function busOf(key) {
    return { master, bgm: bgmBus, amb: ambBus, se: seBus }[key];
  }
  function applyVolumes() {
    if (!ctx) return;
    const m = volumes.muted ? 0 : 1;
    master.gain.setTargetAtTime(volumes.master * m, ctx.currentTime, 0.05);
    bgmBus.gain.setTargetAtTime(volumes.bgm, ctx.currentTime, 0.05);
    ambBus.gain.setTargetAtTime(volumes.amb, ctx.currentTime, 0.05);
    seBus.gain.setTargetAtTime(volumes.se, ctx.currentTime, 0.05);
  }

  function ensure() {
    if (ctx) return true;
    try {
      ctx = new (window.AudioContext || window.webkitAudioContext)();
      master = ctx.createGain(); master.connect(ctx.destination);
      bgmBus = ctx.createGain(); bgmBus.connect(master);
      ambBus = ctx.createGain(); ambBus.connect(master);
      seBus  = ctx.createGain(); seBus.connect(master);
      applyVolumes();
      return true;
    } catch (e) { return false; }
  }
  function resume() { if (ensure() && ctx.state === 'suspended') ctx.resume(); }

  /* ---- ノイズバッファ（雨・グリッチ用） ---- */
  let noiseBuf = null;
  function noise() {
    if (noiseBuf) return noiseBuf;
    const len = ctx.sampleRate * 2;
    noiseBuf = ctx.createBuffer(1, len, ctx.sampleRate);
    const d = noiseBuf.getChannelData(0);
    for (let i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
    return noiseBuf;
  }

  function stopNodes(list) {
    list.forEach(n => { try { n.stop ? n.stop() : n.disconnect(); } catch (e) {} });
    list.length = 0;
  }

  /* ---- 環境音 ---- */
  const AMBIENCES = {
    rain(out) {
      const src = ctx.createBufferSource(); src.buffer = noise(); src.loop = true;
      const bp = ctx.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = 2400; bp.Q.value = 0.4;
      const g = ctx.createGain(); g.gain.value = 0.35;
      src.connect(bp).connect(g).connect(out); src.start();
      // 雨だれ（ローパスノイズの揺らぎ）
      const lfo = ctx.createOscillator(); lfo.frequency.value = 0.13;
      const lg = ctx.createGain(); lg.gain.value = 0.08;
      lfo.connect(lg).connect(g.gain); lfo.start();
      return [src, lfo];
    },
    room(out) {
      const src = ctx.createBufferSource(); src.buffer = noise(); src.loop = true;
      const lp = ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 240;
      const g = ctx.createGain(); g.gain.value = 0.20;
      src.connect(lp).connect(g).connect(out); src.start();
      // PCのファン風ハム
      const o = ctx.createOscillator(); o.type = 'triangle'; o.frequency.value = 58;
      const og = ctx.createGain(); og.gain.value = 0.03;
      o.connect(og).connect(out); o.start();
      return [src, o];
    },
    gate(out) {
      const src = ctx.createBufferSource(); src.buffer = noise(); src.loop = true;
      const bp = ctx.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = 900; bp.Q.value = 2;
      const g = ctx.createGain(); g.gain.value = 0.12;
      src.connect(bp).connect(g).connect(out); src.start();
      const o = ctx.createOscillator(); o.type = 'sawtooth'; o.frequency.value = 30;
      const og = ctx.createGain(); og.gain.value = 0.05;
      o.connect(og).connect(out); o.start();
      return [src, o];
    },
    void_(out) {
      const o = ctx.createOscillator(); o.type = 'sine'; o.frequency.value = 40;
      const og = ctx.createGain(); og.gain.value = 0.10;
      o.connect(og).connect(out); o.start();
      return [o];
    },
  };

  /* ---- BGM：暗いコードパッド ---- */
  const SCALES = {
    safehouse: [110.0, 130.81, 164.81, 196.0],        // Am系 落ち着き
    alley:     [98.0, 116.54, 146.83, 174.61],        // Gm系 湿り
    market:    [103.83, 123.47, 155.56, 185.0],       // G#m系 毒
    dock:      [87.31, 103.83, 130.81, 155.56],       // Fm系 冷たさ
    gate:      [92.5, 110.0, 138.59, 164.81],         // 緊張
    void:      [55.0, 65.41],                         // 虚無
    battle:    [82.41, 98.0, 123.47, 146.83],
  };

  function startBgm(key, out) {
    const scale = SCALES[key] || SCALES.alley;
    const nodes = [];
    scale.forEach((f, i) => {
      const o = ctx.createOscillator();
      o.type = i % 2 ? 'triangle' : 'sine';
      o.frequency.value = f;
      o.detune.value = -detuneAmt + (Math.random() * 4 - 2);
      const g = ctx.createGain(); g.gain.value = 0;
      const lfo = ctx.createOscillator(); lfo.frequency.value = 0.05 + i * 0.021;
      const lg = ctx.createGain(); lg.gain.value = 0.05;
      lfo.connect(lg).connect(g.gain);
      g.gain.setTargetAtTime(0.055, ctx.currentTime, 2 + i);
      o.connect(g).connect(out);
      o.start(); lfo.start();
      nodes.push(o, lfo);
    });
    return nodes;
  }

  /* ---- SE ---- */
  function tone(freq, dur, type = 'square', vol = 0.15, when = 0) {
    if (!ctx) return;
    const t = ctx.currentTime + when;
    const o = ctx.createOscillator(); o.type = type; o.frequency.value = freq;
    const g = ctx.createGain();
    g.gain.setValueAtTime(vol, t);
    g.gain.exponentialRampToValueAtTime(0.001, t + dur);
    o.connect(g).connect(seBus); o.start(t); o.stop(t + dur + 0.02);
  }
  function noiseBurst(dur, freq, vol = 0.3) {
    if (!ctx) return;
    const src = ctx.createBufferSource(); src.buffer = noise();
    const bp = ctx.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = freq; bp.Q.value = 1;
    const g = ctx.createGain();
    g.gain.setValueAtTime(vol, ctx.currentTime);
    g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + dur);
    src.connect(bp).connect(g).connect(seBus);
    src.start(); src.stop(ctx.currentTime + dur + 0.05);
  }

  return {
    unlock() { resume(); },
    /* 音量設定：{master, bgm, amb, se: 0〜1, muted: bool} の部分更新 */
    setVolumes(v) {
      Object.assign(volumes, v);
      applyVolumes();
    },
    getVolumes() { return { ...volumes }; },
    setDistortion(cog) {
      detuneAmt = cog >= 50 ? (cog - 50) * 1.2 : 0; // 違和感50%以上でピッチが下がる
      bgmNodes.forEach(n => { if (n.detune) n.detune.setTargetAtTime(-detuneAmt, ctx ? ctx.currentTime : 0, 3); });
    },
    scene(bgmKey, ambKey) {
      if (!ensure()) return;
      resume();
      if (current.bgm !== bgmKey) {
        stopNodes(bgmNodes);
        if (bgmKey) bgmNodes = startBgm(bgmKey, bgmBus);
        current.bgm = bgmKey;
      }
      if (current.amb !== ambKey) {
        stopNodes(ambNodes);
        const fn = ambKey === 'void' ? AMBIENCES.void_ : AMBIENCES[ambKey];
        if (fn) ambNodes = fn(ambBus);
        current.amb = ambKey;
      }
    },
    stopAll() {
      if (!ctx) return;
      stopNodes(bgmNodes); stopNodes(ambNodes);
      current = { bgm: null, amb: null };
    },
    // ---- SE群 ----
    click()   { resume(); tone(1400, 0.05, 'square', 0.08); },
    hover()   { resume(); tone(2200, 0.03, 'sine', 0.04); },
    blip()    { tone(1800 + Math.random() * 600, 0.015, 'square', 0.025); }, // タイプ音
    confirm() { resume(); tone(880, 0.08, 'square', 0.1); tone(1320, 0.12, 'square', 0.08, 0.07); },
    cancel()  { resume(); tone(300, 0.12, 'square', 0.1); },
    item()    { resume(); tone(660, 0.09, 'triangle', 0.12); tone(990, 0.12, 'triangle', 0.1, 0.09); tone(1320, 0.18, 'triangle', 0.09, 0.18); },
    save()    { resume(); tone(523, 0.1, 'sine', 0.12); tone(784, 0.16, 'sine', 0.1, 0.1); },
    glitch()  { resume(); noiseBurst(0.25, 1200, 0.28); tone(180, 0.2, 'sawtooth', 0.12); },
    bigGlitch(){ resume(); noiseBurst(0.7, 800, 0.4); tone(90, 0.6, 'sawtooth', 0.2); tone(66, 0.8, 'square', 0.12, 0.1); },
    qteStart(){ resume(); tone(1600, 0.09, 'square', 0.16); tone(1600, 0.09, 'square', 0.16, 0.15); },
    qteFail() { resume(); noiseBurst(0.4, 500, 0.35); tone(120, 0.4, 'sawtooth', 0.2); },
    qteOk()   { resume(); tone(1046, 0.07, 'square', 0.14); tone(1568, 0.14, 'square', 0.12, 0.06); },
    hit()     { resume(); noiseBurst(0.12, 900, 0.3); tone(200, 0.1, 'square', 0.15); },
    damage()  { resume(); noiseBurst(0.2, 400, 0.35); tone(110, 0.25, 'sawtooth', 0.18); },
    heartbeat(){ resume(); tone(55, 0.18, 'sine', 0.35); tone(50, 0.22, 'sine', 0.3, 0.28); },
  };
})();
