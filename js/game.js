/* ============================================================
   Delete Me Not. — core engine & UI
   探索 / イベント / QTE / バトル / メタセーブ / エンディング
   ============================================================ */
'use strict';

const LS = { LOOP: 'dmn_loop', SLOTS: 'dmn_slots', ED5: 'dmn_ed5', LEGACY: 'dmn_legacy' };
const $ = (sel) => document.querySelector(sel);
const el = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const rand = (a, b) => a + Math.random() * (b - a);

/* ============ Engine：状態管理 ============ */
const Engine = {
  s: null,
  timers: [],

  readLoop() { return parseInt(localStorage.getItem(LS.LOOP) || '0', 10) || 0; },
  writeLoop(n) { localStorage.setItem(LS.LOOP, String(n)); },
  readSlots() { try { return JSON.parse(localStorage.getItem(LS.SLOTS) || '[null,null,null]'); } catch (e) { return [null, null, null]; } },
  writeSlots(sl) { localStorage.setItem(LS.SLOTS, JSON.stringify(sl)); },

  fresh() {
    const loop = this.readLoop();
    return {
      chapter: 1, map: 'alley', mode: 'explore',
      params: { cigs: PARAM_DEF.cigs.init, dep: 0, cog: loop > 0 ? Math.min(loop * 4, 20) : 0, corr: 0 },
      loop, items: ['access_log'], flags: {}, visitedDock: false,
      finaleChoice: null,
    };
  },

  addParam(key, v) {
    if (!v) return;
    const p = this.s.params;
    p[key] = clamp(p[key] + v, 0, PARAM_DEF[key].max);
    UI.renderParams();
    UI.applyMetaFx();
  },

  clueCount() { return this.s.items.filter(i => ITEMS[i] && (ITEMS[i].clue || ITEMS[i].meta || ITEMS[i].frag)).length; },
  fragCount() { return this.s.items.filter(i => ITEMS[i] && ITEMS[i].frag).length; },

  metaSaveName() {
    const sl = this.readSlots().find(x => x);
    if (!sl) return 'dmn_slots[0] : NULL';
    return `SAVE_${new Date(sl.ts).toISOString().replace(/[-:T]/g, '').slice(0, 14)}.dat`;
  },

  save(slot) {
    const sl = this.readSlots();
    sl[slot] = {
      state: JSON.parse(JSON.stringify(this.s)),
      ts: Date.now(),
      title: CHAPTERS[this.s.chapter].title,
    };
    this.writeSlots(sl);
    AudioEngine.save();
    UI.toast('記憶をバックアップした。');
  },

  load(slot) {
    const sl = this.readSlots();
    const d = sl[slot];
    if (!d) { UI.toast('データが存在しない。'); AudioEngine.cancel(); return false; }
    const loop = this.readLoop() + 1;
    this.writeLoop(loop);
    this.s = JSON.parse(JSON.stringify(d.state));
    this.s.loop = loop;
    this.addParam('cog', 6);
    AudioEngine.glitch();
    UI.fx('glitch');
    UI.enterExplore(this.s.map, true);
    UI.toast(`ロード完了。……何かが、ずれた気がする。`);
    return true;
  },
};

