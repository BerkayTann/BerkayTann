"""data.json -> garden.svg / garden-tr.svg: dolu bir "commit ağacı".

Ağaç iskeleti her zaman dolu görünür; aktif yıllar parlak (pembe/cyan/sarı) yapraklı dallar olur,
henüz boş olan dallar koyu mor yapraklarla büyümeyi bekler. Yaprak yoğunluğu o yılın katkı sayısıyla artar.
(MarieLynneBlock'un "commit bahçesi" fikrinden esinlenilmiştir; kod bu repoya özgüdür.)

Kullanım: python generators/render_garden.py data.json cikti_klasoru
"""
import json
import math
import random
import sys
from pathlib import Path

MAG, VIO, CY, YEL = "#e64cbd", "#b10fd2", "#00f0ff", "#fcee0a"
PANEL, LINE, DIM = "#0d1117", "#2b3345", "#8b949e"
HOT = [MAG, "#ff8ae2", CY, MAG, "#ff8ae2", YEL]
COLD = ["#5b21b6", "#7c3aed", "#3b1d7a", "#6d28d9"]
MONO = "'JetBrains Mono','SFMono-Regular',Consolas,'Courier New',monospace"
TITLE = {"en": "// commit garden", "tr": "// commit bahçesi"}


def render(data, lang="en"):
    years = sorted((int(y), c) for y, c in data["years"].items() if c > 0)
    mx = max((c for _, c in years), default=1)
    W, H = 860, 420
    gx, gy = W / 2, H - 56
    rnd = random.Random(42)
    paths, leaves, labels = [], [], []

    def limb(x, y, ang, length, width, depth, hot, w):
        ex, ey = x + length * math.sin(ang), y - length * math.cos(ang)
        cx, cy = (x + ex) / 2 + rnd.uniform(-1, 1) * length * 0.12, (y + ey) / 2
        paths.append((x, y, cx, cy, ex, ey, width))
        if depth <= 1:
            n = int((8 if depth == 1 else 22) * (1 + 0.9 * w if hot else 1))
            for _ in range(n):
                t = rnd.random() if depth == 1 else 1.0
                px = (1 - t) ** 2 * x + 2 * (1 - t) * t * cx + t * t * ex + rnd.gauss(0, 10)
                py = (1 - t) ** 2 * y + 2 * (1 - t) * t * cy + t * t * ey + rnd.gauss(0, 10)
                leaves.append((px, py, rnd.choice(HOT if hot else COLD), rnd.uniform(1.7, 3.6), rnd.random() < 0.1))
        if depth == 0:
            return ex, ey
        kids = 3 if rnd.random() < 0.3 else 2
        tip = (ex, ey)
        for k in range(kids):
            da = (k - (kids - 1) / 2) * rnd.uniform(0.55, 0.85) + rnd.uniform(-0.12, 0.12)
            tip = limb(ex, ey, ang + da, length * rnd.uniform(0.68, 0.8), width * 0.68, depth - 1, hot, w)
        return tip

    trunk_h = 150
    nl = max(7, len(years) + 3)
    slots = []
    for i in range(nl):
        side = -1 if i % 2 == 0 else 1
        frac = 0.30 + 0.62 * i / max(nl - 1, 1)
        slots.append((i, side, frac))
    assign = {i: years[i] for i in range(min(len(years), nl))}
    # gövde
    paths.append((gx, gy, gx - 5, gy - trunk_h * 0.5, gx, gy - trunk_h, 14))
    for i, side, frac in slots:
        yr = assign.get(i)
        hot = yr is not None
        w = math.sqrt(yr[1] / mx) if hot else 0.0
        sx, sy = gx - 5 * math.sin(frac * math.pi), gy - trunk_h * frac
        ang = side * rnd.uniform(0.85, 1.25)
        tip = limb(sx, sy, ang, (78 + 20 * (1 - frac) + (22 * w if hot else 0)) * 0.78, 6.0, 3, hot, w)
        if hot:
            labels.append((tip[0], tip[1], yr, side))
    for side in (-1, 1):  # taç
        limb(gx, gy - trunk_h, side * 0.32, 56, 6.5, 3, bool(years), 0.5)

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{TITLE[lang]}">',
         f'<defs><linearGradient id="t" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#4c1d95"/><stop offset="1" stop-color="{VIO}"/></linearGradient>'
         f'<linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{MAG}"/><stop offset="1" stop-color="{VIO}"/></linearGradient></defs>',
         f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="{PANEL}" stroke="url(#g)" stroke-opacity=".6" stroke-width="1.3"/>',
         f'<text x="24" y="34" font-family="{MONO}" font-size="15" font-weight="700" fill="{CY}">{TITLE[lang]}</text>']
    for x, y, cx, cy, ex, ey, wd in paths:
        o.append(f'<path d="M{x:.1f},{y:.1f} Q{cx:.1f},{cy:.1f} {ex:.1f},{ey:.1f}" fill="none" stroke="url(#t)" stroke-width="{wd:.1f}" stroke-linecap="round"/>')
    for x, y, c, r, tw in leaves:
        anim = f'<animate attributeName="opacity" values="1;.2;1" dur="{2 + (x % 3):.1f}s" repeatCount="indefinite"/>' if tw else ""
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{c}">{anim}</circle>')
    for x, y, (yr, cnt), side in labels:
        o.append(f'<text x="{x + side * 10:.1f}" y="{y - 14:.1f}" text-anchor="{"start" if side > 0 else "end"}" font-family="{MONO}" font-size="12" font-weight="700" fill="#e6edf3" stroke="#0d1117" stroke-width="4" paint-order="stroke">{yr} · {cnt}</text>')
    # zemin, çimen, çiçekler
    o.append(f'<path d="M30,{gy} L{W - 30},{gy}" stroke="{LINE}" stroke-width="3" stroke-linecap="round" stroke-dasharray="0 8"/>')
    for _ in range(46):
        x = rnd.uniform(40, W - 40)
        h = rnd.uniform(5, 13)
        o.append(f'<path d="M{x:.1f},{gy} l{rnd.uniform(-3, 3):.1f},-{h:.1f}" stroke="#14b8a6" stroke-opacity=".7" stroke-width="1.6" stroke-linecap="round"/>')
    for _ in range(14):
        x = rnd.uniform(60, W - 60)
        o.append(f'<circle cx="{x:.1f}" cy="{gy - rnd.uniform(6, 14):.1f}" r="{rnd.uniform(1.8, 2.8):.1f}" fill="{rnd.choice([MAG, YEL, CY])}"/>')
    # düşen yapraklar
    for k in range(9):
        x0 = rnd.uniform(gx - 280, gx + 280)
        y0 = rnd.uniform(70, 170)
        d = rnd.uniform(7, 13)
        o.append(f'<circle cx="{x0:.0f}" cy="{y0:.0f}" r="2.4" fill="{rnd.choice(HOT)}" opacity="0">'
                 f'<animate attributeName="cy" from="{y0:.0f}" to="{gy - 4}" dur="{d:.1f}s" begin="-{rnd.uniform(0, d):.1f}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="cx" values="{x0:.0f};{x0 + 24:.0f};{x0 - 8:.0f};{x0 + 18:.0f}" dur="{d:.1f}s" begin="-{rnd.uniform(0, d):.1f}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;.9;.9;0" dur="{d:.1f}s" repeatCount="indefinite"/></circle>')
    o.append("</svg>")
    return "".join(o)


if __name__ == "__main__":
    data = json.loads(Path(sys.argv[1]).read_text())
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    (out / "garden.svg").write_text(render(data, "en"), encoding="utf-8")
    (out / "garden-tr.svg").write_text(render(data, "tr"), encoding="utf-8")
    print("yazıldı: garden.svg, garden-tr.svg")
