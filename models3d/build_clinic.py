# -*- coding: utf-8 -*-
"""
診療所 (Back-alley Clinic) — 背景画像3の3D再現。

画像分析メモ:
  - 薄暗い屋内。シアンネオン「診療所」(左壁上部)。
  - 左: 金属フレームの診察ベッド(マットレス+枕)、枕元の机に発光タブレット、
    裸電球(暖色)が上から吊り下がる、赤く光る額縁、点滴スタンド、
    ベッド周りに暗いティール色のカーテン(レール付き)。
  - 奥左: 瓶の並ぶ薬品棚2台、ポスター(赤/白)、ティールのCRT計算機ワゴン。
  - 奥右: 引き出しキャビネット+瓶、金属シンク+蛇口、ピンク発光の医療十字、
    ティールの生体モニター、「注意」黄色看板、隅に赤色回転灯。
  - 右: 私物預かりロッカー(キーパッド「0427」発光)、パイプ。
  - 中央: 二つ折りの衝立(ティール)、瓶を載せたワゴン、救急箱ワゴン、丸椅子。
  - 右下: 机+CRT(心電図波形)、瓶の列。左下: 「第七区画」の刻印、ドラム缶。
  - 床: 濃い汚れ・水たまり・丸い排水溝2つ。ピンク/シアンの反射。
"""
import math
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tools"))

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import trimesh

from kit import (M, std_mats, mat, tex_mat, box, cyl, cone, sphere, quad,
                 disc, T, R, neon_sign, screen_tex, tile_floor_tex, wall_tex,
                 poster_tex, lamp, barrel, crate, pipe_run, export, _font)

std_mats()
S = trimesh.Scene()

ROOM = 11.0
HW = 4.8
HR = ROOM / 2

# ---------------------------------------------------------------- 床と壁
wet = [
    (0.30, 0.45, 0.18, (20, 60, 70)),     # 中央の大きな黒ずみ
    (0.75, 0.30, 0.12, (200, 40, 110)),   # 十字ネオンのピンク反射
    (0.20, 0.25, 0.10, (30, 90, 100)),    # ベッド脇ティール
    (0.60, 0.70, 0.14, (25, 70, 80)),
    (0.88, 0.55, 0.08, (200, 30, 40)),    # 赤色灯
]
floor_m = tex_mat("floor", tile_floor_tex(tile=128, base=(15, 17, 19),
                                          groove=(8, 9, 10), seed=17,
                                          wet_spots=wet),
                  rough=0.4, metallic=0.05)
quad(S, ROOM, ROOM, (0, 0, 0), floor_m, rot=R(-90, "x"),
     uv=np.array([[0, 0], [1, 0], [1, 1], [0, 1]]) * 3.0, double=False)
box(S, (ROOM, 0.3, ROOM), (0, -0.16, 0), M("concrete", (0, 0, 0)))

wall_m = tex_mat("wall", wall_tex(base=(15, 17, 20), seed=19), rough=0.85,
                 metallic=0.25)
wuv = np.array([[0, 0], [2.6, 0], [2.6, 1.2], [0, 1.2]])
quad(S, ROOM, HW, (0, HW / 2, -HR), wall_m, uv=wuv)
quad(S, ROOM, HW, (-HR, HW / 2, 0), wall_m, rot=R(90, "y"), uv=wuv)
quad(S, ROOM, HW, (HR, HW / 2, 0), wall_m, rot=R(-90, "y"), uv=wuv)
for (p, vert) in [((0, 0.12, -HR + 0.06), False), ((-HR + 0.06, 0.12, 0), True),
                  ((HR - 0.06, 0.12, 0), True)]:
    box(S, (0.12, 0.24, ROOM) if vert else (ROOM, 0.24, 0.12), p,
        M("metal_dark", (0, 0, 0)))

# 壁上部の配管
pipe_run(S, (-HR, 4.5, -HR + 0.25), (HR, 4.5, -HR + 0.25), r=0.06)
pipe_run(S, (-HR + 0.25, 4.3, -HR), (-HR + 0.25, 4.3, HR), r=0.05)
pipe_run(S, (HR - 0.3, 0.3, -1.2), (HR - 0.3, 4.4, -1.2), r=0.07)
pipe_run(S, (2.4, 4.6, -HR + 0.2), (2.4, 2.9, -HR + 0.2), r=0.045,
         joints=False)