/* ============ UI ============ */
const UI = {
  root: null,

  init() {
    this.root = $('#game');
    this.buildChrome();
    Title.show();
    // 手がかりカウンターの無作為な明滅（世界の拒絶反応・伏線）
    setInterval(() => {
      if (Engine.s && Engine.s.mode === 'explore' && Math.random() < 0.10) {
        const c = $('#clue-counter');
        if (c) { c.classList.add('flicker-once'); setTimeout(() => c.classList.remove('flicker-once'), 260); }
      }
    }, 5000);
  },

  buildChrome() {
    this.root.innerHTML = `
      <div id="scene"></div>
      <div id="fx-layer"></div>
      <div id="hud">
        <div id="params" class="panel">
          <div class="p-row" id="p-cigs"><span class="p-label">タバコ</span><span class="cigs"></span></div>
          <div class="p-row"><span class="p-label">依存度</span><div class="bar"><div class="fill dep"></div></div><span class="p-val" id="v-dep"></span></div>
          <div class="p-row"><span class="p-label">違和感</span><div class="bar"><div class="fill cog"></div></div><span class="p-val" id="v-cog"></span></div>
          <div class="p-row"><span class="p-label">汚染度</span><div class="bar"><div class="fill corr"></div></div><span class="p-val" id="v-corr"></span></div>
          <div class="p-row small" id="clue-counter">手がかり: <span id="v-clue">0</span></div>
        </div>
        <div id="loc-banner" class="panel"></div>
        <div id="quick" class="panel">
          <button id="btn-items">所持品</button>
          <button id="btn-save">SAVE</button>
          <button id="btn-load">LOAD</button>
        </div>
        <div id="minimap" class="panel"><div class="mm-title">- MAP -</div><svg id="mm-svg" viewBox="0 0 100 90"></svg></div>
        <div id="objective" class="panel"></div>
      </div>
      <div id="event-layer"></div>
      <div id="battle-layer"></div>
      <div id="qte-layer"></div>
      <div id="modal-layer"></div>
      <div id="toast"></div>
      <div id="title-layer"></div>
      <div id="ending-layer"></div>
    `;
    $('#btn-items').onclick = () => { AudioEngine.click(); Modal.items(); };
    $('#btn-save').onclick = () => { AudioEngine.click(); Modal.saveLoad('save'); };
    $('#btn-load').onclick = () => { AudioEngine.click(); Modal.saveLoad('load'); };
  },

  toast(msg, ms = 2400) {
    const t = $('#toast');
    t.textContent = msg; t.classList.add('show');
    clearTimeout(this._tt);
    this._tt = setTimeout(() => t.classList.remove('show'), ms);
  },

  fx(kind) {
    const f = $('#fx-layer');
    if (kind === 'glitch') {
      this.root.classList.add('fx-glitch');
      setTimeout(() => this.root.classList.remove('fx-glitch'), 700);
    } else if (kind === 'redflash') {
      const d = el('div', 'red-flash'); f.appendChild(d);
      this.root.classList.add('fx-shake');
      setTimeout(() => { d.remove(); this.root.classList.remove('fx-shake'); }, 650);
    } else if (kind === 'whiteout') {
      const d = el('div', 'white-out'); f.appendChild(d);
      setTimeout(() => d.remove(), 3200);
    }
  },

  /* --- パラメーターHUD --- */
  renderParams() {
    const p = Engine.s.params;
    const cigsEl = $('#p-cigs .cigs');
    cigsEl.innerHTML = '';
    for (let i = 0; i < PARAM_DEF.cigs.max; i++) {
      cigsEl.appendChild(el('span', 'cig' + (i < p.cigs ? ' on' : ''), ''));
    }
    $('.fill.dep').style.width = p.dep + '%';
    $('.fill.cog').style.width = p.cog + '%';
    $('.fill.corr').style.width = p.corr + '%';
    $('#v-dep').textContent = p.dep + '%';
    $('#v-cog').textContent = p.cog + '%';
    $('#v-corr').textContent = p.corr + '%';
    $('#v-clue').textContent = Engine.clueCount();
  },

  /* --- 違和感レベルに応じたメタ演出 --- */
  applyMetaFx() {
    const cog = Engine.s ? Engine.s.params.cog : 0;
    AudioEngine.setDistortion(cog);
    this.root.classList.toggle('meta-2', cog >= 50 && cog < 100);
    // レベル3：セーブUIの文字化け
    $('#btn-save').textContent = cog >= 80 ? '████' : 'SAVE';
    $('#btn-load').textContent = cog >= 80 ? '████' : 'LOAD';
    // レベル4：第5章はUI消失
    const hide = Engine.s && Engine.s.chapter >= 5;
    $('#hud').style.display = hide ? 'none' : '';
    if (!hide && Engine.s && cog >= 50) this.randomShakeTick();
  },
  randomShakeTick() {
    if (this._shaking) return;
    this._shaking = true;
    const tick = () => {
      if (!Engine.s || Engine.s.params.cog < 50) { this._shaking = false; return; }
      if (Math.random() < 0.35) {
        $('#params').classList.add('fx-shake');
        setTimeout(() => $('#params').classList.remove('fx-shake'), 300);
      }
      setTimeout(tick, rand(4000, 9000));
    };
    setTimeout(tick, 3000);
  },

  /* --- 探索ステート --- */
  enterExplore(mapId, skipFade) {
    const s = Engine.s;
    s.map = mapId; s.mode = 'explore';
    const map = MAPS[mapId];
    const scene = $('#scene');
    scene.className = 'map-' + mapId;
    scene.innerHTML = '';

    // 背景
    const bg = el('div', 'bg');
    if (map.bg && ASSETS.bg[map.bg] && !ASSETS.bg[map.bg].startsWith('ASSET_')) {
      bg.style.backgroundImage = `url("${ASSETS.bg[map.bg]}")`;
    } else {
      bg.classList.add('bg-void');
    }
    scene.appendChild(bg);
    scene.appendChild(el('div', 'scanlines'));
    if (map.ambience === 'rain') scene.appendChild(this.makeRain());

    // プレイヤー（アラヤ）
    const pl = el('div', 'sprite player');
    pl.style.left = map.player.x + '%'; pl.style.top = map.player.y + '%';
    pl.appendChild(this.spriteImg('araya'));
    scene.appendChild(pl);

    // スポット（NPC / オブジェクト / 出口）
    map.spots.forEach(sp => {
      if (sp.chapters && !sp.chapters.includes(s.chapter)) return;
      if (sp.type === 'exit') {
        const tgt = MAPS[sp.target];
        const locked = s.chapter < tgt.unlock || !CHAPTERS[s.chapter].maps.includes(sp.target);
        this.addExit(scene, sp, locked);
      } else if (sp.type === 'npc') {
        this.addNpc(scene, sp);
      } else {
        this.addObject(scene, sp);
      }
    });

    // バナー・目標
    $('#loc-banner').innerHTML = `<span class="loc-name">【${map.name}】</span><span class="loc-ch">${CHAPTERS[s.chapter].title}</span>`;
    $('#objective').textContent = CHAPTERS[s.chapter].goalText;
    this.renderMinimap();
    this.renderParams();
    this.applyMetaFx();
    AudioEngine.scene(map.bgm, map.ambience);
    if (!skipFade) { scene.classList.add('fade-in'); setTimeout(() => scene.classList.remove('fade-in'), 500); }
  },

  spriteImg(key) {
    const img = el('img', 'px');
    img.src = ASSETS.sprite[key]; img.draggable = false;
    return img;
  },

  makeRain() {
    const r = el('div', 'rain');
    for (let i = 0; i < 60; i++) {
      const d = el('span', 'drop');
      d.style.left = Math.random() * 100 + '%';
      d.style.animationDelay = Math.random() * 1.2 + 's';
      d.style.animationDuration = (0.5 + Math.random() * 0.5) + 's';
      r.appendChild(d);
    }
    return r;
  },

  hotspot(sp, cls, inner, label, onClick) {
    const h = el('div', 'spot ' + cls);
    h.style.left = sp.x + '%'; h.style.top = sp.y + '%';
    h.innerHTML = inner;
    const lab = el('div', 'spot-label', label);
    h.appendChild(lab);
    h.onmouseenter = () => AudioEngine.hover();
    h.onclick = (e) => { e.stopPropagation(); AudioEngine.click(); onClick(); };
    return h;
  },

  addNpc(scene, sp) {
    let inner;
    if (sp.builtin) {
      inner = `<span class="marker red-dot pulse"></span>`;
    } else if (sp.silhouette) {
      inner = `<span class="mini-silhouette ${sp.pose}"></span><span class="marker talk-mark">!</span>`;
    } else {
      inner = `<img class="px npc-img" src="${ASSETS.sprite[sp.char]}" draggable="false" style="height:${sp.h}vh"><span class="marker talk-mark">!</span>`;
    }
    scene.appendChild(this.hotspot(sp, 'npc', inner, `[話しかける] ${sp.label}`, () => Flow.talk(sp)));
  },

  addObject(scene, sp) {
    scene.appendChild(this.hotspot(sp, 'object', `<span class="marker red-dot pulse"></span>`, `[調べる] ${sp.label}`, () => Flow.investigate(sp)));
  },

  addExit(scene, sp, locked) {
    const arrow = sp.icon === 'arrow'
      ? `<span class="marker arrow ${sp.dir}">${{ left: '◀', right: '▶', up: '▲', down: '▼' }[sp.dir]}</span>`
      : `<span class="marker exit-dot pulse">◈</span>`;
    const label = locked ? `【封鎖】${sp.label}` : `[移動] ${sp.label}`;
    const h = this.hotspot(sp, 'exit' + (locked ? ' locked' : ''), arrow, label, () => {
      if (locked) { AudioEngine.cancel(); this.toast('この先はまだ通れない。'); return; }
      Flow.travel(sp.target);
    });
    scene.appendChild(h);
  },

  /* --- ミニマップ --- */
  renderMinimap() {
    const s = Engine.s;
    const svg = $('#mm-svg');
    const open = (id) => CHAPTERS[s.chapter].maps.includes(id);
    let html = '';
    MINIMAP_LINKS.forEach(([a, b]) => {
      const A = MINIMAP.find(n => n.id === a), B = MINIMAP.find(n => n.id === b);
      html += `<line x1="${A.x}" y1="${A.y}" x2="${B.x}" y2="${B.y}" class="mm-line ${open(a) && open(b) ? '' : 'off'}"/>`;
    });
    MINIMAP.forEach(n => {
      const st = !open(n.id) ? 'locked' : (n.id === s.map ? 'here' : 'open');
      html += `<g class="mm-node ${st}" data-id="${n.id}">
        <rect x="${n.x - 9}" y="${n.y - 6}" width="18" height="12" rx="1"/>
        <text x="${n.x}" y="${n.y + 2.6}">${n.label}</text></g>`;
    });
    svg.innerHTML = html;
    svg.querySelectorAll('.mm-node.open').forEach(g => {
      g.addEventListener('click', () => { AudioEngine.click(); Flow.travel(g.dataset.id); });
    });
  },
};

