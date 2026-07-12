# -*- coding: utf-8 -*-
"""
闇市 (Black Market) — 背景画像5の3D再現。

画像分析メモ:
  - 屋外の石壁に囲まれた広場。雨。菱形に走る大判タイルの床、
    ピンク/青/橙のネオン反射。
  - 左上: ピンクネオン「闇市」(枠付き)。その下に破れたテント屋台3張
    (暗赤/紫/茶、継ぎ当て付き)。下に木箱・段ボール・樽が山積み。
  - 上空: 電線が渡り、小さな灯りがぶら下がる。
  - 中央右: 屋台カート(焼き網から煙、吊るした燻製肉)、
    上の壁に青ネオン「薬」(枠付き、チェーン吊り)。
  - 右: 瓶がずらりと並ぶ交易ブース+橙色の提灯3つ、
    青ネオン「交換」(枠付き、やや傾く)。
  - 左: ドラム缶、木箱。床に有蓋排水口。
"""
import math
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tools"))

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import trimesh
import random as _rnd

from kit import (M, std_mats, mat, tex_mat, box, cyl, cone, sphere, quad,
                 disc, T, R, neon_sign, tile_floor_tex, wall_tex,
                 poster_tex, lamp, barrel, crate, pipe_run, export, _font)

std_mats()
S = trimesh.Scene()

W_GND, D_GND = 14.0, 12.0

# ---------------------------------------------------------------- 床(菱形タイル)
def market_floor_tex(size=(1024, 1024), seed=37):
    rng = _rnd.Random(seed)
    img = Image.new("RGB", size, (17, 18, 24))
    d = ImageDraw.Draw(img)
    Wt, Ht = size
    step = 128
    # 菱形グリッド(斜め45°の目地)
    for k in range(-Wt, Wt * 2, step):
        d.line([(k, 0), (k + Ht, Ht)], fill=(8, 8, 12), width=5)
        d.line([(k, 0), (k - Ht, Ht)], fill=(8, 8, 12), width=5)
    # タイルのまだら
    for _ in range(700):
        x, y = rng.randint(0, Wt), rng.randint(0, Ht)
        r = rng.randint(8, 36)
        v = rng.uniform(0.65, 1.3)
        d.ellipse([x - r, y - r, x + r, y + r],
                  fill=(int(16 * v), int(17 * v), int(23 * v)))
    # 目地を描き直す
    for k in range(-Wt, Wt * 2, step):
        d.line([(k, 0), (k + Ht, Ht)], fill=(8, 8, 12), width=5)
        d.line([(k, 0), (k - Ht, Ht)], fill=(8, 8, 12), width=5)
    # ネオン反射
    spots = [(0.22, 0.35, 110, (200, 40, 130)), (0.30, 0.75, 90, (170, 30, 110)),
             (0.55, 0.45, 80, (40, 80, 190)), (0.72, 0.40, 90, (60, 90, 200)),
             (0.85, 0.55, 80, (220, 120, 40)), (0.60, 0.80, 70, (50, 70, 150)),
             (0.10, 0.55, 60, (150, 40, 100))]
    ref = Image.new("RGB", size, (0, 0, 0))
    rd = ImageDraw.Draw(ref)
    for (u, v, r, c) in spots:
        x, y = int(u * Wt), int(v * Ht)
        rd.ellipse([x - r, y - int(r * 0.6), x + r, y + int(r * 0.6)], fill=c)
    ref = ref.filter(ImageFilter.GaussianBlur(40))
    img = Image.blend(img, Image.blend(img, ref, 0.9), 0.5)
    return img

floor_m = tex_mat("floor", market_floor_tex(), rough=0.32, metallic=0.06)
quad(S, W_GND, D_GND, (0, 0, 0), floor_m, rot=R(-90, "x"), double=False)
box(S, (W_GND, 0.3, D_GND), (0, -0.16, 0), M("concrete", (0, 0, 0)))

