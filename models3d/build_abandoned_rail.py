# -*- coding: utf-8 -*-
"""
廃線 (Abandoned Rail Crossing) — 背景画像2の3D再現。

画像分析メモ:
  - 屋外・雨・夜。石積みの壁に暗いトンネルアーチ(左上)、線路がそこから
    右下へ延びる。もう1本の線路が左下〜右へ横断(中央でクロス)。
  - トンネル右にピンクネオン縦看板「廃線」(枠付き)。
  - 左に2灯式信号機(赤点灯)。中央右に単灯信号機(赤点灯)+赤十字の小箱。
  - 奥中央: 暗い建物の壁、ドア、シアンの小さな灯り。
  - 右: 大きな風化した「旧駅の時刻表」掲示板(金網フェンスの前、ヒビ)。
  - 左: 有刺鉄線付き金網フェンス+「立入禁止」「危険 高電圧」看板。
  - 中央〜下: 枕木+バラスト、水たまり、雑草、泥。黄黒ストライプの
    バリケード。小さな中継箱ポール(赤点滅)。
  - 右下: 錆びた廃列車(保線車)、正面に赤く光る△マーク、隣にドラム缶。
  - 左下: 防水シートを掛けた台車、ケーブルのコイル、柵。
"""
import math
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tools"))

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import trimesh

from kit import (M, std_mats, mat, tex_mat, box, cyl, cone, sphere, quad,
                 disc, T, R, neon_sign, tile_floor_tex, wall_tex, stripe_tex,
                 poster_tex, timetable_tex, lamp, barrel, crate, pipe_run,
                 fence_chainlink, decay_scatter, export, _font)

std_mats()
S = trimesh.Scene()

W_GND, D_GND = 15.0, 13.0

# ---------------------------------------------------------------- 地面
def dirt_tex(size=(1024, 1024), seed=13):
    import random
    rng = random.Random(seed)
    img = Image.new("RGB", size, (16, 16, 20))
    d = ImageDraw.Draw(img)
    Wt, Ht = size
    for _ in range(900):  # 土・アスファルトのまだら
        x, y = rng.randint(0, Wt), rng.randint(0, Ht)
        r = rng.randint(6, 42)
        v = rng.uniform(0.6, 1.4)
        c = (int(15 * v), int(14 * v), int(15 * v))
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    for _ in range(70):  # ひび
        x, y = rng.randint(0, Wt), rng.randint(0, Ht)
        pts = [(x, y)]
        for _ in range(rng.randint(3, 7)):
            x += rng.randint(-40, 40); y += rng.randint(-30, 30)
            pts.append((x, y))
        d.line(pts, fill=(8, 8, 10), width=2)
    # 水たまり(反射)
    spots = [(0.28, 0.42, 60, (60, 40, 90)), (0.5, 0.62, 90, (40, 60, 110)),
             (0.62, 0.5, 55, (150, 40, 110)), (0.2, 0.75, 70, (30, 50, 90)),
             (0.75, 0.72, 50, (120, 40, 60)), (0.42, 0.3, 45, (90, 30, 90))]
    ref = Image.new("RGB", size, (0, 0, 0))
    rd = ImageDraw.Draw(ref)
    for (u, v, r, c) in spots:
        x, y = int(u * Wt), int(v * Ht)
        rd.ellipse([x - r * 2, y - r, x + r * 2, y + r], fill=c)
    ref = ref.filter(ImageFilter.GaussianBlur(30))
    img = Image.blend(img, Image.blend(img, ref, 0.9), 0.5)
    return img

gm = tex_mat("ground", dirt_tex(), rough=0.5, metallic=0.05)
quad(S, W_GND, D_GND, (0, 0, 0), gm, rot=R(-90, "x"), double=False)
box(S, (W_GND, 0.3, D_GND), (0, -0.16, 0), M("concrete", (0, 0, 0)))

