#!/usr/bin/env python3
"""qaemshahr_weather_pro.py — Professional weather HTML for Qaemshahr"""
import json, urllib.request, pathlib
from datetime import datetime, date

LAT, LON = 36.4631, 52.8604
URL = (
    f"https://api.open-meteo.com/v1/forecast?"
    f"latitude={LAT}&longitude={LON}"
    f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weathercode,windspeed_10m,winddirection_10m,pressure_msl"
    f"&hourly=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation_probability,precipitation,weathercode,windspeed_10m"
    f"&timezone=Asia/Tehran&forecast_days=7"
    f"&models=ecmwf_ifs025"
)

WMO = {
    0:("آفتابی","☀️","linear-gradient(135deg,#f59e0b,#f97316)"),
    1:("غالباً آفتابی","🌤️","linear-gradient(135deg,#fbbf24,#f97316)"),
    2:("نیمه ابری","⛅","linear-gradient(135deg,#94a3b8,#64748b)"),
    3:("ابری","☁️","linear-gradient(135deg,#6b7280,#4b5563)"),
    45:("مه‌آلود","🌫️","linear-gradient(135deg,#9ca3af,#6b7280)"),
    48:("مه یخ‌زده","🌫️","linear-gradient(135deg,#9ca3af,#6b7280)"),
    51:("باران خفیف","🌦️","linear-gradient(135deg,#3b82f6,#60a5fa)"),
    53:("باران متوسط","🌧️","linear-gradient(135deg,#2563eb,#3b82f6)"),
    55:("باران شدید","🌧️","linear-gradient(135deg,#1e40af,#2563eb)"),
    61:("باران سبک","🌧️","linear-gradient(135deg,#3b82f6,#60a5fa)"),
    63:("باران متوسط","🌧️","linear-gradient(135deg,#2563eb,#3b82f6)"),
    65:("باران شدید","🌧️","linear-gradient(135deg,#1e40af,#1d4ed8)"),
    71:("برف سبک","🌨️","linear-gradient(135deg,#cbd5e1,#94a3b8)"),
    80:("رگبار","🌦️","linear-gradient(135deg,#3b82f6,#818cf8)"),
    81:("رگبار","🌧️","linear-gradient(135deg,#2563eb,#3b82f6)"),
    82:("رگبار شدید","⛈️","linear-gradient(135deg,#7c3aed,#6d28d9)"),
    95:("رعد و برق","⛈️","linear-gradient(135deg,#7c3aed,#4c1d95)"),
}
DNAMES={"Saturday":"شنبه","Sunday":"یکشنبه","Monday":"دوشنبه","Tuesday":"سه‌شنبه","Wednesday":"چهارشنبه","Thursday":"پنجشنبه","Friday":"جمعه"}
MNAMES={1:"ژانویه",2:"فوریه",3:"مارس",4:"آوریه",5:"مه",6:"ژوئن",7:"ژوئیه",8:"اوت",9:"سپتامبر",10:"اکتبر",11:"نوامبر",12:"دسامبر"}
PD=str.maketrans("0123456789","۰۱۲۳۴۵۶۷۸۹")

def pn(s): return str(s).translate(PD)
def wmo(code): return WMO.get(code,("نامشخص","❓","linear-gradient(135deg,#374151,#1f2937)"))
def uv_emoji(t):
    if t>=35: return "🔥"
    if t>=28: return "☀️"
    if t>=20: return "🌤️"
    if t>=12: return "🍂"
    return "❄️"
def hlabel(h):
    if h==0: return "۱۲ بامداد"
    if h<12: return f"{h} صبح"
    if h==12: return "۱۲ ظهر"
    if h<18: return f"{h-12} بعدازظهر"
    if h<21: return f"{h-12} عصر"
    return f"{h-12} شب"

# fetch
req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0"})
data=json.loads(urllib.request.urlopen(req,timeout=20).read())
cur=data["current"]
hrl=data["hourly"]

# group days
days={}
for i,t in enumerate(hrl["time"]):
    d=datetime.fromisoformat(t).date()
    days.setdefault(d,[]).append(i)

