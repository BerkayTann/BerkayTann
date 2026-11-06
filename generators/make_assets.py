"""Profil README'si için statik/animasyonlu SVG varlıklarını üretir.

Çalıştırma (repo kökünden):  python generators/make_assets.py
Çıktılar assets/ klasörüne yazılır. Dış servis ya da yazı tipi bağımlılığı yoktur;
ikonlar generators/icons.json içindeki yollardan (simple-icons, CC0) çizilir.
"""
import json
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
OUT.mkdir(exist_ok=True)
ICONS = json.loads((Path(__file__).parent / "icons.json").read_text())

MAG, VIO, CY = "#e64cbd", "#b10fd2", "#22d3ee"
PANEL, LINE, TXT, DIM = "#0d1117", "#2b3345", "#c9d1d9", "#8b949e"
MONO = "'JetBrains Mono','SFMono-Regular',Consolas,'Courier New',monospace"


def lerp_hex(a, b, t):
    a, b = a.lstrip("#"), b.lstrip("#")
    ca = [int(a[i:i + 2], 16) for i in (0, 2, 4)]
    cb = [int(b[i:i + 2], 16) for i in (0, 2, 4)]
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(ca, cb))


def luminance(hexs):
    h = hexs.lstrip("#")
    r, g, b = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --------------------------------------------------------------------------- ikonlar
def icon_color(key):
    h = ICONS[key]["hex"]
    return "#" + h if luminance(h) > 0.22 else "#e6edf3"