# ---------------------------------------------------------------- 奥壁+トンネル
def stone_tex(size=(1024, 512), seed=21):
    import random
    rng = random.Random(seed)
    img = Image.new("RGB", size, (20, 20, 26))
    d = ImageDraw.Draw(img)
    Wt, Ht = size
    bh = 42
    for row, y in enumerate(range(0, Ht, bh)):
        off = (row % 2) * 45
        for x in range(-90, Wt, 90):
            v = rng.uniform(0.7, 1.25)
            c = (int(22 * v), int(21 * v), int(27 * v))
            d.rectangle([x + off + 2, y + 2, x + off + 88, y + bh - 2],
                        fill=c, outline=(9, 9, 12))
            if rng.random() < 0.12:
                d.line([(x + off + 10, y + 6), (x + off + 40, y + bh - 6)],
                       fill=(10, 10, 13), width=2)
    return img

wall_m = tex_mat("stone", stone_tex(), rough=0.95, metallic=0.05)
H_WALL = 6.0
quad(S, W_GND, H_WALL, (0, H_WALL / 2, -D_GND / 2), wall_m,
     uv=np.array([[0, 0], [3, 0], [3, 1.5], [0, 1.5]]))
# 左側壁(石積み、低め)
quad(S, D_GND, 4.5, (-W_GND / 2, 2.25, 0), wall_m, rot=R(90, "y"),
     uv=np.array([[0, 0], [2.6, 0], [2.6, 1.1], [0, 1.1]]))

# トンネルアーチ(左上): 半円アーチ(春目線 y=1.85)+黒い開口
TX = -4.2
ARC_R, ARC_Y = 1.75, 1.85
# 開口(黒): 下部矩形+上部円
box(S, (ARC_R * 2, ARC_Y, 0.4), (TX, ARC_Y / 2, -6.35),
    M("frame_black", (0, 0, 0)))
g = trimesh.creation.cylinder(radius=ARC_R, height=0.4, sections=32)
g.visual = trimesh.visual.TextureVisuals(material=M("frame_black", (0, 0, 0)))
g.apply_transform(T(TX, ARC_Y, -6.35))
S.add_geometry(g)
# アーチリング(石): 上半分だけ地上に見える円環
ring = trimesh.creation.torus(major_radius=ARC_R + 0.1, minor_radius=0.26,
                              major_sections=40, minor_sections=8)
ring.visual = trimesh.visual.TextureVisuals(
    material=M("concrete", (0, 0, 0)))
ring.apply_transform(T(TX, ARC_Y, -6.15))
S.add_geometry(ring)
for sx in (-(ARC_R + 0.1), ARC_R + 0.1):  # アーチ脚
    box(S, (0.5, ARC_Y, 0.5), (TX + sx, ARC_Y / 2, -6.15),
        M("concrete", (0, 0, 0)))
# 楣石(アーチ上の梁)
box(S, (4.8, 0.45, 0.55), (TX, ARC_Y + ARC_R + 0.55, -6.15),
    M("concrete", (0, 0, 0)))

# ピンクネオン縦看板「廃線」
neon_sign(S, "廃線", 1.05, 2.3, (-1.35, 3.6, -5.95), fg=(255, 60, 150),
          vertical=True, name="sign_haisen", font_scale=0.62, tex_h=512)

# 奥の建物ディテール(中央右): ドア+シアン灯
box(S, (0.14, 2.4, 1.4), (2.2, 1.2, -6.15), M("frame_black", (0, 0, 0)),
    rot=R(90, "y"))
quad(S, 1.2, 2.2, (2.2, 1.1, -6.05),
     tex_mat("rail_door", wall_tex(size=(256, 512), seed=33,
                                   base=(22, 24, 30), panel=128),
             metallic=0.5, rough=0.7))
for sy in (2.6, 2.85):
    box(S, (0.5, 0.07, 0.06), (3.1, sy, -6.1), M("neon_cyan", (0, 0, 0)))
box(S, (0.35, 0.5, 0.10), (1.35, 2.3, -6.1), M("metal_dark", (0, 0, 0)))
pipe_run(S, (4.5, 0.3, -6.2), (4.5, 5.0, -6.2), r=0.07)
pipe_run(S, (-7.2, 5.2, -6.2), (7.2, 5.4, -6.2), r=0.04, joints=False)