# ---------------------------------------------------------------- 左壁: ベッド区画
# シアンネオン「診療所」
neon_sign(S, "診療所", 2.5, 0.85, (-5.35, 4.0, -2.2), rot=R(90, "y"),
          fg=(70, 230, 220), name="sign_clinic", tex_h=256)

# 診察ベッド(金属フレーム+マットレス+枕)
BX, BZ = -4.35, -3.1
M("mattress", (0.23, 0.30, 0.30), rough=0.95)
M("sheet", (0.30, 0.38, 0.38), rough=0.95)
box(S, (1.15, 0.16, 2.5), (BX, 0.58, BZ), M("mattress", (0, 0, 0)))
box(S, (1.05, 0.10, 0.9), (BX, 0.68, BZ + 0.6), M("sheet", (0, 0, 0)),
    rot=R(2, "y"))
box(S, (0.6, 0.12, 0.35), (BX, 0.70, BZ - 0.95), M("sheet", (0, 0, 0)),
    rot=R(-6, "y"))                                             # 枕
box(S, (1.2, 0.08, 2.6), (BX, 0.46, BZ), M("metal_mid", (0, 0, 0)))
for dx in (-0.52, 0.52):
    for dz in (-1.2, 1.2):
        cyl(S, 0.035, 0.45, (BX + dx, 0.23, BZ + dz),
            M("frame_black", (0, 0, 0)))
box(S, (1.2, 0.5, 0.07), (BX, 0.85, BZ - 1.28), M("metal_mid", (0, 0, 0)))
box(S, (1.2, 0.35, 0.07), (BX, 0.75, BZ + 1.28), M("metal_mid", (0, 0, 0)))

# 枕元の机+発光タブレット
box(S, (0.9, 0.75, 0.65), (-4.75, 0.375, -4.75), M("metal_dark", (0, 0, 0)))
stx = screen_tex(size=(160, 120), kind="ui", seed=31, hue=(60, 220, 210))
quad(S, 0.42, 0.30, (-4.6, 0.83, -4.7),
     tex_mat("tablet", stx, emissive=(1.4, 1.4, 1.4), emissive_tex=stx),
     rot=R(-90 + 24, "x") @ R(8, "z"))
box(S, (0.3, 0.06, 0.2), (-5.05, 0.78, -4.9), M("metal_rust", (0, 0, 0)))

# 吊り下げ裸電球(暖色)+コード
pipe_run(S, (BX, 4.79, BZ + 0.3), (BX, 3.1, BZ + 0.3), r=0.015, joints=False)
cone(S, 0.16, 0.14, (BX, 3.05, BZ + 0.3), M("metal_dark", (0, 0, 0)),
     rot=R(180, "x"), sections=16)
sphere(S, 0.09, (BX, 2.92, BZ + 0.3), M("lamp_warm", (0, 0, 0)))

# 赤く光る額縁(ベッド上の壁)
box(S, (0.10, 0.55, 0.75), (-5.42, 2.45, -3.3), M("frame_black", (0, 0, 0)))
stx2 = screen_tex(size=(128, 96), kind="static", seed=33, hue=(255, 60, 60))
quad(S, 0.6, 0.42, (-5.35, 2.45, -3.3),
     tex_mat("red_frame", stx2, emissive=(0.9, 0.3, 0.3), emissive_tex=stx2),
     rot=R(90, "y"))

# 点滴スタンド(ポール+フック+バッグ+キャスター)
IX, IZ = -3.35, -2.2
cyl(S, 0.025, 2.1, (IX, 1.05, IZ), M("pipe", (0, 0, 0)))
for a in (0, 90, 180, 270):
    th = math.radians(a)
    cyl(S, 0.015, 0.4, (IX + math.cos(th) * 0.14, 0.06,
                        IZ + math.sin(th) * 0.14),
        M("pipe", (0, 0, 0)), rot=R(a, "y") @ R(80, "z"), sections=8)
