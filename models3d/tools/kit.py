# -*- coding: utf-8 -*-
"""
kit.py — 2Dマップ背景画像を3D(GLB)へ再現するためのプロシージャルモデリング・キット。

trimesh + Pillow で構築する。ネオン看板の日本語テキストは IPAゴシック で
テクスチャに描画し、emissive マテリアルで発光させる。
座標系: glTF準拠 (Y-up, メートル単位)。
"""
import math
import random

import numpy as np
import trimesh
from trimesh.transformations import rotation_matrix, translation_matrix
from trimesh.visual.material import PBRMaterial
from trimesh.visual.texture import TextureVisuals
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

JP_FONT = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"


# ---------------------------------------------------------------- materials
def _pot(img):
    """テクスチャを2のべき乗サイズへリサイズ(NPOTでレンダラが崩れる対策)。"""
    if img is None:
        return None
    def p2(v):
        return max(32, min(1024, 1 << max(5, int(round(math.log2(v))))))
    w, h = img.size
    nw, nh = p2(w), p2(h)
    if (nw, nh) != (w, h):
        img = img.resize((nw, nh), Image.LANCZOS)
    return img


def mat(name, color, metallic=0.2, rough=0.85, emissive=None, tex=None,
        emissive_tex=None):
    tex = _pot(tex)
    emissive_tex = _pot(emissive_tex)
    m = PBRMaterial(
        name=name,
        baseColorFactor=[*color, 1.0] if len(color) == 3 else list(color),
        metallicFactor=metallic,
        roughnessFactor=rough,
    )
    if emissive is not None:
        m.emissiveFactor = list(emissive)
    if tex is not None:
        m.baseColorTexture = tex
    if emissive_tex is not None:
        m.emissiveTexture = emissive_tex
    return m


# 共通マテリアル(遅延生成せず即時定義。色は各背景画像のパレットから採取)
MATS = {}


def M(name, *a, **kw):
    if name not in MATS:
        MATS[name] = mat(name, *a, **kw)
    return MATS[name]


def std_mats():
    """全マップ共通の基本マテリアル群。退廃世界観: 金属は錆びてくすみ、
    彩度低め・茶系に寄せる。"""
    M("metal_dark",   (0.058, 0.054, 0.058), metallic=0.55, rough=0.75)
    M("metal_mid",    (0.105, 0.095, 0.090), metallic=0.50, rough=0.80)
    M("metal_rust",   (0.190, 0.115, 0.075), metallic=0.25, rough=1.00)
    M("frame_black",  (0.026, 0.024, 0.026), metallic=0.45, rough=0.85)
    M("concrete",     (0.095, 0.090, 0.095), metallic=0.03, rough=1.00)
    M("wood_dark",    (0.130, 0.090, 0.060), metallic=0.02, rough=1.00)
    M("cloth_dark",   (0.080, 0.062, 0.070), metallic=0.00, rough=1.00)
    M("pipe",         (0.085, 0.075, 0.070), metallic=0.60, rough=0.70)
    M("cable",        (0.030, 0.030, 0.036), metallic=0.10, rough=0.95)
    M("rubble",       (0.105, 0.098, 0.092), metallic=0.02, rough=1.00)
    M("trash_paper",  (0.34, 0.31, 0.26), metallic=0.0, rough=1.00)
    # 発光体
    M("neon_pink",  (1.00, 0.25, 0.62), emissive=(1.00, 0.15, 0.55), rough=0.4)
    M("neon_blue",  (0.25, 0.65, 1.00), emissive=(0.15, 0.55, 1.00), rough=0.4)
    M("neon_cyan",  (0.20, 0.95, 0.90), emissive=(0.10, 0.90, 0.85), rough=0.4)
    M("neon_red",   (1.00, 0.12, 0.10), emissive=(1.00, 0.08, 0.06), rough=0.4)
    M("neon_amber", (1.00, 0.55, 0.15), emissive=(1.00, 0.45, 0.10), rough=0.4)
    M("lamp_warm",  (1.00, 0.80, 0.45), emissive=(1.00, 0.70, 0.35), rough=0.4)


# ---------------------------------------------------------------- primitives
def T(x=0.0, y=0.0, z=0.0):
    return translation_matrix([x, y, z])


def R(deg, axis):
    ax = {"x": [1, 0, 0], "y": [0, 1, 0], "z": [0, 0, 1]}[axis]
    return rotation_matrix(math.radians(deg), ax)


def box(scene, size, pos, material, rot=None, name=None):
    """size=(sx,sy,sz), pos=中心座標。"""
    g = trimesh.creation.box(extents=list(size))
    g.visual = TextureVisuals(material=material)
    tf = T(*pos)
    if rot is not None:
        tf = tf @ rot
    g.apply_transform(tf)
    scene.add_geometry(g, node_name=name)
    return g


