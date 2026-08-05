#!/usr/bin/env python3
"""Чистые чертежи: марш с дверями и способы замера ширины."""

from __future__ import annotations

import math
from pathlib import Path

import cairosvg

OUT = Path(__file__).resolve().parents[1] / "figures"
ART = Path("/opt/cursor/artifacts")
OUT.mkdir(parents=True, exist_ok=True)
ART.mkdir(parents=True, exist_ok=True)

FONT = "DejaVu Sans"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Plan:
    """Чертёж в метрах. x вправо, y вниз."""

    def __init__(self, w: int, h: int, title: str, subtitle: str, ppm: float, ox: float, oy: float):
        self.W, self.H = w, h
        self.title, self.subtitle = title, subtitle
        self.ppm, self.ox, self.oy = ppm, ox, oy
        self.g: list[str] = []

    def X(self, x: float) -> float:
        return self.ox + x * self.ppm

    def Y(self, y: float) -> float:
        return self.oy + y * self.ppm

    def S(self, v: float) -> float:
        return v * self.ppm

    def add(self, s: str) -> None:
        self.g.append(s)

    # --- primitives ---
    def rect(self, x, y, w, h, fill="none", stroke="#1b2330", sw=1.5, dash=None, rx=0):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(
            f'<rect x="{self.X(x):.2f}" y="{self.Y(y):.2f}" width="{self.S(w):.2f}" '
            f'height="{self.S(h):.2f}" rx="{rx}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{sw}"{d}/>'
        )

    def line(self, x1, y1, x2, y2, stroke="#1b2330", sw=1.5, dash=None, cap="butt"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(
            f'<line x1="{self.X(x1):.2f}" y1="{self.Y(y1):.2f}" x2="{self.X(x2):.2f}" '
            f'y2="{self.Y(y2):.2f}" stroke="{stroke}" stroke-width="{sw}" '
            f'stroke-linecap="{cap}"{d}/>'
        )

    def poly(self, pts, fill="#1b2330", stroke="none", sw=1.0):
        s = " ".join(f"{self.X(a):.2f},{self.Y(b):.2f}" for a, b in pts)
        self.add(f'<polygon points="{s}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def circle(self, x, y, r_px, fill="#1b2330", stroke="none", sw=1.0):
        self.add(
            f'<circle cx="{self.X(x):.2f}" cy="{self.Y(y):.2f}" r="{r_px}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
        )

    def arc(self, cx, cy, r, d1, d2, stroke="#888", sw=1.1, dash="6 5"):
        while d2 - d1 > 180:
            d2 -= 360
        while d2 - d1 < -180:
            d2 += 360
        a1, a2 = math.radians(d1), math.radians(d2)
        x1, y1 = self.X(cx + r * math.cos(a1)), self.Y(cy + r * math.sin(a1))
        x2, y2 = self.X(cx + r * math.cos(a2)), self.Y(cy + r * math.sin(a2))
        large = 1 if abs(d2 - d1) > 180 else 0
        sweep = 1 if d2 > d1 else 0
        self.add(
            f'<path d="M {x1:.2f} {y1:.2f} A {self.S(r):.2f} {self.S(r):.2f} 0 {large} {sweep} '
            f'{x2:.2f} {y2:.2f}" fill="none" stroke="{stroke}" stroke-width="{sw}" '
            f'stroke-dasharray="{dash}"/>'
        )

    def text(self, x, y, s, size=15, fill="#1b2330", weight="normal", anchor="start", dx=0, dy=0):
        self.add(
            f'<text x="{self.X(x) + dx:.2f}" y="{self.Y(y) + dy:.2f}" font-family="{FONT}" '
            f'font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}">'
            f'{esc(s)}</text>'
        )

    def text_px(self, px, py, s, size=15, fill="#1b2330", weight="normal", anchor="start"):
        self.add(
            f'<text x="{px:.2f}" y="{py:.2f}" font-family="{FONT}" font-size="{size}" '
            f'fill="{fill}" font-weight="{weight}" text-anchor="{anchor}">{esc(s)}</text>'
        )

    def label_bg(self, px, py, s, size=16, fill="#c0392b", anchor="middle", pad=6):
        w = len(s) * size * 0.58 + pad * 2
        h = size * 1.4
        x0 = px - w / 2 if anchor == "middle" else (px - pad if anchor == "start" else px - w + pad)
        self.add(
            f'<rect x="{x0:.2f}" y="{py - h * 0.78:.2f}" width="{w:.2f}" height="{h:.2f}" '
            f'rx="3" fill="#ffffff" stroke="#ffffff" stroke-width="2"/>'
        )
        self.text_px(px, py, s, size=size, fill=fill, weight="bold", anchor=anchor)

    def badge(self, x, y, n, color):
        self.circle(x, y, 13, fill=color, stroke="#ffffff", sw=2.5)
        self.text(x, y, str(n), size=15, fill="#ffffff", weight="bold", anchor="middle", dy=5)

    def arrow_head(self, px, py, ang, color, size=8):
        pts = [
            (px, py),
            (px + size * math.cos(ang + 0.35), py + size * math.sin(ang + 0.35)),
            (px + size * math.cos(ang - 0.35), py + size * math.sin(ang - 0.35)),
        ]
        self.add(f'<polygon points="{" ".join(f"{a:.1f},{b:.1f}" for a,b in pts)}" fill="{color}"/>')

    def dim_h(self, y, x1, x2, label, color="#c0392b", above=True, ext_y=None, size=16):
        """Горизонтальный размер вне контура, с выносными линиями."""
        if ext_y is not None:
            for xx in (x1, x2):
                self.line(xx, ext_y, xx, y, stroke=color, sw=0.8, dash="3 3")
        py = self.Y(y)
        px1, px2 = self.X(min(x1, x2)), self.X(max(x1, x2))
        self.add(f'<line x1="{px1:.2f}" y1="{py:.2f}" x2="{px2:.2f}" y2="{py:.2f}" stroke="{color}" stroke-width="1.6"/>')
        self.arrow_head(px1, py, 0, color)
        self.arrow_head(px2, py, math.pi, color)
        for px in (px1, px2):
            self.add(f'<line x1="{px:.2f}" y1="{py-6:.2f}" x2="{px:.2f}" y2="{py+6:.2f}" stroke="{color}" stroke-width="1.6"/>')
        ty = py - 12 if above else py + size + 4
        self.label_bg((px1 + px2) / 2, ty, label, size=size, fill=color)

    def dim_v(self, x, y1, y2, label, color="#c0392b", side="right", ext_x=None, size=16):
        if ext_x is not None:
            for yy in (y1, y2):
                self.line(ext_x, yy, x, yy, stroke=color, sw=0.8, dash="3 3")
        px = self.X(x)
        py1, py2 = self.Y(min(y1, y2)), self.Y(max(y1, y2))
        self.add(f'<line x1="{px:.2f}" y1="{py1:.2f}" x2="{px:.2f}" y2="{py2:.2f}" stroke="{color}" stroke-width="1.6"/>')
        self.arrow_head(px, py1, math.pi / 2, color)
        self.arrow_head(px, py2, -math.pi / 2, color)
        for py in (py1, py2):
            self.add(f'<line x1="{px-6:.2f}" y1="{py:.2f}" x2="{px+6:.2f}" y2="{py:.2f}" stroke="{color}" stroke-width="1.6"/>')
        mid = (py1 + py2) / 2
        if side == "right":
            self.label_bg(px + 14, mid + size * 0.35, label, size=size, fill=color, anchor="start")
        else:
            self.label_bg(px - 14, mid + size * 0.35, label, size=size, fill=color, anchor="end")

    # --- building parts ---
    def wall_hatch(self, x, y, w, h):
        """Стена с лёгкой штриховкой."""
        self.rect(x, y, w, h, fill="#9aa3b0", stroke="#3d4654", sw=1.3)
        # штрихи
        step = 0.08
        x0, y0, x1, y1 = self.X(x), self.Y(y), self.X(x + w), self.Y(y + h)
        clip = f"wh{len(self.g)}"
        self.add(f'<defs><clipPath id="{clip}"><rect x="{x0:.2f}" y="{y0:.2f}" width="{x1-x0:.2f}" height="{y1-y0:.2f}"/></clipPath></defs>')
        lines = []
        i = 0
        while True:
            xx = x - h + i * step
            if xx > x + w:
                break
            lines.append(
                f'<line x1="{self.X(xx):.2f}" y1="{self.Y(y + h):.2f}" '
                f'x2="{self.X(xx + h):.2f}" y2="{self.Y(y):.2f}" '
                f'stroke="#7d8694" stroke-width="0.7"/>'
            )
            i += 1
        self.add(f'<g clip-path="url(#{clip})">{"".join(lines)}</g>')

    def walls_box(self, x0, y0, x1, y1, t=0.20):
        self.wall_hatch(x0 - t, y0 - t, (x1 - x0) + 2 * t, t)
        self.wall_hatch(x0 - t, y1, (x1 - x0) + 2 * t, t)
        self.wall_hatch(x0 - t, y0, t, y1 - y0)
        self.wall_hatch(x1, y0, t, y1 - y0)

    def opening_h(self, x, y, w, t=0.20):
        self.rect(x, y - t, w, t, fill="#ffffff", stroke="#3d4654", sw=1.2)

    def opening_v(self, x, y, h, t=0.20):
        self.rect(x - t, y, t, h, fill="#ffffff", stroke="#3d4654", sw=1.2)

    def door(self, hinge, closed_deg, open_deg, leaf=0.90, th=0.045, color="#1f66b0",
             normal=1, handle=True, swing=True):
        hx, hy = hinge
        a = math.radians(open_deg)
        ux, uy = math.cos(a), math.sin(a)
        nx, ny = -uy * normal, ux * normal
        tx, ty = hx + leaf * ux, hy + leaf * uy
        if swing:
            self.arc(hx, hy, leaf, closed_deg, open_deg, stroke=color, sw=1.0, dash="5 5")
        # полотно
        self.poly(
            [(hx, hy), (tx, ty), (tx + nx * th, ty + ny * th), (hx + nx * th, hy + ny * th)],
            fill=color, stroke="#14283d", sw=1.1,
        )
        # петля
        self.circle(hx, hy, 3.5, fill="#14283d")
        tip_h = None
        if handle:
            bx = hx + (leaf - 0.12) * ux + nx * th
            by = hy + (leaf - 0.12) * uy + ny * th
            tip_h = (bx + nx * 0.07, by + ny * 0.07)
            self.line(bx, by, tip_h[0], tip_h[1], stroke="#c0392b", sw=3.2, cap="round")
            self.circle(tip_h[0], tip_h[1], 2.8, fill="#c0392b")
        return (tx, ty), tip_h, (hx + nx * th / 2, hy + ny * th / 2)  # tip, handle, mid face

    def stairs(self, x0, y0, x1, y1, rise=0.28):
        self.rect(x0, y0, x1 - x0, y1 - y0, fill="#e8eef5", stroke="#1b2330", sw=1.5)
        n = int(round((y1 - y0) / rise))
        for i in range(1, n):
            yy = y0 + i * rise
            self.line(x0, yy, x1, yy, stroke="#9eabb8", sw=1.0)
            # лёгкая тень подступенка
            self.line(x0, yy, x1, yy, stroke="#c5ced6", sw=2.5)

    def railing(self, x, y0, y1):
        """Ограждение: стойки + поручень."""
        # поручень — толстая линия
        self.line(x, y0, x, y1, stroke="#2c3542", sw=7, cap="round")
        # стойки
        step = 0.45
        y = y0 + 0.15
        while y < y1 - 0.1:
            self.line(x - 0.04, y, x + 0.04, y, stroke="#4a5564", sw=2.0)
            y += step

    def break_zigzag(self, x0, x1, y):
        amp = 0.06
        n = 16
        pts = []
        for i in range(n + 1):
            xx = x0 + (x1 - x0) * i / n
            pts.append((xx, y + (amp if i % 2 else -amp)))
        # белый фон обрыва
        self.rect(x0, y - amp - 0.04, x1 - x0, 2 * amp + 0.08, fill="#ffffff", stroke="none")
        path = " ".join(
            f"{'M' if i == 0 else 'L'} {self.X(px):.2f} {self.Y(py):.2f}" for i, (px, py) in enumerate(pts)
        )
        self.add(f'<path d="{path}" fill="none" stroke="#6b7685" stroke-width="1.8"/>')

    def legend_box(self, px, py, w, h, title, rows):
        self.add(
            f'<rect x="{px}" y="{py}" width="{w}" height="{h}" rx="8" fill="#f6f8fb" '
            f'stroke="#cfd7e3" stroke-width="1.4"/>'
        )
        self.text_px(px + 22, py + 34, title, size=18, fill="#1b2330", weight="bold")
        cy = py + 68
        for item in rows:
            if item[0] == "gap":
                cy += item[1]
                continue
            if item[0] == "h":
                self.text_px(px + 22, cy, item[1], size=16, fill="#1b2330", weight="bold")
                cy += 26
                continue
            if item[0] == "n":
                num, color, lines = item[1], item[2], item[3]
                self.add(f'<circle cx="{px + 34}" cy="{cy - 5}" r="12" fill="{color}"/>')
                self.text_px(px + 34, cy + 0.5, str(num), size=14, fill="#fff", weight="bold", anchor="middle")
                for i, ln in enumerate(lines):
                    self.text_px(px + 56, cy + i * 20, ln, size=14.5,
                                 fill="#1b2330" if i == 0 else "#5a6575",
                                 weight="bold" if i == 0 else "normal")
                cy += 20 * len(lines) + 14
                continue
            if item[0] == "t":
                for ln in item[1]:
                    self.text_px(px + 22, cy, ln, size=14.5, fill="#5a6575")
                    cy += 20
                cy += 8

    def save(self, name: str) -> Path:
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.W}" height="{self.H}" '
            f'viewBox="0 0 {self.W} {self.H}">'
            f'<rect width="{self.W}" height="{self.H}" fill="#ffffff"/>'
            f'<rect width="{self.W}" height="88" fill="#1e2f47"/>'
            f'<text x="28" y="36" font-family="{FONT}" font-size="24" fill="#ffffff" font-weight="bold">'
            f'{esc(self.title)}</text>'
            f'<text x="28" y="64" font-family="{FONT}" font-size="16" fill="#b8c7db">'
            f'{esc(self.subtitle)}</text>'
            f'{"".join(self.g)}'
            f'<text x="28" y="{self.H - 18}" font-family="{FONT}" font-size="13" fill="#6b7685">'
            f'{esc("План. Размеры в метрах. Варианты определения ширины при дверях, выходящих на площадку / марш.")}</text>'
            f'</svg>'
        )
        path = OUT / f"{name}.png"
        cairosvg.svg2png(bytestring=svg.encode(), write_to=str(path),
                         output_width=self.W, output_height=self.H)
        (ART / f"{name}.png").write_bytes(path.read_bytes())
        return path