# --- build hero ---
cd,ci,cg=wmo(cur["weathercode"])
hero=f"""<div class="hero" style="background:{cg}">
<div class="hero-loc">📍 قائمشهر، مازندران</div>
<div class="hero-icon">{ci}</div>
<div class="hero-temp">{pn(int(cur['temperature_2m']))}<sup>°C</sup></div>
<div class="hero-desc">{cd} — احساس {pn(int(cur['apparent_temperature']))}°</div>
<div class="hero-details">
<div class="hd"><span class="hd-l">💧 رطوبت</span><span class="hd-v">{pn(int(cur['relative_humidity_2m']))}%</span></div>
<div class="hd"><span class="hd-l">🌬️ باد</span><span class="hd-v">{pn(int(cur['windspeed_10m']))} km/h</span></div>
<div class="hd"><span class="hd-l">🌡️ فشار</span><span class="hd-v">{pn(int(cur.get('pressure_msl',0)))} hPa</span></div>
<div class="hd"><span class="hd-l">{uv_emoji(cur['temperature_2m'])} احساس</span><span class="hd-v">{pn(int(cur['apparent_temperature']))}°</span></div>
</div></div>"""

# --- temp chart (SVG) ---
temps24=[hrl["temperature_2m"][i] for i in range(min(24,len(hrl["time"])))]
labels24=[datetime.fromisoformat(hrl["time"][i]).hour for i in range(min(24,len(hrl["time"])))]
CW,CH=560,150;PL,PR,PT,PB=30,10,25,28
pw=CW-PL-PR;ph=CH-PT-PB
tmin=min(temps24)-2;tmax=max(temps24)+2;tr=tmax-tmin or 1
def tx(i): return PL+(i/max(len(temps24)-1,1))*pw
def ty(v): return PT+ph-((v-tmin)/tr)*ph

pts=" ".join([f"{tx(i):.1f},{ty(t):.1f}" for i,t in enumerate(temps24)])
area=f"{tx(0):.1f},{PT+ph} "+pts+f" {tx(len(temps24)-1):.1f},{PT+ph}"
gridlines=""
ylabels=""
xlabels=""
for i in range(5):
    v=tmin+(tr*i/4)
    yy=ty(v)
    gridlines+=f'<line x1="{PL}" y1="{yy:.1f}" x2="{CW-PR}" y2="{yy:.1f}" stroke="rgba(255,255,255,0.06)" stroke-dasharray="4,4"/>'
    ylabels+=f'<text x="{PL-5}" y="{yy+4:.1f}" fill="#64748b" font-size="9" text-anchor="end" font-family="monospace">{v:.0f}°</text>'
dots=""
dots_vals=""
for i,t in enumerate(temps24):
    dots+=f'<circle cx="{tx(i):.1f}" cy="{ty(t):.1f}" r="2.5" fill="#fbbf24" stroke="#0f172a" stroke-width="1.5"/>'
    if i%4==0:
        xlabels+=f'<text x="{tx(i):.1f}" y="{CH-6}" fill="#475569" font-size="8" text-anchor="middle" font-family="monospace">{labels24[i]:02d}:00</text>'
    if i%3==0:
        dots_vals+=f'<text x="{tx(i):.1f}" y="{ty(t)-8:.1f}" fill="#fbbf24" font-size="8" text-anchor="middle" font-weight="600">{t:.0f}°</text>'

chart_svg=f"""<div class="chart-box scroll-x"><svg viewBox="0 0 {CW} {CH}" style="width:100%;height:auto;display:block;">
<defs><linearGradient id="tg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#fbbf24" stop-opacity="0.3"/><stop offset="100%" stop-color="#fbbf24" stop-opacity="0"/></linearGradient>
<filter id="gl"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
{gridlines}{ylabels}
<polygon points="{area}" fill="url(#tg)"/>
<polyline points="{pts}" fill="none" stroke="#fbbf24" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" filter="url(#gl)"/>
{dots}{dots_vals}{xlabels}
</svg></div>"""

# --- precip bars ---
pop_bars=""
for i in range(min(18,len(hrl["time"]))):
    h=datetime.fromisoformat(hrl["time"][i]).hour
    p=hrl["precipitation_probability"][i]
    bc="#3b82f6" if p>50 else "#818cf8" if p>20 else "#334155"
    pop_bars+=f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:5px;"><span style="width:30px;font-size:0.65rem;color:#94a3b8;text-align:left;font-family:monospace;">{h:02d}</span><div style="flex:1;height:7px;background:#1e293b;border-radius:4px;overflow:hidden;"><div style="width:{p}%;height:100%;background:{bc};border-radius:4px;"></div></div><span style="width:28px;font-size:0.65rem;color:{bc};text-align:right;font-weight:600;">{p}%</span></div>'