def tile(key, x, y, size=44, label=None):
    """Koyu zeminli ikon karosu. key ICONS içinde yoksa monogram çizer."""
    s = size
    g = [f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="10" fill="#161b26" stroke="{LINE}"/>']
    if key in ICONS:
        sc = (s - 18) / 24
        g.append(f'<g transform="translate({x + 9},{y + 9}) scale({sc:.3f})"><path d="{ICONS[key]["path"]}" fill="{icon_color(key)}"/></g>')
    elif key == "windows":
        sc = (s - 20) / 24
        g.append(f'<g transform="translate({x + 10},{y + 10}) scale({sc:.3f})"><path d="M2 3.5l9-1.3v9H2zM12 2l10-1.5v10.7H12zM2 12.5h9v9l-9-1.3zM12 12.5h10V23l-10-1.5z" fill="#3aa0ff"/></g>')
    elif key == "azuredevops":
        g.append(f'<text x="{x + s / 2}" y="{y + s / 2 + 4.5}" text-anchor="middle" font-family="{MONO}" font-size="13" font-weight="700" fill="#3aa0ff">ADO</text>')
    elif key == "phaser":
        g.append(f'<text x="{x + s / 2}" y="{y + s / 2 + 5}" text-anchor="middle" font-family="{MONO}" font-size="16" font-weight="700" fill="{MAG}">Ph</text>')
    return "".join(g)


LABELS = {"html5": "HTML5", "css3": "CSS3", "javascript": "JavaScript", "typescript": "TypeScript", "react": "React",
          "nextjs": "Next.js", "tailwind": "Tailwind", "nodejs": "Node.js", "express": "Express", "dotnet": ".NET",
          "postgres": "PostgreSQL", "mongodb": "MongoDB", "docker": "Docker", "kubernetes": "Kubernetes",
          "argocd": "Argo CD", "rancher": "Rancher", "portainer": "Portainer", "nginx": "NGINX", "gitlab": "GitLab",
          "gitea": "Gitea", "git": "Git", "github": "GitHub", "linux": "Linux", "windows": "Windows Server",
          "railway": "Railway", "azuredevops": "Azure DevOps", "phaser": "Phaser"}


# --------------------------------------------------------------------------- skill grid
def make_skills():
    cats = [
        ("Frontend", ["html5", "css3", "javascript", "react", "nextjs", "tailwind"]),
        ("Backend", ["nodejs", "express", "postgres", "mongodb"]),
        ("DevOps", ["docker", "kubernetes", "nginx", "gitlab", "gitea", "portainer", "azuredevops"]),
        ("Others", ["git", "github", "linux", "windows", "railway", "phaser"]),
        ("Studying", ["dotnet", "argocd", "rancher", "typescript"]),
    ]
    W, pad = 860, 14
    cw = (W - 2 * pad) / 3
    ch = 160
    H = pad * 2 + ch * 2
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Skill set">',
         '<defs><linearGradient id="b" x1="0" y1="0" x2="1" y2="1">'
         f'<stop offset="0" stop-color="{MAG}"/><stop offset="1" stop-color="{VIO}"/></linearGradient></defs>',
         f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="{PANEL}" stroke="url(#b)" stroke-opacity=".7" stroke-width="1.5"/>',
         f'<line x1="{pad + cw}" y1="{pad}" x2="{pad + cw}" y2="{H - pad}" stroke="{LINE}"/>',
         f'<line x1="{pad + 2 * cw}" y1="{pad}" x2="{pad + 2 * cw}" y2="{H - pad}" stroke="{LINE}"/>',
         f'<line x1="{pad}" y1="{H / 2}" x2="{W - pad}" y2="{H / 2}" stroke="{LINE}"/>']
    for idx, (name, keys) in enumerate(cats):
        col, row = idx % 3, idx // 3
        x0, y0 = pad + col * cw + 18, pad + row * ch + 14
        o.append(f'<text x="{x0}" y="{y0 + 14}" font-family="{MONO}" font-size="13" font-weight="700" fill="{MAG if name != "Studying" else CY}">{name}</text>')
        for i, k in enumerate(keys):
            tx, ty = x0 + (i % 4) * 52, y0 + 30 + (i // 4) * 52
            o.append(tile(k, tx, ty))
    # 6. hücre: terminal
    x0, y0 = pad + 2 * cw + 18, pad + ch + 14
    lines = [("$ docker compose up -d", TXT), ("[+] Running 5/5", DIM), (" ✔ db        Healthy", CY), (" ✔ api       Started", CY), (" ✔ web       Started", CY)]
    o.append(f'<text x="{x0}" y="{y0 + 14}" font-family="{MONO}" font-size="13" font-weight="700" fill="{VIO}">Now</text>')
    for i, (t, c) in enumerate(lines):
        o.append(f'<text x="{x0}" y="{y0 + 44 + i * 18}" font-family="{MONO}" font-size="12" fill="{c}" xml:space="preserve">{esc(t)}</text>')
    o.append(f'<rect x="{x0}" y="{y0 + 44 + 5 * 18 - 10}" width="8" height="14" fill="{MAG}"><animate attributeName="opacity" values="1;0;1" dur="1.1s" repeatCount="indefinite" calcMode="discrete"/></rect>')
    o.append("</svg>")
    (OUT / "skills.svg").write_text("\n".join(o), encoding="utf-8")


# --------------------------------------------------------------------------- kayan kartlar
def make_marquee():
    keys = ["docker", "kubernetes", "argocd", "rancher", "portainer", "gitlab", "gitea", "nginx", "nextjs", "react",
            "typescript", "nodejs", "postgres", "mongodb", "linux"]
    W, H, ch, gap = 860, 84, 52, 12
    cards, x = [], 0
    for k in keys:
        label = LABELS[k]
        cwid = 14 + 28 + 10 + int(len(label) * 8.2) + 16
        s = [f'<rect x="{x}" y="0" width="{cwid}" height="{ch}" rx="12" fill="#12161f" stroke="{LINE}"/>']
        if k in ICONS:
            s.append(f'<g transform="translate({x + 14},{ch / 2 - 12}) scale(1)"><path d="{ICONS[k]["path"]}" fill="{icon_color(k)}"/></g>')
        s.append(f'<text x="{x + 14 + 28 + 6}" y="{ch / 2 + 4.5}" font-family="{MONO}" font-size="13" fill="{TXT}">{esc(label)}</text>')
        cards.append("".join(s))
        x += cwid + gap
    total = x
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Beceriler">',
         '<defs>'
         '<linearGradient id="f" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
         '<stop offset=".08" stop-color="#fff"/><stop offset=".92" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
         f'<mask id="m"><rect width="{W}" height="{H}" fill="url(#f)"/></mask></defs>',
         f'<rect width="{W}" height="{H}" rx="14" fill="{PANEL}"/>',
         f'<g mask="url(#m)"><g transform="translate(0,{(H - ch) / 2})"><g>',
         f'<animateTransform attributeName="transform" type="translate" from="0 0" to="-{total} 0" dur="{max(30, total // 40)}s" repeatCount="indefinite"/>',
         "".join(cards),
         f'<g transform="translate({total},0)">' + "".join(cards) + "</g>",
         f'<g transform="translate({2 * total},0)">' + "".join(cards) + "</g>",
         "</g></g></g></svg>"]
    (OUT / "marquee.svg").write_text("\n".join(o), encoding="utf-8")


