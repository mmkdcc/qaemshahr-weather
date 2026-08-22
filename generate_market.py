#!/usr/bin/env python3
"""generate_market.py — Standalone market page generator (no local deps).
Fetches live data from public sources: tgju.org prices/history + news RSS.
Works on GitHub Actions runners.
"""
import gzip, json, re, urllib.request, urllib.parse
from datetime import datetime

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126 Safari/537.36")

def get(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    raw = urllib.request.urlopen(req, timeout=timeout).read()
    try:
        raw = gzip.decompress(raw)
    except Exception:
        pass
    return raw.decode("utf-8", "ignore")

# ---------------------------------------------------------------- prices
def daily_series(profile):
    """Daily closes from a tgju profile page (chartData), in TOMAN."""
    html = get(f"https://www.tgju.org/profile/{profile}")
    arrs = re.findall(r'chartData:\s*(\[\[[\s\S]*?\]\])', html)
    import collections
    best = None
    for a in arrs:
        try:
            data = json.loads(a)
        except Exception:
            continue
        if len(data) > 500:
            byday = collections.OrderedDict()
            for p in data:
                d = datetime.utcfromtimestamp(p[0] / 1000).strftime("%Y-%m-%d")
                byday[d] = float(p[1]) / 10.0  # rial -> toman
            if len(byday) > (len(best) if best else 0):
                best = list(byday.items())
    return best  # [(date, price)] ascending

def ta(series):
    """Simple TA: SMA20 trend + RSI14 + 7d change."""
    vals = [v for _, v in series]
    cur = vals[-1]
    sma20 = sum(vals[-20:]) / 20 if len(vals) >= 20 else None
    # RSI14
    rsi = None
    if len(vals) >= 15:
        gains = losses = 0.0
        for i in range(-14, 0):
            d = vals[i] - vals[i - 1]
            if d > 0:
                gains += d
            else:
                losses += abs(d)
        rsi = 100.0 if losses == 0 else 100 - 100 / (1 + gains / losses)
    chg7 = ((cur - vals[-8]) / vals[-8] * 100) if len(vals) >= 8 else None
    if sma20 is None:
        trend = "نامشخص"
    elif cur > sma20 * 1.005:
        trend = "صعودی 📈"
    elif cur < sma20 * 0.995:
        trend = "نزولی 📉"
    else:
        trend = "خنثی ⏸️"
    return {"current": cur, "sma20": sma20, "rsi": rsi, "trend": trend,
            "chg7": chg7, "old7": vals[-8] if len(vals) >= 8 else None}

def fmt(n):
    if n is None:
        return "—"
    return f"{n:,.0f}"

# ---------------------------------------------------------------- news
IRAN_MARKET_KW = ["اقتصاد", "دلار", "طلا", "تورم", "تحریم", "نرخ", "بازار",
                  "سکه", "ارز", "نفت", "مذاکره", "بانک مرکزی", "قیمت", "بورس",
                  "آمریکا", "ترامپ", "تنگه هرمز", "صادرات", "واردات"]

def iran_news(limit=6):
    out = []
    try:
        h = get("https://www.iranintl.com/sitemap-news.xml")
        titles = re.findall(r"<news:title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</news:title>", h, re.S)
        dates = re.findall(r"<news:publication_date>([^<]+)</news:publication_date>", h)
        for t, d in zip(titles, dates):
            t = re.sub(r"\s+", " ", t).strip()
            if not any(k in t for k in IRAN_MARKET_KW):
                continue
            when = d.replace("T", " ")[:16]
            out.append((t, when))
            if len(out) >= limit:
                break
    except Exception:
        pass
    if len(out) < 3:
        try:
            h = get("https://news.google.com/rss/search?q="
                    + urllib.parse.quote("iran dollar OR gold economy")
                    + "&hl=en&gl=US&ceid=US:en")
            items = re.findall(r"<title>(.*?)</title>", h)[:5]
            for it in items:
                if "<![CDATA[" in it:
                    it = re.sub(r"<!\[CDATA\[|\]\]>", "", it)
                if it and "Google News" not in it:
                    out.append((it.strip(), ""))
                if len(out) >= limit:
                    break
        except Exception:
            pass
    return out

# ---------------------------------------------------------------- forecast
def forecast(gold, dollar):
    lines = []
    if gold.get("rsi") is not None and gold["rsi"] > 70:
        lines.append(f"🥇 <strong>طلا:</strong> {gold['trend']} — RSI {gold['rsi']:.1f}")
        lines.append("⚠️ RSI طلا بالای ۷۰ هست (اشباع خرید) — احتمال اصلاح در کوتاه‌مدت وجود داره.")
    elif gold.get("rsi") is not None:
        lines.append(f"🥇 <strong>طلا:</strong> {gold['trend']} — RSI {gold['rsi']:.1f}")
    if dollar.get("rsi") is not None:
        lines.append(f"💵 <strong>دلار:</strong> {dollar['trend']} — RSI {dollar['rsi']:.1f}")
        if 30 <= dollar["rsi"] <= 70:
            lines.append("✅ RSI دلار در محدوده عادی هست — روند پایدار.")
    return "\n    <br>\n    ".join(lines)

# ---------------------------------------------------------------- main
def main():
    print("fetching dollar history...", flush=True)
    d_series = daily_series("price_dollar_rl")
    print("fetching gold18 history...", flush=True)
    g_series = daily_series("geram18")
    print("fetching mesghal history...", flush=True)
    m_series = daily_series("mesghal")

    d = ta(d_series) if d_series else {}
    g = ta(g_series) if g_series else {}
    m = ta(m_series) if m_series else {}

    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    news = iran_news()

    news_html = "".join(
        f'<div class="news-item"><span class="ni-badge">📰</span>'
        f'<div class="ni-content"><div class="ni-title">{t}</div>'
        f'<div class="ni-desc">{w}</div></div></div>\n'
        for t, w in news
    ) or '<div style="color:#64748b;font-size:0.75rem;text-align:center;padding:12px">اخبار در دسترس نیست</div>'

    def cmp_line(icon, name, data):
        if not data or data.get("old7") is None:
            return f"{icon} <strong>{name}:</strong> —"
        return (f'{icon} <strong>{name}:</strong> {fmt(data["old7"])} → '
                f'{fmt(data["current"])} (<span class="{"up" if data["chg7"]>=0 else "down"}">'
                f'{data["chg7"]:+.1f}%</span>)')

    cmp_html = "<br>\n    ".join([
        cmp_line("💵", "دلار", d),
        cmp_line("🥇", "طلای ۱۸", g),
        cmp_line("⚖️", "مثقال", m),
    ])

    fc_html = forecast(g, d)

    ta_box = lambda icon, name, x: (
        f'<div class="ta-box"><div class="ta-label">{icon} {name}</div>'
        f'<div class="ta-value">{x.get("trend","نامشخص")}'
        f'{f" • RSI {x[chr(39)+chr(39)]}" if False else ""}'
        f'{" • اشباع خرید ⚠️" if x.get("rsi") and x["rsi"] > 70 else ""}'
        f'{" • اشباع فروش 🟢" if x.get("rsi") and x["rsi"] < 30 else ""}'
        f'{" • عادی" if x.get("rsi") and 30 <= x["rsi"] <= 70 else ""}'
        f'</div></div>' if x else
        f'<div class="ta-box"><div class="ta-label">{icon} {name}</div><div class="ta-value">نامشخص</div></div>')

    html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="theme-color" content="#0a0e1a">
<title>تحلیل بازار طلا و دلار</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
@keyframes fadeUp{{from{{opacity:0;transform:translateY(16px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.7}}}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',sans-serif;background:#0a0e1a;color:#e2e8f0;min-height:100vh;padding:16px;max-width:480px;margin:0 auto;line-height:1.7}}
.nav{{display:flex;align-items:center;justify-content:space-between;padding:12px 0;margin-bottom:16px}}
.nav-back{{font-size:0.85rem;color:#64748b;text-decoration:none}}
.hero{{background:linear-gradient(135deg,#1e1b4b,#312e81);border-radius:20px;padding:24px;text-align:center;margin-bottom:20px;border:1px solid rgba(129,140,248,0.2);animation:fadeUp .5s ease}}
.hero-icon{{font-size:2.5rem;margin-bottom:8px}}
.hero-title{{font-size:1.2rem;font-weight:800;color:#f1f5f9}}
.hero-sub{{font-size:0.75rem;color:#818cf8;margin-top:4px}}
.section{{background:#111827;border-radius:16px;padding:18px;margin-bottom:16px;border:1px solid rgba(255,255,255,0.06);animation:fadeUp .5s ease}}
.section-title{{font-size:0.9rem;font-weight:700;margin-bottom:12px}}
.price-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
.price-card{{background:rgba(255,255,255,0.03);border-radius:12px;padding:14px;text-align:center}}
.pc-icon{{font-size:1.6rem;margin-bottom:4px}}
.pc-label{{font-size:0.68rem;color:#64748b;margin-bottom:4px}}
.pc-value{{font-size:1.15rem;font-weight:900}}
.pc-unit{{font-size:0.58rem;color:#475569;margin-top:2px}}
.green{{color:#22c55e}} .gold{{color:#fbbf24}} .purple{{color:#a78bfa}} .orange{{color:#f97316}}
.ta-box{{background:rgba(255,255,255,0.03);border-radius:10px;padding:12px;margin-bottom:8px}}
.ta-label{{font-size:0.7rem;color:#64748b}} .ta-value{{font-size:0.85rem;font-weight:700}}
.news-item{{display:flex;gap:8px;padding:10px;background:rgba(255,255,255,0.03);border-radius:10px;margin-bottom:8px}}
.ni-badge{{font-size:1rem}} .ni-title{{font-size:0.78rem;color:#e2e8f0;line-height:1.6}}
.ni-desc{{font-size:0.62rem;color:#475569;margin-top:2px}}
.cmp{{font-size:0.78rem;color:#94a3b8;line-height:2;padding:10px;background:rgba(255,255,255,0.03);border-radius:10px}}
.up{{color:#22c55e;font-weight:700}} .down{{color:#ef4444;font-weight:700}}
.update-bar{{display:flex;align-items:center;justify-content:center;gap:6px;padding:12px;color:#475569;font-size:0.68rem}}
.ub-dot{{width:6px;height:6px;background:#22c55e;border-radius:50%;animation:pulse 2s infinite}}
.warn{{font-size:0.72rem;color:#94a3b8;margin-top:10px}}
</style>
</head>
<body>
<div class="nav">
  <a href="index.html" class="nav-back">→ صفحه اصلی</a>
  <span style="color:#94a3b8;font-size:0.8rem;font-weight:600">📈 تحلیل بازار</span>
</div>
<div class="hero">
  <div class="hero-icon">📊</div>
  <div class="hero-title">تحلیل حرفه‌ای بازار</div>
  <div class="hero-sub">طلا و دلار ایران • تحلیل تکنیکال + اخبار • منبع: tgju.org</div>
</div>

<div class="section">
  <div class="section-title">💰 قیمت‌های لحظه‌ای</div>
  <div class="price-grid">
    <div class="price-card"><div class="pc-icon">💵</div><div class="pc-label">دلار آمریکا</div><div class="pc-value green">{fmt(d.get('current'))}</div><div class="pc-unit">تومان</div></div>
    <div class="price-card"><div class="pc-icon">🥇</div><div class="pc-label">طلای ۱۸ عیار</div><div class="pc-value gold">{fmt(g.get('current'))}</div><div class="pc-unit">تومان / گرم</div></div>
    <div class="price-card"><div class="pc-icon">⚖️</div><div class="pc-label">مثقال طلا</div><div class="pc-value purple">{fmt(m.get('current'))}</div><div class="pc-unit">تومان</div></div>
    <div class="price-card"><div class="pc-icon">📊</div><div class="pc-label">روند بازار</div><div class="pc-value orange">{g.get('trend', '—')}</div><div class="pc-unit">طلا (۷ روزه: {f"{g['chg7']:+.1f}%" if g.get('chg7') is not None else '—'})</div></div>
  </div>
</div>

<div class="section">
  <div class="section-title">📊 تحلیل تکنیکال</div>
  {ta_box("💵", "دلار", d)}
  {ta_box("🥇", "طلای ۱۸", g)}
  {ta_box("⚖️", "مثقال", m)}
</div>

<div class="section">
  <div class="section-title">📰 آخرین اخبار بازار</div>
  {news_html}
</div>

<div class="section">
  <div class="section-title">📅 مقایسه با هفته قبل</div>
  <div class="cmp">
    {cmp_html}
  </div>
</div>

<div class="section">
  <div class="section-title">🔮 پیش‌بینی هفته آینده</div>
  <div class="cmp">
    {fc_html}
    <div class="warn">⚠️ <strong>هشدار:</strong> این تحلیل آماری است و نصیحت مالی نیست. حد ضرر یادتون نره!</div>
  </div>
</div>

<div class="update-bar">
  <span class="ub-dot"></span>
  آخرین بروزرسانی: {now}
</div>
</body>
</html>"""

    with open("market.html", "w") as f:
        f.write(html)
    print(f"Generated market.html ({len(html)} bytes)")

if __name__ == "__main__":
    main()
