# -*- coding: utf-8 -*-
"""
資料室 (Records / Archive Room) — 背景画像4の3D再現。

画像分析メモ:
  - 暗い文書保管庫。左壁上部にシアンネオン「資料室」。
  - 左壁: ドア(赤色灯+「立入禁止」札+検閲庁告知の貼り紙)、収納棚。
  - 奥壁: 銘板「記録は真実 / Records are Truth」、バインダーがぎっしりの
    アーカイブ棚、ピンクネオン「情報は力 / Information is Power」、
    白い「分類コード」表(A:政府・行政〜E:その他)、丸時計。
  - 右壁: 天井までのバインダー棚が続く。赤色灯。
  - 中央: 大きな作業机。CRT(マゼンタ発光のテキスト画面)、緑っぽい
    デスクランプ(点灯)、散乱した書類、本の山、キーボード。手前にスツール。
  - 机の左: 立ち式端末(斜めキーボード+小さなピンク画面+発光スロット)。
  - 下側: シアン画面のCRTを載せたワゴン、書類箱の台車、布を掛けた台、
    バケツ、机+ランプ(右下)、マンホール(排水溝)、ゴミ箱。
  - 床: 暗いタイル。ピンク/シアンの反射。
"""
import math
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tools"))

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import trimesh
import random as _rnd

from kit import (M, std_mats, mat, tex_mat, box, cyl, cone, sphere, quad,
                 disc, T, R, neon_sign, screen_tex, tile_floor_tex, wall_tex,
                 poster_tex, lamp, barrel, crate, pipe_run, export, _font)

std_mats()
S = trimesh.Scene()

ROOM = 12.0
HW = 5.2
HR = ROOM / 2

# ---------------------------------------------------------------- 床と壁
wet = [
    (0.55, 0.45, 0.16, (200, 40, 110)),   # 机のCRT/ランプのピンク反射
    (0.25, 0.60, 0.10, (180, 40, 100)),
    (0.75, 0.75, 0.12, (40, 90, 110)),    # シアンCRT
    (0.15, 0.20, 0.10, (200, 30, 40)),    # 赤色灯
    (0.42, 0.80, 0.10, (30, 60, 100)),
]
floor_m = tex_mat("floor", tile_floor_tex(tile=86, base=(14, 15, 19),
                                          groove=(7, 7, 10), seed=23,
                                          wet_spots=wet),
                  rough=0.4, metallic=0.05)
quad(S, ROOM, ROOM, (0, 0, 0), floor_m, rot=R(-90, "x"),
     uv=np.array([[0, 0], [1, 0], [1, 1], [0, 1]]) * 3.5, double=False)
box(S, (ROOM, 0.3, ROOM), (0, -0.16, 0), M("concrete", (0, 0, 0)))

wall_m = tex_mat("wall", wall_tex(base=(14, 15, 19), seed=29), rough=0.85,
                 metallic=0.25)
wuv = np.array([[0, 0], [2.8, 0], [2.8, 1.3], [0, 1.3]])
quad(S, ROOM, HW, (0, HW / 2, -HR), wall_m, uv=wuv)
quad(S, ROOM, HW, (-HR, HW / 2, 0), wall_m, rot=R(90, "y"), uv=wuv)
quad(S, ROOM, HW, (HR, HW / 2, 0), wall_m, rot=R(-90, "y"), uv=wuv)

# 配管(壁上部)
pipe_run(S, (-HR, 4.9, -HR + 0.2), (HR, 4.9, -HR + 0.2), r=0.055)
pipe_run(S, (-HR + 0.2, 4.7, -HR), (-HR + 0.2, 4.7, HR), r=0.045)
pipe_run(S, (HR - 0.25, 0.3, 1.5), (HR - 0.25, 4.8, 1.5), r=0.06)

