#!/usr/bin/env python3
"""Generate cute 8-direction animal sprites for the rogue evolution roster.

Reads palette, size, and animation counts from spec_lock.md before every character.
Pixels are hard-edged, fully opaque or transparent, and limited to the locked palette.
"""

from __future__ import annotations

import argparse
import json
import math
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "projects" / "rogue_animals_64x64_20261021"
SPEC_PATH = PROJECT / "spec_lock.md"

DIRS = [
    ("down", 0.0, 1.0, "下"),
    ("downright", 1.0, 1.0, "右下"),
    ("right", 1.0, 0.0, "右"),
    ("upright", 1.0, -1.0, "右上"),
    ("up", 0.0, -1.0, "上"),
    ("upleft", -1.0, -1.0, "左上"),
    ("left", -1.0, 0.0, "左"),
    ("downleft", -1.0, 1.0, "左下"),
]

ACTIONS = [
    ("idle", 4, 6, True, "原地静息"),
    ("walk", 6, 8, True, "移动"),
    ("run", 6, 12, True, "快速移动"),
    ("attack", 4, 10, False, "攻击"),
    ("hurt", 2, 8, False, "受伤"),
]

CHARACTERS = [
    {
        "id": "mini_scorpion",
        "name": "迷拟蝎",
        "animal": "伪拟蝎",
        "color": "橙色",
        "trait": "圆滚滚的腹部，短小的钳子",
    },
    {
        "id": "venom_scorpion",
        "name": "注毒拟蝎",
        "animal": "拟蝎",
        "color": "黄色",
        "trait": "短小但粗壮的钳子",
    },
    {
        "id": "whip_spider",
        "name": "霸王鞭蛛",
        "animal": "鞭蛛",
        "color": "深红色",
        "trait": "又长又粗的钳子，第一对足是长鞭",
    },
    {
        "id": "egg_raptor",
        "name": "手盗龙宝宝",
        "animal": "手盗龙",
        "color": "浅蓝色",
        "trait": "四肢短小，头顶有碎裂的蛋壳",
    },
    {
        "id": "feather_raptor",
        "name": "阔羽盗龙",
        "animal": "阔羽盗龙",
        "color": "浅紫色",
        "trait": "短小的头冠，前肢长出长羽毛",
    },
    {
        "id": "cassowary",
        "name": "暴走鹤鸵",
        "animal": "鹤鸵",
        "color": "浅蓝头冠，黑蓝身体",
        "trait": "突出的头冠与强壮的腿",
    },
    {
        "id": "little_cat",
        "name": "小古猫",
        "animal": "细齿兽",
        "color": "绿色",
        "trait": "细长优雅",
    },
    {
        "id": "false_cat",
        "name": "假虎猫",
        "animal": "假猫",
        "color": "浅绿色",
        "trait": "粗壮的身体",
    },
    {
        "id": "lion_boss",
        "name": "狮老大",
        "animal": "狮子",
        "color": "深绿鬃毛，橙色身体",
        "trait": "硕大的头与鬃毛",
    },
]


def load_palette(path: Path):
    colors = []
    in_palette = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("## palette"):
            in_palette = True
            continue
        if line.startswith("## ") and in_palette:
            break
        if in_palette and line.startswith("- #"):
            hex_color = line[2:].strip().upper()
            colors.append(tuple(int(hex_color[i : i + 2], 16) for i in (1, 3, 5)))
    if len(colors) != 32:
        raise SystemExit(f"Expected 32 palette colors, found {len(colors)}")
    return colors


def anim_state(action: str, frame: int, count: int):
    phase = 2 * math.pi * frame / max(1, count)
    sway = math.sin(phase)
    if action == "idle":
        return dict(bob=frame % 2, stride=0.0, lunge=0.0, recoil=0.0, lean=0.0, sway=sway,
                    blink=frame == 2, flash=False, open=1.0, kick=0.0, wing=0.14 * sway)
    if action == "walk":
        return dict(bob=int(round(abs(sway) * 2)), stride=sway, lunge=0.0, recoil=0.0, lean=1.0,
                    sway=sway, blink=False, flash=False, open=1.0, kick=0.0, wing=0.28 * sway)
    if action == "run":
        return dict(bob=int(round(abs(sway) * 3)), stride=sway * 1.45, lunge=0.0, recoil=0.0,
                    lean=3.2, sway=sway * 1.2, blink=False, flash=False, open=1.05, kick=0.0,
                    wing=0.55 * sway)
    if action == "attack":
        lunges = (-3.2, 5.4, 4.2, 0.6)
        opens = (1.45, 0.32, 0.48, 1.0)
        kicks = (0.0, 8.0, 6.5, 1.0)
        wings = (-0.35, 1.05, 0.85, 0.15)
        return dict(bob=0, stride=0.0, lunge=lunges[frame], recoil=0.0, lean=0.0, sway=sway * 0.2,
                    blink=False, flash=False, open=opens[frame], kick=kicks[frame], wing=wings[frame])
    if action == "hurt":
        return dict(bob=0, stride=0.0, lunge=0.0, recoil=5.0 if frame == 0 else 2.2, lean=0.0,
                    sway=0.0, blink=True, flash=frame == 0, open=1.15, kick=0.0, wing=-0.2)
    raise ValueError(action)


def view_of(fx: float, fy: float) -> str:
    if fy > 0.75 and abs(fx) < 0.5:
        return "front"
    if fy < -0.75 and abs(fx) < 0.5:
        return "back"
    if abs(fy) < 0.45:
        return "side"
    if fy >= 0:
        return "front_diag"
    return "back_diag"


class Pose:
    def __init__(self, fx: float, fy: float, anim: dict):
        mag = math.hypot(fx, fy) or 1.0
        self.fx = fx / mag
        self.fy = fy / mag
        self.anim = anim
        self.view = view_of(self.fx, self.fy)
        shift = anim["lunge"] - anim["recoil"] + anim["lean"]
        self.dx = self.fx * shift
        self.dy = -float(anim["bob"]) + self.fy * (anim["lunge"] - anim["recoil"]) * 0.45
        self.bx = 32.0 + self.dx
        self.by = 36.0 + self.dy


