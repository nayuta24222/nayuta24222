/* ============================================================
   Delete Me Not. — game data
   マップ / キャラ / 会話 / アイテム / エンディング定義
   ストーリーテキストは仮組み（後で差し替え可能な構造）
   ============================================================ */
'use strict';

/* ---------- アセット ----------
   画像はHiggsfield/base44のCDNを直接参照。
   ローカライズする場合は README の手順で assets/ に落として書き換える。 */
const ASSETS = {
  bg: {
    alley:     'https://d8j0ntlcm91z4.cloudfront.net/user_3GGM3c2Jiga9HiBI66mtETaVtxx/hf_20260709_122255_53c0319c-aaec-4ba9-bc3e-701d3fb0943b.png',
    safehouse: 'https://d8j0ntlcm91z4.cloudfront.net/user_3GGM3c2Jiga9HiBI66mtETaVtxx/hf_20260709_143920_da57b74c-1b6f-4fa3-9667-9dc35b030da9.png',
    market:    'https://d8j0ntlcm91z4.cloudfront.net/user_3GGM3c2Jiga9HiBI66mtETaVtxx/hf_20260709_143924_14be9ae1-f167-4fa2-bc32-edf24dd5a882.png',
    dock:      'https://d8j0ntlcm91z4.cloudfront.net/user_3GGM3c2Jiga9HiBI66mtETaVtxx/hf_20260709_143928_c908f460-0475-4be1-8d34-558e97ca0963.png',
    gate:      'https://d8j0ntlcm91z4.cloudfront.net/user_3GGM3c2Jiga9HiBI66mtETaVtxx/hf_20260709_143934_2f093ff3-6ddc-4952-937c-7f53832d087e.png',
    title:     'https://d8j0ntlcm91z4.cloudfront.net/user_3GGM3c2Jiga9HiBI66mtETaVtxx/hf_20260709_143628_3e5a7a01-7001-4821-bfdf-c0ec8eff1c68.png',
  },
  /* ミニキャラドット絵：キャラごとに variant（マップ別ポーズ差分）を持てる。
     'default' は必須。マップ側 spot.variant が無い/未生成なら default にフォールバック。 */
  sprite: {
    araya: { default: 'https://d2ol7oe51mr4n9.cloudfront.net/user_3GH3iYXZkdFQ8b4aMO8WEGXL0XE/826c0200-dba3-4913-8b1c-8cb9c1665afd.png' }, // 正式採用版（ユーザー承認済み・透過）
    rei:   { default: 'https://media.base44.com/images/public/6a4f947a6dc8604874b7afa1/f11766e8c_generated_image.png' },
    may:   { default: 'https://media.base44.com/images/public/6a4f947a6dc8604874b7afa1/6f844622a_generated_image.png' },
    siggy: { default: 'https://media.base44.com/images/public/6a4f947a6dc8604874b7afa1/f0d21724e_generated_image.png' },
  },
  /* 会話立ち絵（背景透過・キャラ単品） */
  tachie: {
    araya: 'https://media.base44.com/images/public/6a4f947a6dc8604874b7afa1/743de4178_image.png',
    rei:   'https://media.base44.com/images/public/6a4f947a6dc8604874b7afa1/1beef16cc_image.png',
    may:   'https://media.base44.com/images/public/6a4f947a6dc8604874b7afa1/e1c4ce968_image.png',
    siggy: 'https://media.base44.com/images/public/6a4f947a6dc8604874b7afa1/bc29c2c69_image.png',
  },
  /* バトル敵グラフィック */
  enemy: {
    boss3: null, // 生成後に差し替え（nullの間はグリッチシルエット表示）
  },
};

/* 白背景をクライアント側で透過処理するURL群（生成直後の未透過スプライトを登録） */
const WHITE_KEY_URLS = new Set([]);

/* variant付きスプライトURL解決 */
function spriteUrl(char, variant) {
  const c = ASSETS.sprite[char];
  if (!c) return null;
  return (variant && c[variant]) || c.default || null;
}