/* ============ タイプライター・イベント表示 ============ */
const EventView = {
  queue: [], onDone: null, typing: false, curText: '',

  show(lines, opts = {}) {
    Engine.s.mode = 'event';
    this.queue = lines.slice();
    this.onDone = opts.onDone || null;
    this.choices = opts.choices || null;
    this.onChoice = opts.onChoice || null;
    const layer = $('#event-layer');
    layer.innerHTML = `
      <div class="ev-dim"></div>
      <div class="ev-tachie"></div>
      <div class="ev-window panel">
        <div class="ev-speaker"></div>
        <div class="ev-text"></div>
        <div class="ev-next">▼</div>
        <div class="ev-choices"></div>
      </div>`;
    layer.classList.add('active');
    layer.querySelector('.ev-window').onclick = () => this.advance();
    this.next();
  },

  glitchify(text) {
    const cog = Engine.s.params.cog;
    if (cog < 20) return text;
    const p = cog >= 80 ? 0.05 : cog >= 50 ? 0.025 : 0.01;
    return text.split('').map(ch => (Math.random() < p && ch.trim()) ? GLITCH_CHARS[Math.floor(Math.random() * GLITCH_CHARS.length)] : ch).join('');
  },

  next() {
    const line = this.queue.shift();
    if (!line) { this.finish(); return; }
    const layer = $('#event-layer');
    const sp = layer.querySelector('.ev-speaker');
    const tx = layer.querySelector('.ev-text');
    const nx = layer.querySelector('.ev-next');
    const ta = layer.querySelector('.ev-tachie');
    sp.textContent = line.speaker || '';
    sp.style.display = line.speaker ? '' : 'none';
    sp.classList.toggle('sys', line.style === 'system');
    // 立ち絵
    ta.innerHTML = '';
    if (line.tachie && ASSETS.tachie[line.tachie]) {
      const img = el('img', 'tachie-img');
      img.src = ASSETS.tachie[line.tachie];
      ta.appendChild(img);
    } else if (line.silhouette) {
      ta.appendChild(el('div', 'tachie-silhouette ' + (line.silhouette === 'white' ? 'white' : '')));
    }
    nx.style.display = 'none';
    // タイピング
    this.typing = true;
    this.curText = this.glitchify(line.text);
    tx.textContent = '';
    let i = 0;
    clearInterval(this._ti);
    this._ti = setInterval(() => {
      tx.textContent = this.curText.slice(0, ++i);
      if (i % 2 === 0) AudioEngine.blip();
      if (i >= this.curText.length) {
        clearInterval(this._ti);
        this.typing = false;
        if (this.queue.length || this.choices || this.onDone) nx.style.display = '';
        if (!this.queue.length && this.choices) this.showChoices();
      }
    }, 26);
  },

  advance() {
    if (this.typing) { // 全文表示
      clearInterval(this._ti);
      $('#event-layer .ev-text').textContent = this.curText;
      this.typing = false;
      const nx = $('#event-layer .ev-next');
      if (this.queue.length || this.choices || this.onDone) nx.style.display = '';
      if (!this.queue.length && this.choices) this.showChoices();
      return;
    }
    if (this.choicesShown) return;
    AudioEngine.click();
    if (this.queue.length) this.next();
    else this.finish();
  },

  showChoices() {
    this.choicesShown = true;
    const box = $('#event-layer .ev-choices');
    box.innerHTML = '';
    $('#event-layer .ev-next').style.display = 'none';
    this.choices.forEach((c) => {
      const locked = c.require && !Engine.s.items.includes(c.require);
      const costNg = c.cost && Engine.s.params.cigs < c.cost;
      const b = el('button', 'choice', `<span class="ch-cursor">▶</span>${c.text}${locked ? ' <span class="dim">（アイテムが必要）</span>' : ''}${costNg ? ' <span class="dim">（タバコ不足）</span>' : ''}`);
      b.disabled = locked || costNg;
      b.onclick = (e) => {
        e.stopPropagation();
        AudioEngine.confirm();
        this.choicesShown = false; this.choices = null;
        box.innerHTML = '';
        this.onChoice && this.onChoice(c);
      };
      box.appendChild(b);
    });
  },

  finish() {
    this.choicesShown = false;
    $('#event-layer').classList.remove('active');
    $('#event-layer').innerHTML = '';
    const cb = this.onDone; this.onDone = null;
    if (cb) { cb(); return; }
    Engine.s.mode = 'explore';
    Flow.afterEvent();
  },
};

