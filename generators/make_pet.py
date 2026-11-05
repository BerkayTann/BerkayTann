"""Orijinal piksel pet: "Bytebug" commit karelerini yiyerek yürür.

Çıktı: assets/pet.svg  (dış servis yok, animasyonlu)
Çalıştırma: python generators/make_pet.py
"""
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(exist_ok=True)

W, H, S = 860, 110, 5
BODY, EAR, EYE, DARK = "#e64cbd", "#00f0ff", "#fcee0a", "#12091f"

SPRITE = [
    "..E......E..",
    "..EE....EE..",
    ".BBBBBBBBBB.",
    "BBBBBBBBBBBB",
    "BBYYBBBBYYBB",
    "BBYKBBBBYKBB",
    "BBBBBBBBBBBB",
    "BBBBMMMMBBBB",
    ".BBBBBBBBBB.",
]
LEGS = [["..LL....LL..", "..LL....LL.."], [".LL......LL.", "..LL....LL.."]]  # yürüme kareleri (ikinci satır sabit)
COL = {"B": BODY, "E": EAR, "Y": EYE, "K": DARK, "M": DARK, "L": "#b0309a"}


def px(rows, x0, y0):
    out = []
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != ".":
                out.append(f'<rect x="{x0 + i * S}" y="{y0 + j * S}" width="{S}" height="{S}" fill="{COL[ch]}"/>')
    return "".join(out)


def main():
    rnd = random.Random(5)
    pal = ["#5c1f6b", "#8a1fa6", "#b10fd2", "#e64cbd", "#00f0ff", "#fcee0a"]
    pet_w = 12 * S
    dur = 16.0
    y_pet = 28
    run_end = 0.92
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Commit yiyen piksel pet">',
         f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="#0d1117" stroke="#2b3345"/>']
    n, x = 38, 24
    gap = (W - 2 * x) / n
    for i in range(n):
        cx = x + i * gap
        col = rnd.choice(pal[:4] if rnd.random() < 0.8 else pal[4:])
        t_eat = (cx - 0) / (W + pet_w) * run_end + 0.02
        kt = f"0;{t_eat:.4f};{t_eat + 0.004:.4f};0.985;1"
        o.append(f'<rect x="{cx:.1f}" y="{y_pet + 36}" width="10" height="10" rx="2" fill="{col}">'
                 f'<animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{kt}" values="1;1;0;0;1"/></rect>')
    # pet
    o.append(f'<g transform="translate(0,{y_pet})"><g>'
             f'<animateTransform attributeName="transform" type="translate" dur="{dur}s" repeatCount="indefinite" keyTimes="0;{run_end};1" values="-{pet_w + 10} 0;{W} 0;{W} 0"/>'
             f'{px(SPRITE, 0, 0)}'
             f'<g><animate attributeName="visibility" dur="0.5s" repeatCount="indefinite" calcMode="discrete" keyTimes="0;.5;1" values="visible;hidden;hidden"/>{px(LEGS[0][:1], 0, 9 * S)}</g>'
             f'<g visibility="hidden"><animate attributeName="visibility" dur="0.5s" repeatCount="indefinite" calcMode="discrete" keyTimes="0;.5;1" values="hidden;visible;visible"/>{px(LEGS[1][:1], 0, 9 * S)}</g>'
             '</g></g>')
    o.append("</svg>")
    (OUT / "pet.svg").write_text("".join(o), encoding="utf-8")
    print("pet.svg", round((OUT / "pet.svg").stat().st_size / 1024, 1), "KB")


if __name__ == "__main__":
    main()