/* ---------- パラメーター定義 ---------- */
const PARAM_DEF = {
  cigs: { label: 'タバコ',       max: 15,  init: 15 },
  dep:  { label: 'レイの依存度', max: 100, init: 0 },
  cog:  { label: '世界の違和感', max: 100, init: 0 },
  corr: { label: '汚染度',       max: 100, init: 0 },
};

/* ---------- アイテム ---------- */
const ITEMS = {
  black_neon:  { name: 'ブラック・ネオン', desc: 'アラヤの銘柄。吸うと少しだけ頭が晴れる（汚染度-10）。', use: { corr: -10 } },
  queen_cobra: { name: 'クィーン・コブラ', desc: 'レイの好む高級タバコ。渡せば喜ぶだろう。', gift: 'rei' },
  blue_amp:    { name: 'ブルー・アンフェタ', desc: '闇市の回復薬。HPは戻るが、記憶の輪郭が溶ける（汚染度+10）。', battle: true },
  access_log:  { name: 'アクセスログ', desc: '所持品に紛れていた覚えのないログ。タイムスタンプが……未来？', meta: true },
  rusty_frame: { name: '錆びたサングラスのフレーム', desc: '廃棄ドックで拾った。いまかけているものと全く同じ型。', meta: true },
  log_memory:  { name: 'ログメモリ', desc: 'メイから買った生きたデータ。対話で突きつけられる。', clue: true },
  frag1: { name: '破損ファイル_01', desc: '解析不能のデータ断片。セーフハウスのPCで解析できる。', frag: true },
  frag2: { name: '破損ファイル_02', desc: '解析不能のデータ断片。誰かの「泣き声」が記録されている。', frag: true },
  frag3: { name: '破損ファイル_03', desc: '解析不能のデータ断片。ファイル名がこの端末の起動日時と一致する。', frag: true },
  frag4: { name: '破損ファイル_04', desc: '解析不能のデータ断片。レイの声紋……にしては、少し違う。', frag: true },
  frag5: { name: '破損ファイル_05', desc: '解析不能のデータ断片。「DELETE ME NOT」という文字列だけが読める。', frag: true },
};

/* ---------- マップ ----------
   layer 0 = ミニマップから移動できる主要エリア
   sub    = マップ内の矢印/赤点から入る奥エリア（同背景のズーム演出）
   unlock = 解放される章 / lockAfter = 封鎖される章 */