def cyl(scene, radius, height, pos, material, rot=None, sections=24, name=None):
    """Y軸方向の円柱。pos=中心座標。"""
    g = trimesh.creation.cylinder(radius=radius, height=height,
                                  sections=sections)
    g.apply_transform(R(90, "x"))  # trimeshはZ軸柱 → Y軸柱へ
    g.visual = TextureVisuals(material=material)
    tf = T(*pos)
    if rot is not None:
        tf = tf @ rot
    g.apply_transform(tf)
    scene.add_geometry(g, node_name=name)
    return g


def cone(scene, radius, height, pos, material, rot=None, sections=24,
         name=None):
    g = trimesh.creation.cone(radius=radius, height=height, sections=sections)
    g.apply_transform(R(90, "x"))
    g.visual = TextureVisuals(material=material)
    tf = T(*pos)
    if rot is not None:
        tf = tf @ rot
    g.apply_transform(tf)
    scene.add_geometry(g, node_name=name)
    return g


def sphere(scene, radius, pos, material, name=None, subdivisions=2):
    g = trimesh.creation.icosphere(subdivisions=subdivisions, radius=radius)
    g.visual = TextureVisuals(material=material)
    g.apply_transform(T(*pos))
    scene.add_geometry(g, node_name=name)
    return g


def quad(scene, w, h, pos, material, rot=None, uv=None, name=None,
         double=True):
    """XY平面上の板ポリ(+Z向き)。テクスチャ用UV付き。"""
    hw, hh = w / 2.0, h / 2.0
    v = np.array([[-hw, -hh, 0], [hw, -hh, 0], [hw, hh, 0], [-hw, hh, 0]],
                 dtype=np.float64)
    f = [[0, 1, 2], [0, 2, 3]]
    if double:
        f += [[0, 2, 1], [0, 3, 2]]
    g = trimesh.Trimesh(vertices=v, faces=np.array(f), process=False)
    if uv is None:
        uv = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float64)
    g.visual = TextureVisuals(uv=uv, material=material)
    tf = T(*pos)
    if rot is not None:
        tf = tf @ rot
    g.apply_transform(tf)
    scene.add_geometry(g, node_name=name)
    return g


# ---------------------------------------------------------------- textures
def _font(size, path=JP_FONT):
    return ImageFont.truetype(path, size)


