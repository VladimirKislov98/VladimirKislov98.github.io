#!/usr/bin/env python3
"""Схема марша с разными дверями и способами определения ширины."""

import math
from pathlib import Path

import cairosvg

OUT = Path(__file__).resolve().parents[1] / "figures"
ART = Path("/opt/cursor/artifacts")
OUT.mkdir(parents=True, exist_ok=True)
ART.mkdir(parents=True, exist_ok=True)

CANVAS_W, CANVAS_H = 1900, 1240
TITLE_H = 96
FONT = "DejaVu Sans"

INK = "#1b2330"
WALL = "#8b939f"
WALL_L = "#414956"
SLAB = "#f5f2ea"
STEP = "#e9eef4"
STEP_L = "#aab5c3"
RAIL = "#2f3742"
DOOR_A = "#1f66b0"
DOOR_B = "#7a49ab"
DOOR_C = "#c2681c"
DIM1 = "#c0392b"
DIM2 = "#1a7a4c"
DIM3 = "#8a5a12"
DIM4 = "#1f66b0"
DIM5 = "#7a49ab"
MUTED = "#5c6675"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class D:
    def __init__(self, title, subtitle, ppm=210.0, origin=(280, 200)):
        self.parts = []
        self.ppm = ppm
        self.ox, self.oy = origin
        self.title = title
        self.subtitle = subtitle

    def X(self, x): return self.ox + x * self.ppm
    def Y(self, y): return self.oy + y * self.ppm
    def S(self, v): return v * self.ppm

    def raw(self, s): self.parts.append(s)

    def rect(self, x, y, w, h, fill="none", stroke=INK, sw=1.4, dash=None, opacity=1):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(
            f'<rect x="{self.X(x):.1f}" y="{self.Y(y):.1f}" width="{self.S(w):.1f}" '
            f'height="{self.S(h):.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
            f'opacity="{opacity}"{d}/>'
        )

    def line(self, x1, y1, x2, y2, stroke=INK, sw=1.4, dash=None, cap="butt"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(
            f'<line x1="{self.X(x1):.1f}" y1="{self.Y(y1):.1f}" x2="{self.X(x2):.1f}" '
            f'y2="{self.Y(y2):.1f}" stroke="{stroke}" stroke-width="{sw}" '
            f'stroke-linecap="{cap}"{d}/>'
        )

    def poly(self, pts, fill=INK, stroke="none", sw=1.0, opacity=1):
        s = " ".join(f"{self.X(a):.1f},{self.Y(b):.1f}" for a, b in pts)
        self.raw(f'<polygon points="{s}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{opacity}"/>')

    def arc(self, cx, cy, r, d1, d2, stroke=MUTED, sw=1.1, dash="7 6"):
        while d2 - d1 > 180: d2 -= 360
        while d2 - d1 < -180: d2 += 360
        a1, a2 = math.radians(d1), math.radians(d2)
        x1, y1 = self.X(cx + r * math.cos(a1)), self.Y(cy + r * math.sin(a1))
        x2, y2 = self.X(cx + r * math.cos(a2)), self.Y(cy + r * math.sin(a2))
        large = 1 if abs(d2 - d1) > 180 else 0
        sweep = 1 if d2 > d1 else 0
        self.raw(
            f'<path d="M {x1:.1f} {y1:.1f} A {self.S(r):.1f} {self.S(r):.1f} 0 {large} {sweep} '
            f'{x2:.1f} {y2:.1f}" fill="none" stroke="{stroke}" stroke-width="{sw}" stroke-dasharray="{dash}"/>'
        )

    def text_px(self, px, py, s, size=16, anchor="start", fill=INK, weight="normal"):
        self.raw(
            f'<text x="{px:.1f}" y="{py:.1f}" font-family="{FONT}" font-size="{size}" '
            f'text-anchor="{anchor}" fill="{fill}" font-weight="{weight}">{esc(s)}</text>'
        )

    def text(self, x, y, s, dx=0, dy=0, **kw):
        self.text_px(self.X(x) + dx, self.Y(y) + dy, s, **kw)

    def boxed(self, px, py, s, size=17, fill=INK, weight="bold", anchor="middle"):
        w = len(s) * size * 0.58 + 12
        h = size * 1.45
        x0 = {"middle": px - w / 2, "start": px - 6, "end": px - w + 6}[anchor]
        self.raw(
            f'<rect x="{x0:.1f}" y="{py - h * 0.76:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'rx="3" fill="#ffffff" opacity="0.95"/>'
        )
        self.text_px(px, py, s, size=size, fill=fill, weight=weight, anchor=anchor)

    def _arr(self, px, py, ang, color, size=9):
        pts = [
            (px, py),
            (px + size * math.cos(ang + 0.34), py + size * math.sin(ang + 0.34)),
            (px + size * math.cos(ang - 0.34), py + size * math.sin(ang - 0.34)),
        ]
        self.raw(f'<polygon points="{" ".join(f"{a:.1f},{b:.1f}" for a,b in pts)}" fill="{color}"/>')

    def dim_h(self, y, x1, x2, label, color=DIM1, above=True, size=17, dx=0, dy=0):
        py = self.Y(y)
        px1, px2 = self.X(min(x1, x2)), self.X(max(x1, x2))
        self.raw(f'<line x1="{px1:.1f}" y1="{py:.1f}" x2="{px2:.1f}" y2="{py:.1f}" stroke="{color}" stroke-width="1.7"/>')
        short = px2 - px1 < 40
        self._arr(px1, py, math.pi if short else 0, color)
        self._arr(px2, py, 0 if short else math.pi, color)
        for px in (px1, px2):
            self.raw(f'<line x1="{px:.1f}" y1="{py-7:.1f}" x2="{px:.1f}" y2="{py+7:.1f}" stroke="{color}" stroke-width="1.7"/>')
        ty = py - 10 if above else py + size + 4
        self.boxed( (px1 + px2) / 2 + dx, ty + dy, label, size=size, fill=color)

    def dim_v(self, x, y1, y2, label, color=DIM1, side="right", size=17, dx=0, dy=0):
        px = self.X(x)
        py1, py2 = self.Y(min(y1, y2)), self.Y(max(y1, y2))
        self.raw(f'<line x1="{px:.1f}" y1="{py1:.1f}" x2="{px:.1f}" y2="{py2:.1f}" stroke="{color}" stroke-width="1.7"/>')
        short = py2 - py1 < 40
        self._arr(px, py1, -math.pi/2 if short else math.pi/2, color)
        self._arr(px, py2, math.pi/2 if short else -math.pi/2, color)
        for py in (py1, py2):
            self.raw(f'<line x1="{px-7:.1f}" y1="{py:.1f}" x2="{px+7:.1f}" y2="{py:.1f}" stroke="{color}" stroke-width="1.7"/>')
        mid = (py1 + py2) / 2
        anchor = "start" if side == "right" else "end"
        off = 12 if side == "right" else -12
        self.boxed(px + off + dx, mid + size * 0.35 + dy, label, size=size, fill=color, anchor=anchor)

    def callout(self, x, y, n, color=DIM1, r=14):
        px, py = self.X(x), self.Y(y)
        self.raw(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r}" fill="{color}" stroke="#fff" stroke-width="2"/>')
        self.text_px(px, py + 5.5, str(n), size=16, anchor="middle", fill="#fff", weight="bold")

    def walls(self, x0, y0, x1, y1, t=0.18):
        self.rect(x0 - t, y0 - t, (x1 - x0) + 2 * t, t, fill=WALL, stroke=WALL_L, sw=1.2)
        self.rect(x0 - t, y1, (x1 - x0) + 2 * t, t, fill=WALL, stroke=WALL_L, sw=1.2)
        self.rect(x0 - t, y0, t, y1 - y0, fill=WALL, stroke=WALL_L, sw=1.2)
        self.rect(x1, y0, t, y1 - y0, fill=WALL, stroke=WALL_L, sw=1.2)

    def opening(self, x, y, w, vertical=False, t=0.18):
        if vertical:
            self.rect(x - t, y, t, w, fill="#fff", stroke=WALL_L, sw=1.2)
        else:
            self.rect(x, y - t, w, t, fill="#fff", stroke=WALL_L, sw=1.2)

    def door(self, hinge, closed, opened, leaf=0.90, th=0.05, color=DOOR_A,
             normal=1, handle=True, swing=True, arc_r=None):
        hx, hy = hinge
        a = math.radians(opened)
        ux, uy = math.cos(a), math.sin(a)
        nx, ny = -uy * normal, ux * normal
        tx, ty = hx + leaf * ux, hy + leaf * uy
        if swing:
            self.arc(hx, hy, arc_r or leaf * 0.55, closed, opened, stroke=color)
        self.poly([
            (hx, hy), (tx, ty),
            (tx + nx * th, ty + ny * th),
            (hx + nx * th, hy + ny * th),
        ], fill=color, stroke=INK, sw=1.2)
        tip_h = None
        if handle:
            bx = hx + (leaf - 0.10) * ux + nx * th
            by = hy + (leaf - 0.10) * uy + ny * th
            tip_h = (bx + nx * 0.06, by + ny * 0.06)
            self.line(bx, by, tip_h[0], tip_h[1], stroke=DIM1, sw=3.4, cap="round")
        return (tx, ty), tip_h

    def rail(self, x1, y1, x2, y2):
        self.line(x1, y1, x2, y2, stroke=RAIL, sw=5.2, cap="round")

    def render(self, name):
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
            f'viewBox="0 0 {CANVAS_W} {CANVAS_H}">'
            f'<rect width="{CANVAS_W}" height="{CANVAS_H}" fill="#fff"/>'
            f'<rect width="{CANVAS_W}" height="{TITLE_H}" fill="#22344f"/>'
            f'<text x="32" y="40" font-family="{FONT}" font-size="25" fill="#fff" font-weight="bold">'
            f'{esc(self.title)}</text>'
            f'<text x="32" y="72" font-family="{FONT}" font-size="17" fill="#c3d1e4">'
            f'{esc(self.subtitle)}</text>'
            f'{"".join(self.parts)}'
            f'<line x1="32" y1="{CANVAS_H - 42}" x2="{CANVAS_W - 32}" y2="{CANVAS_H - 42}" '
            f'stroke="#d6dee9" stroke-width="1.5"/>'
            f'<text x="32" y="{CANVAS_H - 16}" font-family="{FONT}" font-size="14" fill="{MUTED}">'
            f'{esc("Варианты определения ширины пути эвакуации при дверях, выходящих на лестничную клетку / марш. Размеры в метрах.")}</text>'
            f'</svg>'
        )
        png = OUT / f"{name}.png"
        cairosvg.svg2png(bytestring=svg.encode(), write_to=str(png),
                         output_width=CANVAS_W, output_height=CANVAS_H)
        (ART / f"{name}.png").write_bytes(png.read_bytes())
        return png


