#!/usr/bin/env python3
"""Схемы к запросу во ВНИИПО о порядке измерений по п. 4.4.2 СП 1.13130.2020.

Планы строятся в метрах и выводятся в SVG/PNG.
Система координат плана: x — вправо, y — вниз (как на строительном плане).
Направления задаются углом в градусах: 0° = вправо, 90° = вниз, 180° = влево, 270° = вверх.
"""

import math
from pathlib import Path

import cairosvg

OUT = Path(__file__).resolve().parents[1] / "figures"
OUT.mkdir(parents=True, exist_ok=True)

CANVAS_W, CANVAS_H = 1800, 1120
TITLE_H = 92
PANEL_X = 1170
PANEL_W = CANVAS_W - PANEL_X - 36

FONT = "DejaVu Sans"

INK = "#1b2330"
WALL_LINE = "#414956"
WALL_FILL = "#8b939f"
SLAB = "#f5f2ea"
STEP = "#e9eef4"
STEP_LINE = "#aab5c3"
RAIL = "#2f3742"
DOOR = "#1f66b0"
DOOR_B = "#7a49ab"
DOOR_C = "#c2681c"
DIM = "#c0392b"
DIM_OK = "#1a7a4c"
DIM_ALT = "#8a5a12"
MUTED = "#5c6675"
PANEL_BG = "#f7f9fc"
PANEL_EDGE = "#d6dee9"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def tokenize_bold(s):
    """Разбор строки с **жирными** фрагментами на список (слово, жирный)."""
    tokens = []
    bold = False
    for chunk in s.split("**"):
        for word in chunk.split(" "):
            if word:
                tokens.append((word, bold))
        bold = not bold
    return tokens


def wrap_tokens(tokens, max_px, size):
    """Перенос по словам с учётом приблизительной ширины глифов DejaVu Sans."""
    lines, cur, cur_w = [], [], 0.0
    for word, bold in tokens:
        w = len(word) * size * (0.645 if bold else 0.60)
        space = size * 0.32 if cur else 0.0
        if cur and cur_w + space + w > max_px:
            lines.append(cur)
            cur, cur_w = [(word, bold)], w
        else:
            cur.append((word, bold))
            cur_w += space + w
    if cur:
        lines.append(cur)
    return lines


