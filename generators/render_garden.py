"""data.json -> garden.svg: her aktif yıl gövdeden çıkan bir dal, katkı sayısı kadar yaprak.

Kullanım: python generators/render_garden.py data.json cikti_klasoru
(MarieLynneBlock'un "commit bahçesi" fikrinden esinlenilmiştir; kod bu repoya özgüdür.)
"""
import json
import math
import random
import sys
from pathlib import Path

MAG, VIO, CY = "#e64cbd", "#b10fd2", "#22d3ee"
PANEL, LINE, DIM = "#0d1117", "#2b3345", "#8b949e"
LEAF = [MAG, VIO, CY, "#ff8ae2", "#7c3aed"]
MONO = "'JetBrains Mono','SFMono-Regular',Consolas,'Courier New',monospace"


def render(data):
    years = sorted((int(y), c) for y, c in data["years"].items() if c > 0)
    w, h = 860, 380
    gx, gy = w / 2, h - 46
    mx = max((c for _, c in years), default=1)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Commit bahçesi">',
         f'<defs><linearGradient id="t" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="{VIO}"/><stop offset="1" stop-color="{MAG}"/></linearGradient>'
         f'<linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{MAG}"/><stop offset="1" stop-color="{VIO}"/></linearGradient></defs>',
         f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="14" fill="{PANEL}" stroke="url(#g)" stroke-opacity=".6" stroke-width="1.3"/>',
         f'<text x="24" y="34" font-family="{MONO}" font-size="15" font-weight="700" fill="{CY}">// commit bahçesi</text>',
         f'<line x1="40" y1="{gy}" x2="{w - 40}" y2="{gy}" stroke="{LINE}" stroke-dasharray="3 5"/>']
    n = max(len(years), 1)
    trunk_h = min(250, 90 + 34 * n)
    o.append(f'<path d="M{gx},{gy} C{gx - 6},{gy - trunk_h * .4} {gx + 8},{gy - trunk_h * .7} {gx},{gy - trunk_h}" fill="none" stroke="url(#t)" stroke-width="7" stroke-linecap="round"/>')
    leaves = []
    for idx, (year, count) in enumerate(years):
        rnd = random.Random(year)
        frac = (idx + 0.5) / n
        by = gy - trunk_h * (0.18 + 0.78 * frac)
        side = -1 if idx % 2 == 0 else 1
        length = 70 + 150 * math.sqrt(count / mx)
        ang = math.radians(28 + rnd.uniform(-6, 6))
        ex, ey = gx + side * length * math.cos(ang), by - length * math.sin(ang) * 0.75
        mxp, myp = gx + side * length * 0.5, by - length * 0.12
        o.append(f'<path d="M{gx},{by:.1f} Q{mxp:.1f},{myp:.1f} {ex:.1f},{ey:.1f}" fill="none" stroke="url(#t)" stroke-width="{2 + 3 * count / mx:.1f}" stroke-linecap="round"/>')
        nleaf = max(6, min(90, count // 8 + 6))
        for _ in range(nleaf):
            t = rnd.random()
            x = (1 - t) ** 2 * gx + 2 * (1 - t) * t * mxp + t * t * ex + rnd.gauss(0, 9)
            y = (1 - t) ** 2 * by + 2 * (1 - t) * t * myp + t * t * ey + rnd.gauss(0, 9)
            leaves.append((x, y, rnd.choice(LEAF), rnd.uniform(1.6, 3.4), rnd.random() < 0.12))
        lx = ex + (10 if side > 0 else -10)
        o.append(f'<text x="{lx:.1f}" y="{ey - 12:.1f}" text-anchor="{"start" if side > 0 else "end"}" font-family="{MONO}" font-size="11" fill="{DIM}">{year} · {count}</text>')
    for x, y, c, r, tw in leaves:
        anim = f'<animate attributeName="opacity" values="1;.25;1" dur="{2 + (x % 3):.1f}s" repeatCount="indefinite"/>' if tw else ""
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{c}">{anim}</circle>')
    o.append("</svg>")
    return "".join(o)


if __name__ == "__main__":
    data = json.loads(Path(sys.argv[1]).read_text())
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    (out / "garden.svg").write_text(render(data), encoding="utf-8")
    print("yazıldı: garden.svg")
