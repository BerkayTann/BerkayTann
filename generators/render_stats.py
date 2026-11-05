"""data.json -> overview.svg, streak.svg, activity.svg (neon palet, koyu panel).

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


def overview_card(d):
    """Tek 860x230 kart: solda istatistikler, sağda dil çubukları (iki panel, aynı genişlik düzeni)."""
    rows = [(tx("commits"), d["commits"]), (tx("prs"), d["prs"]), (tx("issues"), d["issues"]), (tx("stars"), d["stars"]), (tx("repos"), d["repos"])]
    w, h, mid = 860, 230, 430
    o = [head(w, h, tx("a_stats")),
         f'<line x1="{mid}" y1="24" x2="{mid}" y2="{h - 24}" stroke="{LINE}"/>',
         f'<text x="28" y="40" font-family="{MONO}" font-size="15" font-weight="700" fill="{MAG}">{tx("stats")}</text>']
    for i, (k, v) in enumerate(rows):
        y = 76 + i * 30
        o.append(f'<text x="28" y="{y}" font-family="{MONO}" font-size="13" fill="{DIM}">{k}</text>')
        o.append(f'<text x="{mid - 28}" y="{y}" text-anchor="end" font-family="{MONO}" font-size="14" font-weight="700" fill="{TXT}">{fmt(v)}</text>')
        o.append(f'<line x1="28" y1="{y + 10}" x2="{mid - 28}" y2="{y + 10}" stroke="{LINE}" stroke-dasharray="2 4"/>')
    langs = d["langs"][:5]
    tot = sum(l[1] for l in langs) or 1
    lx = mid + 28
    o.append(f'<text x="{lx}" y="40" font-family="{MONO}" font-size="15" font-weight="700" fill="{CY}">{tx("langs")}</text>')
    if not langs:
        o.append(f'<text x="{lx}" y="86" font-family="{MONO}" font-size="13" fill="{DIM}">-</text>')
    bar_x, bar_w = lx + 110, w - 28 - 52 - (lx + 110)
    for i, (name, size, color) in enumerate(langs):
        y = 76 + i * 30
        pct = 100 * size / tot
        o.append(f'<text x="{lx}" y="{y}" font-family="{MONO}" font-size="13" fill="{TXT}">{name[:12]}</text>')
        o.append(f'<rect x="{bar_x}" y="{y - 10}" width="{bar_w}" height="10" rx="5" fill="{LINE}"/>')
        o.append(f'<rect x="{bar_x}" y="{y - 10}" width="{max(bar_w * pct / 100, 6):.1f}" height="10" rx="5" fill="{color}"/>')
        o.append(f'<text x="{w - 28}" y="{y}" text-anchor="end" font-family="{MONO}" font-size="12" fill="{DIM}">{pct:.1f}%</text>')
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
        for name, fn in (("overview", overview_card), ("streak", streak_card), ("activity", activity_card)):
            (out / (f"{name}.svg" if lang == "en" else f"{name}-{lang}.svg")).write_text(fn(data), encoding="utf-8")
    print("yazıldı: overview, streak, activity (en/tr)")