class Canvas:
    def __init__(self, size=64):
        self.w = self.h = size
        self.buf = [[None for _ in range(size)] for _ in range(size)]
        self.z = [[-999.0 for _ in range(size)] for _ in range(size)]

    def plot(self, x, y, color, z):
        xi = int(math.floor(x))
        yi = int(math.floor(y))
        if xi < 0 or yi < 0 or xi >= self.w or yi >= self.h:
            return
        if z >= self.z[yi][xi]:
            self.z[yi][xi] = z
            self.buf[yi][xi] = color

    def commit(self, pixels, z, outline, ink):
        filled = {(x, y) for x, y, _ in pixels}
        if outline:
            edge = []
            for x, y in filled:
                for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                    if (x + ox, y + oy) not in filled:
                        edge.append((x + ox, y + oy))
            for x, y in edge:
                self.plot(x, y, ink, z)
        for x, y, color in pixels:
            self.plot(x, y, color, z + 0.05)

    def ellipse(self, cx, cy, rx, ry, light, mid, dark, z, angle=0.0, outline=True, shade=True, ink=None):
        if rx < 0.5 or ry < 0.5:
            return
        ink = ink or light
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        reach = max(rx, ry) + 2
        minx = int(math.floor(cx - reach))
        maxx = int(math.ceil(cx + reach))
        miny = int(math.floor(cy - reach))
        maxy = int(math.ceil(cy + reach))
        pixels = []
        for y in range(miny, maxy + 1):
            for x in range(minx, maxx + 1):
                dx = x + 0.5 - cx
                dy = y + 0.5 - cy
                lx = dx * cos_a + dy * sin_a
                ly = -dx * sin_a + dy * cos_a
                nx = lx / rx
                ny = ly / ry
                if nx * nx + ny * ny > 1:
                    continue
                if not shade:
                    color = mid
                else:
                    lnx = lx / (rx * rx)
                    lny = ly / (ry * ry)
                    scale = math.hypot(lnx, lny) or 1.0
                    lnx /= scale
                    lny /= scale
                    snx = lnx * cos_a - lny * sin_a
                    sny = lnx * sin_a + lny * cos_a
                    light_dot = snx * -0.55 + sny * -0.83
                    if light_dot > 0.38:
                        color = light
                    elif light_dot < -0.12:
                        color = dark
                    else:
                        color = mid
                pixels.append((x, y, color))
        self.commit(pixels, z, outline, ink)

    def polygon(self, pts, light, mid, dark, z, outline=True, ink=None):
        ink = ink or light
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        minx = int(math.floor(min(xs))) - 1
        maxx = int(math.ceil(max(xs))) + 1
        miny = int(math.floor(min(ys))) - 1
        maxy = int(math.ceil(max(ys))) + 1
        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)
        pixels = []
        for y in range(miny, maxy + 1):
            for x in range(minx, maxx + 1):
                if not point_in_poly(x + 0.5, y + 0.5, pts):
                    continue
                band = (x - cx) * 0.62 + (y - cy) * 0.78
                if band < -2.4:
                    color = light
                elif band > 2.2:
                    color = dark
                else:
                    color = mid
                pixels.append((x, y, color))
        self.commit(pixels, z, outline, ink)

    def stroke(self, points, color, z, radius=1.2, outline=True, ink=None):
        ink = ink or color
        pixels = []
        r2 = radius * radius + 0.25
        ri = int(math.ceil(radius))
        for (x0, y0), (x1, y1) in zip(points, points[1:]):
            steps = max(1, int(math.hypot(x1 - x0, y1 - y0) * 2))
            for i in range(steps + 1):
                t = i / steps
                x = x0 + (x1 - x0) * t
                y = y0 + (y1 - y0) * t
                cx = int(round(x))
                cy = int(round(y))
                for yy in range(-ri, ri + 1):
                    for xx in range(-ri, ri + 1):
                        if xx * xx + yy * yy <= r2:
                            pixels.append((cx + xx, cy + yy, color))
        self.commit(pixels, z, outline, ink)

    def flash_white(self, white, ink):
        for y in range(self.h):
            for x in range(self.w):
                if self.buf[y][x] is not None and self.buf[y][x] != ink:
                    self.buf[y][x] = white

    def image(self):
        img = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        pix = img.load()
        for y in range(self.h):
            for x in range(self.w):
                color = self.buf[y][x]
                if color is not None:
                    pix[x, y] = (*color, 255)
        return img

    def stats(self):
        colors = set()
        count = 0
        for row in self.buf:
            for color in row:
                if color is not None:
                    colors.add(color)
                    count += 1
        return count, colors


def point_in_poly(x, y, pts):
    inside = False
    j = len(pts) - 1
    for i, (xi, yi) in enumerate(pts):
        xj, yj = pts[j]
        if (yi > y) != (yj > y):
            denom = (yj - yi) or 1e-9
            if x < (xj - xi) * (y - yi) / denom + xi:
                inside = not inside
        j = i
    return inside


def quad(p0, p1, p2, n=18):
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        pts.append((
            u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
            u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1],
        ))
    return pts


def lerp(a, b, t):
    return a + (b - a) * t