# ---------------------------------------------------------------- 線路
M("rail_steel", (0.16, 0.17, 0.20), metallic=0.9, rough=0.35)
M("sleeper", (0.10, 0.075, 0.055), metallic=0.0, rough=1.0)
M("ballast", (0.11, 0.11, 0.13), metallic=0.0, rough=1.0)

def rail_track(p0, p1, gauge=1.45):
    p0 = np.array([p0[0], 0, p0[1]], float)
    p1 = np.array([p1[0], 0, p1[1]], float)
    d = p1 - p0
    L = float(np.linalg.norm(d))
    u = d / L
    ang = math.degrees(math.atan2(u[0], u[2]))  # z軸基準
    side = np.array([u[2], 0, -u[0]])
    mid = (p0 + p1) / 2
    # バラスト
    b = trimesh.creation.box(extents=[gauge + 1.3, 0.09, L])
    b.visual = trimesh.visual.TextureVisuals(material=M("ballast", (0,)))
    b.apply_transform(T(*(mid + [0, 0.045, 0])) @ R(ang, "y"))
    S.add_geometry(b)
    # 枕木
    n = int(L / 0.62)
    for i in range(n):
        t = (i + 0.5) / n
        c = p0 + d * t
        sl = trimesh.creation.box(extents=[gauge + 0.75, 0.09, 0.24])
        sl.visual = trimesh.visual.TextureVisuals(material=M("sleeper", (0,)))
        sl.apply_transform(T(c[0], 0.13, c[2]) @ R(ang, "y"))
        S.add_geometry(sl)
    # レール2本
    for s in (-gauge / 2, gauge / 2):
        c = mid + side * s
        r = trimesh.creation.box(extents=[0.09, 0.14, L])
        r.visual = trimesh.visual.TextureVisuals(
            material=M("rail_steel", (0,)))
        r.apply_transform(T(c[0], 0.24, c[2]) @ R(ang, "y"))
        S.add_geometry(r)
        rb = trimesh.creation.box(extents=[0.16, 0.05, L])
        rb.visual = trimesh.visual.TextureVisuals(
            material=M("rail_steel", (0,)))
        rb.apply_transform(T(c[0], 0.165, c[2]) @ R(ang, "y"))
        S.add_geometry(rb)

rail_track((TX, -6.0), (3.8, 6.4))          # トンネルから右下へ
rail_track((-7.4, 2.2), (7.4, 4.6))         # 横断する第二軌道

# ---------------------------------------------------------------- 信号機
def signal(x, z, heads=2, lit=0, h=2.6, yaw=0):
    cyl(S, 0.05, h, (x, h / 2, z), M("pipe", (0, 0, 0)))
    box(S, (0.4, 0.22 + heads * 0.34, 0.25), (x, h + 0.1, z),
        M("frame_black", (0, 0, 0)), rot=R(yaw, "y"))
    for i in range(heads):
        on = (i == lit)
        mname = "neon_red" if on else "lamp_off"
        M("lamp_off", (0.16, 0.05, 0.05), rough=0.6)
        zoff = 0.14
        yv = h + 0.1 + (heads - 1) * 0.17 - i * 0.34
        cyl(S, 0.11, 0.06, (x + math.sin(math.radians(yaw)) * zoff,
                            yv, z + math.cos(math.radians(yaw)) * zoff),
            M(mname, (0, 0, 0)), rot=R(90, "x"), sections=16)
        # ひさし
        box(S, (0.24, 0.05, 0.18),
            (x + math.sin(math.radians(yaw)) * zoff, yv + 0.10,
             z + math.cos(math.radians(yaw)) * zoff),
            M("frame_black", (0, 0, 0)), rot=R(yaw, "y"))