def draw_panel(d, x, y, w, h, items):
    d.raw(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#f7f9fc" '
        f'stroke="#d6dee9" stroke-width="1.5"/>'
    )
    cy = y + 36
    for item in items:
        kind = item[0]
        if kind == "h":
            d.text_px(x + 22, cy, item[1], size=19, fill=INK, weight="bold")
            cy += 30
        elif kind == "n":
            num, color, lines = item[1], item[2], item[3]
            d.raw(f'<circle cx="{x + 36}" cy="{cy - 5}" r="13.5" fill="{color}"/>')
            d.text_px(x + 36, cy + 1, str(num), size=15, anchor="middle", fill="#fff", weight="bold")
            tx = x + 62
            for i, line in enumerate(lines):
                weight = "bold" if i == 0 else "normal"
                fill = INK if i == 0 else MUTED
                d.text_px(tx, cy + i * 22, line, size=16, fill=fill, weight=weight)
            cy += 22 * len(lines) + 16
        elif kind == "t":
            for line in item[1]:
                d.text_px(x + 22, cy, line, size=16, fill=MUTED)
                cy += 22
            cy += 10
        elif kind == "gap":
            cy += item[1]


def figure_main():
    """Главная схема: марш + 3 двери + 5 способов замера."""
    d = D(
        "Рисунок. Марш лестницы с дверями — варианты определения ширины",
        "План. Три дверных блока и пять способов назначения контрольного размера при открытом полотне.",
        ppm=195.0,
        origin=(250, 190),
    )

    # Геометрия
    B = 1.35          # ширина марша
    LAND = 1.50       # глубина площадки
    FL = 3.40         # длина показанной части марша
    WALL_R = B + 0.15 # правая внутренняя граница с поручнем

    # Контур клетки: площадка сверху + марш вниз
    d.walls(0, 0, WALL_R, LAND + FL, t=0.18)
    d.rect(0, 0, WALL_R, LAND, fill=SLAB, stroke=INK, sw=1.6)  # площадка
    d.rect(0, LAND, WALL_R, FL, fill=STEP, stroke=INK, sw=1.6)  # марш

    # Ступени
    rise = 0.30
    n = int(FL / rise)
    for i in range(1, n + 1):
        yy = LAND + i * rise
        if yy < LAND + FL - 0.02:
            d.line(0, yy, WALL_R, yy, stroke=STEP_L, sw=1.0)

    # Линия первой ступени (верхняя кромка марша = начало первой ступени)
    d.line(0, LAND, WALL_R, LAND, stroke=DIM2, sw=2.4, dash="10 5")
    d.text(WALL_R + 0.08, LAND - 0.05, "линия первой ступени", size=14, fill=DIM2)

    # Поручень / ограждение справа
    d.rail(WALL_R, 0.05, WALL_R, LAND + FL - 0.05)
    # Центр поручня — точка на середине по высоте (в плане — линия)
    rail_x = WALL_R
    rail_center_y = LAND + 1.10  # условная точка «центр поручня» на участке марша
    d.raw(
        f'<circle cx="{d.X(rail_x):.1f}" cy="{d.Y(rail_center_y):.1f}" r="7" '
        f'fill="#fff" stroke="{RAIL}" stroke-width="2.5"/>'
    )
    d.text(WALL_R + 0.10, rail_center_y + 0.05, "центр поручня", size=14, fill=RAIL)

    # Стрелка направления движения по маршу
    d.line(B / 2, LAND + 0.35, B / 2, LAND + FL - 0.45, stroke=MUTED, sw=1.6)
    d._arr(d.X(B / 2), d.Y(LAND + FL - 0.45), math.pi / 2, MUTED, size=11)
    d.text(B / 2, LAND + FL - 0.25, "направление движения", size=14, fill=MUTED, anchor="middle")

    # ---- ДВЕРЬ A: на верхней стене площадки, открыта на 90° ----
    d.opening(0.25, 0.0, 0.90)
    tip_a, h_a = d.door((1.15, 0.0), 180, 90, leaf=0.90, color=DOOR_A, normal=1, arc_r=0.50)
    d.text(1.28, 0.72, "дверь А", size=16, fill=DOOR_A, weight="bold")
    d.text(1.28, 0.72, "(на площадку)", size=13, fill=DOOR_A, dy=18)

    # ---- ДВЕРЬ B: в левой стене площадки, открыта вдоль площадки ----
    d.opening(0.0, 0.20, 0.90, vertical=True)
    tip_b, h_b = d.door((0.0, 1.10), 270, 0, leaf=0.90, color=DOOR_B, normal=-1, arc_r=0.45)
    d.text(0.10, 0.35, "дверь Б", size=16, fill=DOOR_B, weight="bold")
    d.text(0.10, 0.35, "(сбоку площадки)", size=13, fill=DOOR_B, dy=18)

    # ---- ДВЕРЬ C: в левой стене на уровне марша, заходит на марш ----
    d.opening(0.0, LAND + 0.15, 0.90, vertical=True)
    tip_c, h_c = d.door((0.0, LAND + 1.05), 270, 0, leaf=0.90, color=DOOR_C, normal=-1, arc_r=0.45)
    d.text(0.10, LAND + 0.40, "дверь В", size=16, fill=DOOR_C, weight="bold")
    d.text(0.10, LAND + 0.40, "(на марш)", size=13, fill=DOOR_C, dy=18)

    # Подпись зон
    d.text(WALL_R - 0.08, 0.25, "площадка", size=14, fill=MUTED, anchor="end")
    d.text(B / 2 + 0.15, LAND + 2.35, "лестничный марш", size=14, fill=MUTED, anchor="middle")

    # ========== РАЗМЕРЫ / СПОСОБЫ ==========
    # ① От плоскости двери А до поручня (поперёк площадки)
    x_door_a = 1.15
    d.dim_h(0.28, x_door_a, WALL_R, "① 0,35 м", color=DIM1, above=True)
    d.callout(x_door_a - 0.14, 0.28, 1, color=DIM1)

    # ② От первой ступени до кромки двери А (вдоль марша)
    y_door_a_tip = 0.90
    d.dim_v(1.70, y_door_a_tip, LAND, "② 0,60 м", color=DIM2, side="right", dx=2)
    d.callout(1.70, (y_door_a_tip + LAND) / 2, 2, color=DIM2)

    # ②′ От двери Б до первой ступени
    d.dim_v(0.48, 1.15, LAND, "②′ 0,35 м", color=DIM2, side="left", dx=-2)

    # ③ От центра поручня до кромки двери В
    x_door_c = 0.90
    d.dim_h(rail_center_y, x_door_c, rail_x, "③ 0,60 м", color=DIM3, above=True)
    d.callout((x_door_c + rail_x) / 2, rail_center_y - 0.20, 3, color=DIM3)

    # ④ Проектная ширина марша без двери
    d.dim_h(LAND + FL - 0.50, 0.0, WALL_R, "④ 1,50 м — без двери", color=DIM4, above=False)
    d.callout(0.45, LAND + FL - 0.50, 4, color=DIM4)

    # ⑤ От ручки двери В до поручня
    x_handle_c = 0.965
    d.dim_h(LAND + 1.40, x_handle_c, rail_x, "⑤ 0,54 м — до ручки", color=DIM5, above=False)
    d.callout(x_handle_c - 0.12, LAND + 1.40, 5, color=DIM5)

    # Легенда-панель справа
    draw_panel(d, 1280, TITLE_H + 28, 580, 1040, [
        ("h", "Три двери на схеме"),
        ("t", [
            "А — из помещения на этажную площадку;",
            "Б — сбоку площадки, вдоль неё;",
            "В — из помещения прямо на марш.",
        ]),
        ("h", "Способы определения ширины"),
        ("n", 1, DIM1, [
            "От плоскости полотна двери А",
            "до поручня / противоположной стены",
            "(поперёк пути эвакуации по площадке).",
        ]),
        ("n", 2, DIM2, [
            "От первой ступени до открытой двери",
            "(вдоль направления движения по маршу).",
            "Для двери Б — размер ②′ до края площадки.",
        ]),
        ("n", 3, DIM3, [
            "От центра поручня до кромки двери В",
            "(поперёк марша, в створе полотна).",
        ]),
        ("n", 4, DIM4, [
            "Проектная ширина марша без учёта двери:",
            "стена — поручень.",
        ]),
        ("n", 5, DIM5, [
            "От наиболее выступающей части двери",
            "(ручка, доводчик) до поручня.",
        ]),
        ("h", "Суть вопроса"),
        ("t", [
            "Один и тот же марш и одни и те же двери",
            "дают разные контрольные размеры в",
            "зависимости от выбранных точек замера.",
            "Требуется указать, какой из способов",
            "применяется при проверке п. 4.4.2.",
        ]),
    ])

    return d.render("рис-7-marsh-sposoby-zamera")