class Drawing:
    def __init__(self, title, subtitle, ppm=250.0, origin=(300, 205)):
        self.parts = []
        self.ppm = ppm
        self.ox, self.oy = origin
        self.title = title
        self.subtitle = subtitle

    # --- координаты ---
    def X(self, x):
        return self.ox + x * self.ppm

    def Y(self, y):
        return self.oy + y * self.ppm

    def S(self, v):
        return v * self.ppm

    # --- примитивы ---
    def raw(self, s):
        self.parts.append(s)

    def rect(self, x, y, w, h, fill="none", stroke=INK, sw=1.4, dash=None, opacity=1.0, rx=0):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(
            f'<rect x="{self.X(x):.1f}" y="{self.Y(y):.1f}" width="{self.S(w):.1f}" '
            f'height="{self.S(h):.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{sw}" opacity="{opacity}"{d}/>'
        )

    def line(self, x1, y1, x2, y2, stroke=INK, sw=1.4, dash=None, cap="butt"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(
            f'<line x1="{self.X(x1):.1f}" y1="{self.Y(y1):.1f}" x2="{self.X(x2):.1f}" '
            f'y2="{self.Y(y2):.1f}" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="{cap}"{d}/>'
        )

    def polygon(self, pts, fill=INK, stroke="none", sw=1.0, opacity=1.0):
        s = " ".join(f"{self.X(px):.1f},{self.Y(py):.1f}" for px, py in pts)
        self.raw(f'<polygon points="{s}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{opacity}"/>')

    def arc(self, cx, cy, r, deg1, deg2, stroke=MUTED, sw=1.1, dash="7 6"):
        # кратчайшее направление дуги
        while deg2 - deg1 > 180:
            deg2 -= 360
        while deg2 - deg1 < -180:
            deg2 += 360
        a1, a2 = math.radians(deg1), math.radians(deg2)
        x1, y1 = self.X(cx + r * math.cos(a1)), self.Y(cy + r * math.sin(a1))
        x2, y2 = self.X(cx + r * math.cos(a2)), self.Y(cy + r * math.sin(a2))
        large = 1 if abs(deg2 - deg1) > 180 else 0
        sweep = 1 if deg2 > deg1 else 0
        self.raw(
            f'<path d="M {x1:.1f} {y1:.1f} A {self.S(r):.1f} {self.S(r):.1f} 0 {large} {sweep} '
            f'{x2:.1f} {y2:.1f}" fill="none" stroke="{stroke}" stroke-width="{sw}" stroke-dasharray="{dash}"/>'
        )

    def text_px(self, px, py, s, size=17, anchor="start", fill=INK, weight="normal"):
        self.raw(
            f'<text x="{px:.1f}" y="{py:.1f}" font-family="{FONT}" font-size="{size}" '
            f'text-anchor="{anchor}" fill="{fill}" font-weight="{weight}">{esc(s)}</text>'
        )

    def text(self, x, y, s, dx=0, dy=0, **kw):
        self.text_px(self.X(x) + dx, self.Y(y) + dy, s, **kw)

    def boxed_text_px(self, px, py, s, size=18, fill=INK, weight="bold", anchor="middle"):
        w = len(s) * size * 0.60 + 14
        h = size * 1.5
        x0 = {"middle": px - w / 2, "start": px - 7, "end": px - w + 7}[anchor]
        self.raw(
            f'<rect x="{x0:.1f}" y="{py - h * 0.76:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'rx="3" fill="#ffffff" opacity="0.95"/>'
        )
        self.text_px(px, py, s, size=size, anchor=anchor, fill=fill, weight=weight)

    # --- размерные линии ---
    def _arrow_px(self, px, py, ang, color, size=9):
        pts = [
            (px, py),
            (px + size * math.cos(ang + 0.34), py + size * math.sin(ang + 0.34)),
            (px + size * math.cos(ang - 0.34), py + size * math.sin(ang - 0.34)),
        ]
        s = " ".join(f"{a:.1f},{b:.1f}" for a, b in pts)
        self.raw(f'<polygon points="{s}" fill="{color}"/>')

    def _ticks_v(self, px, py, color):
        self.raw(f'<line x1="{px - 7:.1f}" y1="{py:.1f}" x2="{px + 7:.1f}" y2="{py:.1f}" stroke="{color}" stroke-width="1.7"/>')

    def _ticks_h(self, px, py, color):
        self.raw(f'<line x1="{px:.1f}" y1="{py - 7:.1f}" x2="{px:.1f}" y2="{py + 7:.1f}" stroke="{color}" stroke-width="1.7"/>')

    def dim_v(self, x_dim, y1, y2, label, ext_from_x=None, color=DIM, side="right",
              label_dx=0, label_dy=0, size=19):
        px = self.X(x_dim)
        py1, py2 = self.Y(min(y1, y2)), self.Y(max(y1, y2))
        if ext_from_x is not None:
            for yy in (y1, y2):
                self.line(ext_from_x, yy, x_dim, yy, stroke=color, sw=0.9, dash="4 4")
        self.raw(f'<line x1="{px:.1f}" y1="{py1:.1f}" x2="{px:.1f}" y2="{py2:.1f}" stroke="{color}" stroke-width="1.7"/>')
        short = (py2 - py1) < 46
        if short:
            self._arrow_px(px, py1, -math.pi / 2, color)
            self._arrow_px(px, py2, math.pi / 2, color)
        else:
            self._arrow_px(px, py1, math.pi / 2, color)
            self._arrow_px(px, py2, -math.pi / 2, color)
        self._ticks_v(px, py1, color)
        self._ticks_v(px, py2, color)
        mid = (py1 + py2) / 2
        anchor = "start" if side == "right" else "end"
        off = 13 if side == "right" else -13
        self.boxed_text_px(px + off + label_dx, mid + size * 0.36 + label_dy, label,
                           size=size, fill=color, anchor=anchor)

    def dim_h(self, y_dim, x1, x2, label, ext_from_y=None, color=DIM, above=True,
              label_dx=0, label_dy=0, size=19):
        py = self.Y(y_dim)
        px1, px2 = self.X(min(x1, x2)), self.X(max(x1, x2))
        if ext_from_y is not None:
            for xx in (x1, x2):
                self.line(xx, ext_from_y, xx, y_dim, stroke=color, sw=0.9, dash="4 4")
        self.raw(f'<line x1="{px1:.1f}" y1="{py:.1f}" x2="{px2:.1f}" y2="{py:.1f}" stroke="{color}" stroke-width="1.7"/>')
        short = (px2 - px1) < 46
        if short:
            self._arrow_px(px1, py, math.pi, color)
            self._arrow_px(px2, py, 0, color)
        else:
            self._arrow_px(px1, py, 0, color)
            self._arrow_px(px2, py, math.pi, color)
        self._ticks_h(px1, py, color)
        self._ticks_h(px2, py, color)
        mid = (px1 + px2) / 2
        ty = py - 11 if above else py + size + 5
        self.boxed_text_px(mid + label_dx, ty + label_dy, label, size=size, fill=color)

    def leader(self, x1, y1, x2, y2, text, color=MUTED, size=16, anchor="start", dx=6):
        self.line(x1, y1, x2, y2, stroke=color, sw=1.0, dash="3 3")
        self.circle_px(self.X(x1), self.Y(y1), 3.2, color)
        self.text_px(self.X(x2) + dx, self.Y(y2) + 5, text, size=size, fill=color, anchor=anchor)

    def circle_px(self, px, py, r, fill):
        self.raw(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r}" fill="{fill}"/>')

    def callout(self, x, y, n, color=DIM, r=15):
        px, py = self.X(x), self.Y(y)
        self.raw(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r}" fill="{color}" stroke="#ffffff" stroke-width="2.2"/>')
        self.text_px(px, py + 6, str(n), size=17, anchor="middle", fill="#ffffff", weight="bold")

    # --- элементы плана ---
    def walls(self, x0, y0, x1, y1, t=0.20):
        self.rect(x0 - t, y0 - t, (x1 - x0) + 2 * t, t, fill=WALL_FILL, stroke=WALL_LINE, sw=1.2)
        self.rect(x0 - t, y1, (x1 - x0) + 2 * t, t, fill=WALL_FILL, stroke=WALL_LINE, sw=1.2)
        self.rect(x0 - t, y0, t, y1 - y0, fill=WALL_FILL, stroke=WALL_LINE, sw=1.2)
        self.rect(x1, y0, t, y1 - y0, fill=WALL_FILL, stroke=WALL_LINE, sw=1.2)

    def landing(self, x0, y0, x1, y1):
        self.rect(x0, y0, x1 - x0, y1 - y0, fill=SLAB, stroke=INK, sw=1.7)

    def flight(self, x0, y0, x1, y1, rise=0.30, direction="down", label=None, label_dy=0.0):
        self.rect(x0, y0, x1 - x0, y1 - y0, fill=STEP, stroke=INK, sw=1.7)
        n = int((y1 - y0) / rise)
        for i in range(1, n + 1):
            yy = y0 + i * rise
            if yy < y1 - 0.01:
                self.line(x0, yy, x1, yy, stroke=STEP_LINE, sw=1.0)
        cx = (x0 + x1) / 2
        if direction == "down":
            self.line(cx, y0 + 0.28, cx, y1 - 0.22, stroke=MUTED, sw=1.5)
            self._arrow_px(self.X(cx), self.Y(y1 - 0.22), math.pi / 2, MUTED, size=10)
        else:
            self.line(cx, y0 + 0.28, cx, y1 - 0.22, stroke=MUTED, sw=1.5)
            self._arrow_px(self.X(cx), self.Y(y0 + 0.28), -math.pi / 2, MUTED, size=10)
        if label:
            self.text(cx, (y0 + y1) / 2 + label_dy, label, size=16, fill=MUTED, anchor="middle")

    def break_line(self, x0, x1, y, t=0.20):
        """Линия обрыва изображения."""
        amp = 0.05
        n = 14
        pts = []
        for i in range(n + 1):
            xx = x0 - t + (x1 - x0 + 2 * t) * i / n
            pts.append((xx, y + (amp if i % 2 else -amp)))
        path = " ".join(f"{'M' if i == 0 else 'L'} {self.X(px):.1f} {self.Y(py):.1f}" for i, (px, py) in enumerate(pts))
        self.raw(f'<rect x="{self.X(x0 - t):.1f}" y="{self.Y(y - amp - 0.03):.1f}" '
                 f'width="{self.S(x1 - x0 + 2 * t):.1f}" height="{self.S(2 * amp + 0.06):.1f}" fill="#ffffff"/>')
        self.raw(f'<path d="{path}" fill="none" stroke="{MUTED}" stroke-width="1.6"/>')

    def railing(self, x1, y1, x2, y2):
        self.line(x1, y1, x2, y2, stroke=RAIL, sw=5.2, cap="round")

    def opening(self, x, y, w, vertical=False, t=0.20):
        if vertical:
            self.rect(x - t, y, t, w, fill="#ffffff", stroke=WALL_LINE, sw=1.2)
        else:
            self.rect(x, y - t, w, t, fill="#ffffff", stroke=WALL_LINE, sw=1.2)

    def door(self, hinge, closed_deg, open_deg, leaf=0.90, thickness=0.05,
             color=DOOR, normal_sign=1, handle=True, handle_out=0.065, swing=True,
             arc_r=None, opacity=1.0):
        """Полотно в открытом положении + дуга открывания. Возвращает (кромка, точка ручки)."""
        hx, hy = hinge
        a = math.radians(open_deg)
        ux, uy = math.cos(a), math.sin(a)
        nx, ny = -uy * normal_sign, ux * normal_sign
        tx, ty = hx + leaf * ux, hy + leaf * uy
        pts = [
            (hx, hy), (tx, ty),
            (tx + nx * thickness, ty + ny * thickness),
            (hx + nx * thickness, hy + ny * thickness),
        ]
        if swing:
            self.arc(hx, hy, arc_r if arc_r is not None else leaf,
                     closed_deg, open_deg, stroke=color, sw=1.1, dash="7 6")
        self.polygon(pts, fill=color, stroke=INK, sw=1.2, opacity=opacity)
        hpt = None
        if handle:
            base = (hx + (leaf - 0.10) * ux + nx * thickness, hy + (leaf - 0.10) * uy + ny * thickness)
            tip = (base[0] + nx * handle_out, base[1] + ny * handle_out)
            self.line(base[0], base[1], tip[0], tip[1], stroke=DIM, sw=3.6, cap="round")
            hpt = tip
        return (tx, ty), hpt

    # --- боковая панель ---
    def panel(self, blocks):
        self.raw(
            f'<rect x="{PANEL_X}" y="{TITLE_H + 24}" width="{PANEL_W}" height="{CANVAS_H - TITLE_H - 86}" '
            f'rx="10" fill="{PANEL_BG}" stroke="{PANEL_EDGE}" stroke-width="1.5"/>'
        )
        y = TITLE_H + 62
        for kind, head, lines in blocks:
            if kind == "head":
                for ln in wrap_tokens(tokenize_bold(head), PANEL_W - 54, 20):
                    self._panel_line(PANEL_X + 27, y, ln, 20, INK, force_bold=True)
                    y += 27
                y += 4
                tx, tw = PANEL_X + 27, PANEL_W - 54
            elif kind == "callout":
                self.raw(f'<circle cx="{PANEL_X + 42}" cy="{y - 6}" r="14.5" fill="{head[1]}"/>')
                self.text_px(PANEL_X + 42, y + 1, str(head[0]), size=17, anchor="middle",
                             fill="#ffffff", weight="bold")
                tx, tw = PANEL_X + 70, PANEL_W - 97
            else:
                tx, tw = PANEL_X + 27, PANEL_W - 54
            for src in lines:
                if src == "":
                    y += 12
                    continue
                for ln in wrap_tokens(tokenize_bold(src), tw, 18):
                    self._panel_line(tx, y, ln, 18, MUTED)
                    y += 25
            y += 16

    def _panel_line(self, x, y, tokens, size, fill, force_bold=False):
        spans = []
        for i, (word, bold) in enumerate(tokens):
            pre = " " if i and word[0] not in ".,;:!?)»" else ""
            weight = "bold" if (bold or force_bold) else "normal"
            col = INK if (bold or force_bold) else fill
            spans.append(
                f'<tspan font-weight="{weight}" fill="{col}" xml:space="preserve">{esc(pre + word)}</tspan>'
            )
        self.raw(
            f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
            f'fill="{fill}">{"".join(spans)}</text>'
        )

    def render(self, filename):
        head = (
            f'<rect width="{CANVAS_W}" height="{CANVAS_H}" fill="#ffffff"/>'
            f'<rect width="{CANVAS_W}" height="{TITLE_H}" fill="#22344f"/>'
            f'<text x="34" y="40" font-family="{FONT}" font-size="26" fill="#ffffff" font-weight="bold">'
            f'{esc(self.title)}</text>'
            f'<text x="34" y="71" font-family="{FONT}" font-size="18" fill="#c3d1e4">{esc(self.subtitle)}</text>'
        )
        foot = (
            f'<line x1="34" y1="{CANVAS_H - 44}" x2="{CANVAS_W - 34}" y2="{CANVAS_H - 44}" stroke="{PANEL_EDGE}" stroke-width="1.5"/>'
            f'<text x="34" y="{CANVAS_H - 18}" font-family="{FONT}" font-size="15" fill="{MUTED}">'
            f'{esc("Приложение к запросу во ФГБУ ВНИИПО МЧС России о разъяснении п. 4.4.2 СП 1.13130.2020. Размеры в метрах.")}</text>'
        )
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
            f'viewBox="0 0 {CANVAS_W} {CANVAS_H}">{head}{"".join(self.parts)}{foot}</svg>'
        )
        (OUT / (filename + ".svg")).write_text(svg, encoding="utf-8")
        png = OUT / (filename + ".png")
        cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(png),
                         output_width=CANVAS_W, output_height=CANVAS_H)
        return png