signal(-6.3, -3.4, heads=2, lit=0, h=2.4, yaw=25)   # トンネル左の2灯(両方赤風)
signal(2.6, -2.2, heads=3, lit=0, h=3.2, yaw=-15)   # 中央右の縦3灯(赤点灯)
# 赤十字の小箱(信号ポール下)
box(S, (0.42, 0.55, 0.18), (2.6, 1.35, -2.05), M("metal_dark", (0, 0, 0)))
box(S, (0.26, 0.07, 0.04), (2.6, 1.35, -1.95), M("neon_red", (0, 0, 0)))
box(S, (0.07, 0.26, 0.04), (2.6, 1.35, -1.95), M("neon_red", (0, 0, 0)))

# 中継箱ポール(中央、赤点滅灯)
cyl(S, 0.07, 1.15, (-0.6, 0.575, 1.6), M("pipe", (0, 0, 0)))
box(S, (0.34, 0.5, 0.28), (-0.6, 1.35, 1.6), M("metal_dark", (0, 0, 0)))
box(S, (0.08, 0.08, 0.06), (-0.6, 1.45, 1.76), M("neon_red", (0, 0, 0)))
box(S, (0.30, 0.06, 0.24), (-0.6, 1.66, 1.6), M("metal_mid", (0, 0, 0)))

# ---------------------------------------------------------------- 時刻表ボード
tt = timetable_tex()
bx, bz = 5.3, -2.8
for sx in (-1.15, 1.15):
    cyl(S, 0.06, 3.4, (bx + sx * 0.85, 1.7, bz + sx * 0.5),
        M("pipe", (0, 0, 0)))
board_rot = R(-32, "y")
box(S, (2.75, 3.0, 0.14), (bx, 2.15, bz), M("frame_black", (0, 0, 0)),
    rot=board_rot)
quad(S, 2.55, 2.8, (bx - 0.06, 2.15, bz + 0.09),
     tex_mat("timetable", tt, emissive=(0.85, 0.85, 0.85), emissive_tex=tt,
             rough=0.9),
     rot=board_rot)
# ボード裏の金網
fence_chainlink(S, 3.4, 2.2, (6.3, 1.1, -1.0), rot=R(-32, "y"))

# ---------------------------------------------------------------- フェンスと看板
fence_chainlink(S, 4.2, 1.9, (-6.4, 0.95, -1.2), rot=R(75, "y"))
fence_chainlink(S, 3.6, 1.9, (-5.6, 0.95, 3.6), rot=R(58, "y"))
# 立入禁止(白地)
sg = poster_tex([("立入禁止", 0.16, (30, 30, 36))], size=(384, 256),
                bg=(200, 195, 185), fg=(30, 30, 36))
quad(S, 0.85, 0.55, (-5.9, 1.15, 2.2),
     tex_mat("keepout", sg, rough=0.9), rot=R(62, "y") @ R(-3, "z"))
# 危険 高電圧(稲妻マーク)
def hv_tex(size=(320, 384)):
    img = Image.new("RGB", size, (205, 200, 190))
    d = ImageDraw.Draw(img)
    Wt, Ht = size
    f = _font(int(Ht * 0.13))
    d.text((int(Wt * 0.18), int(Ht * 0.04)), "危険", font=f, fill=(180, 30, 30))
    d.text((int(Wt * 0.08), int(Ht * 0.72)), "高電圧", font=f,
           fill=(30, 30, 36))
    d.polygon([(Wt * 0.52, Ht * 0.24), (Wt * 0.34, Ht * 0.52),
               (Wt * 0.47, Ht * 0.52), (Wt * 0.40, Ht * 0.72),
               (Wt * 0.66, Ht * 0.44), (Wt * 0.52, Ht * 0.44),
               (Wt * 0.62, Ht * 0.24)], fill=(200, 160, 20))
    d.rectangle([4, 4, Wt - 5, Ht - 5], outline=(120, 30, 30))
    return img

quad(S, 0.7, 0.85, (-6.55, 1.05, -0.4),
     tex_mat("highvolt", hv_tex(), rough=0.9), rot=R(78, "y") @ R(2, "z"))
# 左壁の配電盤(青灯)
box(S, (0.16, 0.6, 0.45), (-7.35, 2.3, -3.2), M("metal_dark", (0, 0, 0)))
box(S, (0.05, 0.10, 0.16), (-7.26, 2.42, -3.2), M("neon_cyan", (0, 0, 0)))