class Art:
    def __init__(self, palette):
        self.p = palette
        (self.ink, self.shadow, self.slate, self.gray, self.white, self.blush, self.cream,
         self.gold, self.orange, self.orange_d, self.red, self.red_d, self.lilac_l, self.lilac,
         self.lilac_d, self.cyan, self.sky, self.blue, self.navy, self.blackblue, self.shell,
         self.shell_d, self.lime, self.green, self.green_d, self.pale, self.leaf, self.leaf_d,
         self.mane_d, self.mane, self.mane_l, self.plum) = palette

    def shadow_blob(self, c, pose, rx):
        shift = pose.fx * pose.anim["lunge"] * 0.25
        c.ellipse(32 + shift, 55, rx, 3.1, self.shadow, self.shadow, self.shadow, 0,
                  outline=False, shade=False, ink=self.ink)

    def eye(self, c, x, y, look, blink, big, z=16):
        x = int(round(x))
        y = int(round(y))
        if blink:
            span = 3 if big else 2
            for i in range(-span, span + 1):
                c.plot(x + i, y, self.ink, z)
            return
        if big:
            for dy in range(-2, 2):
                for dx in range(-2, 2):
                    c.plot(x + dx, y + dy, self.ink, z)
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    c.plot(x + dx, y + dy, self.white, z + 0.1)
            px = x + (1 if look > 0.35 else -1 if look < -0.35 else 0)
            c.plot(px, y, self.ink, z + 0.2)
            c.plot(px, y + 1, self.ink, z + 0.2)
            c.plot(x - 1, y - 1, self.white, z + 0.3)
        else:
            for dy in range(-1, 1):
                for dx in range(-1, 1):
                    c.plot(x + dx, y + dy, self.white, z)
            c.plot(x + (1 if look > 0.2 else 0), y, self.ink, z + 0.2)

    def face(self, c, hx, hy, pose, big, blush=True, smile=True, beak=None, brows=False):
        if pose.view == "back":
            return
        side = abs(pose.fx) > 0.8 and abs(pose.fy) < 0.45
        if side:
            ex = hx + pose.fx * (3.1 if big else 2.2)
            self.eye(c, ex, hy - 1, pose.fx, pose.anim["blink"], big)
        else:
            spread = (4.6 if big else 3.1) * (1 - abs(pose.fx) * 0.35)
            for sign in (-1, 1):
                ex = hx + sign * spread + pose.fx * 1.4
                ey = hy - 1 + max(pose.fy, 0) * 0.4
                self.eye(c, ex, ey, pose.fx, pose.anim["blink"], big and pose.fy > -0.2)
        if pose.fy < 0.05:
            return
        if blush:
            for sign in (-1, 1):
                if side and sign != (1 if pose.fx > 0 else -1):
                    continue
                c.ellipse(hx + sign * (5.2 if big else 3.6) + pose.fx, hy + 2.2, 1.7, 1.1,
                          self.blush, self.blush, self.blush, 16.4, outline=False, shade=False, ink=self.ink)
        if brows:
            for sign in (-1, 1):
                x0 = hx + sign * 3
                c.stroke([(x0, hy - 5), (x0 + sign * 3, hy - 4)], self.ink, 17, radius=0.55, outline=False, ink=self.ink)
        if beak == "tiny":
            tip = (hx + pose.fx * 4.5, hy + 4 + max(pose.fy, 0))
            c.polygon([(hx - 1.5 + pose.fx, hy + 2), (hx + 1.5 + pose.fx, hy + 2), tip],
                      self.gold, self.gold, self.orange_d, 16.6, ink=self.ink)
        elif beak == "casque":
            tip = (hx + pose.fx * 7, hy + 3)
            c.polygon([(hx - 2, hy + 1), (hx + 2, hy + 2), tip], self.gray, self.slate, self.ink, 16.6, ink=self.ink)
            if pose.fy > 0.4:
                c.ellipse(hx + pose.fx, hy + 5, 2.2, 2.4, self.red, self.red, self.red_d, 16.5, ink=self.ink)
        elif smile and pose.fy > 0.25:
            width = 2 if big else 1
            y = int(round(hy + (4 if big else 3)))
            x = int(round(hx + pose.fx * 1.2))
            for i in range(-width, width + 1):
                c.plot(x + i, y + (0 if abs(i) < width else 1), self.ink, 16.8)

    def pincer(self, c, x, y, dx, dy, length, width, colors, open_amt, z):
        mag = math.hypot(dx, dy) or 1
        dx, dy = dx / mag, dy / mag
        px, py = -dy, dx
        light, mid, dark = colors
        c.ellipse(x, y, width * 0.62, width * 0.5, light, mid, dark, z,
                  angle=math.atan2(dy, dx), ink=self.ink)
        finger_r = max(1.15, width * 0.22)
        # Tips stay apart so the claw reads as two fingers, not one blob.
        sep = finger_r * 2.1 + 1.5
        for sign in (-1, 1):
            fdx = dx * 0.82 + px * sign * 0.55 * open_amt
            fdy = dy * 0.82 + py * sign * 0.55 * open_amt
            fmag = math.hypot(fdx, fdy) or 1
            fdx, fdy = fdx / fmag, fdy / fmag
            cx = x + dx * length * 0.48 + px * sign * sep * 0.72
            cy = y + dy * length * 0.48 + py * sign * sep * 0.72
            c.ellipse(cx, cy, max(2.2, length * 0.42), finger_r, light, mid, dark, z + 0.1,
                      angle=math.atan2(fdy, fdx), ink=self.ink)

    def legs_stub(self, c, pose, bx, by, colors, pairs, reach, y_shift=2):
        light, mid, dark = colors
        stride = pose.anim["stride"]
        for i in range(pairs):
            t = (i / max(1, pairs - 1)) * 2 - 1
            phase = stride if i % 2 == 0 else -stride
            for sign in (-1, 1):
                if pose.view == "side" and sign == (-1 if pose.fx > 0 else 1):
                    continue
                x = bx + sign * reach + pose.fx * phase * 1.6
                y = by + t * 6 + y_shift + abs(phase)
                c.ellipse(x, y, 2.1, 2.5, light, mid, dark, 2.2, ink=self.ink)

    def tail(self, c, pose, bx, by, colors, length, thick, curl=6, lift=0):
        light, mid, dark = colors
        sway = pose.anim["sway"] * 3.0
        x0 = bx - pose.fx * 4
        y0 = by + 2
        x1 = x0 - pose.fx * length * 0.45 + sway
        y1 = y0 + 4 - lift
        x2 = x0 - pose.fx * length * 0.9 + sway * 1.2
        y2 = y0 - curl - lift * 0.35
        c.stroke(quad((x0, y0), (x1, y1), (x2, y2), 14), mid, 1.2, radius=thick, outline=True, ink=self.ink)
        c.ellipse(x2, y2, thick + 1.3, thick + 1.1, light, mid, dark, 1.4, ink=self.ink)

    def feet(self, c, pose, bx, by, colors, spread, size, kick_scale=0.0, z=4, leg=False):
        light, mid, dark = colors
        stride = pose.anim["stride"]
        kick = pose.anim["kick"] * kick_scale
        for i, sign in enumerate((-1, 1)):
            phase = stride if i == 0 else -stride
            k = kick if i == 0 else 0
            if pose.view == "side":
                x = bx + pose.fx * ((7 if i == 0 else -4) + phase * 5.5 + k)
                y = 50 - abs(phase) * 1.4 + pose.dy * 0.1
                hip_x = bx + pose.fx * (2 if i == 0 else -2)
                hip_y = by + 4
                toe = pose.fx
            else:
                extra = k * 0.9 if i == 0 else 0
                x = bx + sign * (spread + extra) + pose.fx * phase * 4.5
                y = 51 + pose.dy * 0.1 + (1.5 if phase < 0 else 0)
                if pose.view == "back" and i == 0:
                    y -= k * 0.45
                hip_x = bx + sign * spread * 0.45
                hip_y = by + 5
                toe = pose.fx if abs(pose.fx) > 0.3 else sign
            if leg:
                c.stroke([(hip_x, hip_y), (x, y - 1)], dark, z - 0.2, radius=max(1.15, size * 0.55), outline=True, ink=self.ink)
            c.ellipse(x, y, size, max(1.6, size * 0.62), dark, mid, dark, z, ink=self.ink)
            if size >= 3.2:
                c.polygon([(x + toe * 2, y), (x + toe * (5 + k * 0.2), y + 1), (x + toe * 2, y + 2)],
                          dark, dark, self.ink, z + 0.1, ink=self.ink)

    def wing(self, c, pose, bx, by, colors, sign):
        light, mid, dark = colors
        if pose.view == "side" and sign != (1 if pose.fx >= 0 else -1):
            z = 2.4
        else:
            z = 5.5
        shoulder = (bx + sign * 3 + pose.fx * 2, by - 1)
        wing = pose.anim["wing"]
        lengths = (11, 16, 13)
        for i, length in enumerate(lengths):
            if pose.view in ("front", "front_diag"):
                dx = sign * (0.75 + i * 0.08)
                dy = 0.55 - wing * 0.25
            elif pose.view in ("back", "back_diag"):
                dx = sign * 0.95
                dy = -0.25 - wing * 0.2
            else:
                dx = -pose.fx * (0.85 - wing) + pose.fx * wing * 0.9
                dy = -0.15 + wing * 0.55
            mag = math.hypot(dx, dy) or 1
            dx, dy = dx / mag, dy / mag
            tip_x = shoulder[0] + dx * length
            tip_y = shoulder[1] + dy * length
            c.ellipse((shoulder[0] + tip_x) / 2, (shoulder[1] + tip_y) / 2, length * 0.52, 2.1 + (i == 1),
                      light, mid, dark, z + i * 0.05, angle=math.atan2(dy, dx), ink=self.ink)
            c.stroke([shoulder, (tip_x, tip_y)], dark, z + 0.4, radius=0.55, outline=False, ink=self.ink)