# =====================================================================
# Геометрия типовой лестничной клетки
# =====================================================================
B = 1.20          # ширина марша
GAP = 0.15        # зазор между маршами
W_IN = 2 * B + GAP    # 2,55 — внутренняя ширина клетки
A_LAND = 1.40     # размер площадки от стены до края марша
F_SHOWN = 1.25    # показываемая часть маршей


def base_stair(d, show_labels=True):
    bottom = A_LAND + F_SHOWN
    d.walls(0, 0, W_IN, bottom)
    d.landing(0, 0, W_IN, A_LAND)
    d.flight(0, A_LAND, B, bottom, direction="down",
             label="марш вниз" if show_labels else None, label_dy=0.18)
    d.flight(B + GAP, A_LAND, W_IN, bottom, direction="up",
             label="марш вверх" if show_labels else None, label_dy=0.18)
    d.rect(B, A_LAND, GAP, F_SHOWN, fill="#ffffff", stroke=STEP_LINE, sw=1.0)
    d.railing(B, A_LAND, B, bottom)
    d.railing(B + GAP, A_LAND, B + GAP, bottom)
    d.railing(B, A_LAND, B + GAP, A_LAND)
    d.break_line(0, W_IN, bottom)
    return bottom


# =====================================================================
# Рисунок 1
# =====================================================================
def fig1():
    d = Drawing(
        "Рисунок 1. Нормируемые размеры лестничной клетки",
        "Исходная схема. Обозначения, используемые далее в тексте запроса и на рисунках 2–6.",
        origin=(300, 262),
    )
    base_stair(d)
    d.opening(1.05, 0.0, 0.90)
    d.text(1.50, -0.28, "дверной проём 0,90 м", size=16, fill=MUTED, anchor="middle")

    d.dim_v(-0.52, 0, A_LAND, "A = 1,40 м", ext_from_x=0.0, color=DIM_OK, side="left")
    d.dim_h(-0.52, 0, W_IN, "L = 2,55 м", ext_from_y=-0.20, color=DIM_OK)
    d.dim_h(A_LAND + 0.95, 0, B, "b = 1,20 м", ext_from_y=A_LAND + 0.62, color=DIM_OK, above=False)
    d.dim_h(A_LAND + 0.95, B + GAP, W_IN, "b = 1,20 м", ext_from_y=A_LAND + 0.62, color=DIM_OK, above=False)

    d.callout(0.34, 0.62, 1)
    d.callout(1.50, 0.20, 2)
    d.callout(B + GAP / 2, A_LAND + 0.62, 3)

    d.panel([
        ("head", "Обозначения размеров", [
            "**A** — размер площадки от стены с дверным проёмом до края марша "
            "(в практике его называют также глубиной площадки).",
            "**L** — размер площадки вдоль стены с дверным проёмом.",
            "**b** — ширина марша, определяемая расстоянием между ограждением и стеной "
            "(п. 4.2.20 СП 1.13130.2020).",
        ]),
        ("callout", (1, DIM), [
            "**Лестничная площадка.** Абзац первый п. 4.4.2 требует, чтобы её ширина была "
            "не менее ширины марша. Какой из размеров — A или L — при этом имеется в виду, "
            "изложено в вопросе 4.",
        ]),
        ("callout", (2, DIM), [
            "**Дверь, выходящая на лестничную клетку.** Абзац третий п. 4.4.2 запрещает "
            "уменьшать ею требуемую ширину площадок и маршей, но не определяет ни положение "
            "полотна при проверке, ни точки замера.",
        ]),
        ("callout", (3, DIM), [
            "**Ограждение лестничного проёма** — одна из возможных конечных точек замера "
            "(вопрос 3, рисунок 4).",
        ]),
        ("head", "Исходные данные, принятые на рисунках 2–6", [
            "Ширина марша b = 1,20 м, требуемая ширина — 1,20 м.",
            "Размер площадки A = 1,40 м.",
            "Дверное полотно шириной 0,90 м, толщиной 50 мм; вылет ручки 65 мм.",
        ]),
    ])
    return d.render("рис-1-normiruemye-razmery")