# ---------------------------------------------------------------- バリケード他
stripe_y = tex_mat("stripe_yellow",
                   stripe_tex(c1=(210, 170, 30), c2=(18, 16, 14)), rough=0.7)
def small_barrier(x, z, ang):
    rot = R(ang, "y")
    quad(S, 1.1, 0.26, (x, 0.55, z), stripe_y, rot=rot)
    for sx in (-0.45, 0.45):
        px = x + sx * math.cos(math.radians(ang))
        pz = z - sx * math.sin(math.radians(ang))
        for lean in (14, -14):
            box(S, (0.04, 0.72, 0.04), (px, 0.34, pz),
                M("metal_rust", (0, 0, 0)), rot=rot @ R(lean, "x"))

small_barrier(-3.1, -1.4, 40)
small_barrier(0.6, 0.4, 12)
small_barrier(-1.8, 5.0, -18)

# ---------------------------------------------------------------- 廃列車(右下)
tx, tz = 4.6, 5.2
train_rot = R(-17.5, "y")   # 軌道Aの向きに合わせる
def train_tex(size=(512, 384), seed=41):
    import random
    rng = random.Random(seed)
    img = wall_tex(size=size, base=(52, 44, 42), seed=seed, panel=96)
    d = ImageDraw.Draw(img)
    for _ in range(24):  # 錆
        x, y = rng.randint(0, size[0] - 40), rng.randint(0, size[1] - 30)
        d.ellipse([x, y, x + rng.randint(12, 60), y + rng.randint(8, 30)],
                  fill=(52, 34, 24))
    return img

# 車体
body = trimesh.creation.box(extents=[2.3, 1.9, 3.4])
body.visual = trimesh.visual.TextureVisuals(
    material=tex_mat("traincar", train_tex(), metallic=0.4, rough=0.85))
body.apply_transform(T(tx, 1.45, tz) @ train_rot)
S.add_geometry(body)
# 屋根+ディテール
roof = trimesh.creation.box(extents=[2.4, 0.25, 3.5])
roof.visual = trimesh.visual.TextureVisuals(material=M("metal_dark", (0,)))
roof.apply_transform(T(tx, 2.5, tz) @ train_rot)
S.add_geometry(roof)
vent = trimesh.creation.box(extents=[0.8, 0.3, 1.1])
vent.visual = trimesh.visual.TextureVisuals(material=M("metal_rust", (0,)))
vent.apply_transform(T(tx, 2.75, tz + 0.4) @ train_rot)
S.add_geometry(vent)
# 正面(手前)の赤い△マーク
def tri_tex(size=(256, 256)):
    img = Image.new("RGB", size, (16, 12, 12))
    d = ImageDraw.Draw(img)
    Wt = size[0]
    d.polygon([(Wt * 0.5, Wt * 0.16), (Wt * 0.14, Wt * 0.80),
               (Wt * 0.86, Wt * 0.80)], outline=(255, 60, 50), width=10)
    d.polygon([(Wt * 0.5, Wt * 0.34), (Wt * 0.30, Wt * 0.70),
               (Wt * 0.70, Wt * 0.70)], fill=(255, 70, 55))
    return img.filter(ImageFilter.GaussianBlur(2))

tt2 = tri_tex()
front_off = train_rot[:3, :3] @ np.array([0, 0, 1.76])
quad(S, 0.85, 0.85, (tx + front_off[0], 1.5, tz + front_off[2]),
     tex_mat("train_tri", tt2, emissive=(1.6, 1.6, 1.6), emissive_tex=tt2,
             rough=0.6),
     rot=train_rot)
# 窓(暗)
win_off = train_rot[:3, :3] @ np.array([0, 0, 1.72])
box(S, (1.6, 0.5, 0.06), (tx + win_off[0], 2.15, tz + win_off[2]),
    M("frame_black", (0, 0, 0)), rot=train_rot)