pipe_run(S, (IX - 0.22, 2.12, IZ), (IX + 0.22, 2.12, IZ), r=0.015,
         joints=False)
M("iv_bag", (0.75, 0.55, 0.45), rough=0.4, emissive=(0.25, 0.12, 0.08))
box(S, (0.16, 0.3, 0.07), (IX - 0.2, 1.92, IZ), M("iv_bag", (0, 0, 0)))
pipe_run(S, (IX - 0.2, 1.77, IZ), (IX - 0.5, 0.9, IZ - 0.5), r=0.008,
         joints=False)

# カーテンレール+カーテン(ティール、たわみ表現で数枚)
pipe_run(S, (-5.4, 2.75, -1.6), (-2.4, 2.75, -1.6), r=0.02)
pipe_run(S, (-2.4, 2.75, -1.6), (-2.4, 2.75, -4.9), r=0.02, joints=False)
M("curtain", (0.13, 0.30, 0.30), rough=1.0)
rng_c = [(-5.1, -1.62, 4), (-4.6, -1.58, -6), (-4.15, -1.62, 3),
         (-2.42, -2.3, 5), (-2.38, -2.9, -4), (-2.42, -4.2, 6)]
for (cx, cz, ang) in rng_c:
    vert = abs(cx + 2.4) < 0.1
    quad(S, 0.5, 2.2, (cx, 1.62, cz), M("curtain", (0, 0, 0)),
         rot=(R(90, "y") if vert else R(0, "y")) @ R(ang, "z"))

# ---------------------------------------------------------------- 奥壁: 棚と機器
def bottle_row(x0, x1, y, z, n, seed=1):
    import random
    rng = random.Random(seed)
    cols = [(0.35, 0.45, 0.40), (0.45, 0.30, 0.20), (0.25, 0.35, 0.45),
            (0.40, 0.40, 0.30)]
    for i in range(n):
        t = i / max(1, n - 1)
        x = x0 + (x1 - x0) * t + rng.uniform(-0.03, 0.03)
        r = rng.uniform(0.035, 0.06)
        h = rng.uniform(0.14, 0.30)
        c = rng.choice(cols)
        nm = f"bottle_{seed}_{i}"
        cyl(S, r, h, (x, y + h / 2, z + rng.uniform(-0.05, 0.05)),
            mat(nm, c, metallic=0.1, rough=0.3), sections=10)

# 薬品棚2台
for (sx, seed) in [(-2.6, 41), (-1.15, 42)]:
    box(S, (1.3, 2.6, 0.55), (sx, 1.3, -5.15), M("metal_dark", (0, 0, 0)))
    for shelf_y in (0.7, 1.35, 2.0):
        box(S, (1.2, 0.05, 0.48), (sx, shelf_y, -5.12),
            M("wood_dark", (0, 0, 0)))
        bottle_row(sx - 0.5, sx + 0.5, shelf_y + 0.03, -5.12, 6,
                   seed=seed + int(shelf_y * 10))
# ポスター(赤/白)
pr = poster_tex([("DADO", 0.10, (230, 60, 60)), ("!", 0.14, (230, 60, 60))],
                size=(192, 256), bg=(40, 18, 18), fg=(230, 60, 60))
quad(S, 0.5, 0.68, (-0.15, 3.4, -5.42), tex_mat("poster_r", pr, rough=0.9),
     rot=R(-3, "z"))
pw = poster_tex([("LATE", 0.09, (60, 60, 66)), ("通知", 0.11, (60, 60, 66))],
                size=(192, 256), bg=(170, 165, 155), fg=(60, 60, 66))
quad(S, 0.45, 0.6, (0.5, 3.1, -5.42), tex_mat("poster_w", pw, rough=0.9),
     rot=R(4, "z"))

# CRT計算機ワゴン(ティール画面)
box(S, (1.0, 1.1, 0.7), (0.35, 0.55, -4.95), M("metal_dark", (0, 0, 0)))
box(S, (0.75, 0.6, 0.6), (0.35, 1.4, -5.0), M("metal_mid", (0, 0, 0)))
stx = screen_tex(size=(192, 144), kind="ui", seed=51, hue=(70, 230, 215))
quad(S, 0.58, 0.45, (0.35, 1.42, -4.69),
     tex_mat("crt_main", stx, emissive=(1.5, 1.5, 1.5), emissive_tex=stx))