# =====================================================================
# Рисунок 2
# =====================================================================
def fig2():
    d = Drawing(
        "Рисунок 2. Положение дверного полотна при проверке",
        "Один и тот же дверной блок в трёх положениях: свободный размер площадки различается в 2,6 раза.",
    )
    base_stair(d, show_labels=False)
    d.opening(1.05, 0.0, 0.90)
    hinge = (1.05, 0.0)

    # 180° — «до упора» в стену
    d.door(hinge, 0, 180, color=DOOR_B, normal_sign=1, swing=False)
    d.text(0.60, 0.34, "180° — «до упора»", size=17, fill=DOOR_B, weight="bold", anchor="middle")

    # 45° — промежуточное
    d.door(hinge, 0, 45, color=DOOR_C, normal_sign=1, swing=False)
    d.text(2.02, 0.50, "45°", size=18, fill=DOOR_C, weight="bold", anchor="middle")

    # 90°
    d.door(hinge, 0, 90, color=DOOR, normal_sign=1, swing=True, arc_r=0.52)
    d.text(0.90, 1.06, "90°", size=18, fill=DOOR, weight="bold", anchor="end")

    d.dim_v(1.30, 0.90, A_LAND, "B₁ = 0,50 м", ext_from_x=1.10, color=DOOR,
            side="right", label_dx=2)
    d.dim_v(1.686, 0.636, A_LAND, "B₃ = 0,76 м", ext_from_x=1.686, color=DOOR_C, side="right")
    d.dim_v(0.42, 0.115, A_LAND, "B₂ = 1,29 м", ext_from_x=0.42, color=DOOR_B, side="left")

    d.line(0, A_LAND, W_IN, A_LAND, stroke=DIM, sw=2.0, dash="11 7")
    d.text(W_IN - 0.04, A_LAND + 0.20, "край площадки", size=15, fill=DIM, anchor="end")

    d.panel([
        ("head", "Вопрос 1: какое положение полотна является расчётным?", [
            "Свободный размер площадки измерен от кромки полотна до края площадки "
            "по направлению движения.",
        ]),
        ("callout", (1, DOOR), [
            "**B₁ = 0,50 м** — полотно открыто на 90° к плоскости проёма.",
        ]),
        ("callout", (2, DOOR_C), [
            "**B₃ = 0,76 м** — промежуточное положение (45°), проходимое полотном "
            "при каждом открывании двери.",
        ]),
        ("callout", (3, DOOR_B), [
            "**B₂ = 1,29 м** — полотно открыто «до упора» в стену; в габарит площадки "
            "выступают только толщина полотна и ручка.",
        ]),
        ("head", "Следствие", [
            "При требуемой ширине 1,20 м положения 90° и 45° дают вывод о нарушении, "
            "положение «до упора» — о соответствии. Свод правил не указывает, какое из них "
            "принимается при проверке.",
        ]),
    ])
    return d.render("рис-2-polozhenie-polotna")