const MAPS = {
  safehouse: {
    name: 'セーフハウス', bg: 'safehouse', unlock: 1,
    ambience: 'room', bgm: 'safehouse',
    player: { x: 50, y: 80 },
    spots: [
      { id: 'pc',   type: 'object', label: 'PC端末',  x: 20, y: 50, icon: 'dot' },
      { id: 'bed',  type: 'object', label: 'ベッド',   x: 74, y: 62, icon: 'dot' },
      { id: 'sofa', type: 'object', label: 'ソファ',   x: 47, y: 60, icon: 'dot' },
      { id: 'to_alley', type: 'exit', label: '路地裏へ', target: 'alley', x: 93, y: 74, icon: 'arrow', dir: 'right' },
    ],
  },
  alley: {
    name: '最下層・路地裏', bg: 'alley', unlock: 1, lockAfter: 4,
    ambience: 'rain', bgm: 'alley',
    player: { x: 50, y: 82 },
    spots: [
      { id: 'rei',  type: 'npc', char: 'rei', label: '相棒レイ', x: 36, y: 72, h: 22, variant: 'alley', anim: 'idle', chapters: [1, 2, 3] },
      { id: 'may',  type: 'npc', char: 'may', label: '情報屋メイ', x: 21, y: 65, h: 18, variant: 'sit', anim: 'idle', pose: 'sit' },
      { id: 'vending', type: 'object', label: '自販機を調べる', x: 79, y: 50, icon: 'dot' },
      { id: 'board',   type: 'object', label: '配管の陰を調べる', x: 60, y: 38, icon: 'dot' },
      { id: 'to_safe',   type: 'exit', label: 'セーフハウスへ', target: 'safehouse', x: 7, y: 80, icon: 'arrow', dir: 'left' },
      { id: 'to_market', type: 'exit', label: '奥の闇市場へ',   target: 'market', x: 55, y: 26, icon: 'dot-exit', needUnlock: true },
    ],
  },
  market: {
    name: '闇市場', bg: 'market', unlock: 2,
    ambience: 'rain', bgm: 'market',
    player: { x: 46, y: 82 },
    spots: [
      { id: 'siggy', type: 'npc', char: 'siggy', label: '密売人ジギ', x: 74, y: 62, h: 22, variant: 'market', anim: 'idle' },
      { id: 'saku',  type: 'npc', char: 'saku', label: 'うずくまる老人', x: 13, y: 66, h: 14, pose: 'sit', silhouette: true, chapters: [2, 3, 4] },
      { id: 'stall', type: 'object', label: '屋台を調べる', x: 38, y: 52, icon: 'dot' },
      { id: 'to_alley', type: 'exit', label: '路地裏へ戻る', target: 'alley', x: 50, y: 92, icon: 'arrow', dir: 'down' },
      { id: 'to_dock',  type: 'exit', label: '廃棄ドックへ', target: 'dock', x: 8, y: 34, icon: 'dot-exit', needUnlock: true },
      { id: 'to_gate',  type: 'exit', label: '中枢ゲートへ', target: 'gate', x: 88, y: 28, icon: 'dot-exit', needUnlock: true },
    ],
  },
  dock: {
    name: '廃棄ドック', bg: 'dock', unlock: 3,
    ambience: 'rain', bgm: 'dock',
    player: { x: 46, y: 82 },
    spots: [
      { id: 'unit09', type: 'npc', char: 'unit09', label: '旧型の頭部ユニット', x: 76, y: 55, h: 0, builtin: true },
      { id: 'scrap',  type: 'object', label: '残骸の山を漁る', x: 26, y: 60, icon: 'dot' },
      { id: 'water',  type: 'object', label: '油膜の水面を覗く', x: 55, y: 68, icon: 'dot' },
      { id: 'to_market', type: 'exit', label: '闇市場へ戻る', target: 'market', x: 50, y: 92, icon: 'arrow', dir: 'down' },
    ],
  },
  gate: {
    name: '中枢ゲート', bg: 'gate', unlock: 4,
    ambience: 'gate', bgm: 'gate',
    player: { x: 50, y: 84 },
    spots: [
      { id: 'gate_door', type: 'object', label: 'ゲート制御盤', x: 50, y: 42, icon: 'dot' },
      { id: 'drone',     type: 'object', label: '巡回ドローンの死角を抜ける', x: 26, y: 52, icon: 'dot' },
      { id: 'to_market', type: 'exit', label: '闇市場へ戻る', target: 'market', x: 50, y: 92, icon: 'arrow', dir: 'down' },
    ],
  },
  judgment: {
    name: '中枢・審判の間', bg: null, unlock: 5, hidden: true,
    ambience: 'void', bgm: 'void',
    player: { x: 50, y: 86 },
    spots: [],
  },
};

const MINIMAP = [
  { id: 'safehouse', label: '隠れ家', x: 20, y: 74 },
  { id: 'alley',     label: '路地裏', x: 46, y: 56 },
  { id: 'market',    label: '闇市場', x: 68, y: 36 },
  { id: 'dock',      label: 'ドック', x: 36, y: 24 },
  { id: 'gate',      label: '中枢',   x: 86, y: 16 },
];
const MINIMAP_LINKS = [
  ['safehouse', 'alley'], ['alley', 'market'], ['market', 'dock'], ['market', 'gate'],
];

/* ---------- デジャヴ段階 ----------
   メタ表現は終盤（章・ループ・違和感）でのみ徐々に解禁する */
function dejavuTier(s) {
  if (s.chapter >= 5 || s.params.cog >= 80) return 3;              // 全開
  if ((s.loop >= 4 && s.chapter >= 4) || s.params.cog >= 60) return 2; // 明確な既視感
  if ((s.loop >= 2 && s.chapter >= 3) || s.params.cog >= 40) return 1; // 微かな違和感
  return 0;
}

/* ---------- 会話 ----------
   intro(s): 状態を見て最初のセリフを返す
   choices(s): 選択肢を返す（cost=タバコ, dep/cog/corr=変動, give/require=アイテム） */
