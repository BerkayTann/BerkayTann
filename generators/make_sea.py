"""Derin deniz sahnesi: mavi Docker balinası + dipte Cthulhu benzeri ahtapot (halfdot / yarım-ton noktalar).

Çıktı: assets/sea.svg  — tek dosya, animasyonlu, yazı tipi ve dış kaynak bağımsız.
Çalıştırma: python generators/make_sea.py   (Pillow + numpy gerekir)
"""
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(exist_ok=True)
SS, P = 4, 5  # süper-örnekleme, nokta aralığı (px)
W, H = 860, 440


# ------------------------------------------------------------------ geometri
def spline(pts, closed=True, n=10):
    """Catmull-Rom ile yumuşatılmış çokgen noktaları."""
    pts = list(pts)
    m = len(pts)
    out = []
    rng = range(m) if closed else range(m - 1)
    for i in rng:
        p0, p1, p2, p3 = (pts[(i - 1) % m], pts[i], pts[(i + 1) % m], pts[(i + 2) % m]) if closed else (
            pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, m - 1)])
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * ((2 * p1[a]) + (-p0[a] + p2[a]) * t + (2 * p0[a] - 5 * p1[a] + 4 * p2[a] - p3[a]) * t * t
                                    + (-p0[a] + 3 * p1[a] - 3 * p2[a] + p3[a]) * t ** 3) for a in (0, 1)))
    return out


class Cv:
    def __init__(self, cw, ch):
        self.cw, self.ch, self.m, self.ox = cw, ch, {}, 0

    def _l(self, n):
        if n not in self.m:
            self.m[n] = Image.new("L", (self.cw * SS, self.ch * SS), 0)
        return ImageDraw.Draw(self.m[n])

    def poly(self, n, pts):
        self._l(n).polygon([((x + self.ox) * SS, y * SS) for x, y in pts], fill=255)

    def sp(self, n, pts, closed=True):
        self.poly(n, spline(pts, closed))

    def ell(self, n, cx, cy, rx, ry):
        cx += self.ox
        self._l(n).ellipse([(cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS], fill=255)

    def rect(self, n, x, y, w, h):
        self._l(n).rounded_rectangle([x * SS, y * SS, (x + w) * SS, (y + h) * SS], radius=0.7 * SS, fill=255)

    def stroke(self, n, pts, w0, w1):
        d, k = self._l(n), len(pts)
        for i, (x, y) in enumerate(pts):
            x += self.ox
            r = (w0 + (w1 - w0) * i / max(k - 1, 1)) / 2
            d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], fill=255)

    def clip(self, n, to):
        from PIL import ImageChops
        self.m[n] = ImageChops.multiply(self.m[n], self.m[to])


def hexrgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def ramp(stops, s):
    """stops = (koyu, orta, açık); s 0..1."""
    a, b, c = (hexrgb(x) for x in stops)
    s = min(max(s, 0.0), 1.0)
    u, v = (a, b) if s < 0.5 else (b, c)
    t = s * 2 if s < 0.5 else (s - 0.5) * 2
    return "#%02x%02x%02x" % tuple(round(u[i] + (v[i] - u[i]) * t) for i in range(3))