# ---------------------------------------------------------------- 岩壁
def rock_tex(size=(1024, 512), seed=43):
    rng = _rnd.Random(seed)
    img = Image.new("RGB", size, (16, 15, 19))
    d = ImageDraw.Draw(img)
    Wt, Ht = size
    for _ in range(260):   # ゴツゴツした岩
        x, y = rng.randint(-30, Wt), rng.randint(-20, Ht)
        w = rng.randint(40, 130)
        h = rng.randint(28, 70)
        v = rng.uniform(0.6, 1.35)
        c = (int(18 * v), int(17 * v), int(21 * v))
        pts = []
        n = rng.randint(5, 7)
        for i in range(n):
            th = 2 * math.pi * i / n + rng.uniform(-0.3, 0.3)
            pts.append((x + math.cos(th) * w / 2 * rng.uniform(0.7, 1.1),
                        y + math.sin(th) * h / 2 * rng.uniform(0.7, 1.1)))
        d.polygon(pts, fill=c, outline=(7, 7, 9))
    return img

wall_m = tex_mat("rock", rock_tex(), rough=1.0, metallic=0.0)
HWALL = 6.5
wuv = np.array([[0, 0], [2.6, 0], [2.6, 1.3], [0, 1.3]])
quad(S, W_GND, HWALL, (0, HWALL / 2, -D_GND / 2), wall_m, uv=wuv)
quad(S, D_GND, HWALL, (-W_GND / 2, HWALL / 2, 0), wall_m, rot=R(90, "y"),
     uv=wuv)
quad(S, D_GND, HWALL, (W_GND / 2, HWALL / 2, 0), wall_m, rot=R(-90, "y"),
     uv=wuv)
# 壁の配管
pipe_run(S, (6.85, 0.3, -4.0), (6.85, 5.8, -4.0), r=0.07)
pipe_run(S, (6.8, 5.8, -4.0), (2.0, 6.1, -5.9), r=0.05, joints=False)

# ---------------------------------------------------------------- ネオン看板
neon_sign(S, "闇市", 1.9, 1.0, (-3.3, 4.45, -5.55), rot=R(4, "z"),
          fg=(255, 60, 200), name="sign_yamiichi", font_scale=0.66,
          tex_h=320)
# 吊りチェーン
pipe_run(S, (-3.9, 5.6, -5.6), (-3.85, 4.95, -5.57), r=0.015, joints=False)
pipe_run(S, (-2.7, 5.5, -5.6), (-2.75, 4.95, -5.57), r=0.015, joints=False)

neon_sign(S, "薬", 1.15, 1.15, (2.3, 4.15, -5.55), fg=(80, 170, 255),
          name="sign_kusuri", font_scale=0.68, tex_h=288)
pipe_run(S, (2.0, 5.3, -5.6), (2.05, 4.75, -5.57), r=0.012, joints=False)
pipe_run(S, (2.6, 5.3, -5.6), (2.55, 4.75, -5.57), r=0.012, joints=False)

neon_sign(S, "交換", 1.7, 1.0, (6.45, 3.55, -1.8), rot=R(-90, "y") @ R(-4, "z"),
          fg=(90, 180, 255), name="sign_koukan", font_scale=0.6, tex_h=288)

# ---------------------------------------------------------------- テント屋台×3
def cloth_tex(base, seed=1, size=(256, 256)):
    rng = _rnd.Random(seed)
    img = Image.new("RGB", size, base)
    d = ImageDraw.Draw(img)
    Wt, Ht = size
    for _ in range(40):   # 汚れ・色ムラ
        x, y = rng.randint(0, Wt), rng.randint(0, Ht)
        r = rng.randint(10, 46)
        v = rng.uniform(0.55, 1.25)
        d.ellipse([x - r, y - r, x + r, y + r],
                  fill=tuple(int(c * v) for c in base))
    for _ in range(4):    # 継ぎ当て
        x, y = rng.randint(10, Wt - 60), rng.randint(10, Ht - 50)
        w, h = rng.randint(30, 60), rng.randint(24, 46)
        c = tuple(int(v * rng.uniform(1.3, 1.9)) for v in base)
        d.rectangle([x, y, x + w, y + h], fill=c, outline=(10, 10, 12))
        for sx in range(x, x + w, 8):   # ステッチ
            d.point((sx, y + 1), fill=(90, 85, 80))
            d.point((sx, y + h - 1), fill=(90, 85, 80))
    return img