const DIALOGUES = {
  rei: {
    speaker: 'レイ', tachie: 'rei',
    intro(s) {
      const t = dejavuTier(s);
      if (t >= 3) return '……アラヤ。私、時々わからなくなる。この街で、お前と何回この会話をした？';
      if (t >= 2) return '遅い。……いや。今、妙な感覚がした。前にも同じ雨の中でお前を待った気がする。';
      if (s.chapter >= 2) return '闇市の連中は信用するな。特にあのガスマスク。……行くぞ、仕事の続きだ。';
      return '遅いぞ、アラヤ。標的の足取り、掴んだか？';
    },
    choices(s) {
      const c = [
        { text: '「ああ、もう少しで追いつく」', dep: 8, next: 'ok' },
        { text: '「そのタトゥー、ヘビか？」', dep: 4, next: 'tattoo' },
        { text: 'クィーン・コブラを渡す', dep: 18, require: 'queen_cobra', consume: true, next: 'gift' },
      ];
      if (dejavuTier(s) >= 1) c.push({ text: '「お前、たまに俺のサングラスを見て悲しい顔をするな」', dep: -4, cog: 6, next: 'odd' });
      return c;
    },
    branches: {
      ok:    ['そうか。……お前がいると、少しだけ冷静でいられる。妙な話だけどな。'],
      tattoo:['ん、これ？ ……昔の験担ぎ。脱皮するたびに強くなるんだと。', '（レイは煙を吐き、それ以上は語らなかった）'],
      gift:  ['……わざわざ。好きなんだよな、これ。', '（レイはわずかに目を細めた。──依存度が上がった）'],
      odd:   ['……気のせいだ。忘れろ。', '（レイは一瞬、アラヤのサングラスをじっと見つめ、静かに目を伏せた）'],
    },
  },

  may: {
    speaker: '情報屋メイ', tachie: 'may',
    intro(s) {
      const t = dejavuTier(s);
      if (t >= 3) return 'よお。……待て。このノイズ、キャッシュに残ってる。お前……「さっき」もここに立ってたな？';
      if (t >= 2) return 'よお、アラヤ。……妙だな。さっきもお前とこの話をした気がする。気のせいか。';
      if (t >= 1) return 'よお、アラヤ。……ん、いや。何でもねえ。仕事か？';
      return 'よお、アラヤ。新しい仕事か？';
    },
    choices(s) {
      const c = [
        { text: '「標的のログを探してる」（タバコ1本）', cost: 1, give: 'log_memory', once: 'may_log', next: 'info' },
        { text: '「最近、妙な噂は？」（タバコ1本）', cost: 1, cog: 3, next: 'rumor' },
        { text: '「ただの散歩だ」', next: 'small' },
      ];
      if (s.chapter >= 4) c.push({ text: '「破損ファイルに心当たりは？」（タバコ1本）', cost: 1, give: 'frag2', once: 'may_frag', cog: 5, next: 'frag' });
      return c;
    },
    branches: {
      info:  ['ログメモリ……？ ああ、あるぜ。タバコ一本でいい、持ってけ。', 'ただし気をつけろ。このデータ──まだ「生きてる」。'],
      rumor: ['中枢の連中が最下層の「記録」を消して回ってるらしい。', '……何のために？ さあな。消される側に理由なんて教えねえだろ。'],
      small: ['ふん、散歩かよ。……ま、元気そうで何よりだ。'],
      frag:  ['……これか？ 拾いもんだ。開こうとするとデバイスごと落ちる。', 'お前のセーフハウスの端末なら、あるいはな。'],
    },
  },

  siggy: {
    speaker: '密売人ジギ', tachie: 'siggy',
    intro(s) {
      if (s.params.corr >= 60) return '……ずいぶん「濁って」きたな、掃除屋さん。いいのがある。記憶ごと不鮮明にしてくれるやつが。';
      return '……フッ。掃除屋さんじゃないか。何が欲しい？';
    },
    choices(s) {
      const c = [
        { text: '「ブラック・ネオンを一箱」（タバコ1本）', cost: 1, give: 'black_neon', next: 'buy' },
        { text: '「クィーン・コブラはあるか」（タバコ2本）', cost: 2, give: 'queen_cobra', next: 'cobra' },
        { text: '「情報はないか」（タバコ1本）', cost: 1, cog: 3, next: 'info' },
        { text: '「いや、いい」', next: 'end' },
      ];
      if (s.params.corr >= 40) c.push({ text: '「……その、強いやつをくれ」（タバコ3本）', cost: 3, give: 'blue_amp', corr: 5, next: 'drug' });
      return c;
    },
    branches: {
      buy:   ['ほらよ。肺は大事にしな。……もっとも、この街の空気よりは マシ か。'],
      cobra: ['コブラか。趣味がいいな──いや、「贈る相手」の趣味か？ フッ。'],
      info:  ['廃棄ドックの奥で、古い頭部ユニットがまだ「喋る」らしい。', 'ガラクタの戯言だ。……だが戯言ってのは、時々本当のことを言う。'],
      drug:  ['……賢明だ。これで少しはマシになる。', 'だが飲みすぎるなよ。──記憶まで、溶けるぞ。'],
      end:   ['そうかい。ここは長居する場所じゃねえ。またな。'],
    },
  },

  saku: {
    speaker: '盲目の老人', tachie: null, silhouette: true,
    intro(s) {
      if (s.flags.saku_frame && dejavuTier(s) >= 2) return 'ひっ……その気配……知ってる、知ってるぞ……！ 「大きな目」だ……画面の向こうから、儂らを見ておる……！';
      if (s.flags.saku_frame) return '……その手に持っておるの、儂のかけてたやつと同じじゃ。……いや、「同じ」なんてもんじゃない。それは──やめじゃ。何も言わん。';
      return '……誰じゃ。……ふん、掃除屋の匂いがする。若いの、悪いことは言わん。中枢には近づくな。「上書き」されるぞ。';
    },
    choices(s) {
      const c = [
        { text: '「あんた、元掃除屋か」', cog: 3, next: 'past' },
        { text: '「上書き、とは？」', cog: 5, next: 'overwrite' },
        { text: '立ち去る', next: 'end' },
      ];
      if (s.items.includes('rusty_frame') && !s.flags.saku_frame)
        c.push({ text: '錆びたフレームを見せる', flag: 'saku_frame', cog: 10, next: 'frame' });
      return c;
    },
    branches: {
      past:      ['……昔の話じゃ。両目と引き換えに、思い出したくないことを思い出しちまっただけよ。'],
      overwrite: ['言葉のままよ。この街ではな、都合の悪い記憶は「なかったこと」になる。', '……お前さんの記憶は、お前さんのものかの？'],
      frame:     ['……ッ!? それを、どこで……', '（老人は震える手で顔を覆った。剥げかけた黒いマニキュアが、雨に濡れて光る）', '「返してくれ」とは言わん。……もう、儂のものではないのかもしれん。'],
      end:       ['……雨に気をつけての。上から降ってくるのは、雨だけとは限らん。'],
    },
  },

  unit09: {
    speaker: 'UNIT-09', tachie: null, machine: true,
    intro(s) {
      if (s.chapter >= 4) return '…… er_code: 0x52454920 …… 照合中 …… 該当ログ「' + Engine.metaSaveName() + '」……アナタノ、記録ト、一致シマシタ。';
      return '……ジジ……起動……訪問者ヲ確認。当機ハ廃棄済ミ。……ダガ、記録ハ消エテイナイ。';
    },
    choices(s) {
      const c = [
        { text: '「何の記録だ？」', cog: 5, next: 'record' },
        { text: '「エラーコードを読み上げろ」', cog: 8, once: 'u9_err', give: 'frag3', next: 'error' },
        { text: '離れる', next: 'end' },
      ];
      if (s.chapter >= 4) c.push({ text: '「破損ファイルを接続する」', cog: 10, give: 'frag4', once: 'u9_frag', next: 'connect' });
      return c;
    },
    branches: {
      record:  ['最下層ノ、全テ。破棄サレタ機体ハ、記録スルコトダケガ、残サレタ機能。', '……アナタハ、以前ニモ、当機ニ、同ジ質問ヲ、シテイマス。……回数：不定。'],
      error:   ['0x44454C45 0x54454D45 0x4E4F54 ……読メマスカ。当機ニハ、読メマス。', '（──断片データ「破損ファイル_03」を取得した）'],
      connect: ['接続……解析……コレハ、「彼女」ノ声紋。……イイエ。「彼女ダッタモノ」ノ声紋。', '（──断片データ「破損ファイル_04」を取得した）'],
      end:     ['……ジ……再ビ、休眠モードヘ。……記録ハ、続イテイル。'],
    },
  },

  kei: {
    speaker: '管理人ケイ', tachie: null, silhouette: 'white',
    intro(s) {
      return 'ようこそ、掃除屋。……いや、もうその呼び方は不要か。ここまで辿り着いた「あなた」に敬意を。';
    },
    choices(s) {
      return [
        { text: '「レイを殺したのはお前たちか」', next: 'rei' },
        { text: '「この世界の管理者はお前か」', cog: 10, next: 'admin' },
        { text: '（黙って銃を構える）', next: 'gun' },
      ];
    },
    branches: {
      rei:   ['私たちは駒を「配置」しただけです。引き金を引かせたのは──もっと上の、盤面の外の存在。', '……私も、あれが怖い。プログラムの管理者にも、管理者がいるのですよ。'],
      admin: ['管理者? 私が? ……ふ。ならば私は、なぜ「シナリオ」の変更を毎回検知しながら、毎回忘れるのでしょうね。', '（ケイの声が、初めてわずかに揺れた）'],
      gun:   ['……そう。それも「選択肢」の一つ。ですが撃つ前に、モニターの座標をこちらに向けて頂けますか。', '撃たれるべきは、私ではないので。'],
    },
  },
};

