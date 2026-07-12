# 3Dマップモデル (models3d)

2Dマップ背景画像をもとに、プロシージャルモデリングで再現した3Dマップ(GLB形式)。

## ファイル構成

- `*.glb` — 各マップの3Dモデル (glTF Binary)
- `build_*.py` — 各モデルの生成スクリプト (Python / trimesh + Pillow)
- `tools/kit.py` — 共通モデリングキット(プリミティブ・ネオン看板・テクスチャ生成)
- `viewer.html` — Three.js製ビューア (`?m=<モデル名>.glb` で切替)
- `lib/` — Three.js (ローカルコピー、CDN不要)

## ビューアの使い方

```bash
cd models3d
python3 -m http.server 8000
# → http://localhost:8000/viewer.html?m=observation_tower.glb
```

マウスドラッグで回転、ホイールでズーム。
`?cx= &cy= &cz=` でカメラ初期位置を指定可能。

## モデルの再生成

```bash
pip install trimesh numpy pillow
python3 models3d/build_observation_tower.py
```

日本語看板テクスチャにはIPAゴシック
(`/usr/share/fonts/truetype/fonts-japanese-gothic.ttf`) を使用。

## マップ一覧

| モデル | 元背景 | 内容 |
|---|---|---|
| observation_tower.glb | 観測塔 | 検問所。観測塔ネオン、監視モニター壁、サーバーラック、遮断ゲート、床スキャナー、プロパガンダ看板、パラボラアンテナ他 |