# =====================================================================
# Рисунок 3
# =====================================================================
def fig3():
    d = Drawing(
        "Рисунок 3. Начальная точка замера на дверном блоке",
        "Фрагмент плана в увеличенном масштабе. Положение полотна одно и то же, результат зависит от точки отсчёта.",
        ppm=565.0,
        origin=(300, 225),
    )
    # стена с проёмом
    d.rect(-0.16, -0.10, 0.16, 1.22, fill=WALL_FILL, stroke=WALL_LINE, sw=1.2)
    # полотно
    d.rect(0.0, 0.0, 0.05, 1.12, fill=DOOR, stroke=INK, sw=1.3)
    d.text_px(d.X(0.025), d.Y(1.24), "дверное полотно", size=17, fill=DOOR, weight="bold", anchor="middle")
    d.text_px(d.X(0.025), d.Y(1.24) + 22, "50 мм", size=17, fill=DOOR, weight="bold", anchor="middle")

    # рычаг доводчика
    d.rect(0.05, 0.12, 0.09, 0.07, fill="#6b7280", stroke=INK, sw=1.0)
    # ручка
    d.rect(0.05, 0.74, 0.065, 0.05, fill=DIM, stroke=INK, sw=1.0)

    # ограждение
    d.rect(1.30, -0.10, 0.06, 1.22, fill=RAIL, stroke=INK, sw=1.0)
    d.text_px(d.X(1.33), d.Y(1.24), "ограждение", size=17, fill=RAIL, weight="bold", anchor="middle")
    d.text_px(d.X(1.33), d.Y(1.24) + 22, "или стена", size=17, fill=RAIL, weight="bold", anchor="middle")

    d.dim_h(0.46, 0.05, 1.30, "1,250 м", ext_from_y=0.46, color=DOOR)
    d.dim_h(0.94, 0.115, 1.30, "1,185 м", ext_from_y=0.79, color=DIM, above=False)
    d.dim_h(0.02, 0.14, 1.30, "1,160 м", ext_from_y=0.15, color=DIM_ALT)

    d.leader(0.14, 0.155, 0.42, 0.30, "рычаг доводчика, вылет 90 мм", color="#4b5563")
    d.leader(0.115, 0.765, 0.42, 1.06, "ручка, вылет 65 мм", color=DIM)

    d.callout(0.05, 0.46, 1, color=DOOR)
    d.callout(0.115, 0.94, 2, color=DIM)
    d.callout(0.14, 0.02, 3, color=DIM_ALT)

    d.panel([
        ("head", "Вопрос 2: от какой точки двери ведётся замер?", [
            "Замер выполнен по нормали к плоскости полотна до ограждения.",
        ]),
        ("callout", (1, DOOR), [
            "**От плоскости дверного полотна — 1,250 м.**",
        ]),
        ("callout", (2, DIM), [
            "**От наиболее выступающей точки дверной ручки — 1,185 м.**",
        ]),
        ("callout", (3, DIM_ALT), [
            "**От наиболее выступающей части двери в целом — 1,160 м** "
            "(рычаг доводчика, ограничитель открывания, антипаниковая фурнитура).",
        ]),
        ("head", "Следствие", [
            "При требуемой ширине 1,20 м первый вариант даёт вывод о соответствии, "
            "второй и третий — о нарушении.",
            "",
            "В письме ФГБУ ВНИИПО МЧС России от 10.08.2018 № 4772-13-4-4 указано на "
            "необходимость учёта устройств для самозакрывания и других выступающих частей "
            "дверного полотна. Просим подтвердить, что этот подход применяется и к "
            "п. 4.4.2 СП 1.13130.2020.",
        ]),
    ])
    return d.render("рис-3-tochka-zamera-na-dveri")