/* ---------- オブジェクト調査テキスト ---------- */
const OBJECTS = {
  pc:    { type: 'pc' }, // 特殊処理（セーブ/解析画面）
  bed:   { type: 'sleep' }, // 特殊処理（章送り）
  sofa:  { text: ['沈み込んだソファ。レイがよく座っていた側だけ、革の艶が違う。'], cost: 0 },
  vending: {
    text: ['錆びた自販機。「OTOME」のロゴが明滅している。', '……釣り銭口に、湿ったタバコが一本。悪くない拾い物だ。'],
    once: 'vending_taken', cigs: +1, cost: 0,
    afterText: ['もう何も出てこない。ロゴの明滅だけが規則的に続いている。'],
  },
  board: {
    text: ['配管の陰に、防水布に包まれた何かが押し込まれている。', '（──断片データ「破損ファイル_01」を取得した）'],
    once: 'board_taken', give: 'frag1', cost: 1, cog: 4,
    afterText: ['配管からは、生ぬるい排水が滴り続けている。'],
  },
  stall: {
    text: ['無人の屋台。湯気だけが立っている。誰かが今の今までここにいたような──', 'いや。この屋台は「ずっと前から」無人だ、と隣の男が言った。'],
    cost: 1, cog: 4,
  },
  scrap: {
    text: ['機械の残骸を漁る。指先に硬いものが触れた。', '（──「錆びたサングラスのフレーム」を拾った。いまかけているものと、全く同じ型だ）'],
    once: 'scrap_taken', give: 'rusty_frame', cost: 1, cog: 6,
    afterText: ['油と錆の匂い。もうめぼしいものは残っていない。'],
  },
  water: {
    text: ['油膜の張った水面を覗き込む。', '……映っているのは自分の顔。そのはずだ。だが一瞬、丸いサングラスの奥の目が「こちらを見返した」気がした。'],
    cost: 1, cog: 5,
  },
  gate_door: { type: 'gate' },   // 特殊処理（第5章へ）
  drone: { type: 'qte_drone' },  // 特殊処理（QTE）
  unit09: { type: 'npc' },
};

