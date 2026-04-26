#!/usr/bin/env python3
"""
Generate the spaiOS project logo.

Layout: "spai" + [neural-sphere] + "S"
The sphere replaces the O. Colors match app design tokens (tokens.py).
"""

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

random.seed(42)

# ── Canvas ─────────────────────────────────────────────────────────────────────
W, H = 2816, 1536
OUT = Path("docs/logos/spaiOS-logo.png")
FONT_PATH = "/usr/share/fonts/truetype/ubuntu/UbuntuSans[wdth,wght].ttf"
FONT_SIZE = 580

# ── Colors (from tokens.py) ────────────────────────────────────────────────────
BG            = (10,  10,  20)
SPHERE_DEEP   = (120, 100, 255)   # SPHERE_IDLE_COLOR   — purple core
SPHERE_SURF   = (80,  160, 255)   # SPHERE_THINKING_COLOR — cyan surface
NODE_HOT      = (220, 240, 255)   # bright firing node (near-white cyan)
SPARK_CLR     = (150, 225, 255)   # signal streak
TEXT_CYAN     = (78,  201, 255)   # left text
TEXT_MID      = (52,  155, 248)
TEXT_BLUE     = (28,  110, 230)   # right text


# ── Helpers ────────────────────────────────────────────────────────────────────

def lerp_color(c1: tuple, c2: tuple, t: float) -> tuple:
    t = max(0.0, min(1.0, t))
    return tuple(int(c1[k] + (c2[k] - c1[k]) * t) for k in range(3))


def fibonacci_sphere(n: int) -> list:
    """Evenly distributed points on a unit sphere via Fibonacci lattice."""
    phi = (1 + 5 ** 0.5) / 2
    pts = []
    for i in range(n):
        theta = math.acos(1 - 2 * (i + 0.5) / n)
        psi = 2 * math.pi * i / phi
        pts.append((
            math.sin(theta) * math.cos(psi),
            math.sin(theta) * math.sin(psi),
            math.cos(theta),
        ))
    return pts


def rotate_y(pts: list, a: float) -> list:
    ca, sa = math.cos(a), math.sin(a)
    return [(x * ca + z * sa, y, -x * sa + z * ca) for x, y, z in pts]


def rotate_x(pts: list, a: float) -> list:
    ca, sa = math.cos(a), math.sin(a)
    return [(x, y * ca - z * sa, y * sa + z * ca) for x, y, z in pts]


def project(x3, y3, z3, cx, cy, r):
    return cx + x3 * r, cy + y3 * r, z3


def dist3d(a, b):
    return math.sqrt(sum((a[k] - b[k]) ** 2 for k in range(3)))


def hgrad_image(x0: int, x1: int, c_left: tuple, c_right: tuple) -> Image.Image:
    """1-row horizontal gradient from x0 to x1, full canvas width."""
    w = x1 - x0
    strip = Image.new("RGB", (w, 1))
    for px in range(w):
        t = px / max(w - 1, 1)
        strip.putpixel((px, 0), lerp_color(c_left, c_right, t))
    tall = strip.resize((w, H), Image.NEAREST)
    canvas = Image.new("RGB", (W, H), (0, 0, 0))
    canvas.paste(tall, (x0, 0))
    return canvas.convert("RGBA")


def apply_gradient_text(
    base: Image.Image,
    text: str,
    x: float,
    y: float,
    c_left: tuple,
    c_right: tuple,
    width: float,
) -> Image.Image:
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).text((int(x), int(y)), text, font=font, fill=255)
    grad = hgrad_image(int(x), int(x + width) + 1, c_left, c_right)
    grad.putalpha(mask)
    return Image.alpha_composite(base, grad)


# ── Font ───────────────────────────────────────────────────────────────────────
font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
try:
    # UbuntuSans[wdth,wght].ttf — axis order: wdth (75-125), wght (100-900)
    font.set_variation_by_axes([100, 800])
    print("Font variation set: wdth=100 wght=800")