# --------------------------------------------------------------------------- scramble yazı
PHRASES = {
    "en": ["berkay@infra:~$ whoami", "devops × javascript", "10 years of enterprise systems", "from infrastructure to interface"],
    "tr": ["berkay@infra:~$ whoami", "devops × javascript", "10 yıl kurumsal sistem tecrübesi", "altyapıdan arayüze"],
}


def make_scramble(lang="en"):
    phrases = PHRASES[lang]
    pool = list("!<>-_\\/[]{}=+*^?#%&@01")
    rnd = random.Random(7)
    step, hold = 0.045, 2.2
    frames, t = [], 0.0
    for p in phrases:
        n = len(p)
        for k in range(n + 1):
            txt = p[:k] + "".join(rnd.choice(pool) if c != " " else " " for c in p[k:])
            frames.append((t, t + step, txt))
            t += step
        frames[-1] = (frames[-1][0], frames[-1][1] + hold, p)  # tam metin bir süre kalsın
        t += hold
        # silinme: sondan başa karıştır
        for k in range(n, -1, -2):
            txt = p[:k] + "".join(rnd.choice(pool) if c != " " else " " for c in p[k:])
            frames.append((t, t + step, txt))
            t += step
    total = t
    W, H = 760, 44
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="berkay@infra:~$ whoami — DevOps × JavaScript">',
         '<defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#e64cbd"/><stop offset="1" stop-color="#22d3ee"/></linearGradient></defs>']
    for a, b, txt in frames:
        ka, kb = a / total, min(b / total, 1.0)
        kt = [0.0, ka, kb, 1.0] if ka > 0 else [0.0, kb, 1.0]
        vals = "hidden;visible;hidden;hidden" if ka > 0 else "visible;hidden;hidden"
        if ka > 0:
            kts = f"0;{ka:.5f};{kb:.5f};1"
        else:
            kts = f"0;{kb:.5f};1"
        o.append(f'<text x="{W / 2}" y="29" text-anchor="middle" font-family="{MONO}" font-size="20" font-weight="600" fill="url(#g)" visibility="hidden" xml:space="preserve">{esc(txt)}'
                 f'<animate attributeName="visibility" dur="{total:.2f}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{kts}" values="{vals}"/></text>')
    o.append("</svg>")
    (OUT / ("scramble.svg" if lang == "en" else f"scramble-{lang}.svg")).write_text("\n".join(o), encoding="utf-8")


# --------------------------------------------------------------------------- halfdot hayvanlar
SS = 6  # süper-örnekleme


class Canvas:
    def __init__(self, cw, ch):
        self.cw, self.ch = cw, ch
        self.layers = {}

    def _m(self, name):
        if name not in self.layers:
            self.layers[name] = Image.new("L", (self.cw * SS, self.ch * SS), 0)
        return self.layers[name]

    def ell(self, name, cx, cy, rx, ry):
        ImageDraw.Draw(self._m(name)).ellipse([(cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS], fill=255)

    def poly(self, name, pts):
        ImageDraw.Draw(self._m(name)).polygon([(x * SS, y * SS) for x, y in pts], fill=255)

    def rect(self, name, x, y, w, h):
        ImageDraw.Draw(self._m(name)).rounded_rectangle([x * SS, y * SS, (x + w) * SS, (y + h) * SS], radius=0.6 * SS, fill=255)

    def stroke(self, name, pts, w0, w1):
        d = ImageDraw.Draw(self._m(name))
        n = len(pts)
        for i, (x, y) in enumerate(pts):
            r = (w0 + (w1 - w0) * i / max(n - 1, 1)) / 2
            d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], fill=255)

    def clip(self, name, to):
        self.layers[name] = ImageChops.multiply(self._m(name), self._m(to))