def rasterize(cv, groups, ramps, order, flat):
    """groups: {ad: ([katmanlar], sigma_hücre)}. Her grup kendi yükseklik haritasından ışıklandırılır."""
    cov = {n: (np.asarray(m, dtype=np.float32) / 255).reshape(cv.ch, SS, cv.cw, SS).mean(axis=(1, 3)) for n, m in cv.m.items()}
    shade = {}
    for g, (layers, sigma) in groups.items():
        ms = [np.asarray(cv.m[n], dtype=np.float32) / 255 for n in layers if n in cv.m]
        if not ms:
            continue
        u = np.max(ms, axis=0)
        img = Image.fromarray((u * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(sigma * SS))
        hmap = np.asarray(img, dtype=np.float32) / 255
        gy, gx = np.gradient(hmap)
        d = -(gx * -0.6 + gy * -0.8)  # ışık sol-üstten
        mag = np.hypot(gx, gy)
        sel = u > 0.5
        k = 0.5 / max(float(np.percentile(mag[sel], 95)), 1e-6) if sel.any() else 1.0
        sh = np.clip(0.5 + k * d * 0.9, 0, 1) * u
        shade[g] = (sh.reshape(cv.ch, SS, cv.cw, SS).sum(axis=(1, 3)) / np.maximum(u.reshape(cv.ch, SS, cv.cw, SS).sum(axis=(1, 3)), 1e-6))
    layer_group = {n: g for g, (ls, _) in groups.items() for n in ls}
    dots = {}
    for j in range(cv.ch):
        for i in range(cv.cw):
            best, tot = None, 0.0
            for n in order:
                c = cov.get(n)
                if c is None:
                    continue
                v = float(c[j, i])
                tot = max(tot, v)
                if v >= 0.45 or (best is None and v > 0):
                    best = n
            if best is None or tot < 0.2:
                continue
            if best in flat:
                col, lit = flat[best], 0.75
            else:
                s = float(shade[layer_group[best]][j, i])
                s = round(s * 7) / 7
                col, lit = ramp(ramps[best], s), s
            dots[(i, j)] = (round(min(1.0, tot) ** 0.6 * (0.62 + 0.38 * lit), 2), col)
    return dots


def dots_svg(dots, ox=0, oy=0):
    by = {}
    for (i, j), (r, col) in dots.items():
        by.setdefault(col, []).append(f'<circle cx="{ox + i * P + P / 2:.1f}" cy="{oy + j * P + P / 2:.1f}" r="{P / 2 * 0.94 * r:.1f}"/>')
    return "".join(f'<g fill="{c}">{"".join(v)}</g>' for c, v in by.items())


# ------------------------------------------------------------------ canlılar
WHALE_RAMPS = {"body": ("#0a2a70", "#1b6bf0", "#86d0ff"), "belly": ("#5c9fe4", "#a9dcff", "#f4fbff"), "fin": ("#09245f", "#1654c4", "#4aa3ff"),
               "box_a": ("#0d4aa8", "#2496ed", "#a6deff"), "box_b": ("#16348a", "#3f8dff", "#e8f6ff")}
WHALE_FLAT = {"eye": "#03102a", "glint": "#ffffff", "box_a": "#2f9bf2", "box_b": "#a9defc"}


def whale():
    cv = Cv(80, 46)
    cv.sp("body", [(20, 29), (28, 22), (40, 19.5), (54, 19), (65, 20.5), (73, 24.5), (76, 29), (72, 34), (60, 38), (44, 40), (30, 37), (22, 33)])
    cv.sp("body", [(24, 28), (18, 24), (13, 18), (11, 12.5), (14.5, 12.5), (17.5, 17), (22, 21.5), (28, 25), (29, 29)])
    cv.sp("body", [(12.5, 13), (6, 11), (2.5, 6.5), (7, 7), (12, 10)], closed=True)
    cv.sp("body", [(13.5, 12.5), (14.5, 6.5), (19, 3.5), (18.5, 9), (16, 13)], closed=True)
    cv.sp("belly", [(24, 34), (40, 31.5), (58, 31.5), (70, 30), (77, 29), (73, 35), (60, 39), (44, 41), (30, 38)])
    cv.clip("belly", "body")
    cv.sp("fin", [(52, 33), (46, 43), (53, 42), (59, 36)])
    rows = [(15.2, [32, 38.8, 45.6, 52.4]), (9.8, [35.4, 42.2, 49]), (4.4, [38.8, 45.6])]
    k = 0
    for y, xs in rows:
        for x in xs:
            cv.rect("box_a" if k % 2 == 0 else "box_b", x, y, 5.4, 4.4)
            k += 1
    cv.ell("eye", 68.5, 27, 1.2, 1.2)
    cv.ell("glint", 68, 26.5, 0.5, 0.5)
    groups = {"b": (["body", "belly"], 5.5), "f": (["fin"], 1.5), "a": (["box_a"], 1.4), "c": (["box_b"], 1.4)}
    return rasterize(cv, groups, WHALE_RAMPS, ["body", "belly", "fin", "box_a", "box_b", "eye", "glint"], WHALE_FLAT)


OCTO_RAMPS = {"wing": ("#07041a", "#1d0f45", "#4b2fa0"), "head": ("#0d0624", "#3a1c78", "#9a6cf5"), "tent": ("#100830", "#4a2494", "#a57bff")}
OCTO_FLAT = {"spot": "#22d3ee", "halo": "#6b6408", "eye": "#fcee0a"}


def octopus_frame(f):
    cv = Cv(124, 70)
    cv.ox = 12
    ph = f * math.pi / 2
    left = [(32, 24), (22, 10), (9, 3), (6, 8), (11, 12), (8, 18), (14, 20), (12, 27), (21, 27), (22, 33), (31, 32)]
    cv.poly("wing", left)
    cv.poly("wing", [(100 - x, y) for x, y in left])
    cv.sp("head", [(30, 30), (31, 18), (38, 9), (50, 6), (62, 9), (69, 18), (70, 30), (64, 38), (50, 41), (36, 38)])
    # yüz dokunaçları (sakal)
    for i in range(6):
        x0 = 37 + i * 5.2
        pts = [(x0 + (x0 - 50) * 0.5 * t + 2.2 * math.sin(5 * t + ph + i * 1.3) * t, 35 + 26 * t ** 0.95) for t in np.linspace(0, 1, 40)]
        cv.stroke("tent", pts, 4.0, 0.9)
    # uzun dokunaçlar (deniz tabanı boyunca)
    for s in (-1, 1):
        for k in range(3):
            sx = 50 + s * (8 + k * 6)
            pts = []
            for t in np.linspace(0, 1, 60):
                x = sx + s * (16 + k * 12) * t
                y = 37 + k * 1.2 + 26 * math.sin(min(t * 1.5, 1) * math.pi / 2) + 2.0 * math.sin(7 * t + ph + k * 1.1 + (0 if s < 0 else 1.7)) * t
                pts.append((x, min(y, 68)))
            cv.stroke("tent", pts, 4.4, 0.9)
            for t_i in range(2, 58, 6):
                x, y = pts[t_i]
                cv.ell("spot", x, y, 0.55, 0.55)
    for ex in (43, 57):
        cv.ell("halo", ex, 25, 4.6, 4.2)
        cv.ell("eye", ex, 25, 2.3, 2.1)
    groups = {"w": (["wing"], 3.5), "h": (["head"], 6.5), "t": (["tent"], 2.2)}
    return rasterize(cv, groups, OCTO_RAMPS, ["wing", "head", "tent", "spot", "halo", "eye"], OCTO_FLAT)


# ------------------------------------------------------------------ sahne
def wave(w, base, amp, wl, ph, y0=0):
    return " ".join(f"{'M' if x < 0 else 'L'}{x},{base + amp * math.sin(2 * math.pi * x / wl + ph):.1f}" for x in range(-10, w + 20, 10))


def build():
    rnd = random.Random(11)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Derin deniz: Docker balinası ve Cthulhu ahtapotu">',
         '<defs><linearGradient id="w" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0c68ad"/><stop offset=".35" stop-color="#083c75"/><stop offset=".75" stop-color="#041a3b"/><stop offset="1" stop-color="#020a1a"/></linearGradient>'
         '<linearGradient id="r" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#bfeaff" stop-opacity=".30"/><stop offset="1" stop-color="#bfeaff" stop-opacity="0"/></linearGradient>'
         f'<clipPath id="c"><rect width="{W}" height="{H}" rx="16"/></clipPath></defs>',
         f'<g clip-path="url(#c)"><rect width="{W}" height="{H}" fill="url(#w)"/>']
    # ışık huzmeleri
    for i, x in enumerate((90, 260, 430, 610, 760)):
        w0, w1 = 22 + rnd.random() * 20, 110 + rnd.random() * 60
        o.append(f'<polygon points="{x - w0},0 {x + w0},0 {x + w1 + 70},{H} {x - w1 + 70},{H}" fill="url(#r)" opacity=".5">'
                 f'<animate attributeName="opacity" values=".25;.6;.25" dur="{7 + i * 1.7:.1f}s" repeatCount="indefinite"/></polygon>')
    # plankton
    for _ in range(46):
        x, y, r = rnd.uniform(10, W - 10), rnd.uniform(40, H - 40), rnd.uniform(0.9, 1.9)
        o.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="#9fe3ff" opacity=".5"><animate attributeName="opacity" values=".15;.8;.15" dur="{rnd.uniform(2, 6):.1f}s" begin="-{rnd.uniform(0, 5):.1f}s" repeatCount="indefinite"/></circle>')
    # yosunlar (noktalı)
    for x in (30, 120, 250, 700, 790, 840):
        hgt = rnd.uniform(110, 190)
        a = f"M{x},{H} C{x - 22},{H - hgt * .35} {x + 22},{H - hgt * .65} {x},{H - hgt}"
        b = f"M{x},{H} C{x + 22},{H - hgt * .35} {x - 22},{H - hgt * .65} {x + 6},{H - hgt}"
        o.append(f'<path d="{a}" fill="none" stroke="#0fa89a" stroke-opacity=".7" stroke-width="5" stroke-linecap="round" stroke-dasharray="0 8"><animate attributeName="d" values="{a};{b};{a}" dur="{rnd.uniform(5, 8):.1f}s" repeatCount="indefinite"/></path>')
    # ahtapot
    frames = [octopus_frame(f) for f in range(4)]
    static = {k: v for k, v in frames[0].items() if all(fr.get(k) == v for fr in frames)}
    ox, oy = W - 124 * P + 6, H - 70 * P + 4
    o.append(f"<g>{dots_svg(static, ox, oy)}</g>")
    n, each = 4, 0.55
    for idx, fr in enumerate(frames):
        diff = {k: v for k, v in fr.items() if k not in static}
        a, b = idx / n, (idx + 1) / n
        if idx == 0:
            kts, vals = f"0;{b:.4f};1", "visible;hidden;hidden"
        elif idx == n - 1:
            kts, vals = f"0;{a:.4f};1", "hidden;visible;visible"
        else:
            kts, vals = f"0;{a:.4f};{b:.4f};1", "hidden;visible;hidden;hidden"
        o.append(f'<g visibility="hidden"><animate attributeName="visibility" dur="{n * each:.2f}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{kts}" values="{vals}"/>{dots_svg(diff, ox, oy)}</g>')
    # göz parıltısı
    for ex in (43, 57):
        o.append(f'<circle cx="{ox + (ex + 12) * P + P / 2:.1f}" cy="{oy + 25 * P + P / 2:.1f}" r="16" fill="#fcee0a" opacity=".12"><animate attributeName="opacity" values=".06;.22;.06" dur="3.2s" repeatCount="indefinite"/></circle>')
    # balina (sürüklenme + dalgalanma)
    o.append('<g transform="translate(30,22)"><g>'
             '<animateTransform attributeName="transform" type="translate" values="0 0;45 -10;90 0;45 10;0 0" dur="30s" repeatCount="indefinite" calcMode="spline" keyTimes="0;.25;.5;.75;1" keySplines=".4 0 .6 1;.4 0 .6 1;.4 0 .6 1;.4 0 .6 1"/>'
             f'{dots_svg(whale())}</g></g>')
    # deniz yüzeyi
    frs = ";".join(wave(W, 14, 3.5, 160, ph) for ph in (0, math.pi, 2 * math.pi))
    o.append(f'<path d="{wave(W, 14, 3.5, 160, 0)}" fill="none" stroke="#9fe3ff" stroke-opacity=".7" stroke-width="3" stroke-linecap="round" stroke-dasharray="0 9"><animate attributeName="d" values="{frs}" dur="7s" repeatCount="indefinite"/></path>')
    # kabarcıklar
    for _ in range(24):
        x, r, d = rnd.uniform(20, W - 20), rnd.uniform(1.8, 5), rnd.uniform(9, 19)
        y0 = rnd.uniform(H - 40, H)
        o.append(f'<circle cx="{x:.0f}" cy="{y0:.0f}" r="{r:.1f}" fill="none" stroke="#d8f4ff" stroke-opacity=".45"><animate attributeName="cy" from="{y0:.0f}" to="-12" dur="{d:.1f}s" begin="-{rnd.uniform(0, d):.1f}s" repeatCount="indefinite"/></circle>')
    # deniz tabanı
    for base, col, op in ((H - 9, "#14456f", .8), (H - 3, "#0b2c4d", 1)):
        o.append(f'<path d="{wave(W, base, 3, 140, base)}" fill="none" stroke="{col}" stroke-opacity="{op}" stroke-width="5" stroke-linecap="round" stroke-dasharray="0 8"/>')
    o.append(f'</g><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="16" fill="none" stroke="#1d63ed" stroke-opacity=".55" stroke-width="1.5"/></svg>')
    (OUT / "sea.svg").write_text("".join(o), encoding="utf-8")
    print("sea.svg", round((OUT / "sea.svg").stat().st_size / 1024), "KB")


if __name__ == "__main__":
    build()