# --- day cards ---
today_str=date.today().isoformat()
dhtml=""
for idx,(d,indices) in enumerate(days.items()):
    dt0=datetime.combine(d,datetime.min.time())
    dow=DNAMES.get(dt0.strftime("%A"),"")
    m=MNAMES.get(d.month,"")
    temps=[hrl["temperature_2m"][i] for i in indices]
    mn,mx=min(temps),max(temps)
    mp=max([hrl["precipitation_probability"][i] for i in indices])
    ah=sum([hrl["relative_humidity_2m"][i] for i in indices])/len(indices)
    di,dicon,dgrad=wmo(hrl["weathercode"][indices[len(indices)//2]])
    tag='<span class="tag-today">امروز</span>' if d.isoformat()==today_str else ('<span class="tag-sub">فردا</span>' if idx==1 else '')
    vis="open" if idx==0 else ""
    
    # mini bars
    mbar=""
    for i in indices:
        hr=datetime.fromisoformat(hrl["time"][i]).hour
        t=hrl["temperature_2m"][i]
        n=(t-mn)/(mx-mn+0.1)
        bh=max(n*45,4)
        bc2="#fbbf24" if 8<=hr<=18 else "#60a5fa"
        mbar+=f'<div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;gap:1px;"><div style="font-size:0.5rem;color:#94a3b8;">{t:.0f}</div><div style="width:100%;max-width:10px;height:{bh:.0f}px;background:{bc2};border-radius:2px;"></div><div style="font-size:0.45rem;color:#475569;">{hr}</div></div>'

    # Daily summary report
    rain_hours = [i for i in indices if hrl["precipitation_probability"][i] > 30]
    hot_hours = [i for i in indices if hrl["temperature_2m"][i] > 30]
    cold_hours = [i for i in indices if hrl["temperature_2m"][i] < 15]
    windy_hours = [i for i in indices if hrl["windspeed_10m"][i] > 20]
    
    summary_parts = []
    
    # Temperature summary
    summary_parts.append(f"🌡️ دما بین {pn(int(mn))}° تا {pn(int(mx))}° در نوسانه")
    
    # Rain summary
    if rain_hours:
        rain_start = datetime.fromisoformat(hrl["time"][rain_hours[0]]).hour
        rain_end = datetime.fromisoformat(hrl["time"][rain_hours[-1]]).hour
        if rain_start == rain_end:
            summary_parts.append(f"🌧️ احتمال بارش در ساعت {pn(rain_start)}")
        else:
            summary_parts.append(f"🌧️ احتمال بارش از ساعت {pn(rain_start)} تا {pn(rain_end)}")
    else:
        summary_parts.append("☀️ بدون احتمال بارش")
    
    # Wind summary
    if windy_hours:
        max_wind = max([hrl["windspeed_10m"][i] for i in windy_hours])
        summary_parts.append(f"🌬️ باد تا {pn(int(max_wind))} km/h")
    else:
        summary_parts.append("🍃 هوای آرام")
    
    # Best time to go out
    good_hours = [i for i in indices if 6 <= datetime.fromisoformat(hrl["time"][i]).hour <= 18 
                  and hrl["precipitation_probability"][i] < 20 
                  and 18 <= hrl["temperature_2m"][i] <= 28]
    if good_hours:
        best_start = datetime.fromisoformat(hrl["time"][good_hours[0]]).hour
        best_end = datetime.fromisoformat(hrl["time"][good_hours[-1]]).hour
        summary_parts.append(f"✅ بهترین زمان بیرون رفتن: {pn(best_start)} تا {pn(best_end)}")
    
    summary_text = " • ".join(summary_parts)
    
    # hourly table rows
    rows=""
    for i in indices:
        dt=datetime.fromisoformat(hrl["time"][i])
        hr=dt.hour;rc="day-row" if 6<=hr<=19 else "night-row"
        t=hrl["temperature_2m"][i];fl=hrl["apparent_temperature"][i]
        hu=hrl["relative_humidity_2m"][i];pp=hrl["precipitation_probability"][i]
        wc=hrl["weathercode"][i];wi=hrl["windspeed_10m"][i]
        wd,wi2,_=wmo(wc)
        rows+=f'<tr class="{rc}"><td class="tc-time">{hr:02d}:00 <span class="tc-lbl">{hlabel(hr)}</span></td><td class="tc-desc">{wi2} {wd}</td><td class="tc-temp">{pn(int(t))}°</td><td class="tc-feels">{pn(int(fl))}°</td><td class="tc-humid">{pn(int(hu))}%</td><td class="tc-pop">{pn(int(pp))}%</td><td class="tc-wind">{pn(int(wi))} km/h</td></tr>'

    dhtml+=f"""<div class="day-card"><details {vis}><summary>
<div class="d-icon">{dicon}</div>
<div class="d-info"><div class="d-title">{dow} <small>{pn(d.day)} {m}</small> {tag}</div><div class="d-desc">{di}</div></div>
<div class="d-stats"><div class="d-trange"><span class="t-hi">{pn(int(mx))}°</span><span class="t-sep">/</span><span class="t-lo">{pn(int(mn))}°</span></div>
<div class="d-meta">{"<span>☔ "+pn(int(mp))+"%</span>" if mp>10 else ""}<span>💧{pn(int(ah))}%</span></div></div>
<div class="d-arrow">‹</div>
</summary>
<div class="h-panel">
<div class="p-sec"><div class="p-title">📊 دمای ساعتی</div><div class="mini-chart">{mbar}</div></div>
<div class="p-sec"><div class="p-title">📋 جزئیات ساعتی</div><div class="scroll-x"><table class="htbl">
<thead><tr><th>ساعت</th><th>وضعیت</th><th>دما</th><th>احساس</th><th>رطوبت</th><th>بارش</th><th>باد</th></tr></thead>
<tbody>{rows}</tbody></table></div></div>
<div class="p-sec summary-box"><div class="p-title">📝 خلاصه وضعیت {dow}</div><div class="summary-text">{summary_text}</div></div>
</div></details></div>"""

# --- assemble ---
now=datetime.now().strftime('%Y/%m/%d %H:%M')
full=f"""<!DOCTYPE html><html lang="fa" dir="rtl"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>آب و هوای قائمشهر</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
@keyframes fadeUp{{from{{opacity:0;transform:translateY(12px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.6}}}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',-apple-system,BlinkMacSystemFont,Vazirmatn,sans-serif;background:#080c18;color:#e2e8f0;min-height:100vh;overflow-x:hidden}}
.hero{{padding:28px 20px 36px;text-align:center;position:relative;overflow:hidden}}
.hero::before{{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:radial-gradient(circle,rgba(255,255,255,.05) 0%,transparent 60%);animation:pulse 4s ease-in-out infinite}}
.hero-loc{{font-size:.75rem;color:rgba(255,255,255,.7);letter-spacing:2px;text-transform:uppercase;margin-bottom:6px;position:relative}}
.hero-icon{{font-size:4.2rem;line-height:1;margin:6px 0;filter:drop-shadow(0 4px 12px rgba(0,0,0,.3));position:relative}}
.hero-temp{{font-size:4.8rem;font-weight:900;color:#fff;text-shadow:0 2px 20px rgba(0,0,0,.3);line-height:1;margin:4px 0;position:relative}}
.hero-temp sup{{font-size:1.8rem;font-weight:700}}
.hero-desc{{font-size:1.05rem;color:rgba(255,255,255,.85);font-weight:600;margin-bottom:14px;position:relative}}
.hero-details{{display:flex;justify-content:center;gap:20px;flex-wrap:wrap;position:relative}}
.hd{{display:flex;flex-direction:column;align-items:center;gap:2px}}
.hd-l{{font-size:.6rem;color:rgba(255,255,255,.5)}}
.hd-v{{font-size:.85rem;font-weight:700;color:#fff}}
.chart-section{{padding:16px 14px 0}}
.chart-section h3,.pop-section h3{{font-size:.8rem;color:#64748b;margin-bottom:8px;font-weight:600}}
.chart-box,.pop-box{{background:#111827;border-radius:16px;padding:14px 8px 8px;border:1px solid rgba(255,255,255,.05)}}
.pop-section{{padding:16px 14px 0}}
.pop-box{{padding:14px}}
.days-container{{padding:16px 10px;display:flex;flex-direction:column;gap:10px}}
.day-card{{background:#111827;border-radius:16px;overflow:hidden;border:1px solid rgba(255,255,255,.06);animation:fadeUp .4s ease;transition:transform .2s}}
.day-card:active{{transform:scale(.99)}}
details{{width:100%}}
details[open]{{background:#0d1220}}
summary{{padding:14px;cursor:pointer;list-style:none;display:flex;align-items:center;gap:10px;-webkit-user-select:none;user-select:none}}
summary::-webkit-details-marker{{display:none}}
.d-icon{{font-size:1.8rem;flex-shrink:0}}
.d-info{{flex:1;min-width:0}}
.d-title{{font-weight:700;font-size:.9rem;color:#f1f5f9}}
.d-title small{{font-weight:400;color:#64748b;font-size:.7rem}}
.d-desc{{font-size:.7rem;color:#94a3b8;margin-top:1px}}
.d-stats{{text-align:left;flex-shrink:0}}
.d-trange{{display:flex;align-items:center;gap:6px}}
.t-hi{{font-size:.95rem;font-weight:800;color:#fbbf24}}
.t-lo{{font-size:.85rem;font-weight:600;color:#64748b}}
.t-sep{{color:#475569;font-size:.8rem}}
.d-meta{{display:flex;gap:6px;margin-top:3px;justify-content:flex-end}}
.d-meta span{{font-size:.6rem;color:#60a5fa;background:rgba(96,165,250,.1);padding:1px 5px;border-radius:4px}}
.tag-today{{background:linear-gradient(135deg,#0284c7,#0ea5e9);color:#fff;font-size:.55rem;padding:2px 7px;border-radius:5px;font-weight:700;margin-right:5px;vertical-align:middle}}
.tag-sub{{background:#1e293b;color:#94a3b8;font-size:.55rem;padding:2px 7px;border-radius:5px;font-weight:600;margin-right:5px;vertical-align:middle;border:1px solid rgba(255,255,255,.08)}}
.d-arrow{{font-size:1.3rem;color:#475569;transition:transform .3s;flex-shrink:0;font-weight:300}}
details[open] .d-arrow{{transform:rotate(90deg);color:#38bdf8}}
.h-panel{{padding:0 14px 14px;border-top:1px solid rgba(255,255,255,.06)}}
.p-sec{{margin-top:14px}}
.p-title{{font-size:.7rem;color:#64748b;font-weight:600;margin-bottom:8px}}
.mini-chart{{display:flex;gap:1px;height:65px;align-items:flex-end;padding:0 4px}}
.htbl{{width:100%;min-width:520px;border-collapse:collapse;font-size:.75rem}}
.htbl th{{padding:7px 5px;color:#475569;font-weight:600;font-size:.6rem;text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid rgba(255,255,255,.08);text-align:center}}
.htbl td{{padding:8px 5px;text-align:center;border-bottom:1px solid rgba(255,255,255,.04)}}
.tc-time{{font-weight:700;color:#e2e8f0;direction:ltr}}
.tc-lbl{{display:block;font-size:.55rem;color:#475569;font-weight:400;margin-top:1px}}
.tc-desc{{color:#94a3b8}}
.tc-temp{{font-weight:800;color:#fbbf24;font-size:.85rem}}
.tc-feels{{color:#94a3b8}}
.tc-humid{{color:#60a5fa}}
.tc-pop{{color:#a78bfa}}
.tc-wind{{color:#34d399}}
.day-row{{background:rgba(255,255,255,.02)}}
.night-row{{background:rgba(15,23,42,.5)}}
.summary-box{{background:linear-gradient(135deg,rgba(59,130,246,.08),rgba(139,92,246,.08));border-radius:12px;padding:14px;margin-top:12px;border:1px solid rgba(99,102,241,.15)}}
.summary-text{{font-size:.8rem;color:#e2e8f0;line-height:1.8;direction:rtl}}
.hint-bar{{text-align:center;padding:10px;color:#475569;font-size:.7rem}}
.footer{{text-align:center;padding:20px 14px 36px;color:#334155;font-size:.65rem}}
.scroll-x{{overflow-x:auto;-webkit-overflow-scrolling:touch}}
.scroll-x::-webkit-scrollbar{{height:3px}}
.scroll-x::-webkit-scrollbar-thumb{{background:#334155;border-radius:4px}}
</style></head><body>
{hero}
<div class="chart-section"><h3>📈 نمودار دمای ۲۴ ساعت آینده</h3>{chart_svg}</div>
<div class="pop-section"><h3>🌧️ احتمال بارش ۱۸ ساعت آینده</h3><div class="pop-box">{pop_bars}</div></div>
<div class="hint-bar">👇 روز مورد نظر رو لمس کن تا جزئیات ساعتی باز بشه</div>
<div class="days-container">{dhtml}</div>
<div class="footer">داده‌ها از <a href="https://open-meteo.com" style="color:#475569">Open-Meteo</a> • بروزرسانی: {now} • ساخته شده با ❤️</div>
</body></html>"""

pathlib.Path("/tmp/qshahr_weather_pro.html").write_text(full,encoding="utf-8")
print("MEDIA:/tmp/qshahr_weather_pro.html")