def tent(x, z, w, depth, h_front, h_back, cloth_base, seed, yaw=0):
    """破れテント: 4本柱+傾いた天幕(前後2枚)+下の商品台。"""
    rot = R(yaw, "y")
    rv = rot[:3, :3]
    tm = tex_mat(f"tent_{seed}", cloth_tex(cloth_base, seed=seed), rough=1.0)
    for (dx, dz, hh) in [(-w/2, -depth/2, h_back), (w/2, -depth/2, h_back),
                         (-w/2, depth/2, h_front), (w/2, depth/2, h_front)]:
        off = rv @ np.array([dx, 0, dz])
        cyl(S, 0.045, hh, (x + off[0], hh / 2, z + off[2]),
            M("wood_dark", (0, 0, 0)), sections=8)
    # 天幕(たわみ表現: 2枚の傾斜quad)
    mid_h = (h_front + h_back) / 2 - 0.12
    ang = math.degrees(math.atan2(h_back - h_front, depth))
    c1 = rv @ np.array([0, 0, -depth * 0.25])
    quad(S, w + 0.3, depth * 0.56, (x + c1[0], (h_back + mid_h) / 2, z + c1[2]),
         tm, rot=rot @ R(-90 + ang * 1.15, "x"))
    c2 = rv @ np.array([0, 0, depth * 0.25])
    quad(S, w + 0.3, depth * 0.56, (x + c2[0], (h_front + mid_h) / 2, z + c2[2]),
         tm, rot=rot @ R(-90 + ang * 0.85, "x"))
    # 垂れ布(前)
    c3 = rv @ np.array([w * 0.4, 0, depth / 2])
    quad(S, 0.5, 0.7, (x + c3[0], h_front - 0.35, z + c3[2]), tm,
         rot=rot @ R(8, "z"))

tent(-4.8, -3.6, 2.6, 2.2, 2.1, 2.7, (64, 22, 26), seed=51, yaw=6)    # 暗赤
tent(-2.4, -3.0, 2.4, 2.2, 2.0, 2.6, (54, 26, 60), seed=52, yaw=-4)   # 紫
tent(-0.2, -3.8, 2.2, 2.0, 1.9, 2.5, (52, 38, 26), seed=53, yaw=3)    # 茶

# テント下の商品(木箱・段ボール・樽)
M("cardboard", (0.42, 0.33, 0.22), rough=1.0)
crate(S, (-5.3, 0, -3.4), size=(0.8, 0.6, 0.8), rot_y=12)
crate(S, (-5.25, 0.6, -3.35), size=(0.65, 0.5, 0.65), rot_y=-8)
crate(S, (-4.4, 0, -3.8), size=(0.7, 0.5, 0.7), rot_y=30)
box(S, (0.6, 0.45, 0.5), (-2.8, 0.225, -3.3), M("cardboard", (0, 0, 0)),
    rot=R(18, "y"))
box(S, (0.5, 0.4, 0.45), (-2.75, 0.65, -3.25), M("cardboard", (0, 0, 0)),
    rot=R(-10, "y"))
crate(S, (-2.0, 0, -3.6), size=(0.65, 0.5, 0.65), rot_y=-22)
box(S, (0.55, 0.4, 0.5), (-0.4, 0.2, -3.5), M("cardboard", (0, 0, 0)),
    rot=R(8, "y"))
crate(S, (0.3, 0, -4.0), size=(0.6, 0.45, 0.6), rot_y=14)
barrel(S, (-1.3, 0, -4.4), r=0.3, h=0.85)
barrel(S, (-6.2, 0, -1.6), r=0.34, h=0.95)
barrel(S, (-6.5, 0, -0.5), r=0.3, h=0.85)
crate(S, (-5.9, 0, 0.6), size=(0.75, 0.55, 0.75), rot_y=-14)

# ---------------------------------------------------------------- 屋台カート(焼き物)
CX, CZ = 2.6, -1.6
cart_rot = R(-8, "y")
crv = cart_rot[:3, :3]
# 本体
body = trimesh.creation.box(extents=[2.0, 0.9, 1.1])
body.visual = trimesh.visual.TextureVisuals(
    material=tex_mat("cart_body", wall_tex(size=(256, 128), seed=61,
                                           base=(48, 34, 28), panel=64),
                     rough=0.9, metallic=0.3))