except Exception as e:
    print(f"Font variation not applied: {e}")

# ── Layout ─────────────────────────────────────────────────────────────────────
_tmp_img = Image.new("RGBA", (1, 1))
_tmp_d   = ImageDraw.Draw(_tmp_img)
cap_bbox = _tmp_d.textbbox((0, 0), "A", font=font)
cap_h    = cap_bbox[3] - cap_bbox[1]   # pixel height of a capital
cap_top  = cap_bbox[1]                  # ascender gap from origin

spai_bbox = _tmp_d.textbbox((0, 0), "spai", font=font)
s_bbox    = _tmp_d.textbbox((0, 0), "S",    font=font)
spai_w    = spai_bbox[2] - spai_bbox[0]
s_w       = s_bbox[2]    - s_bbox[0]

SPHERE_R  = cap_h // 2
GAP       = int(FONT_SIZE * 0.035)  # kerning between letter and sphere

total_w   = spai_w + GAP + SPHERE_R * 2 + GAP + s_w
start_x   = (W - total_w) / 2
text_y    = (H - cap_h) / 2 - cap_top

# Sphere vertically centered with capital letters (same as "S" center = H/2)
SCX       = start_x + spai_w + GAP + SPHERE_R
SCY       = H / 2
S_X       = SCX + SPHERE_R + GAP

# ── Sphere geometry ─────────────────────────────────────────────────────────────
N_NODES   = 90
nodes     = fibonacci_sphere(N_NODES)
nodes     = rotate_y(nodes, math.pi * 0.18)
nodes     = rotate_x(nodes, math.pi * 0.08)

EDGE_THR  = 0.50
edges     = [
    (i, j)
    for i in range(N_NODES)
    for j in range(i + 1, N_NODES)
    if dist3d(nodes[i], nodes[j]) < EDGE_THR
]
by_depth  = sorted(range(N_NODES), key=lambda i: nodes[i][2])

# Firing nodes: front-facing with ~22% probability
firing    = {i for i in range(N_NODES) if nodes[i][2] > 0.25 and random.random() < 0.22}

print(f"Nodes: {N_NODES}, Edges: {len(edges)}, Firing: {len(firing)}")
print(f"Sphere R: {SPHERE_R}px  Cap H: {cap_h}px  Total W: {total_w}px")

# ── Build image ─────────────────────────────────────────────────────────────────
img = Image.new("RGBA", (W, H), (*BG, 255))

