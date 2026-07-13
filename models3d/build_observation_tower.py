# -*- coding: utf-8 -*-
"""
観測塔 (Observation Tower / 検問所) — 背景画像1の3D再現。

画像分析メモ:
  - 等角視点の屋内広場。濡れたタイル床にネオン反射(ピンク/青)。
  - 奥中央: ピンクネオン「観測塔 / OBSERVATION TOWER」+ 金属ドア「立入禁止
    AUTHORIZED ONLY」+ 赤色灯。ドア両脇に大型スピーカー、壁上部にメガホン。
  - 奥壁右: サーバーラック4本(LED点滅)。
  - 左壁: 青ネオン「思想は監視されている」、監視モニター壁(8画面)、
    制御デスク+キーボード+椅子、B2-07ドア、階段+手すり、サーバーラック。
  - 右壁: プロパガンダ看板「真実は危険だ/正しさを信じろ」+目のグラフィック
    +「国家があなたを守る」、「違反者リスト」顔写真ボード、ドア2枚(赤色灯)、
    縦看板「報告せよ」、有刺鉄線フェンス。
  - 中央: 検問。ネオン立て看板「観測中 CHECKPOINT」、警告ストライプの
    バリケード2基、遮断バー付きゲート機、ピンク三連灯ポスト、
    床の円形スキャナーパッド(同心円ピンク発光)、赤色灯ポール。
  - 右下: 大型パラボラアンテナ+ケーブル。左下: レバー付き制御台、
    A型看板「黙れ SILENCE」、木箱、ドラム缶、赤ランプポール、手すり。
"""
import math
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tools"))

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import trimesh

from kit import (M, std_mats, mat, tex_mat, box, cyl, cone, sphere, quad,
                 T, R, neon_sign, screen_tex, led_panel_tex, tile_floor_tex,
                 wall_tex, stripe_tex, poster_tex, mugshot_tex, lamp, barrel,
                 crate, pipe_run, fence_chainlink, decay_scatter, export, _font)

std_mats()
S = trimesh.Scene()

ROOM = 12.0
H_WALL = 5.5

# ---------------------------------------------------------------- 床と壁
wet = [
    (0.50, 0.10, 0.16, (255, 40, 130)),   # 観測塔ドア前のピンク反射
    (0.56, 0.58, 0.13, (255, 50, 140)),   # 検問ネオンの反射
    (0.16, 0.35, 0.12, (40, 90, 255)),    # モニター壁の青反射
    (0.78, 0.68, 0.10, (255, 60, 150)),   # スキャナーパッド周辺
    (0.85, 0.25, 0.08, (255, 40, 60)),    # 右壁赤色灯
    (0.30, 0.80, 0.08, (255, 30, 40)),    # 左下赤ランプ
]
floor_m = tex_mat("floor", tile_floor_tex(wet_spots=wet), rough=0.35,
                  metallic=0.05)
quad(S, ROOM, ROOM, (0, 0, 0), floor_m, rot=R(-90, "x"),
     uv=np.array([[0, 0], [1, 0], [1, 1], [0, 1]]) * 4.0, double=False)
# 床下の暗い台座(側面の見切り)
box(S, (ROOM, 0.3, ROOM), (0, -0.16, 0), M("concrete", (0, 0, 0)))

wall_m = tex_mat("wall", wall_tex(), rough=0.8, metallic=0.3)
wuv = np.array([[0, 0], [3, 0], [3, 1.4], [0, 1.4]])
quad(S, ROOM, H_WALL, (0, H_WALL / 2, -ROOM / 2), wall_m, uv=wuv)          # 奥
quad(S, ROOM, H_WALL, (-ROOM / 2, H_WALL / 2, 0), wall_m, rot=R(90, "y"),
     uv=wuv)                                                               # 左
quad(S, ROOM, H_WALL, (ROOM / 2, H_WALL / 2, 0), wall_m, rot=R(-90, "y"),
     uv=wuv)                                                               # 右