box(S, (0.5, 0.08, 0.3), (0.35, 1.05, -4.7), M("frame_black", (0, 0, 0)),
    rot=R(6, "y"))
for dx in (-0.4, 0.4):
    cyl(S, 0.09, 0.1, (0.35 + dx, 0.09, -4.75), M("frame_black", (0, 0, 0)),
        rot=R(90, "z"), sections=12)

# 引き出しキャビネット+瓶(奥壁右)
box(S, (2.6, 1.15, 0.7), (2.9, 0.575, -5.05), M("metal_mid", (0, 0, 0)))
for row in range(3):
    for col in range(3):
        box(S, (0.72, 0.28, 0.03),
            (2.15 + col * 0.78, 0.28 + row * 0.35, -4.68),
            M("metal_dark", (0, 0, 0)))
        box(S, (0.2, 0.04, 0.04), (2.15 + col * 0.78, 0.28 + row * 0.35,
                                   -4.65), M("frame_black", (0, 0, 0)))
bottle_row(1.8, 4.0, 1.15, -5.0, 9, seed=61)

# シンク(金属、蛇口付き)
box(S, (1.2, 1.0, 0.75), (4.55, 0.5, -5.0), M("metal_mid", (0, 0, 0)))
box(S, (1.0, 0.12, 0.6), (4.55, 1.0, -5.0), M("metal_dark", (0, 0, 0)))
box(S, (0.8, 0.06, 0.45), (4.55, 1.04, -5.0), M("frame_black", (0, 0, 0)))
pipe_run(S, (4.35, 1.05, -5.25), (4.35, 1.45, -5.25), r=0.025, joints=False)
pipe_run(S, (4.35, 1.45, -5.25), (4.55, 1.45, -4.95), r=0.02, joints=False)
pipe_run(S, (4.75, 0.15, -4.9), (4.75, 0.5, -4.9), r=0.03, joints=False)

# ピンク発光の医療十字(奥壁右上)
box(S, (1.0, 1.0, 0.10), (3.5, 3.15, -5.42), M("frame_black", (0, 0, 0)))
def cross_tex(size=(256, 256)):
    img = Image.new("RGB", size, (30, 12, 22))
    d = ImageDraw.Draw(img)
    Wt = size[0]
    a, b = int(Wt * 0.36), int(Wt * 0.64)
    d.rectangle([a, int(Wt * 0.14), b, int(Wt * 0.86)], fill=(255, 70, 140))
    d.rectangle([int(Wt * 0.14), a, int(Wt * 0.86), b], fill=(255, 70, 140))
    return img.filter(ImageFilter.GaussianBlur(3))
ct = cross_tex()
quad(S, 0.85, 0.85, (3.5, 3.15, -5.36),
     tex_mat("med_cross", ct, emissive=(1.8, 1.8, 1.8), emissive_tex=ct))

# 生体モニター(ティール、奥壁右)
box(S, (0.8, 0.55, 0.10), (4.55, 3.1, -5.42), M("metal_dark", (0, 0, 0)))
stx = screen_tex(size=(192, 128), kind="wave", seed=71, hue=(70, 230, 215))
quad(S, 0.68, 0.44, (4.55, 3.1, -5.36),
     tex_mat("vitals", stx, emissive=(1.5, 1.5, 1.5), emissive_tex=stx))

# 「注意」黄色看板+作業灯
cs = poster_tex([("注意", 0.22, (40, 36, 20))], size=(192, 160),
                bg=(200, 170, 40), fg=(40, 36, 20))
quad(S, 0.5, 0.42, (5.05, 2.35, -5.42), tex_mat("caution", cs, rough=0.9),
     rot=R(-4, "z"))