def rasterize(cv, colors, order):
    """Katmanları hücre hücre kapsama oranına çevirir -> {(i,j): (r, renk)}."""
    cov = {}
    for name, m in cv.layers.items():
        a = np.asarray(m, dtype=np.float32) / 255.0
        a = a.reshape(cv.ch, SS, cv.cw, SS).mean(axis=(1, 3))
        cov[name] = a
    hole = cov.get("hole", np.zeros((cv.ch, cv.cw), dtype=np.float32))
    dots = {}
    for j in range(cv.ch):
        for i in range(cv.cw):
            best, bc = None, 0.0
            tot = 0.0
            for name in order:  # sonraki katman önceliklidir
                c = cov.get(name)
                if c is None:
                    continue
                v = float(c[j, i])
                tot = max(tot, v)
                if v >= 0.45 or (best is None and v > bc):
                    best, bc = name, v
            tot = max(0.0, tot - float(hole[j, i]) * 1.2)
            if best is None or tot < 0.18:
                continue
            col = colors[best]
            col = col(j / cv.ch) if callable(col) else col
            dots[(i, j)] = (round(min(1.0, tot) ** 0.6, 2), col)
    return dots


def dots_svg(dots, pitch, x_off=0, y_off=0):
    by = {}
    for (i, j), (r, col) in dots.items():
        rad = round(pitch / 2 * 0.9 * r, 1)
        by.setdefault(col, []).append(f'<circle cx="{x_off + i * pitch + pitch / 2:.1f}" cy="{y_off + j * pitch + pitch / 2:.1f}" r="{rad}"/>')
    return "".join(f'<g fill="{c}">{"".join(v)}</g>' for c, v in by.items())


def cycle_frames(frames, dur_each):
    """Her kare için ayrık görünürlük animasyonu; ortak (sabit) noktalar ayrı çizilir."""
    n = len(frames)
    static = {k: v for k, v in frames[0].items() if all(f.get(k) == v for f in frames)}
    pieces = [(static, None)]
    for idx, f in enumerate(frames):
        pieces.append(({k: v for k, v in f.items() if k not in static}, idx))
    return pieces, n


def animal_svg(name, cv_fn, frames_n, colors, order, cw, ch, pitch=7, bob=4, dur_each=0.5, title=""):
    frames = [rasterize(cv_fn(f), colors, order) for f in range(frames_n)]
    pieces, n = cycle_frames(frames, dur_each)
    W, H = cw * pitch, ch * pitch + bob * 2
    total = n * dur_each
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{title}">',
         f'<g transform="translate(0,{bob})"><animateTransform attributeName="transform" type="translate" values="0 {bob};0 0;0 {bob}" dur="4.5s" repeatCount="indefinite" calcMode="spline" keyTimes="0;.5;1" keySplines=".45 0 .55 1;.45 0 .55 1"/>']
    for dots, idx in pieces:
        if not dots:
            continue
        body = dots_svg(dots, pitch)
        if idx is None:
            o.append(f"<g>{body}</g>")
        else:
            if n == 1:
                o.append(f"<g>{body}</g>")
                continue
            a, b = idx / n, (idx + 1) / n
            if idx == 0:
                kts, vals = f"0;{b:.4f};1", "visible;hidden;hidden"
            elif idx == n - 1:
                kts, vals = f"0;{a:.4f};1", "hidden;visible;visible"
            else:
                kts, vals = f"0;{a:.4f};{b:.4f};1", "hidden;visible;hidden;hidden"
            o.append(f'<g visibility="hidden"><animate attributeName="visibility" dur="{total:.2f}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{kts}" values="{vals}"/>{body}</g>')
    o.append("</g></svg>")
    (OUT / f"{name}.svg").write_text("".join(o), encoding="utf-8")


def grad(t):
    return lerp_hex(MAG, VIO, min(max(t, 0), 1))