# 壁の巾木と天端梁
for (p, r) in [((0, 0.15, -5.93), None), ((-5.93, 0.15, 0), R(90, "y")),
               ((5.93, 0.15, 0), R(90, "y"))]:
    box(S, (ROOM, 0.3, 0.14) if r is None else (0.14, 0.3, ROOM),
        p, M("metal_dark", (0, 0, 0)))
for (p, r) in [((0, H_WALL - 0.15, -5.9), None),
               ((-5.9, H_WALL - 0.15, 0), R(90, "y")),
               ((5.9, H_WALL - 0.15, 0), R(90, "y"))]:
    box(S, (ROOM, 0.3, 0.2) if r is None else (0.2, 0.3, ROOM),
        p, M("metal_mid", (0, 0, 0)))

# ---------------------------------------------------------------- 奥壁: 観測塔ドア
# ドア枠+両開き金属ドア
box(S, (2.3, 3.2, 0.18), (0, 1.6, -5.90), M("frame_black", (0, 0, 0)))
door_tex = poster_tex(
    [("", 0.02, (0, 0, 0)), ("立入禁止", 0.085, (255, 70, 140)),
     ("AUTHORIZED ONLY", 0.035, (255, 90, 150))],
    size=(512, 768), bg=(28, 26, 34), fg=(120, 115, 130))
door_m = tex_mat("door_main", door_tex, rough=0.6, metallic=0.5,
                 emissive=(0.25, 0.05, 0.12), emissive_tex=door_tex)
for sx in (-0.5, 0.5):
    quad(S, 0.98, 3.0, (sx, 1.5, -5.80), door_m)
    box(S, (0.06, 3.0, 0.06), (sx * 2 - (0.03 if sx > 0 else -0.03),
                               1.5, -5.82), M("metal_mid", (0, 0, 0)))
cyl(S, 0.02, 0.5, (0, 1.45, -5.77), M("pipe", (0, 0, 0)), rot=R(90, "z"))
# 赤色灯(回転灯)
box(S, (0.5, 0.22, 0.18), (0, 3.45, -5.86), M("frame_black", (0, 0, 0)))
box(S, (0.34, 0.14, 0.12), (0, 3.45, -5.80), M("neon_red", (0, 0, 0)))
# メインネオン「観測塔」(アーチ状: 中央+両翼を少し傾ける)
neon_sign(S, "観測塔", 2.6, 1.05, (0, 4.35, -5.80),
          fg=(255, 60, 150), sub="OBSERVATION TOWER",
          sub_fg=(255, 120, 180), name="sign_tower", tex_h=320)
M("neon_pink_dim", (0.45, 0.12, 0.28), emissive=(0.45, 0.07, 0.25),
  rough=0.5)
for (sx, ang) in [(-1.95, 14), (1.95, -14)]:
    box(S, (1.1, 0.95, 0.10), (sx, 4.30, -5.83), M("frame_black", (0, 0, 0)),
        rot=R(ang, "y"))
    box(S, (0.9, 0.75, 0.04), (sx, 4.30, -5.78),
        M("neon_pink_dim", (0, 0, 0)), rot=R(ang, "y"))

# 大型スピーカー(ドア両脇、コーン2連)
for sx in (-2.35, 2.35):
    box(S, (1.05, 1.75, 0.55), (sx, 2.55, -5.60), M("metal_dark", (0, 0, 0)))
    for dy in (0.42, -0.42):
        cyl(S, 0.34, 0.10, (sx, 2.55 + dy, -5.32), M("frame_black", (0, 0, 0)),
            rot=R(90, "x"))
        cone(S, 0.28, 0.16, (sx, 2.55 + dy, -5.34), M("metal_mid", (0, 0, 0)),
             rot=R(-90, "x"), sections=20)
# メガホン型拡声器(壁上部に外向き)
for (sx, ang) in [(-1.5, 25), (2.0, -20), (3.4, -35)]:
    cyl(S, 0.03, 0.55, (sx, 5.25, -5.75), M("pipe", (0, 0, 0)))
    cone(S, 0.20, 0.45, (sx, 5.05, -5.45),
         M("frame_black", (0, 0, 0)), rot=R(ang, "y") @ R(-65, "x"),
         sections=18)