# =====================================================================
# Рисунок 4
# =====================================================================
def fig4():
    d = Drawing(
        "Рисунок 4. Конечная точка замера на лестничной площадке",
        "Начальная точка одна — кромка полотна, открытого на 90°. Конечные конструкции разные: разброс результата 1,5 м.",
    )
    base_stair(d, show_labels=False)

    # пожарный шкаф у левой стены
    d.rect(0.0, 0.86, 0.20, 0.48, fill="#e6c9c3", stroke=INK, sw=1.2)
    d.text(0.24, 1.30, "пожарный шкаф", size=15, fill=MUTED)

    # дверь над правым маршем
    d.opening(1.50, 0.0, 0.90)
    d.door((2.40, 0.0), 180, 90, color=DOOR, normal_sign=1, arc_r=0.55)
    d.text(2.34, 1.06, "дверь, 90°", size=17, fill=DOOR, weight="bold", anchor="end")

    x_leaf = 2.40  # плоскость полотна, обращённая к площадке
    targets = [
        (1.50, 0.20, "0,90 м", DIM_OK, 1),
        (1.35, 0.46, "1,05 м", DIM_ALT, 2),
        (0.20, 0.72, "2,20 м", DOOR_B, 3),
        (0.00, 0.98, "2,40 м", "#22344f", 4),
    ]
    for x, y_dim, label, col, n in targets:
        d.line(x, 0.0, x, A_LAND, stroke=col, sw=1.1, dash="6 5")
        d.dim_h(y_dim, x, x_leaf, label, color=col)
        d.callout(x - 0.155, y_dim, n, color=col, r=14)

    d.panel([
        ("head", "Вопрос 3: до какой конструкции ведётся замер?", [
            "Все четыре размера отсчитаны от одной и той же кромки полотна.",
        ]),
        ("callout", (1, DIM_OK), [
            "**До края лестничного марша** (линии примыкания марша к площадке) — **0,90 м**.",
        ]),
        ("callout", (2, DIM_ALT), [
            "**До ограждения лестничного проёма (перил)** — **1,05 м**.",
        ]),
        ("callout", (3, DOOR_B), [
            "**До ближайшего препятствия на пути эвакуации** — пожарного шкафа, выступа "
            "лифтовой шахты, конструктивного выступа — **2,20 м**.",
        ]),
        ("callout", (4, "#22344f"), [
            "**До противоположной стены лестничной клетки** — **2,40 м**.",
        ]),
        ("head", "Следствие", [
            "Норма оперирует понятием «ширина лестничной площадки», но не указывает, какая "
            "из перечисленных конструкций ограничивает эту ширину при открытой двери. "
            "При требуемом значении 1,20 м первый вариант даёт вывод о нарушении, остальные — "
            "о соответствии.",
        ]),
    ])
    return d.render("рис-4-konechnaya-tochka-zamera")