def draw_character(canvas: Canvas, art: Art, slug: str, pose: Pose):
    p = pose
    if slug == "mini_scorpion":
        colors = (art.gold, art.orange, art.orange_d)
        art.shadow_blob(canvas, p, 11)
        side = abs(p.fx)
        aby = p.by + 3
        abx = p.bx - p.fx * 2
        canvas.ellipse(abx, aby, lerp(12.2, 11.2, side), lerp(11.2, 10.4, side), *colors, 3, ink=art.ink)
        canvas.ellipse(abx - 1, aby + 3, 6.4, 5.2, art.gold, art.gold, art.orange, 3.4, outline=False, ink=art.ink)
        for oy in (-1, 4):
            canvas.stroke([(abx - 6, aby + oy), (abx + 6, aby + oy + 1)], art.orange_d, 3.5, radius=0.55, outline=False, ink=art.ink)
        hx = p.bx + p.fx * lerp(1.5, 9, side)
        hy = aby - lerp(12, 7, side)
        canvas.ellipse(hx, hy, 4.8, 4.3, *colors, 6, ink=art.ink)
        art.legs_stub(canvas, p, abx, aby, colors, 3, lerp(11, 7, side))
        _pincers(art, canvas, p, hx, hy, 7.4, 2.7, colors, "short")
        art.face(canvas, hx, hy - 0.4, p, big=False)
    elif slug == "venom_scorpion":
        colors = (art.cream, art.gold, art.orange_d)
        art.shadow_blob(canvas, p, 12)
        side = abs(p.fx)
        aby = p.by + 4
        abx = p.bx - p.fx * 1
        canvas.ellipse(abx, aby, lerp(8.4, 9.2, side), lerp(7.6, 7.2, side), *colors, 3, ink=art.ink)
        hx = p.bx + p.fx * lerp(2, 8, side)
        hy = aby - lerp(10, 6, side)
        canvas.ellipse(hx, hy, 5.1, 4.5, *colors, 6, ink=art.ink)
        art.legs_stub(canvas, p, abx, aby, colors, 3, lerp(8, 6, side))
        _pincers(art, canvas, p, hx, hy, 10.5, 5.1, colors, "stout")
        art.face(canvas, hx, hy - 0.2, p, big=False)
    elif slug == "whip_spider":
        colors = (art.red, art.red_d, art.plum)
        art.shadow_blob(canvas, p, 10)
        side = abs(p.fx)
        bx, by = p.bx, p.by + 2
        canvas.ellipse(bx, by, lerp(8.2, 9.4, side), lerp(6.6, 6.2, side), *colors, 3, ink=art.ink)
        hx = bx + p.fx * lerp(2, 7, side)
        hy = by - lerp(8, 5, side)
        canvas.ellipse(hx, hy, 4.2, 3.8, *colors, 6, ink=art.ink)
        art.legs_stub(canvas, p, bx, by + 2, colors, 2, lerp(6.5, 5, side), y_shift=4)
        _whips(art, canvas, p, hx, hy)
        _pincers(art, canvas, p, hx, hy, 15.5, 3.9, colors, "whip")
        art.face(canvas, hx, hy, p, big=False, smile=False)
    elif slug == "egg_raptor":
        colors = (art.cyan, art.sky, art.blue)
        art.shadow_blob(canvas, p, 9)
        side = abs(p.fx)
        bx, by = p.bx, p.by + 4
        canvas.ellipse(bx, by, lerp(8.2, 8.8, side), lerp(7.2, 6.6, side), *colors, 3, ink=art.ink)
        hx = bx + p.fx * lerp(1, 6, side)
        hy = by - lerp(12, 8, side)
        canvas.ellipse((hx + bx) / 2, (hy + by) / 2 + 1, 3.4, 3.6, *colors, 5, ink=art.ink)
        canvas.ellipse(hx, hy, 9.2, 8.4, *colors, 6, ink=art.ink)
        _eggshell(art, canvas, hx, hy, p.anim["sway"])
        _tiny_arms(art, canvas, p, bx, by, colors)
        art.feet(canvas, p, bx, by, colors, 3.1, 1.8)
        art.face(canvas, hx, hy + 1, p, big=True, beak="tiny")
    elif slug == "feather_raptor":
        colors = (art.lilac_l, art.lilac, art.lilac_d)
        art.shadow_blob(canvas, p, 9)
        side = abs(p.fx)
        bx, by = p.bx - p.fx, p.by + 2
        _tail_fan(art, canvas, p, bx, by, colors)
        art.wing(canvas, p, bx, by, colors, -1)
        art.wing(canvas, p, bx, by, colors, 1)
        canvas.ellipse(bx, by, lerp(6.6, 8.4, side), lerp(8.4, 6.4, side), *colors, 4, ink=art.ink)
        hx = bx + p.fx * lerp(2, 8, side)
        hy = by - lerp(12, 7, side)
        canvas.ellipse(hx, hy, 5.8, 5.4, *colors, 6, ink=art.ink)
        _crest(art, canvas, hx, hy, p, short=True)
        art.feet(canvas, p, bx, by, (art.lilac, art.lilac_d, art.plum), 3.4, 2.3, kick_scale=0.25)
        art.face(canvas, hx, hy, p, big=True, beak="tiny")
    elif slug == "cassowary":
        body = (art.navy, art.blackblue, art.ink)
        art.shadow_blob(canvas, p, 8)
        side = abs(p.fx)
        bx, by = p.bx, p.by + 3
        canvas.ellipse(bx, by, lerp(8.4, 9.2, side), lerp(9.2, 8.2, side), *body, 3, ink=art.ink)
        hx = bx + p.fx * lerp(1.5, 7, side)
        hy = by - lerp(15, 10, side)
        canvas.ellipse((hx + bx) / 2, (hy + by) / 2, 3.6, 5.2, art.navy, art.blackblue, art.ink, 5, ink=art.ink)
        canvas.ellipse(hx, hy, 5.2, 4.8, art.sky, art.blue, art.navy, 6, ink=art.ink)
        _casque(art, canvas, hx, hy, p)
        art.feet(canvas, p, bx, by, (art.gray, art.slate, art.ink), 6.4, 3.4, kick_scale=1.0, z=4.5, leg=True)
        art.face(canvas, hx, hy + 1, p, big=False, blush=True, beak="casque", brows=True)
    elif slug == "little_cat":
        colors = (art.lime, art.green, art.green_d)
        _mammal(art, canvas, p, colors, front=(7.0, 8.6), side=(12.6, 5.4), head=6.6,
                tail=15, tail_r=1.8, ears=6.4, leg_spread=4.6, foot=2.1, fangs=False, mane=False, long_legs=True)
    elif slug == "false_cat":
        colors = (art.pale, art.leaf, art.leaf_d)
        _mammal(art, canvas, p, colors, front=(12.2, 9.2), side=(13.2, 8.4), head=6.8,
                tail=7, tail_r=2.5, ears=4.2, leg_spread=5.2, foot=2.8, fangs=True, mane=False)
    elif slug == "lion_boss":
        colors = (art.gold, art.orange, art.orange_d)
        _mammal(art, canvas, p, colors, front=(7.4, 6.6), side=(8.6, 6.4), head=7.4,
                tail=12, tail_r=2.2, ears=4.4, leg_spread=4.4, foot=2.6, fangs=False, mane=True)
    else:
        raise ValueError(slug)
    if p.anim["flash"]:
        canvas.flash_white(art.white, art.ink)


def _pincers(art, c, pose, hx, hy, length, width, colors, style):
    view = pose.view
    o = pose.anim["open"]
    if view == "front":
        if style == "whip":
            specs = [(-1.0, 0.22, hx - 3, hy + 2), (1.0, 0.22, hx + 3, hy + 2)]
        elif style == "stout":
            specs = [(-0.96, -0.12, hx - 4, hy + 1), (0.96, -0.12, hx + 4, hy + 1)]
        else:
            specs = [(-0.78, -0.55, hx - 4, hy), (0.78, -0.55, hx + 4, hy)]
    elif view == "back":
        specs = [(-0.62, -0.78, hx - 4, hy - 2), (0.62, -0.78, hx + 4, hy - 2)]
    elif view == "side":
        specs = [(pose.fx, -0.28, hx + pose.fx * 3, hy - 1), (pose.fx * 0.92, 0.28, hx + pose.fx * 2, hy + 3)]
    elif view == "front_diag":
        specs = [(pose.fx, -0.05, hx + pose.fx * 4, hy), (pose.fx * 0.45, 0.55, hx + pose.fx * 2, hy + 3)]
    else:
        specs = [(pose.fx * 0.95, -0.4, hx + pose.fx * 4, hy - 2), (pose.fx * 0.35, -0.85, hx + pose.fx, hy - 4)]
    for i, (dx, dy, x, y) in enumerate(specs):
        art.pincer(c, x, y, dx, dy, length * (1.08 if style == "whip" else 1), width, colors, o, 10 + i * 0.2)