# Background vignette — slightly darker at corners
vig   = Image.new("RGBA", (W, H), (0, 0, 0, 0))
vig_d = ImageDraw.Draw(vig)
for s in range(60):
    t  = s / 60
    rw = int(W * (1 - t * 0.55))
    rh = int(H * (1 - t * 0.55))
    vig_d.ellipse([W // 2 - rw, H // 2 - rh, W // 2 + rw, H // 2 + rh],
                  fill=(0, 0, 10, int(t * 3)))
img = Image.alpha_composite(img, vig)

# ── Helper: circular clip mask for sphere ──────────────────────────────────────
# Used to keep mesh/nodes inside the sphere silhouette
sphere_mask = Image.new("L", (W, H), 0)
ImageDraw.Draw(sphere_mask).ellipse(
    [int(SCX - SPHERE_R), int(SCY - SPHERE_R),
     int(SCX + SPHERE_R), int(SCY + SPHERE_R)],
    fill=255,
)

import PIL.ImageChops as IC

def clip_to_sphere(layer: Image.Image) -> Image.Image:
    """Return layer with alpha clamped by sphere_mask."""
    r, g, b, a = layer.split()
    a_clipped   = IC.darker(a, sphere_mask)
    return Image.merge("RGBA", (r, g, b, a_clipped))


# ── Sphere: layered outer halos (soft, not clipped) ───────────────────────────
halo   = Image.new("RGBA", (W, H), (0, 0, 0, 0))
halo_d = ImageDraw.Draw(halo)
for scale, alpha, col in [
    (3.0, 6,   SPHERE_SURF),
    (2.2, 18,  SPHERE_SURF),
    (1.6, 35,  SPHERE_DEEP),
    (1.18, 65, SPHERE_DEEP),
]:
    r = int(SPHERE_R * scale)
    halo_d.ellipse([SCX - r, SCY - r, SCX + r, SCY + r], fill=(*col, alpha))
img = Image.alpha_composite(img, halo.filter(ImageFilter.GaussianBlur(SPHERE_R * 0.65)))

# ── Sphere: luminous inner glow — the sphere glows from within ────────────────
body   = Image.new("RGBA", (W, H), (0, 0, 0, 0))
body_d = ImageDraw.Draw(body)
# Layer 1: very faint dark disk to slightly darken sphere interior vs bg
body_d.ellipse(
    [int(SCX - SPHERE_R), int(SCY - SPHERE_R),
     int(SCX + SPHERE_R), int(SCY + SPHERE_R)],
    fill=(10, 6, 30, 40),
)
# Layer 2: strong radial glow — sphere lit from within, bright center
for s in range(50):
    t     = 1 - s / 50
    r     = int(SPHERE_R * 0.85 * t)
    if t > 0.55:
        col = lerp_color(SPHERE_SURF, NODE_HOT, (t - 0.55) / 0.45)
    else:
        col = lerp_color(SPHERE_DEEP, SPHERE_SURF, t / 0.55)
    alpha = int(t ** 1.2 * 75)
    body_d.ellipse([int(SCX - r), int(SCY - r), int(SCX + r), int(SCY + r)],
                   fill=(*col, alpha))
img = Image.alpha_composite(img, clip_to_sphere(body))

# ── Sphere: mesh edges (clipped to globe) ─────────────────────────────────────
e_layer  = Image.new("RGBA", (W, H), (0, 0, 0, 0))
e_draw   = ImageDraw.Draw(e_layer)
for i, j in edges:
    x1, y1, _ = project(*nodes[i], SCX, SCY, SPHERE_R)
    x2, y2, _ = project(*nodes[j], SCX, SCY, SPHERE_R)
    avg_z = (nodes[i][2] + nodes[j][2]) / 2
    depth = (avg_z + 1) / 2         # 0 = back, 1 = front
    # Limb darkening: edges near silhouette edge are dimmer
    edge_dist = math.sqrt(((x1 + x2) / 2 - SCX) ** 2 + ((y1 + y2) / 2 - SCY) ** 2)
    limb = max(0.0, 1.0 - (edge_dist / SPHERE_R) ** 2.5)
    alpha = int((80 + 175 * depth) * (0.15 + 0.85 * limb))
    # Front edges bright near-white-cyan; back edges dim purple
    col = lerp_color(SPHERE_DEEP, NODE_HOT, depth ** 0.55)
    lw  = max(1, int(1 + depth * 2.5))
    e_draw.line([(int(x1), int(y1)), (int(x2), int(y2))], fill=(*col, alpha), width=lw)
e_blur = clip_to_sphere(e_layer.filter(ImageFilter.GaussianBlur(1.0)))
img = Image.alpha_composite(img, e_blur)
img = Image.alpha_composite(img, clip_to_sphere(e_layer))

# ── Sphere outline ring ────────────────────────────────────────────────────────
ring   = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ring_d = ImageDraw.Draw(ring)
ring_d.ellipse(
    [int(SCX - SPHERE_R), int(SCY - SPHERE_R),
     int(SCX + SPHERE_R), int(SCY + SPHERE_R)],
    outline=(*SPHERE_SURF, 130), width=3,
)
img = Image.alpha_composite(img, ring.filter(ImageFilter.GaussianBlur(3)))
img = Image.alpha_composite(img, ring)

# ── Sphere: nodes back → front (clipped) ──────────────────────────────────────
n_layer  = Image.new("RGBA", (W, H), (0, 0, 0, 0))
n_draw   = ImageDraw.Draw(n_layer)
for idx in by_depth:
    x3, y3, z3 = nodes[idx]
    px, py, _  = project(x3, y3, z3, SCX, SCY, SPHERE_R)
    depth = (z3 + 1) / 2
    if idx in firing:
        nr    = int(4 + 4 * depth)
        col   = lerp_color(SPHERE_SURF, NODE_HOT, depth)
        alpha = min(255, int(195 + 60 * depth))
    else:
        nr    = int(1 + 3 * depth)
        col   = lerp_color(SPHERE_DEEP, SPHERE_SURF, depth)
        alpha = int(65 + 145 * depth)
    n_draw.ellipse([int(px - nr), int(py - nr), int(px + nr), int(py + nr)],
                   fill=(*col, alpha))
img = Image.alpha_composite(img, clip_to_sphere(n_layer.filter(ImageFilter.GaussianBlur(5))))
img = Image.alpha_composite(img, clip_to_sphere(n_layer))

# ── Signal sparks — only from nodes near the sphere surface edge (visible pop) ─
sp_layer  = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sp_draw   = ImageDraw.Draw(sp_layer)
for idx in firing:
    x3, y3, z3 = nodes[idx]
    if z3 < 0.15:
        continue
    px, py, _ = project(x3, y3, z3, SCX, SCY, SPHERE_R)
    # Radial direction from sphere center
    ox, oy = px - SCX, py - SCY
    ol     = math.sqrt(ox * ox + oy * oy) or 1
    ox, oy = ox / ol, oy / ol

    n_sparks = random.randint(2, 4)
    for _ in range(n_sparks):
        ang    = random.uniform(-0.5, 0.5)
        ca, sa = math.cos(ang), math.sin(ang)
        dx, dy = ox * ca - oy * sa, ox * sa + oy * ca

        # Start just outside sphere surface
        start_dist = SPHERE_R + random.uniform(4, 10)
        length     = random.uniform(SPHERE_R * 0.20, SPHERE_R * 0.65)
        sx1 = int(SCX + ox * start_dist)
        sy1 = int(SCY + oy * start_dist)
        sx2 = int(SCX + ox * start_dist + dx * length)
        sy2 = int(SCY + oy * start_dist + dy * length)

        alpha = random.randint(100, 190)
        lw    = random.randint(1, 3)
        sp_draw.line([(sx1, sy1), (sx2, sy2)], fill=(*SPARK_CLR, alpha), width=lw)
        # Glowing tip dot
        tr = random.randint(3, 6)
        sp_draw.ellipse([sx2 - tr, sy2 - tr, sx2 + tr, sy2 + tr],
                        fill=(*NODE_HOT, alpha))

img = Image.alpha_composite(img, sp_layer.filter(ImageFilter.GaussianBlur(3)))
img = Image.alpha_composite(img, sp_layer)

# ── Text glow pass (soft blur first) ──────────────────────────────────────────
glow  = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd    = ImageDraw.Draw(glow)
gd.text((int(start_x), int(text_y)), "spai", font=font, fill=(*TEXT_CYAN, 65))
gd.text((int(S_X),     int(text_y)), "S",    font=font, fill=(*TEXT_BLUE, 65))
img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(20)))

# ── Text sharp gradient pass ────────────────────────────────────────────────────
img = apply_gradient_text(img, "spai", start_x, text_y, TEXT_CYAN, TEXT_MID,  spai_w)
img = apply_gradient_text(img, "S",    S_X,     text_y, TEXT_MID,  TEXT_BLUE, s_w)

# ── Save ────────────────────────────────────────────────────────────────────────
OUT.parent.mkdir(parents=True, exist_ok=True)
img.convert("RGB").save(str(OUT), "PNG", optimize=True)
print(f"Saved: {OUT}  ({W}x{H})")