/* ============ QTE ============ */
const QTE = {
  active: false,
  start(onEnd) {
    if (this.active) return;
    this.active = true;
    const keys = ['W', 'A', 'S', 'D'];
    const key = keys[Math.floor(Math.random() * 4)];
    const layer = $('#qte-layer');
    layer.innerHTML = `
      <div class="qte-box">
        <div class="qte-warn">!! 危険 !!</div>
        <div class="qte-key">${key}</div>
        <div class="qte-gauge"><div class="qte-fill"></div></div>
      </div>`;
    layer.classList.add('active');
    AudioEngine.qteStart();
    const fill = layer.querySelector('.qte-fill');
    requestAnimationFrame(() => fill.style.width = '0%');

    const timeout = setTimeout(() => end(false), 1500);
    const handler = (e) => {
      const k = e.key.toUpperCase();
      if (!keys.includes(k)) return;
      end(k === key);
    };
    const end = (ok) => {
      clearTimeout(timeout);
      window.removeEventListener('keydown', handler);
      this.active = false;
      layer.classList.remove('active'); layer.innerHTML = '';
      if (ok) {
        AudioEngine.qteOk();
        UI.toast('回避成功。');
      } else {
        AudioEngine.qteFail();
        UI.fx('redflash');
        Engine.addParam('corr', 15);
        UI.toast('回避失敗──精神が摩耗した（汚染度+15%）');
      }
      onEnd && onEnd(ok);
    };
    window.addEventListener('keydown', handler);
  },
};