# ---------------------------------------------------------------- 棚(バインダー)
def binder_tex(size=(512, 128), seed=1):
    """バインダーの背表紙が並ぶテクスチャ(1棚ぶん)。"""
    rng = _rnd.Random(seed)
    img = Image.new("RGB", size, (10, 10, 13))
    d = ImageDraw.Draw(img)
    Wt, Ht = size
    x = 4
    cols = [(52, 44, 40), (40, 46, 52), (56, 50, 38), (44, 40, 50),
            (36, 42, 40), (60, 42, 36)]
    while x < Wt - 12:
        w = rng.randint(14, 30)
        h = rng.randint(int(Ht * 0.72), int(Ht * 0.94))
        c = rng.choice(cols)
        lean = rng.random() < 0.08
        y0 = Ht - h
        d.rectangle([x, y0, x + w, Ht], fill=c,
                    outline=tuple(int(v * 0.5) for v in c))
        # ラベル
        ly = y0 + rng.randint(6, max(7, h // 3))
        d.rectangle([x + 3, ly, x + w - 3, ly + rng.randint(6, 14)],
                    fill=(150, 140, 125))
        if rng.random() < 0.4:
            d.rectangle([x + 3, Ht - 18, x + w - 3, Ht - 8],
                        fill=tuple(min(255, int(v * 1.5)) for v in c))
        x += w + rng.randint(1, 4)
        if rng.random() < 0.07:   # 抜けた隙間
            x += rng.randint(10, 26)
    return img

def archive_shelf(x, z, w=2.2, h=3.6, rot_deg=0, seed=1, shelves=4):
    """バインダーがぎっしり入ったアーカイブ棚。rot_deg=0で+z向き。"""
    rot = R(rot_deg, "y")
    rv = rot[:3, :3]
    body = trimesh.creation.box(extents=[w, h, 0.62])
    body.visual = trimesh.visual.TextureVisuals(
        material=M("metal_dark", (0, 0, 0)))
    body.apply_transform(T(x, h / 2, z) @ rot)
    S.add_geometry(body)
    sh = h / shelves
    for i in range(shelves):
        y = i * sh
        # 棚板
        pl = trimesh.creation.box(extents=[w - 0.08, 0.05, 0.6])
        pl.visual = trimesh.visual.TextureVisuals(
            material=M("metal_mid", (0, 0, 0)))
        pl.apply_transform(T(x, y + sh - 0.02, z) @ rot)
        S.add_geometry(pl)
        # バインダー面
        bt = binder_tex(seed=seed * 10 + i)
        off = rv @ np.array([0, 0, 0.33])
        quad(S, w - 0.14, sh - 0.14, (x + off[0], y + sh / 2, z + off[2]),
             tex_mat(f"binders_{seed}_{i}", bt, rough=0.9,
                     emissive=(0.22, 0.22, 0.22), emissive_tex=bt),
             rot=rot)
    # 側板
    for sxo in (-w / 2, w / 2):
        off = rv @ np.array([sxo, 0, 0])
        sp = trimesh.creation.box(extents=[0.06, h, 0.64])
        sp.visual = trimesh.visual.TextureVisuals(
            material=M("metal_dark", (0, 0, 0)))
        sp.apply_transform(T(x + off[0], h / 2, z + off[2]) @ rot)
        S.add_geometry(sp)

# 奥壁の棚2台
archive_shelf(-3.6, -5.55, w=2.4, seed=3)
archive_shelf(-1.0, -5.55, w=2.4, seed=4)
# 右壁の棚3台(内向き)
archive_shelf(5.55, -3.4, w=2.3, rot_deg=-90, seed=5)
archive_shelf(5.55, -0.9, w=2.3, rot_deg=-90, seed=6)
archive_shelf(5.55, 1.6, w=2.3, rot_deg=-90, seed=7, h=3.2)
# 左壁手前の収納棚(低め)
archive_shelf(-5.6, 1.8, w=2.0, rot_deg=90, seed=8, h=2.4, shelves=3)

# ---------------------------------------------------------------- ネオン/掲示
# シアンネオン「資料室」(左壁)
neon_sign(S, "資料室", 2.4, 0.85, (-5.82, 4.35, -3.1), rot=R(90, "y"),
          fg=(80, 230, 220), name="sign_archive", tex_h=256)
# ピンクネオン「情報は力」(奥壁右上)
neon_sign(S, "情報は力", 2.9, 0.95, (1.9, 4.3, -5.85), fg=(255, 70, 150),
          sub="Information is Power", sub_fg=(255, 120, 180),
          name="sign_info", tex_h=288)
# 銘板「記録は真実」
pl = poster_tex([("記録は真実", 0.13, (170, 170, 180)),
                 ("Records are Truth", 0.06, (120, 120, 130))],
                size=(512, 256), bg=(26, 27, 33), fg=(170, 170, 180))
box(S, (1.9, 0.95, 0.08), (-2.4, 3.75, -5.92), M("frame_black", (0, 0, 0)))
quad(S, 1.75, 0.8, (-2.4, 3.75, -5.86),
     tex_mat("plate_truth", pl, emissive=(0.5, 0.5, 0.5), emissive_tex=pl,
             rough=0.8))
# 告知ポスター(横)
an = poster_tex([("告知", 0.10, (70, 65, 70)), ("検閲済", 0.08, (150, 40, 40))],
                size=(224, 288), bg=(160, 152, 140), fg=(70, 65, 70))
quad(S, 0.55, 0.72, (-0.6, 3.5, -5.9), tex_mat("notice", an, rough=0.95),
     rot=R(3, "z"))

# 「分類コード」表(白、奥壁右)
def class_tex(size=(384, 512)):
    img = Image.new("RGB", size, (196, 192, 184))
    d = ImageDraw.Draw(img)
    Wt, Ht = size
    f = _font(int(Ht * 0.075))
    d.text((int(Wt * 0.16), int(Ht * 0.03)), "分類コード", font=f,
           fill=(40, 40, 46))
    f2 = _font(int(Ht * 0.052))
    rows = ["A:政府・行政", "B:軍事・治安", "C:経済・産業",
            "D:社会・文化", "E:その他"]
    y = int(Ht * 0.2)
    for r_ in rows:
        d.text((int(Wt * 0.08), y), r_, font=f2, fill=(45, 45, 52))
        y += int(Ht * 0.14)
    d.rectangle([4, 4, Wt - 5, Ht - 5], outline=(90, 88, 84), width=3)
    return img
ctx = class_tex()
quad(S, 1.15, 1.5, (4.9, 3.55, -5.9),
     tex_mat("classcode", ctx, emissive=(0.45, 0.45, 0.45),
             emissive_tex=ctx, rough=0.9),
     rot=R(-2, "z"))

# 丸時計(奥壁右上)
def clock_tex(size=(256, 256)):
    img = Image.new("RGB", size, (30, 30, 34))
    d = ImageDraw.Draw(img)
    c = size[0] // 2
    d.ellipse([8, 8, size[0] - 8, size[0] - 8], fill=(205, 200, 190),
              outline=(60, 58, 55), width=6)
    for a in range(12):
        th = math.radians(a * 30)
        x1 = c + math.cos(th) * (c - 24)
        y1 = c + math.sin(th) * (c - 24)
        x2 = c + math.cos(th) * (c - 38)
        y2 = c + math.sin(th) * (c - 38)
        d.line([(x1, y1), (x2, y2)], fill=(50, 48, 46), width=5)
    d.line([(c, c), (c + 40, c - 55)], fill=(40, 40, 40), width=7)
    d.line([(c, c), (c - 62, c - 18)], fill=(40, 40, 40), width=5)
    d.ellipse([c - 8, c - 8, c + 8, c + 8], fill=(40, 40, 40))
    return img
ck = clock_tex()
cyl(S, 0.42, 0.08, (4.05, 4.55, -5.88), M("frame_black", (0, 0, 0)),
    rot=R(90, "x"), sections=28)
disc(S, 0.38, (4.05, 4.55, -5.83),
     tex_mat("clock", ck, emissive=(0.4, 0.4, 0.4), emissive_tex=ck))
# discは+Y向きなので壁向き(+z)へ回転し直す
_clock_key = list(S.geometry)[-1]
S.geometry[_clock_key].apply_transform(
    T(4.05, 4.55, -5.83) @ R(90, "x") @ T(-4.05, -4.55, 5.83))

# ---------------------------------------------------------------- 左壁: ドア
box(S, (0.16, 2.7, 1.5), (-5.9, 1.35, -4.2), M("frame_black", (0, 0, 0)))
dt = poster_tex([("立入禁止", 0.09, (255, 80, 100))], size=(320, 576),
                bg=(30, 30, 38), fg=(255, 80, 100))
quad(S, 1.3, 2.5, (-5.8, 1.25, -4.2),
     tex_mat("door_arch", dt, emissive=(0.35, 0.1, 0.14), emissive_tex=dt,
             rough=0.7, metallic=0.4),
     rot=R(90, "y"))
box(S, (0.10, 0.12, 0.3), (-5.8, 2.85, -4.2), M("neon_red", (0, 0, 0)))
# 検閲庁告知(貼り紙、ハンコ付き)
def censor_tex(size=(256, 384)):
    img = Image.new("RGB", size, (185, 178, 165))
    d = ImageDraw.Draw(img)
    Wt, Ht = size
    f = _font(int(Ht * 0.065))
    d.text((int(Wt * 0.10), int(Ht * 0.03)), "検閲庁告知", font=f,
           fill=(55, 52, 50))
    rng = _rnd.Random(9)
    for y in range(int(Ht * 0.2), int(Ht * 0.85), int(Ht * 0.07)):
        d.line([(int(Wt * 0.1), y), (int(Wt * rng.uniform(0.6, 0.9)), y)],
               fill=(95, 90, 86), width=3)
    d.ellipse([int(Wt * 0.62), int(Ht * 0.72), int(Wt * 0.88),
               int(Ht * 0.90)], outline=(170, 40, 40), width=4)
    f2 = _font(int(Ht * 0.05))
    d.text((int(Wt * 0.67), int(Ht * 0.77)), "済", font=f2,
           fill=(170, 40, 40))
    return img
cz = censor_tex()
quad(S, 0.6, 0.9, (-5.86, 2.0, -2.55),
     tex_mat("censor", cz, rough=0.95), rot=R(90, "y") @ R(-3, "z"))
quad(S, 0.5, 0.7, (-5.86, 0.95, -2.7),
     tex_mat("censor2", censor_tex(), rough=0.95),
     rot=R(90, "y") @ R(4, "z"))

# ---------------------------------------------------------------- 中央: 作業机
DX, DZ = 0.6, -0.6
def desk_top_tex(size=(512, 320), seed=15):
    rng = _rnd.Random(seed)
    img = Image.new("RGB", size, (42, 34, 28))
    d = ImageDraw.Draw(img)
    Wt, Ht = size
    for y in range(0, Ht, 14):   # 木目
        d.line([(0, y), (Wt, y + rng.randint(-3, 3))],
               fill=(36, 29, 24), width=2)
    for _ in range(9):           # 散乱書類
        x, y = rng.randint(10, Wt - 90), rng.randint(10, Ht - 70)
        ang = rng.uniform(-0.5, 0.5)
        wpp, hpp = rng.randint(50, 85), rng.randint(65, 95)
        pts = []
        for (ux, uy) in [(-wpp/2, -hpp/2), (wpp/2, -hpp/2), (wpp/2, hpp/2),
                         (-wpp/2, hpp/2)]:
            rx = ux * math.cos(ang) - uy * math.sin(ang)
            ry = ux * math.sin(ang) + uy * math.cos(ang)
            pts.append((x + wpp/2 + rx, y + hpp/2 + ry))
        d.polygon(pts, fill=(168, 160, 148))
        for li in range(4):
            lx0 = pts[0][0] * 0.7 + pts[2][0] * 0.3
            ly0 = pts[0][1] * 0.7 + pts[2][1] * 0.3 + li * 9
            d.line([(lx0, ly0), (lx0 + 34, ly0 + 2)], fill=(90, 85, 80),
                   width=2)
    return img
dt2 = desk_top_tex()
quad(S, 2.6, 1.35, (DX, 0.82, DZ), tex_mat("desk_top", dt2, rough=0.85),
     rot=R(-90, "x"), double=False)
box(S, (2.6, 0.09, 1.35), (DX, 0.77, DZ), M("wood_dark", (0, 0, 0)))
for dx in (-1.15, 1.15):
    for dz in (-0.55, 0.55):
        box(S, (0.09, 0.72, 0.09), (DX + dx, 0.36, DZ + dz),
            M("metal_dark", (0, 0, 0)))
box(S, (0.8, 0.6, 1.1), (DX + 0.85, 0.35, DZ), M("wood_dark", (0, 0, 0)))

# CRT(マゼンタ画面)
box(S, (0.85, 0.7, 0.7), (DX + 0.25, 1.17, DZ - 0.25), M("metal_mid", (0, 0, 0)),
    rot=R(-8, "y"))
stx = screen_tex(size=(224, 168), kind="ui", seed=101, hue=(255, 80, 190))
quad(S, 0.62, 0.5, (DX + 0.20, 1.18, DZ + 0.11),
     tex_mat("crt_pink", stx, emissive=(1.6, 1.6, 1.6), emissive_tex=stx),
     rot=R(-8, "y"))
# キーボード・本・書類(立体)
box(S, (0.5, 0.035, 0.2), (DX - 0.15, 0.85, DZ + 0.42),
    M("frame_black", (0, 0, 0)), rot=R(6, "y"))
for i, (bw, bh, bc) in enumerate([(0.4, 0.07, (0.30, 0.22, 0.18)),
                                  (0.36, 0.06, (0.20, 0.24, 0.30)),
                                  (0.42, 0.08, (0.26, 0.20, 0.26))]):
    box(S, (bw, bh, 0.28), (DX - 1.0, 0.86 + i * 0.07 + 0.03, DZ - 0.3),
        mat(f"book_{i}", bc, rough=0.95), rot=R(4 * (i - 1), "y"))
M("paper", (0.62, 0.59, 0.54), rough=1.0)
for (px, pz, ang) in [(DX - 0.7, DZ + 0.45, 14), (DX + 0.95, DZ + 0.35, -20),
                      (DX - 0.3, DZ - 0.5, 33)]:
    quad(S, 0.28, 0.38, (px, 0.828, pz), M("paper", (0, 0, 0)),
         rot=R(-90, "x") @ R(ang, "z"))

# デスクランプ(緑笠、点灯)
LX, LZ = DX - 0.85, DZ + 0.1
cyl(S, 0.09, 0.04, (LX, 0.85, LZ), M("metal_dark", (0, 0, 0)))
cyl(S, 0.02, 0.5, (LX + 0.08, 1.08, LZ), M("metal_dark", (0, 0, 0)),
    rot=R(-18, "z"))
cyl(S, 0.018, 0.4, (LX + 0.3, 1.32, LZ), M("metal_dark", (0, 0, 0)),
    rot=R(55, "z"))
M("lampshade", (0.12, 0.28, 0.20), rough=0.6, emissive=(0.10, 0.22, 0.15))
cone(S, 0.16, 0.18, (LX + 0.45, 1.28, LZ), M("lampshade", (0, 0, 0)),
     rot=R(25, "z"), sections=18)
sphere(S, 0.06, (LX + 0.48, 1.18, LZ), M("lamp_warm", (0, 0, 0)))

# スツール
cyl(S, 0.26, 0.09, (DX - 0.2, 0.55, DZ + 1.35), M("wood_dark", (0, 0, 0)),
    sections=16)
for a in range(4):
    th = math.radians(a * 90 + 45)
    cyl(S, 0.03, 0.55, (DX - 0.2 + math.cos(th) * 0.16, 0.27,
                        DZ + 1.35 + math.sin(th) * 0.16),
        M("metal_dark", (0, 0, 0)), rot=R(math.degrees(th), "y") @ R(8, "z"),
        sections=8)

# 立ち式端末(机の左)
KX, KZ = -1.9, -1.7
box(S, (0.75, 1.15, 0.6), (KX, 0.575, KZ), M("metal_dark", (0, 0, 0)),
    rot=R(14, "y"))
box(S, (0.7, 0.08, 0.45), (KX + 0.05, 1.2, KZ + 0.18),
    M("frame_black", (0, 0, 0)), rot=R(14, "y") @ R(-16, "x"))
stx = screen_tex(size=(128, 96), kind="ui", seed=111, hue=(255, 90, 180))
quad(S, 0.4, 0.28, (KX - 0.05, 1.5, KZ - 0.1),
     tex_mat("terminal", stx, emissive=(1.4, 1.4, 1.4), emissive_tex=stx),
     rot=R(14, "y") @ R(-10, "x"))
box(S, (0.3, 0.05, 0.08), (KX + 0.28, 0.9, KZ + 0.28),
    M("neon_pink", (0, 0, 0)), rot=R(14, "y"))

# ---------------------------------------------------------------- 下側の什器
# シアンCRTのワゴン(下中央右)
box(S, (1.0, 0.95, 0.75), (2.5, 0.475, 2.6), M("metal_dark", (0, 0, 0)),
    rot=R(-6, "y"))
box(S, (0.8, 0.65, 0.65), (2.5, 1.3, 2.6), M("metal_mid", (0, 0, 0)),
    rot=R(-6, "y"))
stx = screen_tex(size=(192, 144), kind="ui", seed=121, hue=(70, 210, 230))
quad(S, 0.58, 0.46, (2.44, 1.32, 2.95),
     tex_mat("crt_cyan", stx, emissive=(1.5, 1.5, 1.5), emissive_tex=stx),
     rot=R(-6, "y"))
# 布掛けの台(左下)
M("cover_cloth", (0.30, 0.30, 0.34), rough=1.0)
box(S, (1.5, 0.85, 1.0), (-4.75, 0.45, 3.4), M("cover_cloth", (0, 0, 0)))
box(S, (1.62, 0.15, 1.12), (-4.75, 0.86, 3.4), M("cover_cloth", (0, 0, 0)),
    rot=R(2, "y"))
box(S, (0.9, 0.3, 0.6), (-4.7, 1.08, 3.4), M("cover_cloth", (0, 0, 0)),
    rot=R(-4, "y"))
# 書類箱の台車(左下)
box(S, (1.1, 0.12, 0.7), (-2.9, 0.25, 4.5), M("metal_mid", (0, 0, 0)),
    rot=R(10, "y"))
for dx in (-0.42, 0.42):
    cyl(S, 0.09, 0.07, (-2.9 + dx, 0.09, 4.62), M("frame_black", (0, 0, 0)),
        rot=R(90, "z"), sections=12)
crate(S, (-3.05, 0.31, 4.45), size=(0.6, 0.4, 0.5), rot_y=10,
      material=M("wood_dark", (0, 0, 0)))
crate(S, (-2.55, 0.31, 4.6), size=(0.5, 0.35, 0.45), rot_y=24,
      material=M("wood_dark", (0, 0, 0)))
cyl(S, 0.045, 0.8, (-2.35, 0.65, 4.3), M("pipe", (0, 0, 0)),
    rot=R(12, "z"))                                   # 押しハンドル
# 積まれたファイル箱
for i, (bx_, bz_, ry) in enumerate([(-0.9, 4.7, 6), (-0.85, 4.72, -12),
                                    (-1.6, 4.5, 20)]):
    box(S, (0.62, 0.35, 0.45), (bx_, 0.18 + (i % 2) * 0.36, bz_),
        M("wood_dark", (0, 0, 0)) if i != 1 else M("metal_rust", (0, 0, 0)),
        rot=R(ry, "y"))
# バケツ
cyl(S, 0.16, 0.3, (-5.3, 0.15, -0.9), M("metal_mid", (0, 0, 0)), sections=14)
cyl(S, 0.13, 0.02, (-5.3, 0.3, -0.9), M("frame_black", (0, 0, 0)),
    sections=14)

# 机+ランプ(右下)+本
box(S, (1.4, 0.75, 0.8), (4.3, 0.4, 4.3), M("wood_dark", (0, 0, 0)))
cyl(S, 0.02, 0.45, (4.6, 1.0, 4.2), M("metal_dark", (0, 0, 0)),
    rot=R(14, "z"))
M("lampshade2", (0.28, 0.22, 0.12), rough=0.6, emissive=(0.35, 0.25, 0.10))
cone(S, 0.15, 0.15, (4.5, 1.22, 4.2), M("lampshade2", (0, 0, 0)),
     rot=R(18, "z"), sections=16)
sphere(S, 0.05, (4.47, 1.13, 4.2), M("lamp_warm", (0, 0, 0)))
box(S, (0.4, 0.08, 0.3), (3.95, 0.82, 4.4), mat("book_r", (0.28, 0.22, 0.20),
                                                rough=0.95), rot=R(-10, "y"))
bottle = mat("inkpot", (0.2, 0.25, 0.3), rough=0.4)
cyl(S, 0.05, 0.1, (4.15, 0.83, 4.05), bottle, sections=10)

# マンホール(右下)
def grate_tex(size=(256, 256)):
    img = Image.new("RGB", size, (12, 13, 14))
    d = ImageDraw.Draw(img)
    c = size[0] // 2
    for r in (112, 86, 60, 34):
        d.ellipse([c - r, c - r, c + r, c + r], outline=(42, 44, 48),
                  width=9)
    for a in range(0, 360, 30):
        th = math.radians(a)
        d.line([(c + math.cos(th) * 30, c + math.sin(th) * 30),
                (c + math.cos(th) * 112, c + math.sin(th) * 112)],
               fill=(36, 38, 42), width=5)
    return img
disc(S, 0.6, (2.9, 0.012, 4.4), tex_mat("manhole", grate_tex(),
                                        metallic=0.6, rough=0.6))

# ゴミ箱
cyl(S, 0.2, 0.5, (1.4, 0.25, 4.9), M("metal_rust", (0, 0, 0)), sections=14)

# 赤色灯(右壁の棚上)
box(S, (0.14, 0.18, 0.14), (5.6, 3.6, 3.4), M("neon_red", (0, 0, 0)))
box(S, (0.2, 0.06, 0.2), (5.6, 3.72, 3.4), M("frame_black", (0, 0, 0)))

out = os.path.join(os.path.dirname(__file__), "records_room.glb")
size = export(S, out)
print(f"OK records_room.glb {size/1e6:.2f} MB, geoms={len(S.geometry)}")