def _whips(art, c, pose, hx, hy):
    sway = pose.anim["sway"] * 4 + pose.anim["wing"] * 6
    view = pose.view
    if view == "front":
        curves = [
            ((hx - 3, hy - 2), (hx - 16, 8 + sway), (6, 8)),
            ((hx + 3, hy - 2), (hx + 16, 8 - sway), (57, 8)),
        ]
    elif view == "back":
        curves = [
            ((hx - 3, hy - 4), (10, 6), (6, 14 + sway)),
            ((hx + 3, hy - 4), (54, 6), (58, 14 - sway)),
        ]
    elif view == "side":
        curves = [
            ((hx + pose.fx * 2, hy - 3), (hx + pose.fx * 16, hy - 16), (hx + pose.fx * 26, 8 + sway)),
            ((hx + pose.fx * 2, hy + 1), (hx + pose.fx * 14, hy - 8), (hx + pose.fx * 24, hy - 2)),
        ]
    else:
        curves = [
            ((hx + pose.fx * 2, hy - 3), (hx + pose.fx * 14, hy - 14), (hx + pose.fx * 22, 7 + sway)),
            ((hx - pose.fx * 2, hy - 1), (hx + pose.fx * 8, 10), (hx + pose.fx * 16, hy + 8)),
        ]
    for p0, p1, p2 in curves:
        c.stroke(quad(_clamp(p0), _clamp(p1), _clamp(p2), 16), art.red, 8.2, radius=1.15, outline=True, ink=art.ink)


def _clamp(pt):
    return (max(3, min(60, pt[0])), max(3, min(60, pt[1])))