/* ============ バトル ============ */
const Battle = {
  st: null,
  start(bossDef, onEnd) {
    Engine.s.mode = 'battle';
    const maxHp = Math.max(10, 100 - Engine.s.params.corr);
    this.st = { boss: bossDef, bossHp: bossDef.hp, hp: maxHp, maxHp, guard: false, onEnd, dialogue: false };
    const layer = $('#battle-layer');
    layer.innerHTML = `
      <div class="bt-dim"></div>
      <div class="bt-top panel">
        <div class="bt-boss-name">${bossDef.name}</div>
        <div class="bar big"><div class="fill boss"></div></div>
      </div>
      <div class="bt-log panel"></div>
      <div class="bt-me panel">ARAYA HP <span id="bt-hp"></span>/${maxHp}</div>
      <div class="bt-cmds panel">
        <button data-c="atk">1. 攻撃</button>
        <button data-c="def">2. 防御</button>
        <button data-c="item">3. アイテム</button>
        <button data-c="watch">4. 様子を見る</button>
      </div>`;
    layer.classList.add('active');
    layer.querySelectorAll('.bt-cmds button').forEach(b => b.onclick = () => { AudioEngine.click(); this.turn(b.dataset.c); });
    AudioEngine.scene('battle', null);
    this.log(bossDef.intro.join(' '));
    this.render();
  },

  log(msg) {
    const lg = $('#battle-layer .bt-log');
    const d = el('div', 'bt-line', msg);
    lg.appendChild(d); lg.scrollTop = lg.scrollHeight;
    while (lg.children.length > 6) lg.firstChild.remove();
  },

  render() {
    $('#battle-layer .fill.boss').style.width = (this.st.bossHp / this.st.boss.hp * 100) + '%';
    $('#bt-hp').textContent = this.st.hp;
  },

  turn(cmd) {
    const st = this.st;
    if (st.dialogue) return;
    st.guard = false;
    if (cmd === 'atk') {
      const dmg = Math.floor(rand(15, 26));
      st.bossHp = Math.max(0, st.bossHp - dmg);
      AudioEngine.hit();
      this.log(`アラヤの攻撃。敵に ${dmg} のダメージ。`);
    } else if (cmd === 'def') {
      st.guard = true;
      this.log('アラヤは防御の構えを取った。');
    } else if (cmd === 'item') {
      if (Engine.s.items.includes('blue_amp')) {
        Engine.s.items.splice(Engine.s.items.indexOf('blue_amp'), 1);
        st.hp = Math.min(st.maxHp, st.hp + 40);
        Engine.addParam('corr', 10);
        AudioEngine.item();
        this.log('ブルー・アンフェタを注入。HPが40回復した。……輪郭が、溶ける（汚染度+10%）。');
      } else { this.log('使えるアイテムがない。'); return; }
    } else if (cmd === 'watch') {
      Engine.addParam('cog', 2);
      this.log('敵の駆動パターンを観察した。……妙だ。まるで「こちらの入力」を待っているような間がある（違和感+2%）。');
    }
    this.render();
    if (st.bossHp <= 30) { setTimeout(() => this.enterDialogue(), 700); return; }
    // 敵ターン
    setTimeout(() => {
      let dmg = Math.floor(rand(10, 18));
      if (st.guard) dmg = Math.ceil(dmg / 2);
      st.hp = Math.max(0, st.hp - dmg);
      AudioEngine.damage();
      UI.fx('redflash');
      this.log(`敵の反撃。アラヤは ${dmg} のダメージを受けた${st.guard ? '（防御で半減）' : ''}。`);
      this.render();
      if (st.hp <= 0) this.defeat();
    }, 800);
  },

  defeat() {
    this.log('アラヤは膝をついた。……視界が、砕ける。');
    Engine.addParam('corr', 25);
    setTimeout(() => {
      this.close();
      EventView.show([
        { speaker: 'SYSTEM', text: '致命的損傷。強制退避プロトコル起動──セーフハウスへ転送。', style: 'system' },
      ], { onDone: () => { this.st.onEnd('defeat'); } });
    }, 1200);
  },

  enterDialogue() {
    const st = this.st; st.dialogue = true;
    $('#game').classList.add('bt-mono');
    AudioEngine.heartbeat();
    $('#battle-layer .bt-cmds').style.display = 'none';
    this.log('──敵の動きが止まった。対話モードへ移行。');
    setTimeout(() => {
      this.close(true);
      EventView.show([
        { speaker: st.boss.name, text: st.boss.dialogueIntro },
      ], {
        choices: st.boss.choices.map(c => ({ text: c.text, require: c.require, _r: c.result })),
        onChoice: (c) => {
          const r = st.boss.results[c._r];
          if (c._r === 'clue') Engine.s.items.splice(Engine.s.items.indexOf('log_memory'), 1);
          if (r.cog) Engine.addParam('cog', r.cog);
          if (r.corr) Engine.addParam('corr', r.corr);
          Engine.s.flags[r.flag] = true;
          EventView.show(r.text.map(t => ({ speaker: '', text: t })), {
            onDone: () => { document.querySelector('#game').classList.remove('bt-mono'); st.onEnd(c._r); },
          });
        },
      });
    }, 1300);
  },

  close(keepMono) {
    const layer = $('#battle-layer');
    layer.classList.remove('active');
    if (!keepMono) layer.classList.remove('bt-mono');
    layer.innerHTML = '';
  },
};