# =====================================================================
# Рисунок 7 — общий план с тремя дверями
# =====================================================================
def fig7():
    """
    Геометрия (метры):
      внутр. ширина клетки = 2.80
      площадка сверху = 1.60
      марш слева шириной 1.25, пустота/ограждение справа
    """
    p = Plan(
        1760, 1180,
        "Рисунок 7. Марш лестницы с дверями",
        "План этажной площадки и марша. Три двери в максимально открытом положении.",
        ppm=200, ox=250, oy=210,
    )

    W = 2.80          # внутр. ширина
    LAND = 1.60       # глубина площадки
    B = 1.25          # ширина марша
    FL = 2.80         # длина показанного марша
    t = 0.20

    # стены
    p.walls_box(0, 0, W, LAND + FL, t=t)

    # площадка
    p.rect(0, 0, W, LAND, fill="#f3efe6", stroke="#1b2330", sw=1.6)
    p.text(0.10, 0.22, "лестничная площадка", size=14, fill="#6b7685")

    # марш (слева)
    p.stairs(0, LAND, B, LAND + FL, rise=0.28)
    p.text(B / 2, LAND + FL - 0.35, "марш вниз", size=14, fill="#6b7685", anchor="middle")

    # стрелка направления
    p.line(B / 2, LAND + 0.45, B / 2, LAND + FL - 0.55, stroke="#6b7685", sw=1.5)
    p.arrow_head(p.X(B / 2), p.Y(LAND + FL - 0.55), math.pi / 2, "#6b7685", size=10)

    # лестничный проём (пустота справа)
    p.rect(B, LAND, W - B, FL, fill="#fafbfc", stroke="#b0b8c2", sw=1.2)
    p.text((B + W) / 2, LAND + 1.2, "лестничный", size=13, fill="#8a95a3", anchor="middle")
    p.text((B + W) / 2, LAND + 1.2, "проём", size=13, fill="#8a95a3", anchor="middle", dy=18)

    # ограждение
    p.railing(B, LAND + 0.05, LAND + FL - 0.05)
    p.line(B, LAND, W, LAND, stroke="#2c3542", sw=5, cap="round")  # ограждение площадки

    # линия первой ступени
    p.line(-0.55, LAND, B + 0.15, LAND, stroke="#1a7a4c", sw=2.0, dash="8 4")
    p.text(-0.58, LAND, "линия 1-й ступени", size=13, fill="#1a7a4c", anchor="end", dy=-8)

    # обрыв
    p.break_zigzag(-t, W + t, LAND + FL)

    # ---- двери ----
    C_A, C_B, C_C = "#1f66b0", "#7a49ab", "#c2681c"

    # Дверь А — верхняя стена, над маршем, открыта вниз на 90°
    p.opening_h(0.20, 0.0, 0.90, t=t)
    tip_a, h_a, face_a = p.door((1.10, 0.0), 180, 90, leaf=0.90, color=C_A, normal=1)

    # Дверь Б — правая стена площадки, открыта влево
    p.opening_v(W, 0.35, 0.90, t=t)
    tip_b, h_b, face_b = p.door((W, 0.35), 90, 180, leaf=0.90, color=C_B, normal=1)

    # Дверь В — левая стена на марше, открыта вправо на марш
    p.opening_v(0.0, LAND + 0.40, 0.90, t=t)
    tip_c, h_c, face_c = p.door((0.0, LAND + 1.30), 270, 0, leaf=0.90, color=C_C, normal=-1)

    # ---- размеры (все снаружи) ----
    # ширина марша проектная
    p.dim_h(LAND + FL + 0.50, 0, B, "b = 1,25 м", color="#1a7a4c", above=False, ext_y=LAND + FL)
    # глубина площадки
    p.dim_v(-0.85, 0, LAND, "A = 1,60 м", color="#1a7a4c", side="left", ext_x=0)

    # ① от полотна А до противоположной стены (поперёк площадки)
    p.dim_h(-0.55, 1.145, W, "① 1,66 м", color="#c0392b", above=True, ext_y=0.50)
    p.badge((1.145 + W) / 2, -0.78, 1, "#c0392b")

    # ② от 1-й ступени до полотна А
    p.dim_v(1.45, 0.90, LAND, "② 0,70 м", color="#1a7a4c", side="right", ext_x=1.145)
    p.badge(1.68, 1.25, 2, "#1a7a4c")

    # ③ от центра поручня до полотна двери В
    rail_x = B
    door_c_face = 0.90
    y_sect = LAND + 1.30
    p.circle(rail_x, y_sect, 5, fill="#ffffff", stroke="#2c3542", sw=2)
    p.dim_h(y_sect - 0.32, door_c_face, rail_x, "③ 0,35 м", color="#8a5a12", above=True, ext_y=y_sect)
    p.badge(0.45, y_sect - 0.55, 3, "#8a5a12")
    p.text(rail_x + 0.12, y_sect + 0.05, "центр поручня", size=12, fill="#2c3542")

    # ④ от ручки двери В до ограждения
    handle_x = 0.90 + 0.07
    p.dim_h(y_sect + 0.38, handle_x, rail_x, "④ 0,28 м", color="#7a49ab", above=False, ext_y=y_sect)
    p.badge(0.45, y_sect + 0.38, 4, "#7a49ab")

    # ⑤ от полотна двери Б до линии 1-й ступени
    p.dim_v(2.15, 0.395, LAND, "⑤ 1,20 м", color="#1f66b0", side="right", ext_x=W - 0.90)
    p.badge(2.40, 1.0, 5, "#1f66b0")

    # подписи дверей — в свободных местах
    p.text(0.25, -0.28, "дверь А", size=15, fill=C_A, weight="bold")
    p.text(W + 0.08, 0.28, "дверь Б", size=15, fill=C_B, weight="bold")
    p.text(0.12, LAND + 0.55, "дверь В", size=15, fill=C_C, weight="bold")

    # сдвинуть подпись ограждения ниже, чтобы не пересекалась с размерами
    p.text(B + 0.10, LAND + 0.55, "ограждение", size=13, fill="#2c3542")

    # легенда
    p.legend_box(1180, 110, 540, 980, "Что показано на схеме", [
        ("h", "Двери"),
        ("t", [
            "А — из помещения на площадку;",
            "Б — сбоку площадки;",
            "В — из помещения на марш.",
        ]),
        ("gap", 8),
        ("h", "Способы замера"),
        ("n", 1, "#c0392b", [
            "От плоскости полотна двери А",
            "до противоположной стены",
            "(поперёк площадки).",
        ]),
        ("n", 2, "#1a7a4c", [
            "От линии первой ступени",
            "до открытого полотна двери А",
            "(вдоль направления движения).",
        ]),
        ("n", 3, "#8a5a12", [
            "От центра поручня до кромки",
            "полотна двери В (поперёк марша).",
        ]),
        ("n", 4, "#7a49ab", [
            "От дверной ручки до ограждения",
            "(с учётом фурнитуры).",
        ]),
        ("n", 5, "#1f66b0", [
            "От полотна двери Б до линии",
            "первой ступени.",
        ]),
        ("gap", 6),
        ("t", [
            "Зелёные размеры A и b — проектные,",
            "без учёта дверей.",
        ]),
    ])

    return p.save("рис-7-marsh-sposoby-zamera")