# 監視カメラ(奥壁、検問を見下ろす)
for (sx, yaw) in [(-3.6, 25), (1.4, -15)]:
    box(S, (0.10, 0.30, 0.10), (sx, 4.65, -5.82), M("pipe", (0, 0, 0)))
    b = box(S, (0.16, 0.16, 0.42), (sx, 4.50, -5.65),
            M("metal_dark", (0, 0, 0)), rot=R(yaw, "y") @ R(-25, "x"))
    box(S, (0.05, 0.05, 0.05), (sx, 4.42, -5.48), M("neon_red", (0, 0, 0)))

# サーバーラック4本(奥壁右)
led_m = tex_mat("rack_led", led_panel_tex(), emissive=(1.4, 1.4, 1.4),
                emissive_tex=led_panel_tex(), rough=0.5)
for i in range(4):
    x = 3.05 + i * 0.82
    box(S, (0.74, 2.35, 0.68), (x, 1.175, -5.55), M("metal_dark", (0, 0, 0)))
    quad(S, 0.62, 2.15, (x, 1.18, -5.20),
         tex_mat(f"rack_led_{i}", led_panel_tex(seed=3 + i),
                 emissive=(1.4, 1.4, 1.4),
                 emissive_tex=led_panel_tex(seed=3 + i), rough=0.5))
    box(S, (0.74, 0.06, 0.72), (x, 2.38, -5.55), M("metal_mid", (0, 0, 0)))
# ラック上の配線ダクト
pipe_run(S, (2.7, 4.9, -5.7), (5.8, 4.9, -5.7), r=0.07)
pipe_run(S, (5.65, 0.2, -5.65), (5.65, 4.9, -5.65), r=0.09)
pipe_run(S, (-6.0, 5.05, -5.75), (2.7, 5.05, -5.75), r=0.06)

# ---------------------------------------------------------------- 左壁
# 青ネオン「思想は監視されている」
neon_sign(S, "思想は監視されている", 3.9, 0.75, (-5.80, 4.35, -0.9),
          rot=R(90, "y"), fg=(90, 180, 255), name="sign_watched",
          font_scale=0.55, tex_h=224)

# 監視モニター壁(大型フレームに8画面)
box(S, (0.35, 2.6, 3.6), (-5.72, 2.75, 0.9), M("frame_black", (0, 0, 0)))
screens = [
    ("ui",     1, (90, 170, 255)), ("ui",   2, (255, 90, 180)),
    ("static", 3, (90, 170, 255)), ("ui",   4, (120, 200, 255)),
    ("wave",   5, (255, 90, 180)), ("ui",   6, (80, 140, 255)),
    ("static", 7, (200, 90, 255)), ("ui",   8, (90, 200, 255)),
]
k = 0
for row in range(2):
    for col in range(4):
        kind, seed, hue = screens[k]
        k += 1
        stx = screen_tex(size=(256, 192), kind=kind, seed=seed, hue=hue)
        sm = tex_mat(f"mon_{k}", stx, emissive=(1.5, 1.5, 1.5),
                     emissive_tex=stx, rough=0.4)
        z = -0.42 + col * 0.88
        y = 3.32 - row * 1.18
        quad(S, 0.78, 1.02, (-5.53, y, z), sm, rot=R(90, "y"))
        box(S, (0.05, 1.10, 0.86), (-5.56, y, z), M("metal_dark", (0, 0, 0)))
# 壁掛けサブモニター(右寄り、傾き付き)
stx = screen_tex(size=(256, 160), kind="ui", seed=11, hue=(120, 190, 255))
quad(S, 0.95, 0.6, (-5.70, 2.1, 3.05),
     tex_mat("mon_sub", stx, emissive=(1.4, 1.4, 1.4), emissive_tex=stx),
     rot=R(90, "y") @ R(6, "x"))
box(S, (0.10, 0.68, 1.03), (-5.76, 2.1, 3.05), M("frame_black", (0, 0, 0)))