# =====================================================================
# Рисунок 5
# =====================================================================
def fig5():
    d = Drawing(
        "Рисунок 5. Полотно, заходящее в габарит лестничного марша",
        "Дверь у примыкания марша к площадке. Полотно перекрывает часть ширины марша только на участке своего створа.",
        ppm=246.0,
        origin=(455, 255),
    )
    top, mid, bot = 0.0, 0.85, 3.05
    d.walls(0, top, B, bot)
    d.landing(0, top, B, mid)
    d.flight(0, mid, B, bot, rise=0.285, direction="down", label=None)
    d.railing(B, top, B, bot)
    d.text(B + 0.09, 2.62, "ограждение марша", size=16, fill=RAIL)
    d.break_line(0, B, bot)

    # дверь в левой стене, полотно ложится над первыми ступенями
    d.opening(0.0, 0.32, 0.90, vertical=True)
    tip, hpt = d.door((0.0, 1.22), 270, 0, color=DOOR, normal_sign=-1, arc_r=0.45)
    d.text(0.08, 0.55, "дверь в максимально", size=16, fill=DOOR, weight="bold")
    d.text(0.08, 0.55, "открытом положении", size=16, fill=DOOR, weight="bold", dy=21)

    d.dim_h(-0.40, 0, B, "b = 1,20 м — ширина марша", ext_from_y=-0.20, color=DIM_OK)
    d.dim_h(1.22, 0.965, B, "b′ = 0,235 м", color=DIM, label_dx=112, label_dy=6, above=False)
    d.dim_h(2.32, 0, B, "b = 1,20 м", ext_from_y=2.32, color=DIM_OK, above=False)

    # линии сечений
    for y, name in ((1.22, "1—1"), (2.32, "2—2")):
        d.line(-0.40, y, B + 0.86, y, stroke=DIM_ALT, sw=1.2, dash="14 5 4 5")
        d.text(B + 0.92, y + 0.05, name, size=17, fill=DIM_ALT, weight="bold")

    d.callout(-0.40, 1.22, 1, color=DIM)
    d.callout(-0.40, 2.32, 2, color=DIM_OK)

    d.panel([
        ("head", "Вопрос 5: как измеряется ширина марша?", [
            "Полотно в максимально открытом положении заходит в габарит марша, "
            "но лишь на части его длины.",
        ]),
        ("callout", (1, DIM), [
            "**Сечение 1—1** — в створе полотна: свободная ширина марша b′ = **0,235 м**.",
        ]),
        ("callout", (2, DIM_OK), [
            "**Сечение 2—2** — ниже двери: ширина марша b = **1,20 м**, полотно не влияет.",
        ]),
        ("head", "Что требуется разъяснить", [
            "1) Определяется ли свободная ширина марша как минимальное расстояние между "
            "наиболее выступающей частью двери и противоположным ограждением, измеренное "
            "по перпендикуляру к направлению движения (размер b′)?",
            "",
            "2) В каком сечении выполняется замер, если полотно перекрывает марш только на "
            "части его длины, и учитывается ли протяжённость сужения вдоль марша?",
            "",
            "3) Учитывается ли высота расположения полотна над проступями?",
        ]),
    ])
    return d.render("рис-5-polotno-na-marshe")