def _eggshell(art, c, hx, hy, sway):
    pixels = []
    for y in range(int(hy) - 16, int(hy) + 3):
        for x in range(int(hx) - 13, int(hx) + 14):
            dx = x + 0.5 - hx
            dy = y + 0.5 - hy
            if (dx * dx) / (10.6 ** 2) + (dy * dy) / (9.2 ** 2) > 1:
                continue
            jag = 1 if (x // 2) % 2 == 0 else -1
            if y > hy + jag:
                continue
            if abs(x - int(hx + 1)) <= 0 and hy - 12 < y < hy:
                continue
            band = dx + dy
            if band < -7:
                color = art.cream
            elif band > 5:
                color = art.shell_d
            else:
                color = art.shell
            pixels.append((x, y, color))
    c.commit(pixels, 7.2, True, art.ink)
    c.ellipse(hx + 9 + sway, hy - 10, 2.5, 1.8, art.cream, art.shell, art.shell_d, 7.6, angle=0.7, ink=art.ink)
    c.ellipse(hx - 8, hy - 5, 1.8, 1.5, art.cream, art.shell, art.shell_d, 7.5, angle=-0.5, ink=art.ink)


def _tiny_arms(art, c, pose, bx, by, colors):
    flap = pose.anim["wing"] * 2 + pose.anim["lunge"] * 0.15
    for sign in (-1, 1):
        x = bx + sign * 8
        y = by - 1 + flap * sign
        c.ellipse(x, y, 2.0, 1.7, *colors, 5.2, ink=art.ink)


def _crest(art, c, hx, hy, pose, short=True):
    height = 6 if short else 12
    back = -pose.fx * 1.5
    c.polygon([
        (hx + back, hy - 4 - height),
        (hx - 3 + back, hy - 4),
        (hx + 3 + back * 0.2, hy - 3),
    ], art.lilac_l, art.lilac, art.lilac_d, 7.4, ink=art.ink)


def _tail_fan(art, c, pose, bx, by, colors):
    sway = pose.anim["sway"] * 2
    base = (bx - pose.fx * 6, by + 2)
    for i, spread in enumerate((-0.7, 0.0, 0.7)):
        dx = -pose.fx * 8 + spread * 5 + sway
        dy = 6 + abs(spread) * 2
        tip = (base[0] + dx, base[1] + dy)
        c.ellipse((base[0] + tip[0]) / 2, (base[1] + tip[1]) / 2, 6.5, 2.0, *colors, 1.3,
                  angle=math.atan2(dy, dx), ink=art.ink)


def _casque(art, c, hx, hy, pose):
    top = (hx - pose.fx * 1.2, hy - 16)
    c.polygon([
        top,
        (hx - 5, hy - 3),
        (hx + 4.5, hy - 2),
    ], art.cyan, art.sky, art.blue, 7.5, ink=art.ink)
    c.stroke([top, (hx, hy - 4)], art.cyan, 7.7, radius=0.7, outline=False, ink=art.ink)


def _mammal(art, c, pose, colors, front, side, head, tail, tail_r, ears, leg_spread, foot, fangs, mane, long_legs=False):
    light, mid, dark = colors
    side_amt = abs(pose.fx)
    rx = lerp(front[0], side[0], side_amt)
    ry = lerp(front[1], side[1], side_amt)
    if pose.anim["lean"] > 2:
        rx *= 1.06
        ry *= 0.9
    art.shadow_blob(c, pose, max(8, rx * 0.85))
    bx = pose.bx - pose.fx * rx * 0.12
    by = pose.by + (-1 if long_legs else 8 if mane else 2)
    art.tail(c, pose, bx, by, colors if not mane else (art.mane_l, art.mane, art.mane_d), tail, tail_r,
             curl=8 if long_legs else 2 if mane else 4, lift=9 if long_legs else 0)
    c.ellipse(bx, by, rx, ry, light, mid, dark, 3, ink=art.ink)
    if not mane:
        c.ellipse(bx + pose.fx * 1.5, by + ry * 0.15, rx * 0.45, ry * 0.35, light, light, mid, 3.4, outline=False, ink=art.ink)
    hx = bx + pose.fx * lerp(1.2, rx * 0.72, side_amt)
    hy = by - lerp(ry * 0.72 + head * 0.35, head * 0.2, side_amt * 0.85)
    if mane:
        _mane(art, c, hx, hy)
        c.ellipse(hx + pose.fx * 1.2, hy + 1.5, head * 0.92, head * 0.82, art.gold, art.orange, art.orange_d, 7, ink=art.ink)
        _ears(art, c, hx, hy - 2, pose, ears, (art.gold, art.orange, art.orange_d))
        art.feet(c, pose, bx, by, colors, leg_spread, foot, z=4)
        _paw(art, c, pose, colors)
        art.face(c, hx + pose.fx * 1.5, hy + 2, pose, big=True)
        if pose.fy > 0.2 and pose.view != "back":
            c.ellipse(hx + pose.fx * 3.2, hy + 5, 1.5, 1.1, art.orange_d, art.orange_d, art.ink, 16.9, outline=False, shade=False, ink=art.ink)
    else:
        c.ellipse((hx + bx) / 2, (hy + by) / 2, max(3.2, head * 0.48), max(3.4, ry * 0.22), light, mid, dark, 5, ink=art.ink)
        c.ellipse(hx, hy, head, head * 0.92, light, mid, dark, 6, ink=art.ink)
        _ears(art, c, hx, hy, pose, ears, colors)
        art.feet(c, pose, bx, by, colors, leg_spread, foot, z=4, leg=long_legs)
        _paw(art, c, pose, colors)
        art.face(c, hx, hy, pose, big=head >= 6.4)
        if fangs and pose.fy > 0.35 and pose.view != "back":
            for sign in (-1, 1):
                x = hx + pose.fx * 2 + sign * 2
                c.stroke([(x, hy + 5), (x, hy + 8)], art.white, 17, radius=0.6, outline=True, ink=art.ink)


def _ears(art, c, hx, hy, pose, size, colors):
    if pose.view == "front":
        spots = ((hx - size * 0.85, hy - size * 0.15), (hx + size * 0.85, hy - size * 0.15))
    elif pose.view == "back":
        spots = ((hx - size, hy - size * 0.35), (hx + size, hy - size * 0.35))
    elif pose.view == "side":
        spots = ((hx - pose.fx * 1.5, hy - size * 0.55),)
    else:
        spots = ((hx - pose.fx * 2, hy - size * 0.45), (hx + pose.fx * size * 0.4, hy - size * 0.2))
    for x, y in spots:
        c.polygon([
            (x, y - size),
            (x - size * 0.48, y + 1),
            (x + size * 0.48, y + 1),
        ], *colors, 6.6, ink=art.ink)
        c.polygon([
            (x, y - size * 0.62),
            (x - size * 0.22, y - 1),
            (x + size * 0.22, y - 1),
        ], art.blush, art.blush, art.blush, 6.8, ink=art.ink)


def _mane(art, c, hx, hy):
    tufts = ((0, -13), (9, -9), (13, -1), (10, 7), (0, 10), (-10, 7), (-13, -1), (-9, -9))
    for ox, oy in tufts:
        c.ellipse(hx + ox, hy + oy, 5.3, 4.7, art.mane_l, art.mane, art.mane_d, 6.15, ink=art.ink)
    c.ellipse(hx, hy, 11.2, 10.2, art.mane_l, art.mane, art.mane_d, 6.3, ink=art.ink)


def _paw(art, c, pose, colors):
    kick = pose.anim["kick"]
    if kick < 3:
        return
    light, mid, dark = colors
    if abs(pose.fx) < 0.35:
        side = 1 if pose.fy >= 0 else 0.4
        x = pose.bx + side * (9 + kick * 0.55)
        y = pose.by + (4 if pose.fy >= 0 else -2)
    else:
        x = pose.bx + pose.fx * (8 + kick * 0.9)
        y = pose.by + 1
    c.ellipse(x, y, 3.6, 3.1, light, mid, dark, 12, ink=art.ink)
    for sign in (-1, 0, 1):
        c.stroke([(x + sign * 2, y - 2), (x + pose.fx * 3 + sign * 2, y - 5)], art.white, 12.4, radius=0.45, outline=False, ink=art.ink)


def render(slug, direction, action, frame, palette):
    _, fx, fy, _ = direction
    count = dict((name, n) for name, n, *_ in ACTIONS)[action]
    pose = Pose(fx, fy, anim_state(action, frame, count))
    canvas = Canvas(64)
    art = Art(palette)
    draw_character(canvas, art, slug, pose)
    return canvas


def validate(canvas: Canvas, palette, label: str):
    count, colors = canvas.stats()
    problems = []
    if count < 40:
        problems.append("too few pixels")
    if len(colors) > 16:
        problems.append(f"{len(colors)} colors")
    extra = colors - set(palette)
    if extra:
        problems.append(f"out of palette {len(extra)}")
    if problems:
        raise SystemExit(f"{label}: {', '.join(problems)}")


def font(size):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def montage(palette):
    scale = 3
    label_h = 18
    cell = 64 * scale
    cols = 8
    rows = len(CHARACTERS)
    sheet = Image.new("RGBA", (cols * cell, rows * (cell + label_h)), (244, 239, 230, 255))
    draw = ImageDraw.Draw(sheet)
    fnt = font(14)
    for r, char in enumerate(CHARACTERS):
        draw.text((4, r * (cell + label_h) + 1), f"{char['name']} 八方向", fill=(26, 28, 44, 255), font=fnt)
        for c, direction in enumerate(DIRS):
            canvas = render(char["id"], direction, "idle", 0, palette)
            validate(canvas, palette, f"{char['id']} {direction[0]} idle")
            img = canvas.image().resize((cell, cell), Image.Resampling.NEAREST)
            sheet.alpha_composite(img, (c * cell, r * (cell + label_h) + label_h))
    out = Path("/tmp/rogue_dirs.png")
    sheet.convert("RGB").save(out, "PNG")

    frames_w = 6
    anim_sheet = Image.new("RGBA", (frames_w * cell, 4 * (cell + label_h)), (244, 239, 230, 255))
    ad = ImageDraw.Draw(anim_sheet)
    samples = [
        ("mini_scorpion", "down", "walk"),
        ("whip_spider", "right", "attack"),
        ("egg_raptor", "down", "idle"),
        ("lion_boss", "downright", "walk"),
    ]
    counts = {name: n for name, n, *_ in ACTIONS}
    for r, (slug, dir_name, action) in enumerate(samples):
        direction = next(d for d in DIRS if d[0] == dir_name)
        ad.text((4, r * (cell + label_h) + 1), f"{slug} {dir_name} {action}", fill=(26, 28, 44, 255), font=fnt)
        for frame in range(counts[action]):
            canvas = render(slug, direction, action, frame, palette)
            img = canvas.image().resize((cell, cell), Image.Resampling.NEAREST)
            anim_sheet.alpha_composite(img, (frame * cell, r * (cell + label_h) + label_h))
    anim_out = Path("/tmp/rogue_anims.png")
    anim_sheet.convert("RGB").save(anim_out, "PNG")
    print(out)
    print(anim_out)


def save_frames(palette, only=None):
    char_dir = PROJECT / "assets" / "characters"
    char_dir.mkdir(parents=True, exist_ok=True)
    for old in char_dir.glob("*.png"):
        old.unlink()
    game_dir = PROJECT / "sheets" / "game"
    game_dir.mkdir(parents=True, exist_ok=True)
    for old in game_dir.glob("*.png"):
        old.unlink()
    total = 0
    for char in CHARACTERS:
        if only and char["id"] not in only:
            continue
        palette = load_palette(SPEC_PATH)
        art_frames = {action: [] for action, *_ in ACTIONS}
        for direction in DIRS:
            for action, count, *_ in ACTIONS:
                row = []
                for frame in range(count):
                    canvas = render(char["id"], direction, action, frame, palette)
                    validate(canvas, palette, f"{char['id']}_{direction[0]}_{action}_{frame}")
                    img = canvas.image()
                    name = f"{char['id']}_{direction[0]}_{action}_{frame}.png"
                    img.save(char_dir / name, "PNG")
                    row.append(img)
                    total += 1
                art_frames[action].append(row)
        for action, count, *_ in ACTIONS:
            sheet = Image.new("RGBA", (count * 64, len(DIRS) * 64), (0, 0, 0, 0))
            for r, row in enumerate(art_frames[action]):
                for c, img in enumerate(row):
                    sheet.paste(img, (c * 64, r * 64))
            sheet.save(game_dir / f"{char['id']}_{action}.png", "PNG")
        print(f"  {char['name']} frames saved")
    print(f"[OK] {total} frames")


def write_notes():
    notes = PROJECT / "notes"
    notes.mkdir(parents=True, exist_ok=True)
    for char in CHARACTERS:
        text = f"""# {char['id']}

- Category: characters
- Size: 64x64
- Colors used: within Cute Rogue 32, budget 16
- Animation: idle 4, walk 6, run 6, attack 4, hurt 2, each in 8 directions
- Design notes: {char['name']}（{char['animal']}）。主体颜色 {char['color']}。构造重点：{char['trait']}。可爱化处理，保留辨识特征，不做写实解剖。
- Variants: directions down, downright, right, upright, up, upleft, left, downleft
"""
        (notes / f"{char['id']}.md").write_text(text, encoding="utf-8")


def write_palette_files(palette):
    pal_dir = PROJECT / "exports" / "palettes"
    pal_dir.mkdir(parents=True, exist_ok=True)
    gpl = ["GIMP Palette", "Name: Cute Rogue 32", "Columns: 8", "#"]
    for color in palette:
        gpl.append(f"{color[0]:3d} {color[1]:3d} {color[2]:3d}\t#{color[0]:02X}{color[1]:02X}{color[2]:02X}")
    (pal_dir / "cute_rogue_32.gpl").write_text("\n".join(gpl) + "\n", encoding="utf-8")
    act = bytearray(256 * 3)
    for i, color in enumerate(palette):
        act[i * 3:i * 3 + 3] = bytes(color)
    (pal_dir / "cute_rogue_32.act").write_bytes(act)


def write_manifest():
    manifest = {
        "project": "rogue_animals",
        "canvas": {"width": 64, "height": 64},
        "palette": "Cute Rogue 32",
        "light_direction": "top-left",
        "style": "cute outlined cel-shaded pixel",
        "directions": [{"id": d[0], "label": d[3], "row": i} for i, d in enumerate(DIRS)],
        "animations": {
            action: {"frames": count, "fps": fps, "loop": loop, "label": label, "columns": count}
            for action, count, fps, loop, label in ACTIONS
        },
        "layout": "Each game sheet is one action. Rows are directions. Columns are frames.",
        "characters": CHARACTERS,
    }
    path = PROJECT / "sheets" / "game" / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def write_preview(manifest):
    preview = PROJECT / "preview"
    preview.mkdir(parents=True, exist_ok=True)
    html = PREVIEW_HTML.replace("__DATA__", json.dumps(manifest, ensure_ascii=False))
    (preview / "index.html").write_text(html, encoding="utf-8")
    (ROOT / "index.html").write_text(
        """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta http-equiv="refresh" content="0; url=projects/rogue_animals_64x64_20261021/preview/index.html" />
  <title>动物精灵预览</title>
</head>
<body>
  <p><a href="projects/rogue_animals_64x64_20261021/preview/index.html">打开八方向精灵预览</a></p>
</body>
</html>
""",
        encoding="utf-8",
    )


def write_zips():
    export = PROJECT / "exports"
    export.mkdir(parents=True, exist_ok=True)
    master = export / "rogue_animals_sprites.zip"
    with zipfile.ZipFile(master, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in [
            PROJECT / "design_spec.md",
            PROJECT / "spec_lock.md",
            PROJECT / "preview" / "index.html",
            PROJECT / "sheets" / "manifest.json",
        ]:
            if path.exists():
                zf.write(path, path.relative_to(PROJECT).as_posix())
        for folder, pattern in (
            (PROJECT / "sheets" / "game", "*.png"),
            (PROJECT / "sheets" / "game", "*.json"),
            (PROJECT / "assets" / "characters", "*.png"),
            (PROJECT / "notes", "*.md"),
            (export / "palettes", "*"),
        ):
            for path in folder.glob(pattern):
                if path.is_file():
                    zf.write(path, path.relative_to(PROJECT).as_posix())
        for char in CHARACTERS:
            char_zip = export / "characters" / f"{char['id']}.zip"
            char_zip.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(char_zip, "w", compression=zipfile.ZIP_DEFLATED) as cz:
                for action, *_ in ACTIONS:
                    sheet = PROJECT / "sheets" / "game" / f"{char['id']}_{action}.png"
                    cz.write(sheet, sheet.name)
                cz.write(PROJECT / "sheets" / "game" / "manifest.json", "manifest.json")
            zf.write(char_zip, char_zip.relative_to(PROJECT).as_posix())
    print(f"[OK] {master} ({master.stat().st_size} bytes)")


PREVIEW_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>肉鸽动物八方向精灵</title>
  <style>
    :root {
      --ink: #1a1c2c;
      --paper: #f4efe6;
      --panel: #fffdf8;
      --line: #d9d0c3;
      --floor: #d5dcc8;
      --accent: #b13e53;
      --muted: #566c86;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "WenQuanYi Micro Hei", "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", "Source Han Sans SC", sans-serif;
      color: var(--ink);
      background: var(--paper);
    }
    header {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-end;
      padding: 20px 28px 12px;
      border-bottom: 1px solid var(--line);
    }
    h1 { margin: 0; font-size: 22px; font-weight: 700; }
    header p { margin: 4px 0 0; color: var(--muted); font-size: 13px; }
    main {
      display: grid;
      grid-template-columns: 280px minmax(0, 1fr);
      min-height: calc(100vh - 78px);
    }
    aside {
      border-right: 1px solid var(--line);
      padding: 12px;
      background: var(--panel);
    }
    .char-btn, button, .linkish {
      font: inherit;
      color: inherit;
    }
    .char-btn {
      width: 100%;
      text-align: left;
      border: 1px solid transparent;
      background: transparent;
      padding: 8px 10px;
      cursor: pointer;
      display: grid;
      grid-template-columns: 52px 1fr;
      gap: 8px;
      align-items: center;
    }
    .char-btn.active { border-color: var(--ink); background: var(--paper); }
    .thumb {
      width: 52px;
      height: 52px;
      background-color: var(--floor);
      background-repeat: no-repeat;
      image-rendering: pixelated;
    }
    .char-btn strong { display: block; font-size: 14px; }
    .char-btn span { color: var(--muted); font-size: 12px; }
    section { padding: 18px 22px 32px; }
    .stage-wrap {
      display: grid;
      grid-template-columns: 280px 1fr;
      gap: 22px;
      align-items: start;
    }
    .stage {
      width: 256px;
      height: 256px;
      background: var(--floor);
      border: 1px solid var(--ink);
      image-rendering: pixelated;
      background-repeat: no-repeat;
    }
    .meta h2 { margin: 0 0 4px; font-size: 20px; }
    .meta p { margin: 0 0 10px; color: var(--muted); }
    .actions, .transport, .downloads { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; }
    button, .downloads a {
      border: 1px solid var(--ink);
      background: var(--panel);
      padding: 6px 10px;
      cursor: pointer;
      text-decoration: none;
    }
    button.active { background: var(--ink); color: var(--paper); }
    .pad {
      margin-top: 8px;
      display: grid;
      grid-template-columns: repeat(3, 84px);
      grid-template-rows: repeat(3, 84px);
      gap: 6px;
      width: max-content;
    }
    .pad .cell {
      width: 84px;
      height: 84px;
      padding: 0;
      background-color: var(--floor);
      border: 1px solid var(--line);
      image-rendering: pixelated;
      background-repeat: no-repeat;
      cursor: pointer;
      position: relative;
    }
    .pad .cell.active { border-color: var(--accent); }
    .pad .cell i {
      position: absolute;
      left: 4px;
      bottom: 2px;
      font-style: normal;
      font-size: 11px;
      background: var(--panel);
      padding: 0 3px;
    }
    .sheet-wrap { margin-top: 18px; overflow: auto; border: 1px solid var(--line); background: #c9c2b6; }
    .sheet-wrap img { image-rendering: pixelated; display: block; }
    .swatches { display: flex; gap: 4px; margin-top: 8px; }
    .swatches b { width: 14px; height: 14px; display: inline-block; border: 1px solid var(--ink); font-weight: normal; }
    .frame-readout { font-variant-numeric: tabular-nums; color: var(--muted); font-size: 13px; }
    @media (max-width: 860px) {
      main { grid-template-columns: 1fr; }
      aside { border-right: 0; border-bottom: 1px solid var(--line); }
      .stage-wrap { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>肉鸽动物八方向精灵</h1>
      <p>原地静息、移动、快速移动、攻击、受伤。每张图集 8 行朝向，从左到右是帧。</p>
    </div>
    <div class="frame-readout" id="readout"></div>
  </header>
  <main>
    <aside id="roster"></aside>
    <section>
      <div class="stage-wrap">
        <div>
          <div id="stage" class="stage"></div>
          <div class="transport">
            <button id="play" type="button">暂停</button>
            <button id="step" type="button">下一帧</button>
            <button id="scale" type="button">放大 4x</button>
          </div>
        </div>
        <div class="meta">
          <h2 id="title"></h2>
          <p id="trait"></p>
          <div class="actions" id="actions"></div>
          <div class="pad" id="pad"></div>
          <p class="frame-readout" id="spec"></p>
          <div class="downloads">
            <a id="dl-sheet" href="#">下载当前图集</a>
            <a id="dl-char" href="#">下载这个角色</a>
            <a id="dl-all" href="../exports/rogue_animals_sprites.zip" download>下载全部角色</a>
          </div>
          <div class="swatches" id="swatches"></div>
        </div>
      </div>
      <div class="sheet-wrap">
        <img id="sheet" alt="当前动作的八方向精灵图" />
      </div>
    </section>
  </main>
  <script>
    const DATA = __DATA__;
    const state = {
      char: 0,
      action: "idle",
      dir: 0,
      frame: 0,
      scale: 4,
      playing: true,
    };
    const $ = (id) => document.getElementById(id);
    const actionOf = (id) => DATA.animations[id];
    const charOf = () => DATA.characters[state.char];

    function sheetUrl() {
      return `../sheets/game/${charOf().id}_${state.action}.png`;
    }

    function paint(el, dir, frame, scale) {
      const anim = actionOf(state.action);
      el.style.backgroundImage = `url("${sheetUrl()}")`;
      el.style.backgroundSize = `${anim.frames * scale * 64}px ${8 * scale * 64}px`;
      el.style.backgroundPosition = `${-frame * scale * 64}px ${-dir * scale * 64}px`;
    }

    function sync() {
      const anim = actionOf(state.action);
      const ch = charOf();
      if (state.frame >= anim.frames) state.frame = 0;
      paint($("stage"), state.dir, state.frame, state.scale);
      $("stage").style.width = `${state.scale * 64}px`;
      $("stage").style.height = `${state.scale * 64}px`;
      document.querySelectorAll(".cell").forEach((cell) => {
        const dir = Number(cell.dataset.dir);
        paint(cell, dir, state.frame, 1);
        cell.style.backgroundSize = `${anim.frames * 64}px ${8 * 64}px`;
        cell.classList.toggle("active", dir === state.dir);
      });
      document.querySelectorAll(".char-btn").forEach((btn, i) => btn.classList.toggle("active", i === state.char));
      document.querySelectorAll("#actions button").forEach((btn) => btn.classList.toggle("active", btn.dataset.action === state.action));
      $("title").textContent = `${ch.name} · ${ch.animal}`;
      $("trait").textContent = `${ch.color}。${ch.trait}`;
      $("spec").textContent = `${anim.label} · ${anim.frames} 帧 · ${anim.fps} fps · ${anim.loop ? "循环" : "播放一次"} · 朝向 ${DATA.directions[state.dir].label}`;
      $("readout").textContent = `帧 ${state.frame + 1}/${anim.frames}`;
      $("sheet").src = sheetUrl();
      $("dl-sheet").href = sheetUrl();
      $("dl-sheet").download = `${ch.id}_${state.action}.png`;
      $("dl-char").href = `../exports/characters/${ch.id}.zip`;
      $("dl-char").download = `${ch.id}.zip`;
      $("play").textContent = state.playing ? "暂停" : "播放";
      $("scale").textContent = state.scale === 4 ? "放大 6x" : "回到 4x";
    }

    function boot() {
      const roster = $("roster");
      DATA.characters.forEach((ch, i) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "char-btn";
        btn.innerHTML = `<div class="thumb"></div><div><strong>${ch.name}</strong><span>${ch.animal}</span></div>`;
        btn.addEventListener("click", () => { state.char = i; state.frame = 0; sync(); });
        roster.appendChild(btn);
        const thumb = btn.querySelector(".thumb");
        thumb.style.backgroundImage = `url("../sheets/game/${ch.id}_idle.png")`;
        thumb.style.backgroundSize = `${4 * 64}px ${8 * 64}px`;
        thumb.style.backgroundPosition = "0 0";
      });
      const actions = $("actions");
      Object.entries(DATA.animations).forEach(([id, anim]) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.dataset.action = id;
        btn.textContent = anim.label;
        btn.addEventListener("click", () => { state.action = id; state.frame = 0; state.playing = true; sync(); });
        actions.appendChild(btn);
      });
      const pad = $("pad");
      const slots = [
        { dir: 5, grid: "1 / 1" },
        { dir: 4, grid: "1 / 2" },
        { dir: 3, grid: "1 / 3" },
        { dir: 6, grid: "2 / 1" },
        { dir: 2, grid: "2 / 3" },
        { dir: 7, grid: "3 / 1" },
        { dir: 0, grid: "3 / 2" },
        { dir: 1, grid: "3 / 3" },
      ];
      slots.forEach((slot) => {
        const cell = document.createElement("button");
        cell.type = "button";
        cell.className = "cell";
        cell.dataset.dir = String(slot.dir);
        cell.style.gridColumn = slot.grid.split(" / ")[1];
        cell.style.gridRow = slot.grid.split(" / ")[0];
        cell.innerHTML = `<i>${DATA.directions[slot.dir].label}</i>`;
        cell.addEventListener("click", () => { state.dir = slot.dir; sync(); });
        pad.appendChild(cell);
      });
      const colors = ["#EF7D57", "#FFCD75", "#B13E53", "#41A6F6", "#C4A1E8", "#1A2744", "#38B764", "#8FD96A", "#146B3A"];
      colors.forEach((color) => {
        const sw = document.createElement("b");
        sw.style.background = color;
        $("swatches").appendChild(sw);
      });
      $("play").addEventListener("click", () => { state.playing = !state.playing; sync(); });
      $("step").addEventListener("click", () => {
        state.playing = false;
        const anim = actionOf(state.action);
        state.frame = (state.frame + 1) % anim.frames;
        sync();
      });
      $("scale").addEventListener("click", () => { state.scale = state.scale === 4 ? 6 : 4; sync(); });
      document.addEventListener("keydown", (event) => {
        const map = { ArrowDown: 0, ArrowRight: 2, ArrowUp: 4, ArrowLeft: 6 };
        if (event.key in map) { state.dir = map[event.key]; sync(); }
        if (event.key === " ") { event.preventDefault(); state.playing = !state.playing; sync(); }
      });
      sync();
      let last = performance.now();
      function tick(now) {
        const anim = actionOf(state.action);
        const step = 1000 / anim.fps;
        if (state.playing && now - last >= step) {
          last = now;
          if (state.frame + 1 >= anim.frames && !anim.loop) {
            state.playing = false;
          } else {
            state.frame = (state.frame + 1) % anim.frames;
          }
          sync();
        }
        if (!state.playing) last = now;
        requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    }
    boot();
  </script>
</body>
</html>
"""


def rebuild_game_sheets():
    """Repack direction rows from the post-processed frame files."""
    game_dir = PROJECT / "sheets" / "game"
    char_dir = PROJECT / "assets" / "characters"
    game_dir.mkdir(parents=True, exist_ok=True)
    for char in CHARACTERS:
        for action, count, *_rest in ACTIONS:
            sheet = Image.new("RGBA", (count * 64, len(DIRS) * 64), (0, 0, 0, 0))
            for row, direction in enumerate(DIRS):
                for frame in range(count):
                    path = char_dir / f"{char['id']}_{direction[0]}_{action}_{frame}.png"
                    frame_img = Image.open(path).convert("RGBA")
                    sheet.paste(frame_img, (frame * 64, row * 64))
            sheet.save(game_dir / f"{char['id']}_{action}.png", "PNG")
    print("[OK] rebuilt game sheets from frames")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--montage", action="store_true")
    parser.add_argument("--only", default="")
    parser.add_argument("--pack", action="store_true", help="Rebuild sheets, preview, and zip from existing frames")
    args = parser.parse_args()
    palette = load_palette(SPEC_PATH)
    if args.pack:
        rebuild_game_sheets()
        manifest = write_manifest()
        write_preview(manifest)
        write_zips()
        return
    if args.montage:
        montage(palette)
        return
    only = {item for item in args.only.split(",") if item} or None
    save_frames(palette, only=only)
    write_notes()
    write_palette_files(palette)
    manifest = write_manifest()
    write_preview(manifest)
    if only is None:
        write_zips()


if __name__ == "__main__":
    main()
