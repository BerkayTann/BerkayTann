"""Cyberpunk 2077 renklerinde (sarı / neon mavi / pembe) animasyonlu nokta-matris banner.

Çıktı: assets/banner.svg  (yazı tipi bağımsız: harfler daire noktalarla çizilir)
Çalıştırma: python generators/make_banner.py
"""
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(exist_ok=True)

YEL, CYN, PNK = "#fcee0a", "#00f0ff", "#ff2a9d"
MONO = "'JetBrains Mono','SFMono-Regular',Consolas,'Courier New',monospace"

FONT = {
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "N": ["10001", "11001", "10101", "10101", "10011", "10001", "10001"],
}


def build(text="BERKAY TAN", pitch=12, r=4.5):
    cols, x = [], 0
    for ch in text:
        if ch == " ":
            x += 3
            continue
        g = FONT[ch]
        for c in range(5):
            cols.append((x + c, [row for row in range(7) if g[row][c] == "1"]))
        x += 6
    width = (x - 1) * pitch
    return cols, width


def wave_path(w, base, amp, wl, phase):
    pts = []
    for x in range(-10, w + 20, 10):
        y = base + amp * math.sin(2 * math.pi * x / wl + phase)
        pts.append(f"{'M' if not pts else 'L'}{x},{y:.1f}")
    return " ".join(pts)


def main():
    W, H, P = 860, 250, 12
    cols, tw = build(pitch=P)
    x0, y0 = (W - tw) / 2 + P / 2, 46
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Berkay Tan — DevOps × JavaScript">',
         "<defs>",
         '<linearGradient id="s" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="860" y2="0" spreadMethod="repeat">'
         '<animate attributeName="x1" values="0;860" dur="8s" repeatCount="indefinite"/><animate attributeName="x2" values="860;1720" dur="8s" repeatCount="indefinite"/>'
         f'<stop offset="0" stop-color="{YEL}"/><stop offset=".28" stop-color="{YEL}"/><stop offset=".34" stop-color="{CYN}"/><stop offset=".60" stop-color="{CYN}"/>'
         f'<stop offset=".66" stop-color="{PNK}"/><stop offset=".94" stop-color="{PNK}"/><stop offset="1" stop-color="{YEL}"/>'
         "</linearGradient>",
         '<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#fff" opacity=".035"/></pattern>',
         '<g id="txt">']
    for i, (c, rows) in enumerate(cols):
        dots = "".join(f'<circle cx="{c * P:.1f}" cy="{r * P:.1f}" r="4.5"/>' for r in rows)
        o.append(f'<g transform="translate({x0:.1f},{y0})"><g>{dots}<animateTransform attributeName="transform" type="translate" values="0 0;0 -5;0 0;0 5;0 0" dur="3.4s" begin="-{i * 0.13:.2f}s" repeatCount="indefinite"/></g></g>')
    o.append("</g></defs>")
    o.append(f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="16" fill="#090b12" stroke="url(#s)" stroke-width="1.5"/>')
    o.append(f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="16" fill="url(#scan)"/>')
    # glitch kopyaları
    o.append(f'<use href="#txt" xlink:href="#txt" fill="{PNK}" transform="translate(-3,1)" opacity="0"><animate attributeName="opacity" dur="5.5s" repeatCount="indefinite" calcMode="discrete" keyTimes="0;.60;.62;.66;.68;1" values="0;0;.75;0;.5;0"/></use>')
    o.append(f'<use href="#txt" xlink:href="#txt" fill="{CYN}" transform="translate(3,-1)" opacity="0"><animate attributeName="opacity" dur="5.5s" repeatCount="indefinite" calcMode="discrete" keyTimes="0;.60;.62;.66;.68;1" values="0;0;.75;0;.5;0"/></use>')
    o.append('<use href="#txt" xlink:href="#txt" fill="url(#s)"/>')
    o.append(f'<text x="{W / 2}" y="168" text-anchor="middle" font-family="{MONO}" font-size="17" font-weight="700" letter-spacing="7" fill="url(#s)">DEVOPS × JAVASCRIPT</text>')
    # HUD
    o.append(f'<text x="26" y="30" font-family="{MONO}" font-size="11" fill="{YEL}" opacity=".85">SYS://BERKAY.TAN</text>')
    o.append(f'<text x="{W - 26}" y="30" text-anchor="end" font-family="{MONO}" font-size="11" fill="{CYN}" opacity=".85">STATUS: ONLINE<animate attributeName="opacity" values=".85;.3;.85" dur="2.2s" repeatCount="indefinite"/></text>')
    # dalgalar
    cfg = [(208, 8, 230, "1", 6.5), (220, 11, 310, ".65", 8.0), (232, 6, 190, ".4", 5.0)]
    for base, amp, wl, op, dur in cfg:
        frames = ";".join(wave_path(W, base, amp, wl, ph) for ph in (0, math.pi / 2, math.pi, 3 * math.pi / 2, 2 * math.pi))
        o.append(f'<path d="{wave_path(W, base, amp, wl, 0)}" fill="none" stroke="url(#s)" stroke-width="4" stroke-linecap="round" stroke-dasharray="0 10" opacity="{op}">'
                 f'<animate attributeName="d" values="{frames}" dur="{dur}s" repeatCount="indefinite"/></path>')
    o.append("</svg>")
    (OUT / "banner.svg").write_text("".join(o), encoding="utf-8")
    print("banner.svg", round((OUT / "banner.svg").stat().st_size / 1024, 1), "KB")


if __name__ == "__main__":
    main()