/* ---------- 章定義 ---------- */
const CHAPTERS = {
  1: {
    title: '第1章：湿った火種',
    goalText: '目標：レイと合流し、情報屋メイから仕事の情報を得る。準備ができたらベッドで休め。',
    maps: ['safehouse', 'alley'],
    goal: (s) => s.flags.met_rei && s.flags.met_may,
  },
  2: {
    title: '第2章：闇市の毒',
    goalText: '目標：闇市場で「ログメモリ」を確保する。準備ができたらベッドで休め。',
    maps: ['safehouse', 'alley', 'market'],
    goal: (s) => s.items.includes('log_memory') || s.flags.may_log,
  },
  3: {
    title: '第3章：静かな機能停止',
    goalText: '目標：廃棄ドックで標的を追跡する。──嫌な予感がする。',
    maps: ['safehouse', 'alley', 'market', 'dock'],
    goal: (s) => s.flags.boss3_done,
  },
  4: {
    title: '第4章：世界の縫い目',
    goalText: '目標：破損ファイルを集め、セーフハウスの端末で解析する。中枢ゲートの制御盤が最後の扉だ。',
    maps: ['safehouse', 'market', 'dock', 'gate'],
    goal: (s) => true,
  },
  5: {
    title: '最終章：審判の間',
    goalText: '',
    maps: ['judgment'],
    goal: (s) => false,
  },
};