# 制御デスク(L字)+機器
box(S, (1.1, 0.08, 3.4), (-5.05, 0.78, 1.0), M("metal_mid", (0, 0, 0)))   # 天板
box(S, (1.0, 0.74, 3.3), (-5.05, 0.37, 1.0), M("metal_dark", (0, 0, 0)))  # 箱
box(S, (1.5, 0.08, 1.0), (-4.35, 0.78, 2.55), M("metal_mid", (0, 0, 0)))  # L字部
box(S, (1.4, 0.74, 0.9), (-4.35, 0.37, 2.55), M("metal_dark", (0, 0, 0)))
# 卓上モニター3台(角度違い)
for (z, ang, seed) in [(-0.1, 18, 21), (0.9, 0, 22), (1.9, -14, 23)]:
    stx = screen_tex(size=(192, 128), kind="ui", seed=seed,
                     hue=(100, 180, 255))
    quad(S, 0.52, 0.36, (-5.05, 1.12, z),
         tex_mat(f"desk_mon_{seed}", stx, emissive=(1.3, 1.3, 1.3),
                 emissive_tex=stx),
         rot=R(90 + ang, "y") @ R(-8, "x"))
    box(S, (0.05, 0.42, 0.58), (-5.09, 1.10, z), M("frame_black", (0, 0, 0)),
        rot=R(ang, "y"))
    cyl(S, 0.03, 0.22, (-5.08, 0.90, z), M("frame_black", (0, 0, 0)))
# キーボード2枚+小物
for z in (0.35, 1.45):
    box(S, (0.42, 0.03, 0.16), (-4.72, 0.83, z), M("frame_black", (0, 0, 0)),
        rot=R(8, "y"))
box(S, (0.22, 0.05, 0.15), (-4.30, 0.83, 2.45), M("metal_rust", (0, 0, 0)))
box(S, (0.05, 0.05, 0.05), (-4.6, 0.845, 2.7), M("neon_amber", (0, 0, 0)))
# オフィスチェア
cyl(S, 0.05, 0.45, (-4.15, 0.45, 1.0), M("frame_black", (0, 0, 0)))
box(S, (0.55, 0.10, 0.55), (-4.15, 0.72, 1.0), M("cloth_dark", (0, 0, 0)))
box(S, (0.10, 0.75, 0.55), (-3.85, 1.15, 1.0), M("cloth_dark", (0, 0, 0)),
    rot=R(-8, "z"))
for a in range(5):
    th = math.radians(a * 72)
    cyl(S, 0.025, 0.4, (-4.15 + math.cos(th) * 0.18, 0.12,
                        1.0 + math.sin(th) * 0.18),
        M("frame_black", (0, 0, 0)), rot=R(math.degrees(th), "y") @ R(75, "z"),
        sections=8)

# 左壁のサーバーラック(奥寄り)
box(S, (0.70, 2.1, 0.75), (-5.55, 1.05, -2.9), M("metal_dark", (0, 0, 0)))
stx = led_panel_tex(seed=31)
quad(S, 0.60, 1.9, (-5.18, 1.05, -2.9),
     tex_mat("rack_led_l", stx, emissive=(1.3, 1.3, 1.3), emissive_tex=stx),
     rot=R(90, "y"))

# B2-07ドア(左壁奥、階段の上)
LAND_Y = 1.62
box(S, (0.16, 2.5, 1.6), (-5.90, LAND_Y + 1.25, -4.3),
    M("frame_black", (0, 0, 0)))
d_tex = poster_tex([("B2-07", 0.14, (255, 90, 90)),
                    ("DISTRICT", 0.06, (150, 140, 150))],
                   size=(384, 640), bg=(30, 28, 36), fg=(120, 115, 130))
quad(S, 1.3, 2.3, (-5.80, LAND_Y + 1.2, -4.3),
     tex_mat("door_b207", d_tex, rough=0.7, metallic=0.4), rot=R(90, "y"))
box(S, (0.12, 0.10, 0.28), (-5.80, LAND_Y + 2.55, -4.3),
    M("neon_red", (0, 0, 0)))