body.apply_transform(T(CX, 0.75, CZ) @ cart_rot)
S.add_geometry(body)
# 車輪
for dxs in (-0.85, 0.85):
    off = crv @ np.array([dxs, 0, 0.62])
    cyl(S, 0.3, 0.1, (CX + off[0], 0.3, CZ + off[2]),
        M("wood_dark", (0, 0, 0)), rot=cart_rot @ R(90, "x"), sections=16)
    off2 = crv @ np.array([dxs, 0, -0.62])
    cyl(S, 0.3, 0.1, (CX + off2[0], 0.3, CZ + off2[2]),
        M("wood_dark", (0, 0, 0)), rot=cart_rot @ R(90, "x"), sections=16)
# 焼き網+炭火(発光)
M("coals", (0.9, 0.25, 0.08), emissive=(0.9, 0.18, 0.04), rough=0.8)
box(S, (0.9, 0.08, 0.6), (CX - 0.3, 1.24, CZ), M("coals", (0, 0, 0)),
    rot=cart_rot)
box(S, (1.0, 0.05, 0.7), (CX - 0.3, 1.3, CZ), M("frame_black", (0, 0, 0)),
    rot=cart_rot)
# 屋根(柱4本+暗い天幕)
for (dx, dz) in [(-0.9, -0.5), (0.9, -0.5), (-0.9, 0.5), (0.9, 0.5)]:
    off = crv @ np.array([dx, 0, dz])
    cyl(S, 0.035, 2.4, (CX + off[0], 1.2 + 0.6, CZ + off[2]),
        M("wood_dark", (0, 0, 0)), sections=8)
tm = tex_mat("cart_roof", cloth_tex((30, 32, 38), seed=63), rough=1.0)
quad(S, 2.4, 1.5, (CX, 3.05, CZ), tm, rot=cart_rot @ R(-90 + 7, "x"))
quad(S, 2.4, 0.5, (CX - 0.1, 2.85, CZ + 0.75), tm,
     rot=cart_rot @ R(12, "z"))
# 吊るした燻製肉(棒+紐+肉)
off = crv @ np.array([0, 0, 0.55])
pipe_run(S, (CX - 1.0 + off[0], 2.55, CZ + off[2]),
         (CX + 1.0 + off[0], 2.55, CZ + off[2]), r=0.02, joints=False)
M("meat", (0.45, 0.14, 0.08), rough=0.85)
rng = _rnd.Random(65)
for i in range(5):
    mx = CX - 0.8 + i * 0.4 + rng.uniform(-0.05, 0.05)
    h = rng.uniform(0.28, 0.45)
    pipe_run(S, (mx + off[0], 2.55, CZ + off[2]),
             (mx + off[0], 2.4, CZ + off[2]), r=0.008, joints=False)
    box(S, (0.14, h, 0.12), (mx + off[0], 2.4 - h / 2, CZ + off[2]),
        M("meat", (0, 0, 0)), rot=R(rng.uniform(-12, 12), "y"))
# 煙(半透明の球が立ち上る)
smoke = mat("smoke", (0.55, 0.55, 0.60, 0.30), metallic=0.0, rough=1.0)
smoke.alphaMode = "BLEND"
for i, (sy, sr, sdx) in enumerate([(1.7, 0.14, 0), (2.2, 0.20, 0.08),
                                   (2.8, 0.28, 0.02), (3.5, 0.38, -0.12),
                                   (4.2, 0.5, -0.05)]):
    sphere(S, sr, (CX - 0.3 + sdx, sy, CZ), smoke, subdivisions=2)

# ---------------------------------------------------------------- 交易ブース(右)
BX, BZ = 5.9, -0.6
# 棚本体
box(S, (0.8, 2.6, 3.2), (BX + 0.4, 1.3, BZ), M("wood_dark", (0, 0, 0)))
def bottles(x0, z0, x1, z1, y, n, seed):
    rng = _rnd.Random(seed)
    cols = [(0.5, 0.42, 0.30), (0.35, 0.45, 0.50), (0.55, 0.30, 0.22),
            (0.42, 0.42, 0.35), (0.30, 0.38, 0.45)]
    for i in range(n):
        t = i / max(1, n - 1)
        x = x0 + (x1 - x0) * t + rng.uniform(-0.03, 0.03)
        z = z0 + (z1 - z0) * t + rng.uniform(-0.04, 0.04)
        r = rng.uniform(0.045, 0.07)
        h = rng.uniform(0.18, 0.34)
        c = rng.choice(cols)
        cyl(S, r, h, (x, y + h / 2, z), mat(f"btl_{seed}_{i}", c,
                                            metallic=0.05, rough=0.25),
            sections=10)
        if rng.random() < 0.6:   # 栓
            cyl(S, r * 0.4, 0.05, (x, y + h + 0.02, z),
                M("wood_dark", (0, 0, 0)), sections=8)