/* ============ Flow：進行制御 ============ */
const Flow = {
  travel(mapId) {
    const s = Engine.s;
    // 第3章：初めてドックに入るとレイ死亡イベント→ボス戦
    if (mapId === 'dock' && s.chapter === 3 && !s.flags.rei_dead) {
      this.reiDeathSequence();
      return;
    }
    // 移動時QTE（ドック・ゲートで確率発生）
    const danger = { dock: 0.35, gate: 0.5 }[mapId] || 0;
    UI.enterExplore(mapId);
    if (danger && Math.random() < danger && s.chapter >= 3) {
      setTimeout(() => QTE.start(), 600);
    }
  },

  talk(sp) {
    const s = Engine.s;
    const d = DIALOGUES[sp.char];
    if (!d) return;
    if (sp.char === 'rei') s.flags.met_rei = true;
    if (sp.char === 'may') s.flags.met_may = true;
    const line = { speaker: d.speaker, text: d.intro(s), tachie: d.tachie, silhouette: d.silhouette };
    EventView.show([line], {
      choices: d.choices(s).filter(c => !(c.once && s.flags[c.once])),
      onChoice: (c) => this.applyChoice(d, c),
    });
  },

  applyChoice(d, c) {
    const s = Engine.s;
    if (c.cost) Engine.addParam('cigs', -c.cost);
    if (c.dep) Engine.addParam('dep', c.dep);
    if (c.cog) Engine.addParam('cog', c.cog);
    if (c.corr) Engine.addParam('corr', c.corr);
    if (c.once) s.flags[c.once] = true;
    if (c.flag) s.flags[c.flag] = true;
    if (c.give && !s.items.includes(c.give)) { s.items.push(c.give); AudioEngine.item(); }
    if (c.require && c.consume) s.items.splice(s.items.indexOf(c.require), 1);
    UI.renderParams();
    const texts = d.branches[c.next] || ['……'];
    EventView.show(texts.map(t => ({ speaker: d.speaker, text: t, tachie: d.tachie, silhouette: d.silhouette })));
  },

  investigate(sp) {
    const s = Engine.s;
    const o = OBJECTS[sp.id];
    if (!o) return;
    if (o.type === 'pc') { Modal.pc(); return; }
    if (o.type === 'sleep') { this.sleep(); return; }
    if (o.type === 'gate') { this.gateDoor(); return; }
    if (o.type === 'qte_drone') {
      EventView.show([{ speaker: '', text: 'ドローンの巡回パターンを読み、死角へ踏み込む──' }], {
        onDone: () => { Engine.s.mode = 'explore'; QTE.start((ok) => { if (ok) Engine.addParam('cog', 3); this.afterEvent(); }); },
      });
      return;
    }
    const done = o.once && s.flags[o.once];
    if (!done && o.cost) Engine.addParam('cigs', -o.cost);
    const lines = (done ? o.afterText : o.text) || ['何もない。'];
    if (!done) {
      if (o.give && !s.items.includes(o.give)) { s.items.push(o.give); AudioEngine.item(); }
      if (o.cigs) Engine.addParam('cigs', o.cigs);
      if (o.cog) Engine.addParam('cog', o.cog);
      if (o.once) s.flags[o.once] = true;
    }
    UI.renderParams();
    EventView.show(lines.map(t => ({ speaker: '', text: t })));
  },

  /* タバコ切れチェック（イベント終了ごとに呼ばれる） */
  afterEvent() {
    const s = Engine.s;
    if (s.mode !== 'explore') return;
    if (s.params.cigs > 0) return;
    if (s.chapter <= 2) {
      EventView.show([
        { speaker: 'SYSTEM', text: '行動リソース枯渇。意識が、途切れる──', style: 'system' },
        { speaker: '', text: '（アラヤは朦朧としたままセーフハウスに戻り、泥のように眠った）' },
      ], { onDone: () => this.nextChapter() });
    } else if (s.chapter === 3 && !s.flags.rei_dead) {
      EventView.show([
        { speaker: 'SYSTEM', text: '警告：相棒の信号が途絶。廃棄ドックへ強制転送されます。', style: 'system' },
      ], { onDone: () => this.reiDeathSequence() });
    } else if (s.chapter === 4) {
      EventView.show([
        { speaker: 'SYSTEM', text: '行動リソース枯渇。──中枢ゲートが、内側から開いた。', style: 'system' },
        { speaker: '', text: '（招かれている。行くしかない）' },
      ], { onDone: () => this.enterFinale() });
    } else {
      this.nextChapter();
    }
  },

  sleep() {
    const s = Engine.s;
    const goal = CHAPTERS[s.chapter].goal(s);
    if (s.chapter >= 4) {
      EventView.show([{ speaker: '', text: '眠れる気がしない。……終わらせるしか、ないんだろうな。' }]);
      return;
    }
    EventView.show([{ speaker: '', text: goal ? '今日はもう休もう。' : 'まだやり残したことがある気がする。それでも眠るか？' }], {
      choices: [
        { text: '眠る（次の章へ）', _a: 'sleep' },
        { text: 'まだ動く', _a: 'no' },
      ],
      onChoice: (c) => {
        if (c._a === 'sleep') this.nextChapter();
        else EventView.finish();
      },
    });
  },

  nextChapter() {
    const s = Engine.s;
    if (s.chapter >= 4) { this.enterFinale(); return; }
    s.chapter++;
    s.params.cigs = PARAM_DEF.cigs.init;
    const ch = CHAPTERS[s.chapter];
    const map = ch.maps.includes('safehouse') ? 'safehouse' : ch.maps[0];
    UI.fx('glitch'); AudioEngine.glitch();
    EventView.show([
      { speaker: '', text: `──${ch.title}──`, style: 'system' },
      { speaker: '', text: ch.goalText, style: 'system' },
    ], { onDone: () => { Engine.s.mode = 'explore'; UI.enterExplore(map); } });
  },

  /* 第3章：レイ死亡→ボス戦 */
  reiDeathSequence() {
    const s = Engine.s;
    s.flags.rei_dead = true;
    UI.enterExplore('dock', true);
    EventView.show(REI_DEATH.slice(), {
      onDone: () => {
        Battle.start(BOSS3, (result) => {
          s.flags.boss3_done = true;
          Engine.s.mode = 'explore';
          if (result === 'defeat') {
            UI.enterExplore('safehouse');
            UI.toast('意識が戻った。……何かを、失った気がする。');
          } else {
            EventView.show([
              { speaker: '', text: '雨が、機械の墓場を洗っている。', },
              { speaker: 'アラヤ', tachie: 'araya', text: '……帰ろう。いや──「帰る場所」って、どこだったか。' },
            ], { onDone: () => { Engine.s.mode = 'explore'; this.nextChapter(); } });
          }
        });
      },
    });
  },

  gateDoor() {
    const s = Engine.s;
    if (s.chapter < 4) { UI.toast('制御盤は沈黙している。'); return; }
    EventView.show([
      { speaker: '', text: '制御盤に手を置く。認証は──通った。最初から、お前を待っていたかのように。' },
    ], {
      choices: [
        { text: '中枢へ進む（最終章・後戻りはできない）', _a: 'go' },
        { text: '引き返す', _a: 'no' },
      ],
      onChoice: (c) => { if (c._a === 'go') this.enterFinale(); else EventView.finish(); },
    });
  },

  /* 最終章 */
  enterFinale() {
    const s = Engine.s;
    s.chapter = 5;
    UI.enterExplore('judgment', true);
    UI.applyMetaFx(); // UI消失
    AudioEngine.scene('void', 'void');
    const kei = DIALOGUES.kei;
    EventView.show([
      { speaker: '', text: '純白の空間。ノイズの膜の向こうに、白いスーツの男が立っている。', style: 'system' },
      { speaker: kei.speaker, text: kei.intro(s), silhouette: 'white' },
    ], {
      choices: kei.choices(s).map(c => ({ ...c })),
      onChoice: (c) => {
        if (c.cog) Engine.addParam('cog', c.cog);
        EventView.show(kei.branches[c.next].map(t => ({ speaker: kei.speaker, text: t, silhouette: 'white' })), {
          onDone: () => this.arayaFinale(),
        });
      },
    });
  },

  arayaFinale() {
    const s = Engine.s;
    EventView.show(FINALE.arayaIntro(s), {
      choices: FINALE.choices(s),
      onChoice: (c) => {
        if (c.dep) Engine.addParam('dep', c.dep);
        if (c.cog) Engine.addParam('cog', c.cog);
        s.finaleChoice = c.id === 'push' ? 'push' : c.id;
        if (c.id === 'truth') {
          EventView.show([
            { speaker: 'アラヤ', tachie: 'araya', text: '……そのファイル。ぜんぶ、俺の──いや、「俺たち」の記録か。' },
            { speaker: 'アラヤ', tachie: 'araya', text: 'DELETE ME NOT。……消してくれるな、って。誰が書いたと思う？' },
          ], { onDone: () => Ending.run(judgeEnding(s, s.finaleChoice)) });
        } else {
          Ending.run(judgeEnding(s, s.finaleChoice));
        }
      },
    });
  },
};