# =====================================================================
# Рисунок 8 — укрупнённый марш, только поперечные способы
# =====================================================================
def fig8():
    p = Plan(
        1760, 1120,
        "Рисунок 8. Способы замера ширины марша",
        "Укрупнённый план. Дверь заходит в габарит марша. Все поперечные размеры — в одном створе.",
        ppm=300, ox=300, oy=200,
    )

    B = 1.25
    LAND = 0.85
    FL = 2.60
    t = 0.18
    C = "#c2681c"

    p.walls_box(0, 0, B, LAND + FL, t=t)
    p.rect(0, 0, B, LAND, fill="#f3efe6", stroke="#1b2330", sw=1.6)
    p.text(0.08, 0.22, "площадка", size=14, fill="#6b7685")
    p.stairs(0, LAND, B, LAND + FL, rise=0.28)
    p.railing(B, 0.08, LAND + FL - 0.08)
    p.break_zigzag(-t, B + t, LAND + FL)

    # линия первой ступени
    p.line(-0.55, LAND, B + 0.70, LAND, stroke="#1a7a4c", sw=2.0, dash="8 4")
    p.text(B + 0.75, LAND, "линия 1-й ступени", size=14, fill="#1a7a4c", dy=5)

    # дверь
    p.opening_v(0.0, LAND + 0.20, 0.90, t=t)
    tip, handle, face = p.door((0.0, LAND + 1.10), 270, 0, leaf=0.90, color=C, normal=-1)
    p.text(0.10, LAND + 0.35, "дверь", size=15, fill=C, weight="bold")
    p.text(0.10, LAND + 0.35, "макс. открытие", size=13, fill=C, dy=18)

    # створ замера
    y = LAND + 1.10
    p.line(-0.55, y, B + 0.85, y, stroke="#8a5a12", sw=1.2, dash="10 4 3 4")
    p.text(B + 0.90, y, "створ 1—1", size=14, fill="#8a5a12", weight="bold", dy=5)

    # центр поручня
    p.circle(B, y, 6, fill="#ffffff", stroke="#2c3542", sw=2.2)
    p.text(B + 0.12, y - 0.18, "центр", size=13, fill="#2c3542")
    p.text(B + 0.12, y - 0.18, "поручня", size=13, fill="#2c3542", dy=16)

    leaf_x = 0.90
    handle_x = 0.97

    # размеры — разнесены по высоте, не пересекаются
    # ① проектная ширина внизу
    p.dim_h(LAND + FL + 0.40, 0, B, "① 1,25 м  стена → ограждение", color="#1f66b0",
            above=False, ext_y=LAND + FL)
    p.badge(0.35, LAND + FL + 0.40, 1, "#1f66b0")

    # ② полотно → грань ограждения (чуть выше створа)
    p.dim_h(y - 0.35, leaf_x, B, "② 0,35 м  полотно → ограждение", color="#c0392b",
            above=True, ext_y=y)
    p.badge(leaf_x - 0.18, y - 0.35, 2, "#c0392b")

    # ③ ручка → ограждение (чуть ниже створа)
    p.dim_h(y + 0.35, handle_x, B, "③ 0,28 м  ручка → ограждение", color="#7a49ab",
            above=False, ext_y=y)
    p.badge(handle_x - 0.18, y + 0.35, 3, "#7a49ab")

    # ④ полотно → центр поручня (та же линия, отдельная подпись)
    # show as short note near center
    p.badge(B, y, 4, "#8a5a12")
    p.text(B + 0.12, y + 0.22, "④ конечная точка —", size=13, fill="#8a5a12")
    p.text(B + 0.12, y + 0.22, "центр поручня", size=13, fill="#8a5a12", dy=16)

    # ⑤ вдоль марша: от 1-й ступени до полотна
    p.dim_v(-0.55, LAND, y, "⑤ 1,10 м", color="#1a7a4c", side="left", ext_x=0.45)
    p.badge(-0.55, (LAND + y) / 2, 5, "#1a7a4c")
    p.text(-0.55, LAND + 0.25, "от 1-й ступени", size=12, fill="#1a7a4c", anchor="end", dx=-16)
    p.text(-0.55, LAND + 0.25, "до полотна", size=12, fill="#1a7a4c", anchor="end", dx=-16, dy=16)

    p.legend_box(1180, 110, 540, 920, "Пять способов замера", [
        ("n", 1, "#1f66b0", [
            "Стена → ограждение — 1,25 м",
            "Проектная ширина марша",
            "без учёта двери.",
        ]),
        ("n", 2, "#c0392b", [
            "Плоскость полотна → ограждение",
            "— 0,35 м. Ширина «в свету».",
        ]),
        ("n", 3, "#7a49ab", [
            "Ручка → ограждение — 0,28 м.",
            "С учётом выступающей фурнитуры.",
        ]),
        ("n", 4, "#8a5a12", [
            "Та же поперечная линия, но",
            "конечная точка — центр поручня,",
            "а не грань ограждения.",
        ]),
        ("n", 5, "#1a7a4c", [
            "От линии 1-й ступени до полотна",
            "— 1,10 м. Участок, на котором",
            "дверь заходит в габарит марша.",
        ]),
        ("gap", 10),
        ("t", [
            "Способы ①–④ отвечают на вопрос:",
            "«какая ширина остаётся».",
            "Способ ⑤ — «на каком участке марша».",
        ]),
    ])

    return p.save("рис-8-marsh-detal-zamera")


if __name__ == "__main__":
    print(fig7())
    print(fig8())