for (sy, seed) in [(0.75, 71), (1.45, 72), (2.1, 73)]:
    box(S, (0.7, 0.05, 3.0), (BX + 0.35, sy, BZ), M("wood_dark", (0, 0, 0)))
    bottles(BX + 0.35, BZ - 1.3, BX + 0.35, BZ + 1.3, sy + 0.03, 9,
            seed=seed)
# カウンター
box(S, (0.6, 0.9, 2.6), (BX - 0.5, 0.45, BZ), M("wood_dark", (0, 0, 0)))
box(S, (0.75, 0.07, 2.8), (BX - 0.5, 0.93, BZ), M("metal_rust", (0, 0, 0)))
bottles(BX - 0.5, BZ - 1.0, BX - 0.5, BZ + 0.4, 0.97, 4, seed=75)
crate(S, (BX - 0.7, 0, BZ + 2.0), size=(0.65, 0.5, 0.65), rot_y=18)
box(S, (0.5, 0.4, 0.45), (BX - 1.3, 0.2, BZ + 2.6), M("cardboard", (0, 0, 0)),
    rot=R(-12, "y"))

# 橙色の提灯×3(吊り下げ)
M("lantern", (1.0, 0.55, 0.18), emissive=(1.0, 0.42, 0.10), rough=0.5)
for (lx, ly, lz) in [(4.6, 2.9, -0.2), (5.3, 2.3, 1.3), (4.9, 2.6, 2.3)]:
    pipe_run(S, (lx, ly + 0.55, lz), (lx, ly + 0.22, lz), r=0.01,
             joints=False)
    g = trimesh.creation.icosphere(subdivisions=2, radius=0.22)
    g.apply_scale([1.0, 1.25, 1.0])
    g.visual = trimesh.visual.TextureVisuals(material=M("lantern", (0,)))
    g.apply_transform(T(lx, ly, lz))
    S.add_geometry(g)
    for cy in (ly + 0.26, ly - 0.26):
        cyl(S, 0.09, 0.05, (lx, cy, lz), M("frame_black", (0, 0, 0)),
            sections=12)
# 提灯を吊る横木
pipe_run(S, (4.4, 3.5, -0.3), (5.1, 2.9, 2.5), r=0.03, joints=False)

# ---------------------------------------------------------------- 電線と小さな灯り
pipe_run(S, (-6.9, 5.9, -4.5), (-1.5, 5.1, -5.0), r=0.015, joints=False)
pipe_run(S, (-1.5, 5.1, -5.0), (4.0, 5.7, -5.4), r=0.015, joints=False)
pipe_run(S, (-5.5, 6.1, -2.0), (2.0, 5.3, -3.2), r=0.015, joints=False)
rng = _rnd.Random(77)
for t in (0.2, 0.45, 0.7):
    x = -5.5 + 7.5 * t
    y = 6.1 - 0.8 * t - 0.3 * math.sin(t * math.pi)
    z = -2.0 - 1.2 * t
    pipe_run(S, (x, y, z), (x, y - 0.25, z), r=0.008, joints=False)
    sphere(S, 0.06, (x, y - 0.3, z), M("lamp_warm", (0, 0, 0)),
           subdivisions=1)

# 排水口(有蓋)
def grate_tex(size=(256, 256)):
    img = Image.new("RGB", size, (11, 12, 14))
    d = ImageDraw.Draw(img)
    c = size[0] // 2
    for r in (110, 82, 54, 26):
        d.ellipse([c - r, c - r, c + r, c + r], outline=(40, 42, 46),
                  width=8)
    return img
disc(S, 0.5, (-1.2, 0.012, 3.6), tex_mat("drain", grate_tex(),
                                         metallic=0.5, rough=0.7))

# 手前の残り物
crate(S, (2.2, 0, 3.9), size=(0.6, 0.45, 0.6), rot_y=26)
barrel(S, (-4.4, 0, 4.3), r=0.28, h=0.8)

out = os.path.join(os.path.dirname(__file__), "dark_market.glb")
size = export(S, out)
print(f"OK dark_market.glb {size/1e6:.2f} MB, geoms={len(S.geometry)}")
