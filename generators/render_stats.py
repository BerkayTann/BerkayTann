"""data.json -> stats.svg, langs.svg, streak.svg, activity.svg (neon palet, koyu panel).

Kullanım: python generators/render_stats.py data.json cikti_klasoru
"""
import datetime as dt
import json
import sys
from pathlib import Path

MAG, VIO, CY = "#e64cbd", "#b10fd2", "#22d3ee"
PANEL, LINE, TXT, DIM = "#0d1117", "#2b3345", "#c9d1d9", "#8b949e"
T = {
    "en": {"stats": "// stats", "commits": "Commits (2 yrs)", "prs": "Pull requests", "issues": "Issues", "stars": "Stars", "repos": "Repos",
           "langs": "// languages", "total": "total contributions", "cur": "current streak", "best": "longest streak", "day": "days", "act": "// last 31 days",
           "a_stats": "GitHub stats", "a_langs": "Top languages", "a_streak": "Contribution streak", "a_act": "Last 31 days activity"},
    "tr": {"stats": "// istatistikler", "commits": "Son 2 yıl commit", "prs": "Pull request", "issues": "Issue", "stars": "Yıldız", "repos": "Repo",
           "langs": "// diller", "total": "toplam katkı", "cur": "güncel seri", "best": "en uzun seri", "day": "gün", "act": "// son 31 gün",
           "a_stats": "GitHub istatistikleri", "a_langs": "En çok kullanılan diller", "a_streak": "Katkı serisi", "a_act": "Son 31 gün aktivite"},
}
L = "en"


def tx(k):
    return T[L][k]


MONO = "'JetBrains Mono','SFMono-Regular',Consolas,'Courier New',monospace"