# ---------------------------------------------------------------- 右壁
# 赤色回転灯(右壁上部)
box(S, (0.18, 0.14, 0.4), (5.38, 3.9, -3.2), M("frame_black", (0, 0, 0)))
box(S, (0.12, 0.20, 0.24), (5.34, 4.06, -3.2), M("neon_red", (0, 0, 0)))

# 私物預かりロッカー(キーパッド0427)
box(S, (0.75, 1.9, 1.1), (5.05, 0.95, -3.9), M("metal_rust", (0, 0, 0)))
box(S, (0.06, 1.7, 0.95), (4.65, 0.95, -3.9), M("metal_dark", (0, 0, 0)))
lk = poster_tex([("私物預かり", 0.075, (180, 150, 120)),
                 ("PERSONAL", 0.05, (150, 130, 110)),
                 ("EFFECTS", 0.05, (150, 130, 110))],
                size=(256, 384), bg=(52, 42, 34), fg=(180, 150, 120))
quad(S, 0.9, 1.5, (4.61, 1.05, -3.9), tex_mat("locker", lk, rough=0.85),
     rot=R(-90, "y"))
def keypad_tex(size=(128, 96)):
    img = Image.new("RGB", size, (12, 10, 10))
    d = ImageDraw.Draw(img)
    f = _font(int(size[1] * 0.5))
    d.text((int(size[0] * 0.12), int(size[1] * 0.2)), "0427", font=f,
           fill=(255, 90, 60))
    d.rectangle([2, 2, size[0] - 3, size[1] - 3], outline=(120, 50, 40))
    return img
kt = keypad_tex()
quad(S, 0.28, 0.20, (4.60, 1.75, -3.55),
     tex_mat("keypad", kt, emissive=(1.6, 1.6, 1.6), emissive_tex=kt),
     rot=R(-90, "y"))
cyl(S, 0.02, 0.22, (4.62, 1.3, -4.25), M("pipe", (0, 0, 0)), rot=R(90, "x"))

# ---------------------------------------------------------------- 中央
# 二つ折りの衝立(ティール)
M("screen_cloth", (0.14, 0.29, 0.29), rough=1.0)
for (px, pz, ang) in [(0.15, 1.0, 20), (1.05, 1.25, -25)]:
    box(S, (0.06, 1.8, 0.06), (px - 0.48 * math.cos(math.radians(ang)),
                               0.9, pz + 0.48 * math.sin(math.radians(ang))),
        M("pipe", (0, 0, 0)), rot=R(ang, "y"))
    box(S, (0.06, 1.8, 0.06), (px + 0.48 * math.cos(math.radians(ang)),
                               0.9, pz - 0.48 * math.sin(math.radians(ang))),
        M("pipe", (0, 0, 0)), rot=R(ang, "y"))
    quad(S, 0.9, 1.5, (px, 0.95, pz), M("screen_cloth", (0, 0, 0)),
         rot=R(ang, "y"))
    pipe_run(S, (px - 0.48 * math.cos(math.radians(ang)), 1.82,
                 pz + 0.48 * math.sin(math.radians(ang))),
             (px + 0.48 * math.cos(math.radians(ang)), 1.82,
              pz - 0.48 * math.sin(math.radians(ang))), r=0.02, joints=False)
# タオル掛け
box(S, (0.3, 0.4, 0.04), (0.5, 1.55, 1.12), M("sheet", (0, 0, 0)),
    rot=R(20, "y") @ R(4, "x"))

# 瓶ワゴン
box(S, (0.9, 0.06, 0.6), (1.5, 0.85, 0.1), M("metal_mid", (0, 0, 0)))
box(S, (0.9, 0.06, 0.6), (1.5, 0.4, 0.1), M("metal_mid", (0, 0, 0)))
for dx in (-0.4, 0.4):
    for dz in (-0.25, 0.25):
        cyl(S, 0.02, 0.85, (1.5 + dx, 0.45, 0.1 + dz),
            M("pipe", (0, 0, 0)), sections=8)
        cyl(S, 0.05, 0.06, (1.5 + dx, 0.03, 0.1 + dz),
            M("frame_black", (0, 0, 0)), rot=R(90, "z"), sections=10)
bottle_row(1.15, 1.85, 0.88, 0.1, 5, seed=81)