def grunge(img, seed=1, strength=0.55, streaks=True, dust=True):
    """汚し処理: 黒ずみシミ+錆だれの縦筋+土埃。全テクスチャに適用可能。"""
    rng = random.Random(seed)
    W, H = img.size
    # 黒ずみシミ
    ov = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(ov)
    for _ in range(int(120 * strength)):
        x, y = rng.randint(0, W), rng.randint(0, H)
        r = rng.randint(4, int(20 + 60 * strength))
        d.ellipse([x - r, y - r, x + r, y + r],
                  fill=rng.randint(25, 110))
    ov = ov.filter(ImageFilter.GaussianBlur(max(2, W // 160)))
    dark = Image.new("RGB", (W, H), (9, 8, 7))
    img = Image.composite(dark, img,
                          ov.point(lambda v: int(v * strength)))
    # 錆だれ(上から下へ垂れる筋)
    if streaks:
        st = Image.new("L", (W, H), 0)
        ds = ImageDraw.Draw(st)
        for _ in range(int(26 * strength)):
            x = rng.randint(0, W)
            y0 = rng.randint(0, H // 2)
            ln = rng.randint(H // 8, H // 2)
            ds.line([(x, y0), (x + rng.randint(-5, 5), y0 + ln)],
                    fill=rng.randint(40, 110), width=rng.randint(2, 6))
            ds.ellipse([x - 5, y0 - 4, x + 5, y0 + 4],
                       fill=rng.randint(60, 120))
        st = st.filter(ImageFilter.GaussianBlur(2))
        rust = Image.new("RGB", (W, H), (64, 40, 22))
        img = Image.composite(rust, img, st)
    # 土埃(下辺・角に溜まる)
    if dust:
        du = Image.new("L", (W, H), 0)
        dd = ImageDraw.Draw(du)
        for _ in range(int(60 * strength)):
            x = rng.randint(0, W)
            y = H - abs(int(rng.gauss(0, H * 0.18)))
            r = rng.randint(6, 30)
            dd.ellipse([x - r, y - r // 2, x + r, y + r // 2],
                       fill=rng.randint(20, 70))
        du = du.filter(ImageFilter.GaussianBlur(6))
        dusty = Image.new("RGB", (W, H), (52, 44, 34))
        img = Image.composite(dusty, img, du)
    return img


def age_paper(img, seed=1, strength=0.7):
    """張り紙の経年劣化: 黄ばみ・シミ・破れ縁・めくれ角・テープ。"""
    rng = random.Random(seed)
    W, H = img.size
    # 黄ばみ(乗算)
    tint = Image.new("RGB", (W, H), (232, 210, 168))
    img = Image.blend(img, ImageChops.multiply(img, tint), 0.85)
    d = ImageDraw.Draw(img)
    # 水シミ
    for _ in range(int(8 * strength)):
        x, y = rng.randint(0, W), rng.randint(0, H)
        r = rng.randint(W // 10, W // 3)
        for k in range(3):
            d.ellipse([x - r + k * 2, y - r // 2 + k, x + r - k * 2,
                       y + r // 2 - k],
                      outline=(150 - k * 12, 128 - k * 10, 95 - k * 8))
    # 破れた縁(黒く欠けさせる=背景色で塗る)
    edge = (12, 11, 12)
    for _ in range(int(14 * strength)):
        side = rng.randint(0, 3)
        if side == 0:
            x, y = rng.randint(0, W), 0
        elif side == 1:
            x, y = rng.randint(0, W), H
        elif side == 2:
            x, y = 0, rng.randint(0, H)
        else:
            x, y = W, rng.randint(0, H)
        pts = [(x + rng.randint(-14, 14), y + rng.randint(-10, 10))
               for _ in range(5)]
        d.polygon(pts, fill=edge)
    # めくれ角(暗い三角)
    cw = rng.randint(W // 8, W // 4)
    corner = rng.choice([(0, 0, 1, 1), (W, 0, -1, 1), (0, H, 1, -1),
                         (W, H, -1, -1)])
    cx, cy, sx, sy = corner
    d.polygon([(cx, cy), (cx + sx * cw, cy), (cx, cy + sy * cw)], fill=edge)
    d.polygon([(cx + sx * cw, cy), (cx, cy + sy * cw),
               (cx + sx * cw * 0.55, cy + sy * cw * 0.55)],
              fill=(168, 152, 120))
    # セロテープ
    for _ in range(2):
        tx = rng.randint(0, W - 40)
        d.rectangle([tx, 0, tx + rng.randint(24, 44), rng.randint(10, 18)],
                    fill=(185, 178, 158))
    return img


def neon_sign_tex(text, fg=(255, 60, 150), bg=(8, 6, 12), size=(1024, 256),
                  border=True, border_col=None, sub=None, sub_fg=None,
                  vertical=False, font_scale=0.62, flicker=True, seed=None):
    """発光看板テクスチャ。退廃仕様: 文字ごとに管が死んでいたり弱っていたり、
    枠の管も途切れ、パネルは煤けている。"""
    rng = random.Random(seed if seed is not None
                        else sum(ord(c) for c in text) * 7 + len(text))
    W, H = size
    img = Image.new("RGB", size, bg)

    def dim(c, f_):
        return tuple(int(v * f_) for v in c)

    def levels(n):
        lv = []
        for _ in range(n):
            r = rng.random()
            if flicker and r < 0.16:
                lv.append(rng.uniform(0.08, 0.25))    # 死にかけの管
            elif flicker and r < 0.36:
                lv.append(rng.uniform(0.5, 0.75))     # 弱った管
            else:
                lv.append(1.0)
        if n and max(lv) < 0.5:
            lv[rng.randrange(n)] = 1.0
        return lv

    glow = Image.new("RGB", size, (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    d = ImageDraw.Draw(img)

    # 文字位置と輝度を先に決め、グロー→シャープの順に2回描く
    chars = []   # (ch, x, y, font, color)
    if vertical:
        fs = int(W * font_scale)
        f = _font(fs)
        total = len(text)
        pad = (H - fs * total) // (total + 1)
        lv = levels(total)
        y = pad
        for i, ch in enumerate(text):
            bbox = d.textbbox((0, 0), ch, font=f)
            x = (W - (bbox[2] - bbox[0])) // 2 - bbox[0]
            chars.append((ch, x, y, f, dim(fg, lv[i])))
            y += fs + pad
    else:
        fs = int(H * (font_scale if sub is None else font_scale * 0.82))
        f = _font(fs)
        widths = [d.textlength(ch, font=f) for ch in text]
        total_w = sum(widths)
        bbox = d.textbbox((0, 0), text, font=f)
        x = (W - total_w) // 2
        y = (H - (bbox[3] - bbox[1])) // 2 - bbox[1]
        if sub:
            y = int(H * 0.08)
        lv = levels(len(text))
        for i, ch in enumerate(text):
            chars.append((ch, int(x), y, f, dim(fg, lv[i])))
            x += widths[i]
        if sub:
            f2 = _font(int(H * 0.18))
            bbox2 = d.textbbox((0, 0), sub, font=f2)
            x2 = (W - (bbox2[2] - bbox2[0])) // 2 - bbox2[0]
            sub_lv = 1.0 if not flicker or rng.random() > 0.3 else 0.4
            chars.append((sub, x2, int(H * 0.72), f2,
                          dim(sub_fg or fg, sub_lv)))
    for (ch, x, y, f_, c) in chars:
        gd.text((x, y), ch, font=f_, fill=c)
    blur = glow.filter(ImageFilter.GaussianBlur(H // 24 if not vertical
                                                else W // 24))
    img = Image.blend(img, Image.blend(img, blur, 0.9), 0.55)
    d = ImageDraw.Draw(img)
    for (ch, x, y, f_, c) in chars:
        d.text((x, y), ch, font=f_, fill=c)

    if border:
        bc = border_col or fg
        # 枠の管も部分的に死んでいる: 辺を分割して描き、所々消す
        edges = [((6, 6), (W - 7, 6)), ((W - 7, 6), (W - 7, H - 7)),
                 ((W - 7, H - 7), (6, H - 7)), ((6, H - 7), (6, 6))]
        for (p0, p1) in edges:
            segs = 6
            for si in range(segs):
                r = rng.random()
                if flicker and r < 0.18:
                    continue                       # 消えた区間
                f_ = 0.45 if (flicker and r < 0.38) else 1.0
                t0, t1 = si / segs, (si + 1) / segs
                a = (p0[0] + (p1[0] - p0[0]) * t0,
                     p0[1] + (p1[1] - p0[1]) * t0)
                b = (p0[0] + (p1[0] - p0[0]) * t1,
                     p0[1] + (p1[1] - p0[1]) * t1)
                d.line([a, b], fill=dim(bc, f_), width=3)
    # パネルの煤け
    img = grunge(img, seed=rng.randint(0, 9999), strength=0.3,
                 streaks=True, dust=False)
    return img


def neon_sign(scene, text, w, h, pos, rot=None, fg=(255, 60, 150),
              bg=(8, 6, 12), frame_mat=None, sub=None, sub_fg=None,
              vertical=False, depth=0.08, name=None, font_scale=0.62,
              tex_h=256):
    """枠付き発光看板を配置。板ポリ(発光テクスチャ)+背面フレーム箱。"""
    ar = max(1, int(tex_h * (w / h)))
    tex = neon_sign_tex(text, fg=fg, bg=bg, size=(ar, tex_h), sub=sub,
                        sub_fg=sub_fg, vertical=vertical,
                        font_scale=font_scale)
    m = mat(name or f"sign_{text[:6]}", (1, 1, 1), metallic=0.0, rough=0.5,
            emissive=(1.6, 1.6, 1.6), tex=tex, emissive_tex=tex)
    fm = frame_mat or M("frame_black", (0.022, 0.022, 0.030))
    # フレーム
    fb = trimesh.creation.box(extents=[w + 0.12, h + 0.12, depth])
    fb.visual = TextureVisuals(material=fm)
    tf = T(*pos)
    if rot is not None:
        tf = tf @ rot
    fb.apply_transform(tf @ T(0, 0, -depth / 2 - 0.005))
    scene.add_geometry(fb)
    quad(scene, w, h, pos, m, rot=rot, name=name)
    return m


def screen_tex(size=(512, 512), base=(10, 14, 30), kind="ui", seed=1,
               hue=(90, 170, 255)):
    """モニタ画面のノイズUIテクスチャ。kind: ui / static / map / list"""
    rng = random.Random(seed)
    img = Image.new("RGB", size, base)
    d = ImageDraw.Draw(img)
    W, H = size
    if kind == "ui":
        for _ in range(rng.randint(18, 30)):
            x0 = rng.randint(0, W - 40)
            y0 = rng.randint(0, H - 20)
            w = rng.randint(20, W // 3)
            h = rng.randint(4, 26)
            c = tuple(int(v * rng.uniform(0.25, 1.0)) for v in hue)
            if rng.random() < 0.5:
                d.rectangle([x0, y0, x0 + w, y0 + h], outline=c)
            else:
                d.rectangle([x0, y0, x0 + w, y0 + h], fill=c)
        for _ in range(14):
            y = rng.randint(0, H - 1)
            d.line([(rng.randint(0, W // 2), y),
                    (rng.randint(W // 2, W), y)],
                   fill=tuple(int(v * 0.8) for v in hue), width=1)
    elif kind == "static":
        px = img.load()
        for yy in range(0, H, 2):
            for xx in range(0, W, 2):
                v = rng.randint(0, 90)
                px[xx, yy] = (v // 2, v // 2 + 8, v + 20)
    elif kind == "wave":
        cx = tuple(hue)
        for x in range(0, W - 1, 3):
            y = int(H / 2 + math.sin(x * 0.06 + seed) * H * 0.22
                    * rng.uniform(0.5, 1.0))
            d.line([(x, H // 2), (x, y)], fill=cx, width=2)
    return img


def led_panel_tex(size=(256, 512), seed=3):
    """サーバーラック前面のLEDテクスチャ(黒地に色ドット列)。"""
    rng = random.Random(seed)
    img = Image.new("RGB", size, (6, 7, 10))
    d = ImageDraw.Draw(img)
    W, H = size
    for y in range(18, H - 10, 26):
        d.rectangle([8, y - 9, W - 8, y + 11], fill=(12, 13, 18))
        for x in range(20, W - 16, 18):
            if rng.random() < 0.55:
                c = rng.choice([(40, 255, 120), (60, 160, 255),
                                (255, 70, 60), (255, 170, 40)])
                if rng.random() < 0.35:
                    c = tuple(v // 5 for v in c)
                d.ellipse([x, y - 3, x + 6, y + 3], fill=c)
    return img


def tile_floor_tex(size=(1024, 1024), tile=64, base=(16, 18, 26),
                   groove=(6, 7, 11), seed=7, wet_spots=None):
    """濡れたタイル床。wet_spots=[(u,v,r,(r,g,b)), ...] 0-1座標のネオン反射。"""
    rng = random.Random(seed)
    img = Image.new("RGB", size, base)
    d = ImageDraw.Draw(img)
    W, H = size
    for ty in range(0, H, tile):
        for tx in range(0, W, tile):
            v = rng.uniform(0.72, 1.15)
            c = tuple(min(255, int(b * v)) for b in base)
            d.rectangle([tx + 1, ty + 1, tx + tile - 2, ty + tile - 2],
                        fill=c)
            r = rng.random()
            if r < 0.05:            # 剥がれ落ちたタイル(下地の土)
                d.rectangle([tx + 1, ty + 1, tx + tile - 2, ty + tile - 2],
                            fill=(24, 19, 14))
                for _ in range(5):
                    px_ = tx + rng.randint(3, tile - 6)
                    py_ = ty + rng.randint(3, tile - 6)
                    d.ellipse([px_, py_, px_ + rng.randint(2, 7),
                               py_ + rng.randint(2, 5)], fill=(38, 32, 24))
            elif r < 0.17:          # ひび割れたタイル
                x0, y0 = tx + rng.randint(2, tile - 4), ty + 2
                pts = [(x0, y0)]
                while pts[-1][1] < ty + tile - 4:
                    pts.append((pts[-1][0] + rng.randint(-7, 7),
                                pts[-1][1] + rng.randint(6, 16)))
                d.line(pts, fill=(6, 6, 7), width=2)
            elif r < 0.30:          # 汚れ
                d.rectangle([tx + 6, ty + 6, tx + tile - 8, ty + tile - 8],
                            fill=tuple(int(x * 0.7) for x in c))
    for t in range(0, W, tile):
        d.line([(t, 0), (t, H)], fill=groove, width=2)
        d.line([(0, t), (W, t)], fill=groove, width=2)
    img = grunge(img, seed=seed + 5, strength=0.5, streaks=False)
    if wet_spots:
        ref = Image.new("RGB", size, (0, 0, 0))
        rd = ImageDraw.Draw(ref)
        for (u, v, r, c) in wet_spots:
            x, y = int(u * W), int(v * H)
            rr = int(r * W)
            rd.ellipse([x - rr, y - int(rr * 1.6), x + rr, y + int(rr * 1.6)],
                       fill=c)
        ref = ref.filter(ImageFilter.GaussianBlur(W // 20))
        img = Image.blend(img, Image.blend(img, ref, 0.85), 0.45)
    return img


def wall_tex(size=(1024, 512), base=(13, 14, 20), seed=11, panel=128):
    """金属パネル壁。リベットとパネル継ぎ目。"""
    rng = random.Random(seed)
    img = Image.new("RGB", size, base)
    d = ImageDraw.Draw(img)
    W, H = size
    for py in range(0, H, panel):
        for px_ in range(0, W, panel):
            v = rng.uniform(0.82, 1.12)
            c = tuple(min(255, int(b * v)) for b in base)
            d.rectangle([px_ + 1, py + 1, px_ + panel - 2, py + panel - 2],
                        fill=c)
            for (rx, ry) in [(px_ + 8, py + 8), (px_ + panel - 10, py + 8),
                             (px_ + 8, py + panel - 10),
                             (px_ + panel - 10, py + panel - 10)]:
                d.ellipse([rx, ry, rx + 4, ry + 4],
                          fill=tuple(int(x * 0.6) for x in c))
            if rng.random() < 0.18:  # 錆だれ
                sx = rng.randint(px_ + 8, px_ + panel - 8)
                d.line([(sx, py + 4), (sx, py + rng.randint(20, panel))],
                       fill=(42, 28, 20), width=rng.randint(2, 4))
    for t in range(0, W, panel):
        d.line([(t, 0), (t, H)], fill=(5, 5, 8), width=3)
    for t in range(0, H, panel):
        d.line([(0, t), (W, t)], fill=(5, 5, 8), width=3)
    return grunge(img, seed=seed + 3, strength=0.65)


def stripe_tex(c1=(255, 60, 150), c2=(12, 10, 14), size=(512, 64), n=8):
    """警告ストライプ(斜め)。"""
    img = Image.new("RGB", size, c2)
    d = ImageDraw.Draw(img)
    W, H = size
    step = W // n
    for i in range(-1, n + 1):
        x = i * step
        d.polygon([(x, H), (x + step // 2, H), (x + step // 2 + H, 0),
                   (x + H, 0)], fill=c1)
    return img


def poster_tex(lines, size=(512, 768), bg=(24, 22, 28), fg=(190, 185, 200),
               accent=None, seed=5, title_scale=0.10, aged=True):
    """紙ポスター/掲示板テクスチャ。lines=[(text, scale, color), ...]
    aged=True で黄ばみ・破れ・シミの経年劣化を加える。"""
    img = Image.new("RGB", size, bg)
    d = ImageDraw.Draw(img)
    W, H = size
    y = int(H * 0.06)
    for (text, scale, color) in lines:
        fs = int(H * scale)
        f = _font(fs)
        bbox = d.textbbox((0, 0), text, font=f)
        x = (W - (bbox[2] - bbox[0])) // 2 - bbox[0]
        d.text((x, y), text, font=f, fill=color)
        y += int(fs * 1.35)
    d.rectangle([4, 4, W - 5, H - 5], outline=tuple(int(v * 0.5) for v in fg))
    if aged:
        img = age_paper(img, seed=seed)
    return img


def mugshot_tex(size=(512, 640), rows=3, cols=3, seed=9):
    """違反者リスト:顔写真グリッド。"""
    rng = random.Random(seed)
    img = Image.new("RGB", size, (20, 16, 22))
    d = ImageDraw.Draw(img)
    W, H = size
    f = _font(int(H * 0.08))
    d.text((int(W * 0.16), int(H * 0.02)), "違反者リスト", font=f,
           fill=(255, 90, 140))
    top = int(H * 0.16)
    cw, ch = W // cols, (H - top) // rows
    for r in range(rows):
        for c in range(cols):
            x0, y0 = c * cw + 10, top + r * ch + 8
            x1, y1 = x0 + cw - 20, y0 + ch - 26
            d.rectangle([x0, y0, x1, y1], fill=(48, 44, 52),
                        outline=(90, 80, 95))
            fx, fy = (x0 + x1) // 2, (y0 + y1) // 2
            fw, fh = (x1 - x0) // 3, (y1 - y0) // 3
            skin = rng.choice([(120, 100, 90), (105, 88, 80), (92, 78, 72)])
            d.ellipse([fx - fw, fy - fh - 6, fx + fw, fy + fh - 6], fill=skin)
            d.rectangle([fx - fw, fy + fh - 14, fx + fw, y1 - 4],
                        fill=tuple(int(v * 0.5) for v in skin))
            d.line([(x0 + 4, y1 + 8), (x1 - 4, y1 + 8)], fill=(120, 110, 120))
    return img


def timetable_tex(size=(640, 768)):
    """旧駅の時刻表。"""
    img = Image.new("RGB", size, (58, 56, 50))
    d = ImageDraw.Draw(img)
    W, H = size
    f = _font(int(H * 0.055))
    d.text((int(W * 0.22), int(H * 0.02)), "旧駅の時刻表", font=f,
           fill=(30, 28, 26))
    f2 = _font(int(H * 0.032))
    d.text((int(W * 0.10), int(H * 0.11)), "下り 方面", font=f2,
           fill=(140, 40, 40))
    d.text((int(W * 0.58), int(H * 0.11)), "上り 方面", font=f2,
           fill=(140, 40, 40))
    d.text((int(W * 0.06), int(H * 0.16)), "ネオトーキョー方面", font=f2,
           fill=(40, 38, 36))
    d.text((int(W * 0.58), int(H * 0.16)), "ハネダ 方面", font=f2,
           fill=(40, 38, 36))
    rng = random.Random(4)
    f3 = _font(int(H * 0.030))
    y = int(H * 0.22)
    for hr in range(5, 22):
        for (x, off) in [(int(W * 0.08), 0), (int(W * 0.58), 5)]:
            mins = " ".join(f"{rng.randint(0, 59):02d}"
                            for _ in range(rng.randint(1, 2)))
            d.text((x, y), f"{hr:2d}  {mins}", font=f3, fill=(45, 42, 40))
        y += int(H * 0.042)
        if y > H * 0.90:
            break
    d.text((int(W * 0.08), int(H * 0.93)), "最終電車のご案内  下り 23:47  上り 23:52",
           font=f2, fill=(150, 45, 45))
    d.rectangle([3, 3, W - 4, H - 4], outline=(35, 33, 30))
    for _ in range(30):  # 汚れ
        x0, y0 = rng.randint(0, W - 30), rng.randint(0, H - 20)
        d.ellipse([x0, y0, x0 + rng.randint(4, 26), y0 + rng.randint(3, 14)],
                  fill=(rng.randint(40, 52), rng.randint(38, 48),
                        rng.randint(34, 44)))
    return img


# ---------------------------------------------------------------- assemblies
def tex_mat(name, tex, emissive=None, metallic=0.1, rough=0.85,
            emissive_tex=None):
    return mat(name, (1, 1, 1), metallic=metallic, rough=rough,
               emissive=emissive, tex=tex, emissive_tex=emissive_tex)


def lamp(scene, pos, color_mat, pole_h=1.1, cage=True):
    """縦ポール+発光ヘッドの警告灯。"""
    x, y, z = pos
    cyl(scene, 0.035, pole_h, (x, y + pole_h / 2, z), M("pipe", (0, 0, 0)))
    box(scene, (0.16, 0.10, 0.16), (x, y + pole_h + 0.05, z),
        M("frame_black", (0, 0, 0)))
    box(scene, (0.10, 0.14, 0.10), (x, y + pole_h + 0.17, z), color_mat)
    box(scene, (0.14, 0.03, 0.14), (x, y + pole_h + 0.26, z),
        M("frame_black", (0, 0, 0)))
    if cage:
        for a in range(4):
            th = math.radians(a * 90 + 45)
            cyl(scene, 0.008, 0.22,
                (x + math.cos(th) * 0.07, y + pole_h + 0.15,
                 z + math.sin(th) * 0.07), M("pipe", (0, 0, 0)), sections=8)


def barrel(scene, pos, r=0.30, h=0.85, material=None, ribs=True):
    x, y, z = pos
    m = material or M("metal_rust", (0, 0, 0))
    cyl(scene, r, h, (x, y + h / 2, z), m)
    if ribs:
        for fy in (0.25, 0.5, 0.75):
            cyl(scene, r + 0.015, 0.03, (x, y + h * fy, z),
                M("frame_black", (0, 0, 0)))


def crate(scene, pos, size=(0.7, 0.55, 0.7), material=None, rot_y=0.0):
    m = material or M("wood_dark", (0, 0, 0))
    x, y, z = pos
    rot = R(rot_y, "y") if rot_y else None
    box(scene, size, (x, y + size[1] / 2, z), m, rot=rot)
    # 縁の補強
    fr = M("metal_dark", (0, 0, 0))
    box(scene, (size[0] + 0.02, 0.05, size[2] + 0.02),
        (x, y + size[1] - 0.02, z), fr, rot=rot)
    box(scene, (size[0] + 0.02, 0.05, size[2] + 0.02),
        (x, y + 0.03, z), fr, rot=rot)


def pipe_run(scene, p0, p1, r=0.055, material=None, joints=True):
    """2点間の直管+フランジ。"""
    m = material or M("pipe", (0, 0, 0))
    p0, p1 = np.array(p0, float), np.array(p1, float)
    d = p1 - p0
    L = float(np.linalg.norm(d))
    if L < 1e-6:
        return
    mid = (p0 + p1) / 2
    g = trimesh.creation.cylinder(radius=r, height=L, sections=16)
    g.visual = TextureVisuals(material=m)
    # Z軸→d方向
    align = trimesh.geometry.align_vectors([0, 0, 1], d / L)
    g.apply_transform(T(*mid) @ align)
    scene.add_geometry(g)
    if joints:
        for p in (p0, p1, (p0 + p1) / 2):
            gg = trimesh.creation.cylinder(radius=r * 1.35, height=r * 1.2,
                                           sections=16)
            gg.visual = TextureVisuals(material=m)
            gg.apply_transform(T(*p) @ align)
            scene.add_geometry(gg)


def fence_chainlink(scene, w, h, pos, rot=None, barbed=True):
    """金網フェンス(枠+網テクスチャ)+有刺鉄線コイル。"""
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i in range(-256, 256, 16):
        d.line([(i, 0), (i + 256, 256)], fill=(70, 74, 84, 255), width=2)
        d.line([(i + 256, 0), (i, 256)], fill=(70, 74, 84, 255), width=2)
    m = mat("chainlink", (1, 1, 1, 1), metallic=0.6, rough=0.6, tex=img)
    m.alphaMode = "BLEND"
    uv = np.array([[0, 0], [w / h, 0], [w / h, 1], [0, 1]])
    quad(scene, w, h, pos, m, rot=rot, uv=uv)
    fm = M("pipe", (0, 0, 0))
    x, y, z = pos
    # 枠(rotはY回転想定なので直接オフセットが効くように単純化: 縦ポールのみ)
    n = max(2, int(w / 1.5) + 1)
    for i in range(n):
        off = -w / 2 + i * (w / (n - 1))
        p = np.array([off, 0, 0, 1.0])
        if rot is not None:
            p = rot @ p
        cyl(scene, 0.03, h, (x + p[0], y, z + p[2]), fm, sections=10)
    if barbed:
        axis = np.array([1.0, 0, 0])
        if rot is not None:
            axis = (rot @ np.array([1.0, 0, 0, 0]))[:3]
        for i in range(int(w / 0.22)):
            t = -w / 2 + 0.11 + i * 0.22
            c = np.array([x, y, z]) + axis * t
            g = trimesh.creation.torus(major_radius=0.11, minor_radius=0.012,
                                       major_sections=16, minor_sections=6)
            g.visual = TextureVisuals(material=fm)
            g.apply_transform(T(c[0], y + h / 2 + 0.11, c[2])
                              @ R(90, "y" if abs(axis[0]) > 0.5 else "x"))
            scene.add_geometry(g)


def decay_scatter(scene, x_range, z_range, seed=1, n_rubble=22, n_trash=12,
                  n_stain=10, n_puddle=6, avoid=None):
    """瓦礫・ゴミ・シミ・水たまりを床に散乱させる退廃演出。
    avoid=[(x, z, r), ...] は避けるエリア(主要オブジェクト)。"""
    rng = random.Random(seed)
    M("stain", (0.045, 0.040, 0.036), rough=1.0)
    M("puddle", (0.035, 0.045, 0.060), metallic=0.0, rough=0.06)

    def pick():
        for _ in range(20):
            x = rng.uniform(*x_range)
            z = rng.uniform(*z_range)
            if not avoid or all((x - ax) ** 2 + (z - az) ** 2 > ar ** 2
                                for (ax, az, ar) in avoid):
                return x, z
        return None

    for _ in range(n_stain):        # 油染み・黒ずみ
        p = pick()
        if p:
            disc(scene, rng.uniform(0.2, 0.75), (p[0], 0.004, p[1]),
                 M("stain", (0,)), sections=18)
    for _ in range(n_puddle):       # 水たまり(鏡面)
        p = pick()
        if p:
            disc(scene, rng.uniform(0.25, 0.7), (p[0], 0.006, p[1]),
                 M("puddle", (0,)), sections=18)
    for _ in range(n_rubble):       # 瓦礫・剥がれたコンクリ片
        p = pick()
        if p:
            s = rng.uniform(0.05, 0.22)
            box(scene, (s, s * rng.uniform(0.3, 0.7), s * rng.uniform(0.6, 1.4)),
                (p[0], s * 0.25, p[1]),
                M("rubble", (0,)) if rng.random() < 0.7
                else M("metal_rust", (0,)),
                rot=R(rng.uniform(0, 360), "y") @ R(rng.uniform(-14, 14), "x"))
    for _ in range(n_trash):        # 丸めた紙屑・ゴミ
        p = pick()
        if p:
            g = trimesh.creation.icosphere(subdivisions=1,
                                           radius=rng.uniform(0.04, 0.09))
            g.apply_scale([1.0, rng.uniform(0.5, 0.8), 1.0])
            g.visual = TextureVisuals(material=M("trash_paper", (0,)))
            g.apply_transform(T(p[0], 0.04, p[1]))
            scene.add_geometry(g)


def disc(scene, radius, pos, material, sections=48, name=None):
    """上向き(+Y)のUV付き円盤。テクスチャは全面にマップ。"""
    th = np.linspace(0, 2 * math.pi, sections, endpoint=False)
    v = np.zeros((sections + 1, 3))
    v[1:, 0] = np.cos(th) * radius
    v[1:, 2] = np.sin(th) * radius
    uv = np.zeros((sections + 1, 2))
    uv[0] = [0.5, 0.5]
    uv[1:, 0] = 0.5 + np.cos(th) * 0.5
    uv[1:, 1] = 0.5 - np.sin(th) * 0.5
    f = [[0, ((i + 1) % sections) + 1, (i % sections) + 1]
         for i in range(sections)]
    g = trimesh.Trimesh(vertices=v, faces=np.array(f), process=False)
    g.visual = TextureVisuals(uv=uv, material=material)
    g.apply_transform(T(*pos))
    scene.add_geometry(g, node_name=name)
    return g


def export(scene, path):
    glb = trimesh.exchange.gltf.export_glb(scene)
    with open(path, "wb") as fp:
        fp.write(glb)
    return len(glb)
