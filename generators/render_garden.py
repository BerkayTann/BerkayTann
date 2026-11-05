"""data.json -> garden.svg / garden-tr.svg: gerçek katkı verisine bağlı "commit ağacı".

Kurallar (veriyle uyum için):
- Her aktif yıl, gövdeden çıkan bir dal olur. Aktif yıl yoksa yalnızca fidan çizilir.
- Bir yaprak = bir katkı. Toplam MAX_LEAVES'i aşarsa ölçek büyür (1 yaprak = N katkı) ve legend'de yazar.
- Dolgu / süs yaprağı YOKTUR; ağaç ne kadar doluysa veri o kadardır.
- Ağacın boyutu da toplam katkıyla birlikte büyür.
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
MONO = "'JetBrains Mono','SFMono-Regular',Consolas,'Courier New',monospace"
MAX_LEAVES = 700
TXT = {
    "en": {"title": "// commit garden", "total": "contributions", "unit": "1 leaf = {n} contribution{s}", "empty": "no contributions yet"},
    "tr": {"title": "// commit bahçesi", "total": "katkı", "unit": "1 yaprak = {n} katkı", "empty": "henüz katkı yok"},
}


def render(data, lang="en"):
    tx = TXT[lang]
    years = sorted((int(y), c) for y, c in data["years"].items() if c > 0)
    total = sum(c for _, c in years)
    per_leaf = max(1, math.ceil(total / MAX_LEAVES))
    mx = max((c for _, c in years), default=1)
    W, H = 860, 420
    gx, gy = W / 2, H - 56
    rnd = random.Random(42)
    size = min(1.0, 0.55 + math.sqrt(total) / 40)  # az veri -> küçük ağaç
    trunk_h = 150 * size
    paths, pts_by_limb, labels = [], {}, []

    def limb(x, y, ang, length, width, depth, key):
        ex, ey = x + length * math.sin(ang), y - length * math.cos(ang)
        cx, cy = (x + ex) / 2 + rnd.uniform(-1, 1) * length * 0.12, (y + ey) / 2
        paths.append((x, y, cx, cy, ex, ey, width))
        for t in (0.45, 0.7, 1.0):  # yaprakların tutunabileceği noktalar (uçlar daha çok)
            px = (1 - t) ** 2 * x + 2 * (1 - t) * t * cx + t * t * ex
            py = (1 - t) ** 2 * y + 2 * (1 - t) * t * cy + t * t * ey
            pts_by_limb.setdefault(key, []).extend([(px, py)] * (3 if t == 1.0 else 1) * (2 if depth <= 1 else 1))
        if depth == 0:
            return ex, ey
        tip = (ex, ey)
        for k in range(3 if rnd.random() < 0.3 else 2):
            n = 3 if False else 2
            da = (k - 0.5) * rnd.uniform(0.6, 0.9) + rnd.uniform(-0.12, 0.12)
            tip = limb(ex, ey, ang + da, length * rnd.uniform(0.68, 0.8), width * 0.68, depth - 1, key)
        return tip

    # gövde
    paths.append((gx, gy, gx - 5, gy - trunk_h * 0.5, gx, gy - trunk_h, 12 * size + 3))
    if not years:
        limb(gx, gy - trunk_h, 0.0, 30, 4, 1, "sapling")
    else:
        n = len(years)
        for i, (yr, cnt) in enumerate(years):
            side = -1 if i % 2 == 0 else 1
            frac = 0.35 + 0.6 * i / max(n - 1, 1) if n > 1 else 0.7
            sx, sy = gx - 4 * math.sin(frac * math.pi), gy - trunk_h * frac
            length = (60 + 42 * math.sqrt(cnt / mx)) * size
            tip = limb(sx, sy, side * rnd.uniform(0.85, 1.2), length, 5.0 * size + 1.5, 3, yr)
            labels.append((tip[0], tip[1], yr, cnt, side))

    leaves = []
    for yr, cnt in years:
        pool = pts_by_limb.get(yr, [])
        for _ in range(max(1, round(cnt / per_leaf))):
            px, py = rnd.choice(pool)
            leaves.append((px + rnd.gauss(0, 6), py + rnd.gauss(0, 6), rnd.choice(HOT), rnd.uniform(2.4, 3.8), rnd.random() < 0.1))

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{tx["title"]}">',
         f'<defs><linearGradient id="t" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#4c1d95"/><stop offset="1" stop-color="{VIO}"/></linearGradient>'
         f'<linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{MAG}"/><stop offset="1" stop-color="{VIO}"/></linearGradient></defs>',
         f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="{PANEL}" stroke="url(#g)" stroke-opacity=".6" stroke-width="1.3"/>',
         f'<text x="24" y="34" font-family="{MONO}" font-size="15" font-weight="700" fill="{CY}">{tx["title"]} · {total} {tx["total"]}</text>',
         f'<text x="{W - 24}" y="34" text-anchor="end" font-family="{MONO}" font-size="12" fill="{DIM}">{tx["unit"].format(n=per_leaf, s="" if per_leaf == 1 else "s")}</text>']
    for x, y, cx, cy, ex, ey, wd in paths:
        o.append(f'<path d="M{x:.1f},{y:.1f} Q{cx:.1f},{cy:.1f} {ex:.1f},{ey:.1f}" fill="none" stroke="url(#t)" stroke-width="{wd:.1f}" stroke-linecap="round"/>')
    for x, y, c, r, tw in leaves:
        anim = f'<animate attributeName="opacity" values="1;.25;1" dur="{2 + (x % 3):.1f}s" repeatCount="indefinite"/>' if tw else ""
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{c}">{anim}</circle>')
    for x, y, yr, cnt, side in labels:
        o.append(f'<text x="{x + side * 10:.1f}" y="{y - 12:.1f}" text-anchor="{"start" if side > 0 else "end"}" font-family="{MONO}" font-size="12" font-weight="700" fill="#e6edf3" stroke="#0d1117" stroke-width="4" paint-order="stroke">{yr} · {cnt}</text>')
    if not years:
        o.append(f'<text x="{W / 2}" y="{gy - trunk_h - 40}" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{DIM}">{tx["empty"]}</text>')
    # zemin
    o.append(f'<path d="M30,{gy} L{W - 30},{gy}" stroke="{LINE}" stroke-width="3" stroke-linecap="round" stroke-dasharray="0 8"/>')
    for _ in range(46):
        x, h = rnd.uniform(40, W - 40), rnd.uniform(5, 12)
        o.append(f'<path d="M{x:.1f},{gy} l{rnd.uniform(-3, 3):.1f},-{h:.1f}" stroke="#14b8a6" stroke-opacity=".6" stroke-width="1.6" stroke-linecap="round"/>')
    o.append("</svg>")
    return "".join(o)


if __name__ == "__main__":
    data = json.loads(Path(sys.argv[1]).read_text())
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    (out / "garden.svg").write_text(render(data, "en"), encoding="utf-8")
    (out / "garden-tr.svg").write_text(render(data, "tr"), encoding="utf-8")
    print("yazıldı: garden.svg, garden-tr.svg")