# 救急箱ワゴン(白箱+赤十字)
box(S, (0.8, 0.7, 0.55), (-0.7, 0.35, 2.4), M("metal_dark", (0, 0, 0)))
M("firstaid", (0.75, 0.72, 0.68), rough=0.6)
box(S, (0.5, 0.35, 0.4), (-0.7, 0.88, 2.4), M("firstaid", (0, 0, 0)),
    rot=R(-8, "y"))
box(S, (0.2, 0.06, 0.02), (-0.7, 0.9, 2.61), M("neon_red", (0, 0, 0)),
    rot=R(-8, "y"))
box(S, (0.06, 0.2, 0.02), (-0.7, 0.9, 2.61), M("neon_red", (0, 0, 0)),
    rot=R(-8, "y"))

# 丸椅子(キャスター付き)
cyl(S, 0.24, 0.07, (-1.85, 0.62, 0.5), M("cloth_dark", (0, 0, 0)),
    sections=18)
cyl(S, 0.035, 0.55, (-1.85, 0.3, 0.5), M("pipe", (0, 0, 0)))
for a in range(4):
    th = math.radians(a * 90 + 45)
    cyl(S, 0.015, 0.3, (-1.85 + math.cos(th) * 0.14, 0.08,
                        0.5 + math.sin(th) * 0.14),
        M("pipe", (0, 0, 0)), rot=R(math.degrees(th), "y") @ R(75, "z"),
        sections=8)

# ---------------------------------------------------------------- 右下
# 机+CRT(心電図)
box(S, (1.5, 0.8, 0.9), (4.3, 0.4, 3.9), M("metal_dark", (0, 0, 0)))
box(S, (0.7, 0.55, 0.55), (4.15, 1.1, 3.85), M("metal_mid", (0, 0, 0)))
stx = screen_tex(size=(192, 144), kind="wave", seed=91, hue=(70, 230, 215))
quad(S, 0.55, 0.42, (3.87, 1.12, 3.85),
     tex_mat("crt_ecg", stx, emissive=(1.5, 1.5, 1.5), emissive_tex=stx),
     rot=R(-90, "y"))
bottle_row(4.9, 5.3, 0.8, 3.7, 3, seed=95)
crate(S, (5.0, 0, 4.8), size=(0.65, 0.5, 0.65), rot_y=12)
bottle_row(4.4, 5.2, 0.5, 4.85, 4, seed=97)

# ---------------------------------------------------------------- 左下
# 「第七区画」刻印ブロック
blk = poster_tex([("第七区画", 0.16, (60, 160, 160))], size=(384, 192),
                 bg=(18, 22, 26), fg=(60, 160, 160))
box(S, (1.6, 0.75, 0.5), (-4.6, 0.375, 4.9), M("concrete", (0, 0, 0)))
quad(S, 1.4, 0.55, (-4.6, 0.4, 4.63),
     tex_mat("dist7", blk, emissive=(0.5, 0.5, 0.5), emissive_tex=blk,
             rough=0.9))
barrel(S, (-4.95, 0, 3.6))
crate(S, (-3.6, 0, 4.85), size=(0.7, 0.55, 0.7), rot_y=-9)

# ---------------------------------------------------------------- 排水溝2つ
def grate_tex(size=(256, 256)):
    img = Image.new("RGB", size, (10, 11, 12))
    d = ImageDraw.Draw(img)
    c = size[0] // 2
    for r in (110, 84, 58, 32):
        d.ellipse([c - r, c - r, c + r, c + r], outline=(38, 40, 44), width=8)
    d.ellipse([c - 118, c - 118, c + 118, c + 118], outline=(50, 52, 56),
              width=6)
    return img
gt = grate_tex()
for (gx, gz) in [(0.1, -0.9), (-1.7, 3.0)]:
    disc(S, 0.55, (gx, 0.012, gz),
         tex_mat("grate", gt, metallic=0.6, rough=0.6))

out = os.path.join(os.path.dirname(__file__), "clinic.glb")
size = export(S, out)
print(f"OK clinic.glb {size/1e6:.2f} MB, geoms={len(S.geometry)}")