def head(w, h, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{label}">'
            f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{MAG}"/><stop offset="1" stop-color="{VIO}"/></linearGradient>'
            f'<linearGradient id="a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{MAG}" stop-opacity=".45"/><stop offset="1" stop-color="{VIO}" stop-opacity="0"/></linearGradient></defs>'
            f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="14" fill="{PANEL}" stroke="url(#g)" stroke-opacity=".6" stroke-width="1.3"/>')


def fmt(n):
    return f"{n:,}".replace(",", ".")


def streaks(days):
    today = dt.date.today()
    dates = sorted(dt.date.fromisoformat(d) for d, c in days.items() if c > 0)
    if not dates:
        return 0, 0
    best = run = 1
    for a, b in zip(dates, dates[1:]):
        run = run + 1 if (b - a).days == 1 else 1
        best = max(best, run)
    s = set(dates)
    cur, d = 0, today if today in s else today - dt.timedelta(days=1)
    while d in s:
        cur += 1
        d -= dt.timedelta(days=1)
    return cur, best


def stats_card(d):
    rows = [(tx("commits"), d["commits"]), (tx("prs"), d["prs"]), (tx("issues"), d["issues"]), (tx("stars"), d["stars"]), (tx("repos"), d["repos"])]
    w, h = 420, 210
    o = [head(w, h, tx("a_stats")), f'<text x="24" y="38" font-family="{MONO}" font-size="15" font-weight="700" fill="{MAG}">{tx("stats")}</text>']
    for i, (k, v) in enumerate(rows):
        y = 72 + i * 28
        o.append(f'<text x="24" y="{y}" font-family="{MONO}" font-size="13" fill="{DIM}">{k}</text>')
        o.append(f'<text x="{w - 24}" y="{y}" text-anchor="end" font-family="{MONO}" font-size="14" font-weight="700" fill="{TXT}">{fmt(v)}</text>')
        o.append(f'<line x1="24" y1="{y + 9}" x2="{w - 24}" y2="{y + 9}" stroke="{LINE}" stroke-dasharray="2 4"/>')
    o.append("</svg>")
    return "".join(o)


def langs_card(d):
    langs = d["langs"][:6]
    tot = sum(l[1] for l in langs) or 1
    w, h = 420, 210
    o = [head(w, h, tx("a_langs")), f'<text x="24" y="38" font-family="{MONO}" font-size="15" font-weight="700" fill="{CY}">{tx("langs")}</text>']
    bar_x, bar_w = 24, w - 48
    x = bar_x
    o.append(f'<clipPath id="c"><rect x="{bar_x}" y="52" width="{bar_w}" height="10" rx="5"/></clipPath><g clip-path="url(#c)">')
    for _, size, color in langs:
        seg = bar_w * size / tot
        o.append(f'<rect x="{x:.1f}" y="52" width="{seg:.1f}" height="10" fill="{color}"/>')
        x += seg
    o.append("</g>")
    for i, (name, size, color) in enumerate(langs):
        col, row = i % 2, i // 2
        cx, cy = 24 + col * 200, 92 + row * 30
        o.append(f'<circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{color}"/>')
        o.append(f'<text x="{cx + 18}" y="{cy}" font-family="{MONO}" font-size="13" fill="{TXT}">{name}</text>')
        o.append(f'<text x="{cx + 170}" y="{cy}" text-anchor="end" font-family="{MONO}" font-size="12" fill="{DIM}">{100 * size / tot:.1f}%</text>')
    o.append("</svg>")
    return "".join(o)


def streak_card(d):
    cur, best = streaks(d["days"])
    total = sum(d["days"].values())
    w, h = 860, 130
    cols = [(fmt(total), tx("total"), MAG), (f"{cur} {tx('day')}", tx("cur"), CY), (f"{best} {tx('day')}", tx("best"), VIO)]
    o = [head(w, h, tx("a_streak"))]
    for i, (v, l, c) in enumerate(cols):
        cx = w / 6 + i * w / 3
        o.append(f'<text x="{cx}" y="64" text-anchor="middle" font-family="{MONO}" font-size="30" font-weight="700" fill="{c}">{v}</text>')
        o.append(f'<text x="{cx}" y="92" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{DIM}">{l}</text>')
        if i:
            o.append(f'<line x1="{i * w / 3}" y1="28" x2="{i * w / 3}" y2="{h - 28}" stroke="{LINE}"/>')
    o.append("</svg>")
    return "".join(o)


def activity_card(d):
    today = dt.date.today()
    pts = [(today - dt.timedelta(days=30 - i)) for i in range(31)]
    vals = [d["days"].get(p.isoformat(), 0) for p in pts]
    w, h = 860, 220
    l, r, t, b = 48, 24, 46, 36
    top = max(max(vals), 4)
    xs = [l + i * (w - l - r) / 30 for i in range(31)]
    ys = [t + (h - t - b) * (1 - v / top) for v in vals]
    line = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(zip(xs, ys)))
    area = line + f" L{xs[-1]:.1f},{h - b} L{xs[0]:.1f},{h - b} Z"
    o = [head(w, h, tx("a_act")), f'<text x="24" y="32" font-family="{MONO}" font-size="15" font-weight="700" fill="{MAG}">{tx("act")}</text>']
    for k in range(5):
        y = t + (h - t - b) * k / 4
        o.append(f'<line x1="{l}" y1="{y:.1f}" x2="{w - r}" y2="{y:.1f}" stroke="{LINE}" stroke-dasharray="2 5"/>')
        o.append(f'<text x="{l - 8}" y="{y + 4:.1f}" text-anchor="end" font-family="{MONO}" font-size="10" fill="{DIM}">{round(top * (1 - k / 4))}</text>')
    o.append(f'<path d="{area}" fill="url(#a)"/><path d="{line}" fill="none" stroke="{MAG}" stroke-width="2.2" stroke-linejoin="round"/>')
    for x, y, v in zip(xs, ys, vals):
        if v:
            o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="{CY}"/>')
    for i in (0, 10, 20, 30):
        o.append(f'<text x="{xs[i]:.1f}" y="{h - 12}" text-anchor="middle" font-family="{MONO}" font-size="10" fill="{DIM}">{pts[i].strftime("%d.%m")}</text>')
    o.append("</svg>")
    return "".join(o)


if __name__ == "__main__":
    data = json.loads(Path(sys.argv[1]).read_text())
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    for lang in ("en", "tr"):
        L = lang
        for name, fn in (("stats", stats_card), ("langs", langs_card), ("streak", streak_card), ("activity", activity_card)):
            (out / (f"{name}.svg" if lang == "en" else f"{name}-{lang}.svg")).write_text(fn(data), encoding="utf-8")
    print("yazıldı: stats, langs, streak, activity (en/tr)")
