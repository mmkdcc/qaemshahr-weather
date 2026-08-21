#!/usr/bin/env python3
"""market_gen.py — Generate market analysis HTML using fast.py data"""
import json, subprocess, sys, os
from datetime import datetime

def run_fast(topic):
    """Run fast.py and get output"""
    try:
        result = subprocess.run(
            ["python3", "/root/scripts/fast.py", topic],
            capture_output=True, text=True, timeout=15
        )
        return result.stdout.strip()
    except Exception as e:
        return f"خطا در دریافت داده: {e}"

def parse_prices(output):
    """Parse prices from fast.py output"""
    prices = {}
    for line in output.split("\n"):
        if "—" in line:
            parts = line.split("—")
            if len(parts) >= 2:
                label = parts[0].strip().replace("•", "").strip()
                value_part = parts[1].strip()
                # Extract numbers
                nums = []
                for word in value_part.split():
                    clean = word.replace(",", "").replace("تومان", "")
                    if clean.isdigit():
                        nums.append(int(clean))
                if nums:
                    prices[label] = nums[0]
    return prices

def format_number(n):
    if n is None:
        return "—"
    return f"{n:,}"

def generate_html():
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    
    # Get data
    arz = run_fast("arz")
    gold = run_fast("gold")
    
    arz_prices = parse_prices(arz)
    gold_prices = parse_prices(gold)
    
    # Extract specific prices
    dollar_buy = arz_prices.get("دلار آمریکا", None)
    dollar_sell = arz_prices.get("دلار آمریکا", None)
    
    # Try to get both buy/sell from the output
    for line in arz.split("\n"):
        if "دلار آمریکا" in line and "خرید" in line and "فروش" in line:
            import re
            nums = re.findall(r'[\d,]+', line)
            if len(nums) >= 2:
                dollar_buy = int(nums[0].replace(",", ""))
                dollar_sell = int(nums[1].replace(",", ""))
                break
    
    gold18 = gold_prices.get("گرم طلای ۱۸ عیار", None)
    mesghal = gold_prices.get("آبشده(مثقال طلا)", None)
    sekkeh = gold_prices.get("سکه امامی (طرح جدید)", None)
    
    # Calculate spread
    dollar_spread = None
    if dollar_buy and dollar_sell:
        dollar_spread = ((dollar_sell - dollar_buy) / dollar_buy * 100)
    
    # Calculate bubble
    hobab = None
    hobab_pct = None
    if gold18 and sekkeh:
        gold_value = gold18 * 8.13  # 8.13 grams in sekkeh
        hobab = sekkeh - gold_value
        hobab_pct = (hobab / sekkeh * 100) if sekkeh else 0
    
    # Market assessment
    market_mood = "آرام"
    if dollar_spread and dollar_spread > 1.5:
        market_mood = "پرنوسان"
    elif dollar_spread and dollar_spread < 0.5:
        market_mood = "بسیار آرام"
    
    return f"""<!DOCTYPE html>
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
body{{font-family:'Inter',-apple-system,sans-serif;background:#0a0e1a;color:#e2e8f0;min-height:100vh;padding:16px;max-width:480px;margin:0 auto;line-height:1.7}}
.nav{{display:flex;align-items:center;justify-content:space-between;padding:12px 0;margin-bottom:20px}}
.nav-back{{font-size:0.85rem;color:#64748b;text-decoration:none}}
.nav-title{{font-size:0.8rem;color:#94a3b8;font-weight:600}}
.hero{{background:linear-gradient(135deg,#1e1b4b,#312e81);border-radius:20px;padding:24px;text-align:center;margin-bottom:20px;border:1px solid rgba(129,140,248,0.2);animation:fadeUp .5s ease}}
.hero-icon{{font-size:2.5rem;margin-bottom:8px}}
.hero-title{{font-size:1.2rem;font-weight:800;color:#f1f5f9}}
.hero-sub{{font-size:0.75rem;color:#818cf8;margin-top:4px}}
.price-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px}}
.price-card{{background:#111827;border-radius:16px;padding:16px;text-align:center;border:1px solid rgba(255,255,255,0.06);animation:fadeUp .5s ease}}
.price-card:nth-child(2){{animation-delay:.1s}}
.price-card:nth-child(3){{animation-delay:.2s}}
.price-card:nth-child(4){{animation-delay:.3s}}
.pc-icon{{font-size:1.8rem;margin-bottom:4px}}
.pc-label{{font-size:0.7rem;color:#64748b;margin-bottom:6px}}
.pc-value{{font-size:1.3rem;font-weight:900;color:#f1f5f9}}
.pc-unit{{font-size:0.6rem;color:#475569;margin-top:2px}}
.dollar .pc-value{{color:#22c55e}}
.gold .pc-value{{color:#fbbf24}}
.mesghal .pc-value{{color:#a78bfa}}
.sekkeh .pc-value{{color:#f97316}}
.analysis-box,.news-section{{background:#111827;border-radius:16px;padding:18px;margin-bottom:16px;border:1px solid rgba(255,255,255,0.06);animation:fadeUp .5s ease}}
.ab-title,.ns-title{{font-size:0.9rem;font-weight:700;color:#f1f5f9;margin-bottom:12px}}
.ab-content{{font-size:0.8rem;color:#94a3b8;line-height:1.8}}
.ab-content p{{margin-bottom:8px;padding:8px;background:rgba(255,255,255,0.03);border-radius:8px}}
.ab-content strong{{color:#e2e8f0}}
.news-item{{display:flex;align-items:flex-start;gap:10px;padding:10px;background:rgba(255,255,255,0.03);border-radius:10px;margin-bottom:8px}}
.ni-badge{{font-size:1.2rem;flex-shrink:0}}
.ni-content{{flex:1}}
.ni-title{{font-size:0.8rem;font-weight:600;color:#e2e8f0;margin-bottom:2px}}
.ni-desc{{font-size:0.7rem;color:#64748b}}
.update-bar{{display:flex;align-items:center;justify-content:center;gap:8px;padding:12px;color:#475569;font-size:0.7rem}}
.ub-dot{{width:6px;height:6px;background:#22c55e;border-radius:50%;animation:pulse 2s infinite}}
</style>
</head>
<body>
<div class="nav">
  <a href="index.html" class="nav-back">→ صفحه اصلی</a>
  <span class="nav-title">📈 تحلیل بازار</span>
</div>
<div class="hero">
  <div class="hero-icon">📊</div>
  <div class="hero-title">تحلیل حرفه‌ای بازار</div>
  <div class="hero-sub">طلا و دلار ایران • بروزرسانی خودکار</div>
</div>

<div class="price-grid">
  <div class="price-card dollar">
    <div class="pc-icon">💵</div>
    <div class="pc-label">دلار آمریکا</div>
    <div class="pc-value">{format_number(dollar_sell) if dollar_sell else "—"}</div>
    <div class="pc-unit">تومان (فروش)</div>
  </div>
  <div class="price-card gold">
    <div class="pc-icon">🥇</div>
    <div class="pc-label">طلای ۱۸ عیار</div>
    <div class="pc-value">{format_number(gold18)}</div>
    <div class="pc-unit">تومان / گرم</div>
  </div>
  <div class="price-card mesghal">
    <div class="pc-icon">⚖️</div>
    <div class="pc-label">مثقال طلا</div>
    <div class="pc-value">{format_number(mesghal)}</div>
    <div class="pc-unit">تومان</div>
  </div>
  <div class="price-card sekkeh">
    <div class="pc-icon">🪙</div>
    <div class="pc-label">سکه امامی</div>
    <div class="pc-value">{format_number(sekkeh)}</div>
    <div class="pc-unit">تومان</div>
  </div>
</div>

<div class="analysis-box">
  <div class="ab-title">📊 تحلیل وضعیت فعلی</div>
  <div class="ab-content">
    <p>💵 <strong>دلار:</strong> خرید {format_number(dollar_buy)} / فروش {format_number(dollar_sell)} — اسپرد {f"{dollar_spread:.1f}" if dollar_spread else "—"}٪ — بازار {market_mood}</p>
    <p>🥇 <strong>طلا:</strong> هر گرم {format_number(gold18)} تومان — مثقال {format_number(mesghal)} تومان</p>
    {"<p>🪙 <strong>سکه:</strong> " + format_number(sekkeh) + " تومان — حباب " + format_number(int(hobab)) + " تومان (" + f"{hobab_pct:.1f}" + "٪)" + " — " + ("طبیعی" if hobab_pct and hobab_pct < 10 else "بالا ⚠️") + "</p>" if hobab else ""}
  </div>
</div>

<div class="news-section">
  <div class="ns-title">📰 اطلاعات بازار</div>
  <div class="news-item">
    <span class="ni-badge">📊</span>
    <div class="ni-content">
      <div class="ni-title">منابع داده</div>
      <div class="ni-desc">tgju.org • Binance • Open-Meteo</div>
    </div>
  </div>
  <div class="news-item">
    <span class="ni-badge">⏱️</span>
    <div class="ni-content">
      <div class="ni-title">بروزرسانی خودکار</div>
      <div class="ni-desc">هر ۵ ساعت اطلاعات تازه میشه</div>
    </div>
  </div>
</div>

<div class="update-bar">
  <span class="ub-dot"></span>
  آخرین بروزرسانی: {now}
</div>
</body>
</html>"""

if __name__ == "__main__":
    html = generate_html()
    with open("/tmp/weather-site/market.html", "w") as f:
        f.write(html)
    print("Generated: /tmp/weather-site/market.html")