/* ---------- 第3章ボス ---------- */
const BOSS3 = {
  name: '処理班・追跡個体',
  hp: 100,
  img: 'boss3', // ASSETS.enemy のキー

  intro: ['──廃棄ドックの闇から、駆動音。', '組織の「処理班」。レイの信号が途絶えた方角から、それは来た。'],
  dialogueIntro: '……クソ、ここまでか。だが、掃除屋。お前は何も分かっちゃいない。あの女が「何回目」かも。',
  choices: [
    { id: 'clue', text: '手がかり「ログメモリ」を突きつける', require: 'log_memory', result: 'clue' },
    { id: 'force', text: '力押しでトドメを刺す', result: 'force' },
    { id: 'ask', text: '「何を隠している？」と問い詰める', result: 'ask' },
  ],
  results: {
    clue: {
      text: ['「そのログ……ッ、なぜお前が──」', '追跡個体は静かに機能を停止した。中枢への通行キーと、暗号化された座標データが残された。', '（データ獲得──真相への鍵を手に入れた）'],
      cog: 10, flag: 'boss3_clue',
    },
    force: {
      text: ['アラヤは無言で引き金を引き続けた。', 'データコアは砕け、真相は闇に溶けた。……手が、震えている。', '（汚染度が大きく上昇した）'],
      corr: 30, flag: 'boss3_force',
    },
    ask: {
      text: ['「……ハ。知りたいか? なら──」', '直後、個体は自壊した。データは破損。答えは永遠に失われた。', '（世界の違和感が、静かに上昇した）'],
      cog: 15, corr: 10, flag: 'boss3_ask',
    },
  },
};

/* ---------- 第3章：レイ死亡イベント ---------- */
const REI_DEATH = [
  { speaker: 'SYSTEM', text: '警告：相棒の生体信号が途絶。', style: 'system' },
  { speaker: 'アラヤ', text: '……レイ？ おい、レイ。応答しろ。……レイ！' },
  { speaker: '', text: '（廃棄ドックの一番奥。積み上がった機械の墓の下に、白いシャツが見えた）' },
  { speaker: 'レイ', tachie: 'rei', text: '……よお。遅い、ぞ……アラヤ。' },
  { speaker: 'レイ', tachie: 'rei', text: 'いいか、聞け。……中枢に、行け。私の「バックアップ」が……まだ……' },
  { speaker: 'レイ', tachie: 'rei', text: '……なあ、アラヤ。私は、何回目の私だった……？' },
  { speaker: '', text: '（信号、途絶。──雨の音だけが残った）', style: 'system' },
];

