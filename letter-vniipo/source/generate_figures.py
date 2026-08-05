#!/usr/bin/env python3
"""Generate measurement schematic figures for VNIIPO letter on SP 1.13130.2020 p.4.4.2."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "figures"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1400, 980
BG = (250, 251, 253)
INK = (28, 35, 48)
MUTED = (90, 100, 118)
ACCENT = (180, 45, 45)
OK = (20, 110, 70)
DOOR = (70, 105, 160)
FILL = (230, 236, 245)
LANDING = (238, 232, 220)
STAIR = (220, 225, 232)
RAIL = (55, 60, 70)
DIM = (200, 70, 40)
ARROW = (200, 70, 40)


def font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


F_TITLE = font(28, True)
F_SUB = font(20, True)
F_BODY = font(18)
F_SMALL = font(15)
F_TINY = font(13)


def new_canvas(title, subtitle=""):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 72), fill=(32, 48, 72))
    d.text((28, 18), title, fill=(255, 255, 255), font=F_TITLE)
    if subtitle:
        d.text((28, 90), subtitle, fill=MUTED, font=F_BODY)
    d.rectangle((0, H - 46, W, H), fill=(32, 48, 72))
    d.text((28, H - 34), "Приложение к запросу во ФГБУ ВНИИПО МЧС России · п. 4.4.2 СП 1.13130.2020", fill=(210, 218, 230), font=F_TINY)
    return img, d


def draw_arrow_h(d, x1, x2, y, label, color=DIM, above=True):
    if x1 > x2:
        x1, x2 = x2, x1
    d.line((x1, y, x2, y), fill=color, width=3)
    ah = 10
    d.polygon([(x1, y), (x1 + ah, y - ah // 2), (x1 + ah, y + ah // 2)], fill=color)
    d.polygon([(x2, y), (x2 - ah, y - ah // 2), (x2 - ah, y + ah // 2)], fill=color)
    bbox = d.textbbox((0, 0), label, font=F_SUB)
    tw = bbox[2] - bbox[0]
    ty = y - 28 if above else y + 10
    d.text(((x1 + x2) / 2 - tw / 2, ty), label, fill=color, font=F_SUB)


def draw_arrow_v(d, x, y1, y2, label, color=DIM, right=True):
    if y1 > y2:
        y1, y2 = y2, y1
    d.line((x, y1, x, y2), fill=color, width=3)
    ah = 10
    d.polygon([(x, y1), (x - ah // 2, y1 + ah), (x + ah // 2, y1 + ah)], fill=color)
    d.polygon([(x, y2), (x - ah // 2, y2 - ah), (x + ah // 2, y2 - ah)], fill=color)
    bbox = d.textbbox((0, 0), label, font=F_SUB)
    tw = bbox[2] - bbox[0]
    tx = x + 12 if right else x - tw - 12
    d.text((tx, (y1 + y2) / 2 - 10), label, fill=color, font=F_SUB)


def draw_wall(d, box, width=10):
    d.rectangle(box, fill=(70, 78, 92), outline=INK, width=1)


def draw_rail(d, points):
    d.line(points, fill=RAIL, width=5)


def draw_door_leaf(d, hinge, tip, thickness=18, color=DOOR):
    # approximate door as thick line / rotated rectangle
    import math
    x1, y1 = hinge
    x2, y2 = tip
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy) or 1
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    pts = [
        (x1 + px * thickness / 2, y1 + py * thickness / 2),
        (x2 + px * thickness / 2, y2 + py * thickness / 2),
        (x2 - px * thickness / 2, y2 - py * thickness / 2),
        (x1 - px * thickness / 2, y1 - py * thickness / 2),
    ]
    d.polygon(pts, fill=color, outline=INK)
    # handle nub near tip, outer side
    hx = x2 - ux * 40 + px * (thickness / 2 + 8)
    hy = y2 - uy * 40 + py * (thickness / 2 + 8)
    d.ellipse((hx - 7, hy - 7, hx + 7, hy + 7), fill=ACCENT, outline=INK)
    return (hx, hy)


def label_box(d, xy, lines, fill=(255, 255, 255)):
    x, y = xy
    pad = 10
    widths = [d.textbbox((0, 0), t, font=F_SMALL)[2] for t in lines]
    tw = max(widths) if widths else 0
    th = len(lines) * 22 + pad * 2
    d.rectangle((x, y, x + tw + pad * 2, y + th), fill=fill, outline=MUTED, width=1)
    for i, t in enumerate(lines):
        d.text((x + pad, y + pad + i * 22), t, fill=INK, font=F_SMALL)


def fig1():
    img, d = new_canvas(
        "Рисунок 1. Дверь открыта на 90° — замер ширины площадки",
        "План этажной лестничной площадки (вид сверху). Вариант А: замер от полотна/фурнитуры до ограждения марша.",
    )
    # walls / stairwell outline
    d.rectangle((120, 160, 1280, 860), outline=INK, width=3)
    # landing
    d.rectangle((160, 220, 1240, 560), fill=LANDING, outline=INK, width=2)
    d.text((170, 230), "Лестничная площадка", fill=MUTED, font=F_BODY)
    # upper flight (going up, to the left conceptually) - two flights U
    # left flight going down
    for i in range(8):
        y0 = 560 + i * 28
        d.rectangle((160, y0, 520, y0 + 26), fill=STAIR, outline=MUTED, width=1)
    d.text((250, 780), "Марш вниз", fill=MUTED, font=F_BODY)
    # right flight going up
    for i in range(8):
        y0 = 560 + i * 28
        d.rectangle((880, y0, 1240, y0 + 26), fill=STAIR, outline=MUTED, width=1)
    d.text((970, 780), "Марш вверх", fill=MUTED, font=F_BODY)
    # railings
    draw_rail(d, [(520, 560), (520, 840)])
    draw_rail(d, [(880, 560), (880, 840)])
    draw_rail(d, [(520, 560), (880, 560)])
    d.text((640, 575), "Ограждение", fill=RAIL, font=F_SMALL)

    # doorway on top wall of landing
    draw_wall(d, (560, 160, 840, 220))
    d.rectangle((620, 170, 780, 218), fill=(200, 210, 225), outline=INK, width=2)
    d.text((640, 182), "Дверной проём", fill=INK, font=F_TINY)

    # door open 90° into landing (hinge left)
    handle = draw_door_leaf(d, (620, 220), (620, 520), thickness=16)
    d.text((640, 360), "Дверь 90°", fill=DOOR, font=F_SUB)

    # Dimension B1: from door/handle to opposite edge of landing (bottom of landing / rail)
    # Clear width across landing past door - from handle to right wall? 
    # Better: remaining clear path along landing between door leaf and opposite boundary
    # Measure from outer face of door (x=628) to right landing edge or to opposite?
    # Classic question: from door to railing of inner void / opposite wall
    # Show two candidate measurements labeled as questions

    # Measurement line from handle to inner railing (horizontal across remaining landing)
    x_door = 628
    x_rail = 880
    y_m = 400
    d.line((x_door, 220, x_door, 520), fill=ACCENT, width=1)
    draw_arrow_h(d, x_door + 8, x_rail, y_m, "B₁ = ?", color=DIM, above=True)
    d.line((x_rail, 360, x_rail, 560), fill=DIM, width=2)

    # Depth of landing without door
    draw_arrow_v(d, 200, 220, 560, "L ≥ bмарша", color=OK, right=True)

    label_box(d, (900, 250), [
        "Точки замера (вопрос):",
        "• от плоскости полотна или",
        "  от наиболее выступающей",
        "  части (ручка, доводчик)?",
        "• B₁ — до ограждения марша",
        "  или до противоположной стены?",
    ], fill=(255, 248, 240))

    label_box(d, (160, 880), [
        "Условные обозначения: красная стрелка — контролируемый «свободный» размер при открытой двери.",
    ], fill=(245, 247, 250))

    img.save(OUT / "рис-01-dver-90-ploshchadka.png", optimize=True)
    return OUT / "рис-01-dver-90-ploshchadka.png"


def fig2():
    img, d = new_canvas(
        "Рисунок 2. Дверь в максимально открытом положении («до упора»)",
        "План. Дверь прижата к стене / ограничителю; полотно и фурнитура могут выступать в световой габарит площадки.",
    )
    d.rectangle((120, 160, 1280, 860), outline=INK, width=3)
    d.rectangle((160, 220, 1240, 560), fill=LANDING, outline=INK, width=2)
    d.text((170, 230), "Лестничная площадка", fill=MUTED, font=F_BODY)

    for i in range(8):
        y0 = 560 + i * 28
        d.rectangle((160, y0, 520, y0 + 26), fill=STAIR, outline=MUTED, width=1)
        d.rectangle((880, y0, 1240, y0 + 26), fill=STAIR, outline=MUTED, width=1)
    draw_rail(d, [(520, 560), (520, 840)])
    draw_rail(d, [(880, 560), (880, 840)])
    draw_rail(d, [(520, 560), (880, 560)])

    # doorway
    d.rectangle((180, 170, 340, 218), fill=(200, 210, 225), outline=INK, width=2)
    d.text((195, 182), "Проём", fill=INK, font=F_TINY)

    # door fully open against left wall - nearly parallel to wall, slight protrusion
    handle = draw_door_leaf(d, (180, 220), (180, 500), thickness=16)
    # wall stop
    d.rectangle((160, 220, 175, 500), fill=(90, 95, 105))
    d.text((195, 320), "Дверь «до упора»", fill=DOOR, font=F_SUB)
    d.text((195, 350), "(макс. угол по конструкции)", fill=MUTED, font=F_SMALL)

    # remaining clear width of landing depth from protruding handle to opposite edge
    # Here door is along left wall - protrusion into landing is thickness + handle
    x_face = handle[0] + 8
    draw_arrow_h(d, x_face, 1240, 390, "B₂ = ? (световая ширина площадки)", color=DIM, above=True)

    # also show flight clear width unaffected
    draw_arrow_h(d, 880, 1240, 700, "bмарша", color=OK, above=True)

    label_box(d, (520, 250), [
        "Вопросы к ВНИИПО:",
        "1) Какой угол считать «максимально",
        "   открытым» — 90°, 180°, угол до",
        "   ограничителя/стены по паспорту двери?",
        "2) B₂ измеряется до стены, до края",
        "   перекрытия или до ограждения?",
        "3) Учитывается ли выступ ручки,",
        "   доводчика, ограничителя открывания?",
    ], fill=(255, 248, 240))

    img.save(OUT / "рис-02-dver-max-otkrytie.png", optimize=True)
    return OUT / "рис-02-dver-max-otkrytie.png"


def fig3():
    img, d = new_canvas(
        "Рисунок 3. Дверь заходит на лестничный марш — замер ширины марша",
        "Ситуация: полотно в макс. открытом положении пересекает световой габарит марша.",
    )
    d.rectangle((200, 150, 1200, 900), outline=INK, width=3)
    # landing top
    d.rectangle((240, 190, 1160, 380), fill=LANDING, outline=INK, width=2)
    d.text((250, 200), "Площадка", fill=MUTED, font=F_BODY)
    # single flight below
    for i in range(12):
        y0 = 380 + i * 36
        d.rectangle((420, y0, 980, y0 + 34), fill=STAIR, outline=MUTED, width=1)
    d.text((650, 820), "Лестничный марш", fill=MUTED, font=F_BODY)
    draw_rail(d, [(420, 380), (420, 860)])
    draw_rail(d, [(980, 380), (980, 860)])

    # door from side wall of landing opening and overlapping flight
    d.rectangle((240, 220, 280, 360), fill=(200, 210, 225), outline=INK, width=2)
    # door swung down over left part of flight
    handle = draw_door_leaf(d, (280, 300), (700, 300), thickness=18)
    d.text((480, 250), "Дверь (макс. открытие)", fill=DOOR, font=F_SUB)

    # clear width of flight past door tip/handle
    x_clear_start = handle[0] + 10
    draw_arrow_h(d, x_clear_start, 950, 520, "bсв = ? (ширина марша «в свету»)", color=DIM, above=True)
    draw_arrow_h(d, 430, 960, 740, "bпроектная марша", color=OK, above=False)

    label_box(d, (1000, 200), [
        "Контрольный размер:",
        "минимальное расстояние",
        "по горизонтали между",
        "выступающей частью двери",
        "и ограждением/стеной",
        "на участке марша.",
        "",
        "Подтвердить методику?",
    ], fill=(255, 248, 240))

    img.save(OUT / "рис-03-dver-na-marsh.png", optimize=True)
    return OUT / "рис-03-dver-na-marsh.png"


def fig4():
    img, d = new_canvas(
        "Рисунок 4. Точки контроля на П-образной лестничной клетке",
        "Сводная схема: ширина/глубина площадки (по ГОСТ 9818) и «свободные» размеры при открытой двери.",
    )
    # outer walls
    d.rectangle((180, 150, 1220, 900), outline=INK, width=3)
    # landing
    d.rectangle((220, 190, 1180, 470), fill=LANDING, outline=INK, width=2)
    # flights
    for i in range(10):
        y0 = 470 + i * 36
        d.rectangle((220, y0, 520, y0 + 34), fill=STAIR, outline=MUTED, width=1)
        d.rectangle((880, y0, 1180, y0 + 34), fill=STAIR, outline=MUTED, width=1)
    # void
    d.rectangle((520, 470, 880, 880), fill=(245, 247, 250), outline=MUTED, width=1)
    d.text((600, 650), "Лестничный", fill=MUTED, font=F_BODY)
    d.text((620, 680), "проём", fill=MUTED, font=F_BODY)
    draw_rail(d, [(520, 470), (520, 860)])
    draw_rail(d, [(880, 470), (880, 860)])
    draw_rail(d, [(520, 470), (880, 470)])

    # doors: apartment door on top, elevator door on side
    d.rectangle((700, 155, 900, 188), fill=(200, 210, 225), outline=INK, width=2)
    d.text((740, 160), "Дверь кв./пом.", fill=INK, font=F_TINY)
    handle1 = draw_door_leaf(d, (700, 190), (700, 450), thickness=14)

    d.rectangle((1185, 250, 1215, 400), fill=(200, 210, 225), outline=INK, width=2)
    handle2 = draw_door_leaf(d, (1180, 250), (950, 250), thickness=14)
    d.text((980, 210), "Дверь лифта / пом.", fill=DOOR, font=F_TINY)

    # dimensions
    draw_arrow_v(d, 250, 190, 470, "A — глубина площадки", color=OK, right=True)
    draw_arrow_h(d, handle1[0] + 10, 1180, 360, "B — свободная ширина площадки при откр. двери", color=DIM, above=True)
    draw_arrow_h(d, 890, 1170, 620, "C — ширина марша", color=OK, above=True)
    draw_arrow_v(d, 1050, 264, 460, "D — до полотна/ручки", color=DIM, right=False)

    label_box(d, (540, 500), [
        "Просим подтвердить:",
        "A — параметр «ширина площадки»",
        "    по п. 4.4.2 / «глубина» по ГОСТ 9818?",
        "B, D — как измерять при открытой двери?",
        "C — контролируется ли при заходе",
        "    полотна на марш?",
        "Точки: полотно / ручка / доводчик /",
        "ограждение / стена / край перекрытия.",
    ], fill=(255, 248, 240))

    img.save(OUT / "рис-04-tochki-kontrolya.png", optimize=True)
    return OUT / "рис-04-tochki-kontrolya.png"


def fig5():
    img, d = new_canvas(
        "Рисунок 5. Элементы двери, учитываемые при замере «в свету»",
        "Фрагмент плана. Какая точка принимается как граница дверного препятствия?",
    )
    # wall and door leaf detail
    d.rectangle((120, 200, 200, 820), fill=(70, 78, 92))
    d.rectangle((200, 260, 720, 340), fill=DOOR, outline=INK, width=2)
    d.text((360, 285), "Дверное полотно", fill=(255, 255, 255), font=F_SUB)

    # handle
    d.ellipse((700, 280, 760, 340), fill=ACCENT, outline=INK, width=2)
    d.text((700, 350), "Ручка", fill=ACCENT, font=F_BODY)

    # closer body
    d.rectangle((220, 220, 340, 255), fill=(90, 90, 90), outline=INK)
    d.text((220, 185), "Доводчик", fill=INK, font=F_BODY)

    # stop / limiter
    d.ellipse((680, 360, 710, 390), fill=(120, 80, 40), outline=INK)
    d.text((720, 365), "Ограничитель / упор", fill=INK, font=F_BODY)

    # railing opposite
    d.rectangle((1100, 200, 1130, 820), fill=RAIL)
    d.text((1145, 480), "Ограждение", fill=RAIL, font=F_BODY)
    d.text((1145, 510), "(или стена)", fill=MUTED, font=F_SMALL)

    # candidate measurement lines
    y1, y2, y3 = 300, 420, 540
    draw_arrow_h(d, 720, 1100, y1, "Вариант 1: от плоскости полотна", color=(40, 100, 180), above=True)
    draw_arrow_h(d, 760, 1100, y2, "Вариант 2: от наружной точки ручки", color=DIM, above=True)
    draw_arrow_h(d, 340, 1100, y3, "Вариант 3: с учётом доводчика/упора (если выступает больше)", color=(140, 90, 20), above=True)

    label_box(d, (200, 620), [
        "В письме ВНИИПО № 4772-13-4-4 от 10.08.2018 указано, что необходимо учитывать",
        "максимально возможное открывание полотна, в т.ч. устройства для самозакрывания",
        "и другие выступающие части дверного полотна.",
        "",
        "Просим подтвердить применимость этого подхода к п. 4.4.2 СП 1.13130.2020",
        "и указать точку начала замера на двери (полотно / ручка / наиболее выступающая часть).",
    ], fill=(255, 248, 240))

    img.save(OUT / "рис-05-elementy-dveri.png", optimize=True)
    return OUT / "рис-05-elementy-dveri.png"


def fig6():
    img, d = new_canvas(
        "Рисунок 6. Минимальный просвет при промежуточном угле открывания",
        "Вопрос: контролируется ли только «макс. открытие» или также положение с минимальным просветом?",
    )
    d.rectangle((150, 170, 1250, 860), outline=INK, width=3)
    d.rectangle((200, 220, 1200, 520), fill=LANDING, outline=INK, width=2)
    for i in range(8):
        y0 = 520 + i * 32
        d.rectangle((200, y0, 500, y0 + 30), fill=STAIR, outline=MUTED, width=1)
        d.rectangle((900, y0, 1200, y0 + 30), fill=STAIR, outline=MUTED, width=1)
    draw_rail(d, [(500, 520), (500, 820)])
    draw_rail(d, [(900, 520), (900, 820)])
    draw_rail(d, [(500, 520), (900, 520)])

    # door at ~45-60 degrees - worst case for clear width to railing corner
    import math
    hinge = (620, 220)
    angle = math.radians(55)
    length = 300
    tip = (hinge[0] + length * math.sin(angle), hinge[1] + length * math.cos(angle))
    handle = draw_door_leaf(d, hinge, tip, thickness=16)
    d.rectangle((560, 175, 760, 218), fill=(200, 210, 225), outline=INK, width=2)
    d.text((590, 185), "Проём", fill=INK, font=F_TINY)

    # min clear to railing corner
    rail_pt = (500, 520)
    d.line((handle[0], handle[1], rail_pt[0], rail_pt[1]), fill=DIM, width=3)
    d.ellipse((rail_pt[0] - 6, rail_pt[1] - 6, rail_pt[0] + 6, rail_pt[1] + 6), fill=DIM)
    d.ellipse((handle[0] - 6, handle[1] - 6, handle[0] + 6, handle[1] + 6), fill=DIM)
    d.text((560, 420), "Bmin = ?", fill=DIM, font=F_SUB)

    # ghost max open
    tip2 = (hinge[0], hinge[1] + 300)
    d.line((hinge[0], hinge[1], tip2[0], tip2[1]), fill=(160, 180, 210), width=3)
    d.text((635, 480), "макс. открытие", fill=(100, 130, 170), font=F_SMALL)

    label_box(d, (720, 560), [
        "В письме ВНИИПО (2018) указано, что",
        "«открытое положение» = максимально",
        "возможное открытое положение.",
        "",
        "Просим разъяснить для п. 4.4.2 СП 1.13130.2020:",
        "нужно ли дополнительно проверять угол,",
        "при котором просвет до ограждения/края",
        "площадки минимален (Bmin), если он меньше,",
        "чем при полном открытии?",
    ], fill=(255, 248, 240))

    img.save(OUT / "рис-06-minimalnyj-prosvet.png", optimize=True)
    return OUT / "рис-06-minimalnyj-prosvet.png"


def main():
    paths = [fig1(), fig2(), fig3(), fig4(), fig5(), fig6()]
    for p in paths:
        print(p)


if __name__ == "__main__":
    main()