/* ============ エンディング ============ */
const Ending = {
  run(key) {
    const ed = ENDINGS[key];
    const s = Engine.s;
    AudioEngine.stopAll();
    const layer = $('#ending-layer');
    layer.className = 'active ' + ed.class;
    layer.innerHTML = `<div class="ed-body"><div class="ed-title">${ed.title}</div><div class="ed-sub">${ed.sub}</div><div class="ed-lines"></div><div class="ed-foot"></div></div>`;
    const linesEl = layer.querySelector('.ed-lines');
    let i = 0;
    const step = () => {
      if (i >= ed.lines.length) { this.finale(key); return; }
      const d = el('div', 'ed-line', ed.lines[i] || '&nbsp;');
      linesEl.appendChild(d);
      i++;
      setTimeout(step, 1700);
    };
    if (key === 'ed3') { AudioEngine.bigGlitch(); UI.fx('glitch'); }
    if (key === 'ed1') UI.fx('whiteout');
    if (key === 'ed5') AudioEngine.heartbeat();
    setTimeout(step, key === 'ed1' ? 2600 : 1000);
  },

  finale(key) {
    const layer = $('#ending-layer');
    const foot = layer.querySelector('.ed-foot');
    if (key === 'ed1') {
      // ステータス初期化してタイトルへ（LOOP_COUNTだけ残る）
      foot.innerHTML = '<button class="choice">──記憶、初期化──</button>';
      foot.querySelector('button').onclick = () => {
        AudioEngine.bigGlitch();
        Engine.s = null;
        layer.className = ''; layer.innerHTML = '';
        Title.show();
      };
    } else if (key === 'ed2') {
      foot.innerHTML = '<div class="ed-dead">（……反応がない）</div>';
      // どのボタンも反応しない演出：全クリックを飲み込む
      layer.style.pointerEvents = 'auto';
      layer.onclick = () => { /* 虚無 */ };
    } else if (key === 'ed3') {
      setTimeout(() => {
        layer.innerHTML = '<div class="ed-crash"><div class="crash-noise"></div><div class="crash-msg">通信切断：世界が消失しました</div></div>';
        AudioEngine.stopAll();
      }, 1500);
    } else if (key === 'ed4') {
      foot.innerHTML = '<div class="ed-dead">（操作権は、剥奪された）</div>';
      layer.onclick = () => {};
    } else if (key === 'ed5') {
      localStorage.setItem(LS.ED5, '1');
      foot.innerHTML = '<button class="choice">「……ああ。ずっと一緒だ、相棒」</button>';
      foot.querySelector('button').onclick = () => {
        layer.className = ''; layer.innerHTML = '';
        Engine.s = null;
        Title.show();
      };
    }
  },
};