def whale(frame):
    cv = Canvas(64, 40)
    cv.ell("body", 36, 26, 24, 11)
    cv.ell("body", 51, 27, 10, 9)
    cv.poly("body", [(16, 23), (9, 19), (7, 12), (10, 12), (13, 16), (20, 20)])
    cv.poly("body", [(7, 12), (1, 9), (3, 13.5), (7, 15)])
    cv.poly("body", [(9, 12), (12, 7), (13.5, 12)])
    cv.ell("belly", 42, 33, 21, 6.5)
    cv.clip("belly", "body")
    cv.ell("hole", 54.5, 24.5, 1.1, 1.1)
    boxes = [(14.4, [22, 27, 32, 37]), (10.8, [24.5, 29.5, 34.5]), (7.2, [27, 32])]
    k = 0
    for y, xs in boxes:
        for x in xs:
            cv.rect("box_a" if k % 2 == 0 else "box_b", x, y, 4.2, 3.2)
            k += 1
    lift = [0, 1.2, 2.4][frame % 3]
    for dx, dy in [(56, 14), (55, 10.5), (57, 7)]:
        cv.ell("spout", dx, dy - lift * 0.6, 0.9, 0.9)
    return cv


def octopus(frame):
    cv = Canvas(48, 48)
    cv.ell("body", 24, 16, 14, 13)
    cv.ell("belly", 19, 10, 6, 3.5)
    cv.clip("belly", "body")
    cv.ell("hole", 18.5, 17.5, 2.2, 2.6)
    cv.ell("hole", 29.5, 17.5, 2.2, 2.6)
    ph = frame * math.pi / 2
    for i in range(7):
        x0 = 11 + i * 4.3
        pts = []
        for s in range(0, 41):
            t = s / 40
            x = x0 + (x0 - 24) * 0.85 * t + 2.6 * math.sin(t * 7 + ph + i * 0.9) * (0.35 + t)
            y = 25 + t * 21
            pts.append((x, y))
        cv.stroke("body", pts, 3.6, 1.0)
    return cv


def jellyfish(frame):
    cv = Canvas(40, 56)
    pts = [(20 + 16 * math.cos(a), 20 + 15 * math.sin(a)) for a in np.linspace(math.pi, 2 * math.pi, 40)]
    pts += [(36 - i * 32 / 24, 20 + 1.3 * math.sin(i * 1.3)) for i in range(25)]
    cv.poly("body", pts)
    inner = [(20 + 10 * math.cos(a), 19 + 9 * math.sin(a)) for a in np.linspace(math.pi, 2 * math.pi, 30)]
    cv.poly("belly", inner)
    cv.clip("belly", "body")
    ph = frame * math.pi / 2
    for i in range(6):
        x0 = 7 + i * 5.2
        pts = [(x0 + 2.3 * math.sin(s / 40 * 8 + ph + i), 21 + s / 40 * 30) for s in range(41)]
        cv.stroke("body", pts, 1.5, 0.7)
    for i, x0 in enumerate((15, 25)):
        pts = [(x0 + 3 * math.sin(s / 40 * 5 + ph + i * 2), 21 + s / 40 * 22) for s in range(41)]
        cv.stroke("arm", pts, 2.6, 1.0)
    return cv


def make_animals():
    cols = {"body": grad, "belly": "#e39ad6", "box_a": CY, "box_b": "#ff8ae2", "spout": "#9be7f7", "arm": "#ff8ae2"}
    order = ["body", "belly", "arm", "box_a", "box_b", "spout"]
    animal_svg("whale", whale, 3, cols, order, 64, 40, title="Docker balinası")
    animal_svg("octopus", octopus, 4, cols, order, 48, 48, dur_each=0.45, title="Ahtapot")
    animal_svg("jellyfish", jellyfish, 4, cols, order, 40, 56, dur_each=0.55, title="Denizanası")


if __name__ == "__main__":
    make_skills()
    make_marquee()
    make_scramble("en")
    make_scramble("tr")
    for p in sorted(OUT.glob("*.svg")):
        print(f"{p.name:16s}{p.stat().st_size / 1024:7.1f} KB")