def figure_detail():
    """Укрупнённый фрагмент: только марш + дверь на марш, все поперечные варианты."""
    d = D(
        "Рисунок. Способы замера ширины марша при двери, заходящей в его габарит",
        "Укрупнённый план участка марша. Все размеры отсчитываются в одном створе полотна.",
        ppm=320.0,
        origin=(320, 220),
    )

    B = 1.35
    top = 0.0
    mid = 0.70   # площадка
    bot = 3.20

    d.walls(0, top, B, bot, t=0.16)
    d.rect(0, top, B, mid, fill=SLAB, stroke=INK, sw=1.6)
    d.rect(0, mid, B, bot - mid, fill=STEP, stroke=INK, sw=1.6)

    rise = 0.28
    n = int((bot - mid) / rise)
    for i in range(1, n + 1):
        yy = mid + i * rise
        if yy < bot - 0.02:
            d.line(0, yy, B, yy, stroke=STEP_L, sw=1.0)

    # первая ступень
    d.line(-0.25, mid, B + 0.55, mid, stroke=DIM2, sw=2.0, dash="10 5")
    d.text(B + 0.60, mid + 0.05, "первая ступень", size=15, fill=DIM2)

    # поручень
    d.rail(B, top + 0.05, B, bot - 0.05)
    cy = mid + 0.95
    d.raw(
        f'<circle cx="{d.X(B):.1f}" cy="{d.Y(cy):.1f}" r="8" fill="#fff" '
        f'stroke="{RAIL}" stroke-width="2.5"/>'
    )
    d.text(B + 0.10, cy + 0.04, "центр поручня", size=15, fill=RAIL)

    # дверь
    d.opening(0.0, mid - 0.35, 0.90, vertical=True)
    tip, hpt = d.door((0.0, mid + 0.55), 270, 0, leaf=0.90, color=DOOR_C, normal=-1, arc_r=0.42)
    d.text(0.08, mid - 0.15, "дверь в максимально", size=15, fill=DOOR_C, weight="bold")
    d.text(0.08, mid - 0.15, "открытом положении", size=15, fill=DOOR_C, weight="bold", dy=20)

    x_leaf = 0.90
    x_handle = 0.965

    # сечения
    d.line(-0.35, cy, B + 0.85, cy, stroke=DIM3, sw=1.2, dash="12 5 3 5")
    d.text(B + 0.90, cy + 0.04, "створ 1—1", size=15, fill=DIM3, weight="bold")

    # ① стена — поручень (проектная)
    d.dim_h(bot - 0.45, 0, B, "① 1,35 м — стена → поручень", color=DIM4, above=False)

    # ② полотно — поручень
    d.dim_h(cy - 0.22, x_leaf, B, "② 0,45 м — полотно → поручень", color=DIM1, above=True)

    # ③ ручка — поручень
    d.dim_h(cy + 0.28, x_handle, B, "③ 0,385 м — ручка → поручень", color=DIM5, above=False)

    # ④ полотно — центр поручня (то же по x, но подчеркнуто)
    # already ② to rail line; show callout at center
    d.callout(B, cy, 4, color=DIM3)
    d.text(B + 0.12, cy + 0.22, "④ до центра поручня", size=15, fill=DIM3)

    # ⑤ от первой ступени до полотна (вдоль)
    d.dim_v(-0.28, mid, mid + 0.55, "⑤ 0,55 м", color=DIM2, side="left")
    d.text(-0.28, mid + 0.28, "от 1-й ступени", size=14, fill=DIM2, anchor="end", dx=-18, dy=-12)
    d.text(-0.28, mid + 0.28, "до полотна", size=14, fill=DIM2, anchor="end", dx=-18, dy=8)

    d.callout(x_leaf / 2, cy - 0.22, 2, color=DIM1)
    d.callout(x_handle - 0.08, cy + 0.28, 3, color=DIM5)
    d.callout(0.40, bot - 0.45, 1, color=DIM4)
    d.callout(-0.28, mid + 0.28, 5, color=DIM2)

    draw_panel(d, 1280, TITLE_H + 28, 580, 980, [
        ("h", "Пять способов в одном створе"),
        ("n", 1, DIM4, [
            "Стена → поручень — 1,35 м",
            "Проектная ширина марша без двери.",
        ]),
        ("n", 2, DIM1, [
            "Плоскость полотна → поручень — 0,45 м",
            "Остающаяся ширина «в свету».",
        ]),
        ("n", 3, DIM5, [
            "Ручка / фурнитура → поручень — 0,385 м",
            "С учётом выступающих частей двери.",
        ]),
        ("n", 4, DIM3, [
            "До центра поручня",
            "Та же поперечная линия, но конечная",
            "точка — ось поручня, а не его грань.",
        ]),
        ("n", 5, DIM2, [
            "От первой ступени до полотна — 0,55 м",
            "Размер вдоль марша (глубина захода",
            "двери в габарит марша).",
        ]),
        ("h", "Зачем это нужно"),
        ("t", [
            "Способы ①–④ отвечают на вопрос «какая",
            "ширина марша остаётся».",
            "Способ ⑤ — на вопрос «на каком участке",
            "марша дверь его уменьшает».",
            "",
            "Для проверки абзаца третьего п. 4.4.2",
            "необходимо указать, какой из них",
            "является контрольным.",
        ]),
    ])

    return d.render("рис-8-marsh-detal-zamera")


if __name__ == "__main__":
    print(figure_main())
    print(figure_detail())