# 階段(10段)+踊り場+手すり
STEPS = 9
for i in range(STEPS):
    sy = (i + 1) * (LAND_Y / STEPS)
    box(S, (1.15, sy, 0.42), (-5.4, sy / 2, -1.55 - i * 0.30),
        M("concrete", (0, 0, 0)))
box(S, (1.4, 0.16, 1.5), (-5.3, LAND_Y - 0.08, -4.35),
    M("metal_mid", (0, 0, 0)))
rail_pts = [(-4.82, LAND_Y, -4.9), (-4.82, LAND_Y, -4.0),
            (-4.82, 0.35, -1.45)]
for i, (px, py, pz) in enumerate(rail_pts):
    cyl(S, 0.03, 0.85, (px, py + 0.42, pz), M("pipe", (0, 0, 0)))
pipe_run(S, (-4.82, LAND_Y + 0.85, -4.9), (-4.82, LAND_Y + 0.85, -4.0),
         r=0.035, joints=False)
pipe_run(S, (-4.82, LAND_Y + 0.85, -4.0), (-4.82, 1.2, -1.45), r=0.035,
         joints=False)
pipe_run(S, (-4.82, LAND_Y + 0.45, -4.0), (-4.82, 0.8, -1.45), r=0.025,
         joints=False)

# ---------------------------------------------------------------- 右壁
# プロパガンダ看板(目のグラフィック入り)
def propaganda_tex(size=(768, 640)):
    img = Image.new("RGB", size, (26, 18, 26))
    d = ImageDraw.Draw(img)
    W, Hh = size
    f1 = _font(int(Hh * 0.115))
    for i, line in enumerate(["真実は危険だ", "正しさを信じろ"]):
        bbox = d.textbbox((0, 0), line, font=f1)
        d.text(((W - bbox[2] + bbox[0]) // 2 - bbox[0],
                int(Hh * 0.05) + i * int(Hh * 0.15)),
               line, font=f1, fill=(255, 70, 130))
    # 目
    cx, cy, ew, eh = W // 2, int(Hh * 0.55), int(W * 0.30), int(Hh * 0.13)
    d.ellipse([cx - ew, cy - eh, cx + ew, cy + eh], outline=(255, 90, 150),
              width=6)
    d.ellipse([cx - eh, cy - eh, cx + eh, cy + eh], fill=(60, 20, 40),
              outline=(255, 90, 150), width=4)
    d.ellipse([cx - eh // 2, cy - eh // 2, cx + eh // 2, cy + eh // 2],
              fill=(255, 80, 140))
    f2 = _font(int(Hh * 0.075))
    line = "国家があなたを守る"
    bbox = d.textbbox((0, 0), line, font=f2)
    d.text(((W - bbox[2] + bbox[0]) // 2 - bbox[0], int(Hh * 0.80)),
           line, font=f2, fill=(230, 140, 180))
    blur = img.filter(ImageFilter.GaussianBlur(8))
    img = Image.blend(img, blur, 0.35)
    d = ImageDraw.Draw(img)
    d.rectangle([5, 5, W - 6, Hh - 6], outline=(120, 50, 80), width=3)
    return img

pt = propaganda_tex()
box(S, (0.22, 3.0, 3.9), (5.85, 3.35, -2.6), M("frame_black", (0, 0, 0)))
quad(S, 3.7, 2.8, (5.70, 3.35, -2.6),
     tex_mat("propaganda", pt, emissive=(0.9, 0.9, 0.9), emissive_tex=pt,
             rough=0.6),
     rot=R(-90, "y"))

# 違反者リスト(顔写真ボード)
mt = mugshot_tex()
box(S, (0.14, 2.0, 1.6), (5.90, 1.55, -0.1), M("metal_dark", (0, 0, 0)))
quad(S, 1.45, 1.85, (5.80, 1.55, -0.1),
     tex_mat("mugshots", mt, emissive=(0.55, 0.55, 0.55), emissive_tex=mt,
             rough=0.8),
     rot=R(-90, "y"))
# 小さな告知ポスター(傾き)
pp = poster_tex([("通達", 0.09, (60, 55, 60)), ("第7区", 0.07, (70, 60, 65))],
                size=(256, 384), bg=(165, 155, 140), fg=(60, 55, 60))
quad(S, 0.55, 0.8, (5.86, 1.9, 1.15),
     tex_mat("notice", pp, rough=0.95), rot=R(-90, "y") @ R(4, "z"))

# 右壁ドア2枚+赤色灯+縦看板「報告せよ」
for z in (2.3, 4.4):
    box(S, (0.16, 2.7, 1.5), (5.90, 1.35, z), M("frame_black", (0, 0, 0)))
    quad(S, 1.3, 2.5, (5.80, 1.25, z),
         tex_mat(f"door_r_{z}", wall_tex(size=(256, 512), seed=int(z * 7),
                                         base=(24, 24, 32), panel=128),
                 metallic=0.5, rough=0.6),
         rot=R(-90, "y"))
    box(S, (0.10, 0.12, 0.30), (5.82, 2.85, z), M("neon_red", (0, 0, 0)))
neon_sign(S, "報告せよ", 0.55, 2.3, (5.80, 2.6, 3.35), rot=R(-90, "y"),
          fg=(255, 200, 90), bg=(30, 22, 12), vertical=True,
          name="sign_report", font_scale=0.66, tex_h=640)

# 有刺鉄線フェンス(右壁手前)
fence_chainlink(S, 2.6, 1.6, (5.5, 0.8, 5.3), rot=R(-64, "y"))

# ---------------------------------------------------------------- 中央: 検問
# ネオン立て看板「観測中 CHECKPOINT」
neon_sign(S, "観測中", 1.75, 0.95, (0.4, 1.05, 0.5), rot=R(6, "y"),
          fg=(255, 70, 150), sub="CHECKPOINT", sub_fg=(255, 120, 180),
          name="sign_checkpoint", tex_h=288)
for sx in (-0.5, 0.5):
    box(S, (0.08, 1.1, 0.08), (0.4 + sx, 0.55, 0.52),
        M("frame_black", (0, 0, 0)), rot=R(6, "y"))

# 警告ストライプのバリケード2基(A脚)
stripe_m = tex_mat("stripe", stripe_tex(), rough=0.6)
def barricade(x, z, ang):
    rot = R(ang, "y")
    b = trimesh.creation.box(extents=[1.5, 0.32, 0.06])
    b.visual = trimesh.visual.TextureVisuals(
        uv=None, material=stripe_m)
    # ストライプ板はquadで(両面テクスチャ)
    quad(S, 1.5, 0.32, (x, 0.72, z), stripe_m, rot=rot)
    box(S, (1.5, 0.05, 0.05), (x, 0.53, z), M("metal_mid", (0, 0, 0)),
        rot=rot)
    for sx in (-0.62, 0.62):
        for lean in (16, -16):
            px = x + sx * math.cos(math.radians(ang))
            pz = z - sx * math.sin(math.radians(ang))
            box(S, (0.05, 0.95, 0.05), (px, 0.44, pz),
                M("metal_rust", (0, 0, 0)), rot=rot @ R(lean, "x"))
barricade(-1.35, 1.0, -8)
barricade(1.85, 0.75, 5)

# 遮断バー付きゲート機(ピンク発光)
box(S, (0.55, 1.15, 0.55), (3.3, 0.575, 1.5), M("metal_dark", (0, 0, 0)))
box(S, (0.45, 0.18, 0.45), (3.3, 1.24, 1.5), M("neon_pink", (0, 0, 0)))
box(S, (0.30, 0.30, 0.30), (3.3, 1.05, 1.5), M("neon_pink", (0, 0, 0)))
# 三連ピンク灯ポスト
box(S, (0.28, 1.9, 0.28), (2.65, 0.95, 0.30), M("metal_dark", (0, 0, 0)))
for i in range(3):
    box(S, (0.20, 0.20, 0.20), (2.65, 1.35 + i * 0.28 - 0.28, 0.42),
        M("neon_pink", (0, 0, 0)))
# 遮断バー(ストライプ、やや上がり気味)
bar_m = tex_mat("bar_stripe", stripe_tex(n=10, size=(1024, 64)), rough=0.5)
bl = 3.6
bar = trimesh.creation.box(extents=[bl, 0.10, 0.10])
uv_dummy = None
bar.visual = trimesh.visual.TextureVisuals(material=bar_m)
bar.apply_transform(T(3.3, 1.05, 1.5) @ R(-38, "y") @ R(7, "z")
                    @ T(-bl / 2 - 0.1, 0, 0))
S.add_geometry(bar)
# バー先端の受けポール
cyl(S, 0.05, 0.75, (0.75, 0.375, 3.6), M("metal_rust", (0, 0, 0)))

# 赤色灯ポール(検問周辺に3本)
lamp(S, (-0.5, 0, 1.7), M("neon_red", (0, 0, 0)), pole_h=1.15)
lamp(S, (1.15, 0, 1.85), M("neon_red", (0, 0, 0)), pole_h=1.0)
lamp(S, (2.35, 0, 3.1), M("neon_red", (0, 0, 0)), pole_h=1.05)
lamp(S, (-3.3, 0, 3.3), M("neon_red", (0, 0, 0)), pole_h=1.3)

# 床の円形スキャナーパッド(同心円発光)
def scanner_tex(size=(512, 512)):
    img = Image.new("RGB", size, (24, 18, 28))
    d = ImageDraw.Draw(img)
    c = size[0] // 2
    for r, wd in [(240, 14), (192, 8), (144, 10), (98, 6), (52, 8)]:
        d.ellipse([c - r, c - r, c + r, c + r], outline=(255, 60, 140),
                  width=wd)
    d.ellipse([c - 28, c - 28, c + 28, c + 28], fill=(255, 90, 160))
    for a in range(0, 360, 45):
        x = c + int(math.cos(math.radians(a)) * 216)
        y = c + int(math.sin(math.radians(a)) * 216)
        d.rectangle([x - 10, y - 10, x + 10, y + 10], fill=(255, 70, 150))
    return img.filter(ImageFilter.GaussianBlur(1))

from kit import disc
sc = scanner_tex()
cyl(S, 1.35, 0.07, (3.3, 0.035, 2.7), M("metal_dark", (0, 0, 0)),
    sections=40)
disc(S, 1.28, (3.3, 0.075, 2.7),
     tex_mat("scanner", sc, emissive=(2.2, 2.2, 2.2), emissive_tex=sc,
             rough=0.4))

# ケーブル類(床を這う)
pipe_run(S, (3.3, 0.05, 1.8), (3.6, 0.05, -2.0), r=0.04, joints=False)
pipe_run(S, (3.6, 0.05, -2.0), (4.2, 0.05, -5.2), r=0.04, joints=False)
pipe_run(S, (4.9, 0.05, 4.6), (5.6, 0.05, 2.0), r=0.035, joints=False)
pipe_run(S, (0.4, 0.04, 0.9), (-2.0, 0.04, -1.5), r=0.03, joints=False)

# ---------------------------------------------------------------- 右下: パラボラ
px, pz = 5.05, 5.35
box(S, (0.7, 0.35, 0.7), (px, 0.175, pz), M("metal_rust", (0, 0, 0)))
cyl(S, 0.07, 0.7, (px, 0.65, pz), M("pipe", (0, 0, 0)))
dish_rot = R(35, "y") @ R(58, "x")
cone(S, 0.95, 0.38, (px - 0.30, 1.20, pz - 0.30),
     M("metal_dark", (0, 0, 0)), rot=dish_rot, sections=36)
cyl(S, 0.03, 1.0, (px - 0.55, 1.35, pz - 0.55), M("pipe", (0, 0, 0)),
    rot=dish_rot)
sphere(S, 0.08, (px - 0.75, 1.62, pz - 0.75), M("neon_red", (0, 0, 0)))
pipe_run(S, (px + 0.2, 0.05, pz + 0.2), (5.8, 0.05, 4.4), r=0.03,
         joints=False)

# ---------------------------------------------------------------- 左下
# レバー付き制御台
bx, bz = -4.3, 4.3
box(S, (1.6, 0.9, 1.2), (bx, 0.45, bz), M("metal_dark", (0, 0, 0)))
box(S, (1.7, 0.10, 1.3), (bx, 0.95, bz), M("metal_mid", (0, 0, 0)))
box(S, (0.5, 0.12, 0.35), (bx + 0.2, 1.06, bz - 0.1),
    M("frame_black", (0, 0, 0)))
cyl(S, 0.03, 0.5, (bx + 0.2, 1.30, bz - 0.1), M("pipe", (0, 0, 0)),
    rot=R(-25, "x"))
sphere(S, 0.07, (bx + 0.2, 1.52, bz - 0.0), M("neon_red", (0, 0, 0)))
box(S, (0.10, 0.10, 0.10), (bx - 0.55, 1.05, bz + 0.35),
    M("neon_red", (0, 0, 0)))
box(S, (0.35, 0.06, 0.5), (bx - 0.45, 0.98, bz - 0.3),
    M("metal_rust", (0, 0, 0)))
# 側面の段差ディテール
box(S, (0.3, 0.5, 0.9), (bx - 0.95, 0.25, bz + 0.1),
    M("metal_rust", (0, 0, 0)))

# A型看板「黙れ SILENCE」
ax, az = -1.9, 4.7
sp = poster_tex([("黙", 0.30, (255, 70, 140)), ("れ", 0.30, (255, 70, 140)),
                 ("SILENCE", 0.06, (255, 110, 160))],
                size=(320, 640), bg=(16, 12, 18), fg=(255, 70, 140))
spm = tex_mat("silence", sp, emissive=(0.9, 0.9, 0.9), emissive_tex=sp,
              rough=0.7)
for lean in (16, -16):
    quad(S, 0.62, 1.05, (ax, 0.50, az + (0.14 if lean > 0 else -0.14)),
         spm, rot=R(12, "y") @ R(lean, "x"))
box(S, (0.66, 0.04, 0.36), (ax, 0.99, az), M("frame_black", (0, 0, 0)),
    rot=R(12, "y"))

# 木箱・ドラム缶・配管(左下奥)
crate(S, (-5.2, 0, 2.6), size=(0.75, 0.6, 0.75), rot_y=8)
crate(S, (-5.15, 0.6, 2.65), size=(0.6, 0.5, 0.6), rot_y=-14)
crate(S, (-4.4, 0, 2.3), size=(0.6, 0.45, 0.6), rot_y=22)
barrel(S, (-5.35, 0, 1.55))
barrel(S, (2.3, 0, -4.9), r=0.28, h=0.8)
# 手すり(左下の床端)
pipe_run(S, (-5.9, 0.85, 5.6), (-2.6, 0.85, 5.6), r=0.035)
pipe_run(S, (-5.9, 0.45, 5.6), (-2.6, 0.45, 5.6), r=0.025, joints=False)
for fx in (-5.8, -4.7, -3.6, -2.65):
    cyl(S, 0.03, 0.85, (fx, 0.425, 5.6), M("pipe", (0, 0, 0)))

# 垂れ下がる配線(壁上部)
pipe_run(S, (-5.9, 5.3, -5.9), (-2.0, 4.6, -5.85), r=0.02, joints=False)
pipe_run(S, (-2.0, 4.6, -5.85), (2.0, 5.2, -5.85), r=0.02, joints=False)
pipe_run(S, (-5.85, 5.3, -5.0), (-5.85, 4.5, -1.5), r=0.02, joints=False)

# ---------------------------------------------------------------- 出力
# 退廃演出: 瓦礫・ゴミ・シミ・水たまり
decay_scatter(S, (-5.4, 5.4), (-4.8, 5.4), seed=3,
              avoid=[(3.3, 2.7, 1.6), (0.6, 0.6, 1.2)])

out = os.path.join(os.path.dirname(__file__), "observation_tower.glb")
size = export(S, out)
print(f"OK observation_tower.glb {size/1e6:.2f} MB, "
      f"geoms={len(S.geometry)}")