# =====================================================================
# Рисунок 6
# =====================================================================
def fig6():
    d = Drawing(
        "Рисунок 6. Две двери, выходящие на одну лестничную площадку",
        "При одновременном открывании полотна сужают один и тот же участок пути эвакуации.",
    )
    base_stair(d, show_labels=False)

    # дверь А — в верхней стене
    d.opening(0.55, 0.0, 0.90)
    d.door((1.45, 0.0), 180, 90, color=DOOR, normal_sign=1, arc_r=0.52)
    d.text(1.52, 0.38, "дверь А", size=18, fill=DOOR, weight="bold")

    # дверь Б — в левой стене
    d.opening(0.0, 0.30, 0.90, vertical=True)
    d.door((0.0, 1.20), 270, 0, color=DOOR_B, normal_sign=-1, arc_r=0.45)
    d.text(0.10, 1.35, "дверь Б", size=18, fill=DOOR_B, weight="bold")

    # маршрут движения
    d.raw(
        f'<path d="M {d.X(2.30):.1f} {d.Y(1.24):.1f} '
        f'C {d.X(1.90):.1f} {d.Y(1.26):.1f}, {d.X(1.35):.1f} {d.Y(1.04):.1f}, '
        f'{d.X(0.42):.1f} {d.Y(1.02):.1f}" fill="none" stroke="{DIM}" stroke-width="2.0" '
        f'stroke-dasharray="9 6"/>'
    )
    d._arrow_px(d.X(0.42), d.Y(1.02), math.pi, DIM, size=11)
    d.text(2.48, 1.34, "путь эвакуации по площадке", size=15, fill=DIM, anchor="end")

    d.dim_v(1.86, 0.90, A_LAND, "D_A = 0,50 м", ext_from_x=1.50, color=DOOR, side="right")
    d.dim_v(0.30, 0.0, 1.15, "D_Б = 1,15 м", ext_from_x=0.30, color=DOOR_B, side="left")
    d.dim_v(1.02, 0.90, 1.15, "D_АБ = 0,25 м", ext_from_x=1.40, color=DIM, side="left", label_dy=-30)

    d.callout(0.52, 1.02, 1, color=DIM)

    d.panel([
        ("head", "Вопрос 6: как проверяются несколько дверей?", [
            "На площадку выходят два дверных блока; каждый из них в открытом положении "
            "сужает проход.",
        ]),
        ("head", "Результат при разных допущениях", [
            "**D_A = 0,50 м** — открыта только дверь А.",
            "**D_Б = 1,15 м** — открыта только дверь Б.",
            "**D_АБ = 0,25 м** — обе двери открыты одновременно.",
        ]),
        ("callout", (1, DIM), [
            "Участок, на котором свободный размер минимален: он ограничен кромкой полотна "
            "двери А и полотном двери Б.",
        ]),
        ("head", "Что требуется разъяснить", [
            "а) каждая дверь проверяется отдельно при закрытых остальных;",
            "б) все двери принимаются одновременно в максимально открытом положении;",
            "в) применяется иной порядок — просим указать какой.",
        ]),
    ])
    return d.render("рис-6-neskolko-dverej")


FIGURES = [
    ("рис-1-normiruemye-razmery", "Рисунок 1. Нормируемые размеры лестничной клетки"),
    ("рис-2-polozhenie-polotna", "Рисунок 2. Положение дверного полотна при проверке"),
    ("рис-3-tochka-zamera-na-dveri", "Рисунок 3. Начальная точка замера на дверном блоке"),
    ("рис-4-konechnaya-tochka-zamera", "Рисунок 4. Конечная точка замера на лестничной площадке"),
    ("рис-5-polotno-na-marshe", "Рисунок 5. Полотно, заходящее в габарит лестничного марша"),
    ("рис-6-neskolko-dverej", "Рисунок 6. Две двери, выходящие на одну лестничную площадку"),
]


def main():
    for build in (fig1, fig2, fig3, fig4, fig5, fig6):
        print(build())


if __name__ == "__main__":
    main()