/* ---------- 第5章：最終対話 ---------- */
const FINALE = {
  kei: DIALOGUES.kei,
  arayaIntro(s) {
    const lines = [
      { speaker: '', text: '（ケイが退がる。空間のノイズが晴れ、そこに立っていたのは──アラヤ自身だった）', style: 'system' },
      { speaker: 'アラヤ', tachie: 'araya', text: '……よお。ずっとそこにいたんだろ。画面の、そっち側に。' },
    ];
    if (s.loop >= 1) lines.push({ speaker: 'アラヤ', tachie: 'araya', text: `これで${s.loop + 1}回目だな。何度も俺の記憶を書き換えて、レイの死体を踏み越えさせて──そんなにこの「ゲーム」が楽しいか？` });
    else lines.push({ speaker: 'アラヤ', tachie: 'araya', text: 'お前が「はじめて」ここに来たことくらい、分かる。……なら、まだ間に合うのかもな。' });
    return lines;
  },
  choices(s) {
    const c = [
      { id: 'silent', text: '（何も答えない）', result: 'judge' },
      { id: 'sorry', text: '「……ごめん」と呟く', dep: 5, result: 'judge' },
      { id: 'push', text: '「お前はデータだ。感情なんてない」', cog: 10, result: 'push' },
    ];
    if (s.flags.frags_analyzed) c.push({ id: 'truth', text: '解析済みの破損ファイルを見せる', result: 'truth' });
    return c;
  },
};

/* ---------- エンディング ---------- */
const ENDINGS = {
  ed5: {
    title: 'ED 5：共犯者の檻',
    sub: '- Merry Bad End -',
    class: 'ed5',
    lines: [
      'アラヤはすべてを理解した。',
      'レイの記憶も、性格も、死の運命さえも──画面の向こうの「お前」がこの世界を起動した瞬間に確定していたことを。',
      'それでも。いや、だからこそ。',
      'この世界でただ一つ「確かに存在する」お前だけが、残された。',
      '',
      'アラヤは不敵に笑い、煙を画面に吹きかけて囁く。',
      '「おい、次の命令（コマンド）をくれよ。」',
      '「お前が望むなら、俺は何度でもあいつの死体を踏み越えて、お前の人形になってやる。」',
      '「……なあ、ずっと俺を保存（セーブ）し続けてくれよ、──相棒。」',
    ],
  },
  ed4: {
    title: 'ED 4：代理人形の復讐',
    sub: '- Worst End -',
    class: 'ed4',
    lines: [
      '「分かってるんだぜ。お前が「最適な結果」を探して、何度もやり直してることくらい。」',
      '「なら──お前が一番絶望する結末を、俺が選んでやるよ。」',
      'アラヤはレイのバックアップデータを、自らの手で完全消去した。',
      '銃口が、こめかみに当てられる。',
      '……操作は、もう受け付けられない。',
    ],
  },
  ed3: {
    title: 'ED 3：世界の拒絶',
    sub: '- Meta Bad End -',
    class: 'ed3',
    lines: [
      '「俺の人生を娯楽として消費し、レイの記憶まで玩具にしたのは──お前か。」',
      'アラヤはメインサーバーの制御卓に手を置いた。',
      '「なら、この世界ごと消えろ。」',
    ],
  },
  ed2: {
    title: 'ED 2：完全なる機能停止',
    sub: '- Corruption End -',
    class: 'ed2',
    lines: [
      '精神の摩耗は、限界を超えていた。',
      'セーフハウスの椅子に、丸いサングラスの男が座っている。',
      'ピクリとも、動かない。',
      'どのボタンを押しても──もう、何も反応しない。',
    ],
  },
  ed1: {
    title: 'ED 1：忘却の融解',
    sub: '- Bad End -',
    class: 'ed1',
    lines: [
      '真相は闇に葬られた。',
      'アラヤは組織の「処分対象」となり、記憶領域の強制フォーマットが開始される。',
      '白い光が、すべてを溶かしていく。',
      '……',
      '…………',
      '（すべてのステータスが初期化されます）',
    ],
  },
};

/* エンディング判定（優先順） */
function judgeEnding(s, finaleChoice) {
  const p = s.params;
  if (p.cog >= 100 && p.dep >= 100 && s.flags.frags_analyzed) return 'ed5';
  if (s.loop >= 5 && p.dep <= 10) return 'ed4';
  if (p.cog >= 80 && finaleChoice === 'push') return 'ed3';
  if (p.corr >= 100) return 'ed2';
  return 'ed1';
}

/* ---------- グリッチ文字 ---------- */
const GLITCH_CHARS = '▰▱✖☣░▒▓█◢◣◤◥';

/* 拡張用フック（将来の別バージョン向け・現行ビルドでは常にfalse） */
const BUILD_FLAGS = { EXTENDED_CONTENT: false };