# 車輪
for dz in (-1.1, 1.1):
    for dxs in (-0.85, 0.85):
        off = train_rot[:3, :3] @ np.array([dxs, 0, dz])
        cyl(S, 0.34, 0.22, (tx + off[0], 0.34, tz + off[2]),
            M("metal_dark", (0, 0, 0)), rot=train_rot @ R(90, "z"),
            sections=20)
# 連結器・バッファ
buf_off = train_rot[:3, :3] @ np.array([0, 0, 1.9])
box(S, (0.5, 0.25, 0.3), (tx + buf_off[0], 0.6, tz + buf_off[2]),
    M("metal_rust", (0, 0, 0)), rot=train_rot)

barrel(S, (6.4, 0, 5.6), r=0.32, h=0.9)
barrel(S, (6.9, 0, 4.7), r=0.28, h=0.8)
crate(S, (6.6, 0, 3.6), size=(0.7, 0.5, 0.7), rot_y=15)

# ---------------------------------------------------------------- 左下
# 防水シートの台車
cart = trimesh.creation.box(extents=[1.5, 0.75, 1.1])
cart.visual = trimesh.visual.TextureVisuals(material=M("cloth_dark", (0,)))
cart.apply_transform(T(-5.6, 0.65, 4.9) @ R(14, "y"))
S.add_geometry(cart)
top = trimesh.creation.box(extents=[1.2, 0.4, 0.85])
top.visual = trimesh.visual.TextureVisuals(material=M("cloth_dark", (0,)))
top.apply_transform(T(-5.5, 1.15, 4.85) @ R(20, "y") @ R(4, "z"))
S.add_geometry(top)
box(S, (1.3, 0.28, 0.95), (-5.6, 0.14, 4.9), M("metal_rust", (0, 0, 0)),
    rot=R(14, "y"))
for dxs in (-0.55, 0.55):
    cyl(S, 0.16, 0.12, (-5.6 + dxs, 0.16, 5.35), M("frame_black", (0, 0, 0)),
        rot=R(90, "z"), sections=14)
# ケーブルコイル
for i in range(4):
    ring = trimesh.creation.torus(major_radius=0.42 - i * 0.01,
                                  minor_radius=0.045,
                                  major_sections=24, minor_sections=8)
    ring.visual = trimesh.visual.TextureVisuals(material=M("cable", (0,)))
    ring.apply_transform(T(-6.7, 0.06 + i * 0.09, 3.0) @ R(90, "x") @ R(0, "y"))
    S.add_geometry(ring)

# ---------------------------------------------------------------- 雑草・小物
import random as _rnd
rng = _rnd.Random(5)
M("weed", (0.10, 0.13, 0.07), rough=1.0)
for _ in range(26):
    x = rng.uniform(-7, 7)
    z = rng.uniform(-5.5, 6)
    if abs(x - TX) < 2.5 and z < -4:   # トンネル前は避ける
        continue
    h = rng.uniform(0.15, 0.42)
    for k in range(rng.randint(2, 4)):
        cone(S, 0.03 + rng.uniform(0, 0.02), h * rng.uniform(0.7, 1.3),
             (x + rng.uniform(-0.12, 0.12), h / 2,
              z + rng.uniform(-0.12, 0.12)),
             M("weed", (0, 0, 0)),
             rot=R(rng.uniform(-14, 14), "x") @ R(rng.uniform(-14, 14), "z"),
             sections=6)

# 架線柱風ポール+垂れワイヤー
cyl(S, 0.08, 4.6, (7.0, 2.3, -0.5), M("pipe", (0, 0, 0)))
pipe_run(S, (7.0, 4.5, -0.5), (4.5, 5.3, -6.1), r=0.02, joints=False)
pipe_run(S, (-7.3, 4.4, -6.0), (-2.0, 3.9, -6.1), r=0.02, joints=False)

# 退廃演出
decay_scatter(S, (-7.0, 7.0), (-5.5, 6.0), seed=7, n_rubble=34,
              n_trash=16, n_stain=14, n_puddle=10)

out = os.path.join(os.path.dirname(__file__), "abandoned_rail.glb")
size = export(S, out)
print(f"OK abandoned_rail.glb {size/1e6:.2f} MB, geoms={len(S.geometry)}")