/* ============ モーダル（所持品・セーブ・PC） ============ */
const Modal = {
  open(html) {
    const m = $('#modal-layer');
    m.innerHTML = `<div class="md-dim"></div><div class="md-box panel">${html}<button class="md-close">✕ 閉じる</button></div>`;
    m.classList.add('active');
    m.querySelector('.md-dim').onclick = () => this.close();
    m.querySelector('.md-close').onclick = () => { AudioEngine.cancel(); this.close(); };
  },
  close() { const m = $('#modal-layer'); m.classList.remove('active'); m.innerHTML = ''; },

  items() {
    const s = Engine.s;
    let rows = s.items.map(id => {
      const it = ITEMS[id];
      const usable = it.use ? `<button class="mini-btn" data-use="${id}">使う</button>` : '';
      return `<div class="it-row${it.meta || it.frag ? ' meta' : ''}"><b>${it.name}</b>${usable}<div class="it-desc">${it.desc}</div></div>`;
    }).join('') || '<div class="dim">何も持っていない。</div>';
    this.open(`<h3>所持品</h3><div class="it-list">${rows}</div>`);
    document.querySelectorAll('[data-use]').forEach(b => b.onclick = () => {
      const id = b.dataset.use; const it = ITEMS[id];
      Object.entries(it.use).forEach(([k, v]) => Engine.addParam(k, v));
      s.items.splice(s.items.indexOf(id), 1);
      AudioEngine.item(); this.close();
      UI.toast(`${it.name}を使った。`);
    });
  },

  slotRows(mode) {
    const cog = Engine.s ? Engine.s.params.cog : 0;
    return Engine.readSlots().map((sl, i) => {
      let label = sl ? `${sl.title}<br><span class="dim">${new Date(sl.ts).toLocaleString('ja-JP')}</span>` : '<span class="dim">- 空きスロット -</span>';
      if (sl && cog >= 80) label = 'データ破損：■■■■<br><span class="dim">▓▓▓▓/▓▓/▓▓ ▓▓:▓▓</span>';
      const dis = mode === 'load' && !sl;
      return `<button class="slot" data-slot="${i}" ${dis ? 'disabled' : ''}><span class="slot-no">${i + 1}</span>${label}</button>`;
    }).join('');
  },

  saveLoad(mode) {
    this.open(`<h3>${mode === 'save' ? 'SAVE — 記憶のバックアップ' : 'LOAD — 記憶の巻き戻し'}</h3><div class="slots">${this.slotRows(mode)}</div>
      ${mode === 'load' ? '<div class="dim small">※ロードすると LOOP_COUNT が増加します。</div>' : ''}`);
    document.querySelectorAll('.slot').forEach(b => b.onclick = () => {
      const i = +b.dataset.slot;
      this.close();
      if (mode === 'save') Engine.save(i);
      else Engine.load(i);
    });
  },

  pc() {
    const s = Engine.s;
    const frags = Engine.fragCount();
    const legacyRow = (s.loop >= 1 && !s.items.includes('frag5') && !s.flags.frag5_taken)
      ? `<button class="mini-btn" id="pc-legacy">見覚えのないバックアップを開く</button>` : '';
    const analyzeRow = frags >= 5 && !s.flags.frags_analyzed
      ? `<button class="mini-btn" id="pc-analyze">破損ファイルを一括解析する（5/5）</button>`
      : `<div class="dim small">破損ファイル：${frags}/5 ${s.flags.frags_analyzed ? '──解析済' : ''}</div>`;
    this.open(`<h3>PC端末</h3>
      <div class="pc-menu">
        <button class="mini-btn" id="pc-save">セーブ</button>
        <button class="mini-btn" id="pc-load">ロード</button>
        ${analyzeRow}${legacyRow}
      </div>`);
    $('#pc-save').onclick = () => { this.close(); this.saveLoad('save'); };
    $('#pc-load').onclick = () => { this.close(); this.saveLoad('load'); };
    const an = $('#pc-analyze');
    if (an) an.onclick = () => {
      this.close();
      s.flags.frags_analyzed = true;
      Engine.addParam('cog', 20);
      AudioEngine.bigGlitch(); UI.fx('glitch');
      EventView.show([
        { speaker: 'SYSTEM', text: '解析完了。──ファイル群は、この端末の「外側」で生成されています。', style: 'system' },
        { speaker: 'アラヤ', tachie: 'araya', text: '外側……？ この街の外なんて、あるわけ──' },
        { speaker: '', text: '（画面の奥から、何かに「見られている」感覚だけが残った）' },
      ]);
    };
    const lg = $('#pc-legacy');
    if (lg) lg.onclick = () => {
      this.close();
      s.flags.frag5_taken = true;
      if (!s.items.includes('frag5')) s.items.push('frag5');
      Engine.addParam('cog', 8);
      AudioEngine.glitch();
      EventView.show([
        { speaker: 'SYSTEM', text: `未登録のバックアップを検出：${Engine.metaSaveName()}`, style: 'system' },
        { speaker: '', text: '（──断片データ「破損ファイル_05」を取得した。作成者名の欄には、読めない文字列）' },
      ]);
    };
  },
};

/* ============ タイトル ============ */
const Title = {
  show() {
    AudioEngine.stopAll();
    const loop = Engine.readLoop();
    const ed5 = localStorage.getItem(LS.ED5) === '1';
    const hasSave = Engine.readSlots().some(x => x);
    const layer = $('#title-layer');
    layer.className = 'active' + (ed5 ? ' ed5-title' : '');
    layer.innerHTML = `
      <div class="tt-bg"></div>
      <div class="tt-rain"></div>
      <div class="tt-body">
        <h1 class="tt-logo glitch-text" data-text="Delete Me Not.">Delete Me Not.</h1>
        <div class="tt-sub">${ed5 ? '- 共犯者の檻 -' : '最下層、記憶改変サスペンス'}</div>
        <div class="tt-menu">
          <button id="tt-new">はじめから</button>
          <button id="tt-cont" ${hasSave ? '' : 'disabled'}>つづきから</button>
        </div>
        <div class="tt-loop">${loop > 0 ? `SYSTEM: LOOP_COUNT = ${loop}` : ''}</div>
      </div>`;
    const rain = layer.querySelector('.tt-rain');
    for (let i = 0; i < 40; i++) {
      const d = el('span', 'drop');
      d.style.left = Math.random() * 100 + '%';
      d.style.animationDelay = Math.random() * 1.5 + 's';
      rain.appendChild(d);
    }
    $('#tt-new').onclick = () => {
      AudioEngine.unlock(); AudioEngine.confirm();
      layer.className = ''; layer.innerHTML = '';
      Engine.s = Engine.fresh();
      this.prologue();
    };
    $('#tt-cont').onclick = () => {
      AudioEngine.unlock(); AudioEngine.confirm();
      const slots = Engine.readSlots();
      let idx = 0, best = 0;
      slots.forEach((sl, i) => { if (sl && sl.ts > best) { best = sl.ts; idx = i; } });
      Engine.s = Engine.fresh();
      layer.className = ''; layer.innerHTML = '';
      if (!Engine.load(idx)) { Engine.s = Engine.fresh(); UI.enterExplore('alley'); }
    };
  },

  prologue() {
    UI.enterExplore('alley', true);
    const s = Engine.s;
    const lines = [
      { speaker: '', text: '上層から降り続ける酸性の排水が、今日も路地を洗っている。', style: 'system' },
      { speaker: 'アラヤ', tachie: 'araya', text: '……最悪の朝だ。いや、ここに「朝」なんてないか。' },
      { speaker: 'アラヤ', tachie: 'araya', text: '仕事だ。レイが待ってる。' },
    ];
    if (s.loop >= 1) lines.push({ speaker: '', text: '（ポケットの中で、覚えのないアクセスログが微かに熱を持っている）', style: 'system' });
    EventView.show(lines);
  },
};

/* ============ 起動 ============ */
window.addEventListener('DOMContentLoaded', () => {
  UI.init();
  window.addEventListener('pointerdown', () => AudioEngine.unlock(), { once: true });
});
