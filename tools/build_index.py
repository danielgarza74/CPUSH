#!/usr/bin/env python3
"""Rebuild index.html from the HTML pages in this repository.

Run from anywhere:  python3 tools/build_index.py
Every unit-*/<chapter>/*.html page is picked up automatically; add a new
unit's title and colors to UNITS below when a new unit folder appears.
"""
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# folder -> (label, title, dark color, accent color), in course order.
UNITS = {
    "unit-1-colonies-revolutions-and-constitution": ("Unit 1", "Colonies, Revolutions, and Constitution", "#16413B", "#D2AA4B"),
    "unit-2-an-expanding-nation": ("Unit 2", "An Expanding Nation", "#2D3D1A", "#D26B4B"),
    "unit-3-4-bridge": ("Units 3–4 Bridge", "Constitution to Reconstruction", "#362337", "#A6871D"),
    "unit-3-a-house-divided-and-rebuilt": ("Unit 3", "A House Divided and Rebuilt", "#1B283C", "#D24B54"),
    "unit-4-industry-empire-and-reform": ("Unit 4", "Industry, Empire, and Reform", "#2C1D3A", "#D2A14B"),
    "unit-5-war-prosperity-and-cultural-conflict": ("Unit 5", "War, Prosperity, and Cultural Conflict", "#3E1926", "#4BD2CE"),
    "unit-6-depression-and-world-war": ("Unit 6", "Depression and World War", "#3D291A", "#4B9CD2"),
    "unit-7-the-american-age": ("Unit 7", "The American Age", "#252B31", "#DD7A40"),
}

# filename prefix -> (key, label, short blurb, icon), in display order.
ACTIVITIES = [
    ("interactive-reading", "reading", "Interactive Reading", "Read and annotate the chapter", "📖"),
    ("source-detective", "detective", "Source Detective", "Crack the case with primary sources", "🔍"),
    ("sort-and-defend", "sort", "Sort and Defend", "Sort the evidence, defend your call", "⚖️"),
    ("cause-and-effect-dominos", "dominos", "Cause-and-Effect Dominos", "Line up how one event led to the next", "🔗"),
    ("escape-room", "escape", "Escape Room", "Solve the puzzles to break out", "🔐"),
    ("caption-this", "caption", "Caption This", "Write captions for historical images", "🖼️"),
    ("two-truths-and-a-lie", "truths", "Two Truths and a Lie", "Spot the false statement", "🤔"),
    ("would-you-rather", "rather", "Would You Rather", "Pick a side and explain why", "🧭"),
]

SPANISH_DEFAULT = {"una", "democracia", "destino", "guerra"}


def read(p):
    return p.read_text(encoding="utf-8", errors="replace")


def first(pattern, text):
    m = re.search(pattern, text, re.S)
    return html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""


def chapter_info(folder, pages):
    num = int(folder.name.split("-", 1)[0])
    title, years = "", ""
    for p in pages:
        t = read(p)
        page_title = first(r"<title>(.*?)</title>", t)
        if p.name.startswith("interactive-reading") and not title:
            title = page_title.split(" · ", 1)[-1]
        eyebrow = first(r'class="eyebrow"[^>]*>(.*?)<', t)
        sub = first(r'class="sub"[^>]*>(.*?)<', t)
        for cand in (eyebrow, sub):
            m = re.match(r"(\d{4}\s*[-–]\s*\d{4})", cand)
            if m and not years:
                years = m.group(1).replace("-", "–").replace(" ", "")
    if not title:
        title = folder.name.split("-", 1)[1].replace("-", " ").title()
    return num, title, years


def link_for(p):
    t = read(p)
    rel = p.relative_to(ROOT).as_posix()
    for prefix, key, label, blurb, icon in ACTIVITIES:
        if p.name.startswith(prefix):
            break
    else:
        return None
    page_title = first(r"<title>(.*?)</title>", t)
    note = blurb
    if key in ("detective", "sort"):
        note = page_title.split(" · ", 1)[0] or blurb
    lang = ""
    if key == "reading" and p.parent.parent.name == "unit-3-4-bridge":
        word = p.stem.split("-")[3] if len(p.stem.split("-")) > 3 else ""
        lang = "es" if word in SPANISH_DEFAULT else "en"
    order = [a[1] for a in ACTIVITIES].index(key)
    return dict(href=rel, key=key, label=label, note=note, icon=icon, lang=lang,
                order=(order, 0 if lang != "es" else 1))


def render_link(l):
    label = l["label"]
    badge = ""
    if l["lang"] == "en":
        badge = '<span class="lang">EN · ES · AR</span>'
    elif l["lang"] == "es":
        label = "Lectura interactiva"
        l["note"] = "Abre en español"
        badge = '<span class="lang">ES · EN · AR</span>'
    return (
        f'<li><a class="act" data-kind="{l["key"]}" href="{html.escape(l["href"])}">'
        f'<span class="ico" aria-hidden="true">{l["icon"]}</span>'
        f'<span class="txt"><span class="lbl">{html.escape(label)}{badge}</span>'
        f'<span class="note">{html.escape(l["note"])}</span></span>'
        f'<span class="arrow" aria-hidden="true">→</span></a></li>'
    )


def build():
    units_html, nav_html = [], []
    total_pages = total_chapters = 0
    unit_dirs = [ROOT / name for name in UNITS if (ROOT / name).is_dir()]
    unknown = sorted(d.name for d in ROOT.glob("unit-*") if d.is_dir() and d.name not in UNITS)
    for name in unknown:
        UNITS[name] = (name.replace("-", " ").title(), "", "#2A3340", "#C9A347")
        unit_dirs.append(ROOT / name)

    for udir in unit_dirs:
        label, utitle, dark, accent = UNITS[udir.name]
        is_bridge = "bridge" in udir.name
        chapters = []
        for cdir in sorted((d for d in udir.iterdir() if d.is_dir()), key=lambda d: int(d.name.split("-", 1)[0])):
            pages = sorted(cdir.glob("*.html"))
            if not pages:
                continue
            num, ctitle, years = chapter_info(cdir, pages)
            links = sorted(filter(None, map(link_for, pages)), key=lambda l: l["order"])
            total_pages += len(links)
            total_chapters += 1
            kind = "Bridge Lesson" if is_bridge else "Chapter"
            search = html.escape(f"{label} {utitle} {kind} {num} {ctitle} {years}".lower())
            chapters.append(
                f'<article class="chapter" data-search="{search}">'
                f'<header><span class="num">{num}</span><div>'
                f'<p class="kicker">{kind} {num}{" · " + years if years else ""}</p>'
                f'<h3>{html.escape(ctitle)}</h3></div></header>'
                f'<ul class="acts">{"".join(map(render_link, links))}</ul></article>'
            )
        if not chapters:
            continue
        nums = re.findall(r'class="num">(\d+)<', "".join(chapters))
        span = f"Lessons {nums[0]}–{nums[-1]}" if is_bridge else (
            f"Chapters {nums[0]}–{nums[-1]}" if len(nums) > 1 else f"Chapter {nums[0]}")
        uid = udir.name
        nav_html.append(f'<a href="#{uid}" style="--u:{dark};--ua:{accent}"><b>{html.escape(label)}</b><span>{html.escape(utitle)}</span></a>')
        units_html.append(
            f'<section class="unit{" bridge" if is_bridge else ""}" id="{uid}" style="--u:{dark};--ua:{accent}">'
            f'<div class="unit-head"><p class="eyebrow">{html.escape(label)} · {span}</p>'
            f'<h2>{html.escape(utitle)}</h2>'
            + ('<p class="unit-note">Two-day bridge lessons with trilingual readings (English, Español, العربية).</p>' if is_bridge else "")
            + f'</div><div class="chapters">{"".join(chapters)}</div></section>'
        )

    chips = "".join(
        f'<button type="button" class="chip" data-kind="{key}" aria-pressed="false"><span aria-hidden="true">{icon}</span> {label}</button>'
        for _, key, label, _, icon in ACTIVITIES
    )
    out = TEMPLATE
    for k, v in {
        "{{NAV}}": "".join(nav_html),
        "{{UNITS}}": "".join(units_html),
        "{{CHIPS}}": chips,
        "{{PAGES}}": str(total_pages),
        "{{CHAPTERS}}": str(total_chapters),
        "{{UNITCOUNT}}": str(sum(1 for d in unit_dirs if "bridge" not in d.name)),
    }.items():
        out = out.replace(k, v)
    (ROOT / "index.html").write_text(out, encoding="utf-8")
    print(f"index.html: {total_pages} pages, {total_chapters} chapters/lessons")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CPUSH Course Hub</title>
<meta name="description" content="Every CPUSH interactive reading, source detective, escape room, and review activity, organized by unit and chapter.">
<style>
:root{
  --bg:#F4F1EA;--paper:#FFFFFF;--ink:#1D2430;--dim:#5A6270;--rule:#E2DDD1;
  --hero:#16413B;--hero2:#0F2E2A;--gold:#D2AA4B;--hl:#E1C88E;
  --shadow:0 1px 2px rgba(20,24,32,.06),0 6px 20px rgba(20,24,32,.06);
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#12161C;--paper:#1B2129;--ink:#E8EAEE;--dim:#A3ABB8;--rule:#2C3440;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 6px 20px rgba(0,0,0,.25);
}}
:root[data-theme="dark"]{
  --bg:#12161C;--paper:#1B2129;--ink:#E8EAEE;--dim:#A3ABB8;--rule:#2C3440;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 6px 20px rgba(0,0,0,.25);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:130px}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 "Segoe UI",system-ui,-apple-system,Roboto,Verdana,sans-serif;-webkit-font-smoothing:antialiased}
a{color:inherit}
.wrap{max-width:1180px;margin:0 auto;padding:0 16px}

/* Hero */
.hero{position:relative;overflow:hidden;color:#EBF4F3;background:radial-gradient(900px 420px at 85% -20%,#2B6E63 0%,transparent 60%),linear-gradient(160deg,var(--hero) 0%,var(--hero2) 100%);border-bottom:4px solid var(--gold)}
.hero::after{content:"";position:absolute;inset:0;background:repeating-linear-gradient(90deg,transparent 0 46px,rgba(255,255,255,.025) 46px 47px);pointer-events:none}
.hero .wrap{position:relative;z-index:1;padding-top:56px;padding-bottom:40px}
.hero .eyebrow{color:var(--hl)}
.hero h1{margin:.1em 0 .15em;font-family:Georgia,"Times New Roman",serif;font-weight:700;font-size:clamp(36px,7vw,64px);line-height:1.02;letter-spacing:-.01em}
.hero h1 em{font-style:normal;color:var(--gold)}
.hero p.lede{max-width:640px;margin:0;color:#D4E3E1;font-size:clamp(16px,2.2vw,19px)}
.stats{display:flex;flex-wrap:wrap;gap:12px 28px;margin:26px 0 0;padding:0;list-style:none}
.stats li{display:flex;align-items:baseline;gap:8px;color:#D4E3E1;font-size:14px;letter-spacing:.04em}
.stats b{font-family:Georgia,serif;font-size:30px;color:#fff;letter-spacing:0}
.eyebrow{margin:0;font-size:12px;font-weight:700;letter-spacing:.16em;text-transform:uppercase}

/* Unit nav */
.unit-nav{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:10px;margin:28px 0 0}
.unit-nav a{display:flex;flex-direction:column;gap:2px;padding:12px 14px;border-radius:12px;text-decoration:none;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.16);border-left:4px solid var(--ua);transition:background .15s,transform .15s}
.unit-nav a:hover{background:rgba(255,255,255,.14);transform:translateY(-1px)}
.unit-nav b{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--hl)}
.unit-nav span{font-size:14px;line-height:1.3;color:#fff}

/* Toolbar */
.toolbar{position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--bg) 88%,transparent);-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);border-bottom:1px solid var(--rule)}
.toolbar .wrap{display:grid;grid-template-columns:1fr auto;align-items:center;gap:10px;padding-top:10px;padding-bottom:10px}
.search{position:relative;min-width:0}
.search input{width:100%;padding:10px 14px 10px 38px;border:1px solid var(--rule);border-radius:999px;background:var(--paper);color:var(--ink);font:inherit;font-size:16px}
.search input:focus{outline:2px solid var(--gold);outline-offset:1px}
.search svg{position:absolute;left:13px;top:50%;transform:translateY(-50%);width:16px;height:16px;stroke:var(--dim)}
.chips{grid-column:1/-1;display:flex;gap:6px;overflow-x:auto;scrollbar-width:none;min-width:0;padding:2px;margin:0 -2px}
.chips::-webkit-scrollbar{display:none}
@media (min-width:760px){.chips{flex-wrap:wrap;overflow:visible}}
.chip{flex:none;padding:7px 12px;border-radius:999px;border:1px solid var(--rule);background:var(--paper);color:var(--ink);font:inherit;font-size:13px;font-weight:600;cursor:pointer;white-space:nowrap}
.chip:hover{border-color:var(--gold)}
.chip[aria-pressed="true"]{background:var(--hero);border-color:var(--hero);color:#fff}
.theme{display:grid;place-items:center;width:42px;height:42px;border-radius:50%;border:1px solid var(--rule);background:var(--paper);color:var(--ink);cursor:pointer}
.theme svg{width:18px;height:18px}
.theme:hover{border-color:var(--gold)}

/* Units */
main{padding:28px 0 60px}
.unit{margin:0 0 44px}
.unit-head{position:relative;padding:22px 24px;border-radius:16px;color:#fff;background:linear-gradient(135deg,var(--u) 0%,color-mix(in srgb,var(--u) 75%,#000) 100%);box-shadow:var(--shadow);overflow:hidden}
.unit-head::before{content:"";position:absolute;left:0;top:0;bottom:0;width:6px;background:var(--ua)}
.unit-head .eyebrow{color:var(--ua);filter:brightness(1.15)}
.unit-head h2{margin:.15em 0 0;font-family:Georgia,"Times New Roman",serif;font-size:clamp(24px,4vw,34px);line-height:1.15}
.unit-note{margin:.4em 0 0;color:rgba(255,255,255,.8);font-size:14px}
.chapters{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:16px;margin-top:16px}
.chapter{background:var(--paper);border:1px solid var(--rule);border-radius:14px;box-shadow:var(--shadow);overflow:hidden;display:flex;flex-direction:column}
.chapter>header{display:flex;gap:14px;align-items:center;padding:16px 18px 14px;border-bottom:1px solid var(--rule);border-top:3px solid var(--ua)}
.num{flex:none;display:grid;place-items:center;width:44px;height:44px;border-radius:50%;background:var(--u);color:#fff;font-family:Georgia,serif;font-weight:700;font-size:20px;box-shadow:inset 0 0 0 2px var(--ua)}
.kicker{margin:0;font-size:11px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--dim)}
.chapter h3{margin:.1em 0 0;font-size:18px;line-height:1.25}
.acts{list-style:none;margin:0;padding:6px}
.act{display:flex;align-items:center;gap:12px;padding:9px 12px;border-radius:10px;text-decoration:none;transition:background .12s}
.act:hover,.act:focus-visible{background:color-mix(in srgb,var(--ua) 13%,transparent);outline:none}
.act:focus-visible{box-shadow:inset 0 0 0 2px var(--ua)}
.ico{flex:none;display:grid;place-items:center;width:34px;height:34px;border-radius:9px;background:color-mix(in srgb,var(--u) 9%,var(--paper));border:1px solid var(--rule);font-size:17px}
.txt{flex:1;min-width:0;display:flex;flex-direction:column}
.lbl{font-weight:600;font-size:15px;line-height:1.25;display:flex;flex-wrap:wrap;align-items:center;gap:6px}
.note{color:var(--dim);font-size:13px;line-height:1.3}
.lang{font-size:10px;font-weight:700;letter-spacing:.08em;padding:2px 6px;border-radius:5px;background:color-mix(in srgb,var(--ua) 20%,transparent);color:var(--ink)}
.arrow{flex:none;color:var(--dim);opacity:0;transform:translateX(-4px);transition:.15s}
.act:hover .arrow,.act:focus-visible .arrow{opacity:1;transform:none}
.act[data-kind="reading"] .ico{background:var(--u);border-color:var(--u)}
.hidden{display:none!important}
.empty{text-align:center;color:var(--dim);padding:40px 0}
footer{border-top:1px solid var(--rule);color:var(--dim);font-size:13px;padding:20px 0 40px}
@media (max-width:420px){.chapters{grid-template-columns:1fr}.unit-head{padding:18px}}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}*{transition:none!important}}
</style>
</head>
<body>
<header class="hero">
  <div class="wrap">
    <p class="eyebrow">CPUSH · United States History</p>
    <h1>Course <em>Hub</em></h1>
    <p class="lede">Every interactive reading, source investigation, and review game for the course, organized by unit and chapter. Pick a unit to jump in.</p>
    <ul class="stats">
      <li><b>{{UNITCOUNT}}</b> units</li>
      <li><b>{{CHAPTERS}}</b> chapters &amp; lessons</li>
      <li><b>{{PAGES}}</b> activities</li>
    </ul>
    <nav class="unit-nav" aria-label="Units">{{NAV}}</nav>
  </div>
</header>

<div class="toolbar">
  <div class="wrap">
    <label class="search">
      <svg viewBox="0 0 24 24" fill="none" stroke-width="2.2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
      <input id="q" type="search" placeholder="Search chapters, topics, or years…" aria-label="Search chapters">
    </label>
    <button type="button" class="theme" id="theme" aria-label="Toggle dark mode" title="Toggle dark mode"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg></button>
    <div class="chips" role="group" aria-label="Filter by activity">{{CHIPS}}</div>
  </div>
</div>

<main class="wrap">
  {{UNITS}}
  <p class="empty hidden" id="empty">No chapters match that search.</p>
</main>

<footer>
  <div class="wrap">CPUSH · United States History · Course Hub</div>
</footer>

<script>
(function(){
  var q=document.getElementById('q'),chips=[].slice.call(document.querySelectorAll('.chip')),kind=null;
  function apply(){
    var term=q.value.trim().toLowerCase(),anyShown=false;
    document.querySelectorAll('.unit').forEach(function(u){
      var unitShown=false;
      u.querySelectorAll('.chapter').forEach(function(c){
        var matchText=!term||c.getAttribute('data-search').indexOf(term)>-1||c.textContent.toLowerCase().indexOf(term)>-1;
        var acts=c.querySelectorAll('.act'),visible=0;
        acts.forEach(function(a){var ok=!kind||a.getAttribute('data-kind')===kind;a.parentNode.classList.toggle('hidden',!ok);if(ok)visible++;});
        var show=matchText&&visible>0;c.classList.toggle('hidden',!show);if(show)unitShown=true;
      });
      u.classList.toggle('hidden',!unitShown);if(unitShown)anyShown=true;
    });
    document.getElementById('empty').classList.toggle('hidden',anyShown);
  }
  q.addEventListener('input',apply);
  chips.forEach(function(ch){ch.addEventListener('click',function(){
    var k=ch.getAttribute('data-kind');kind=(kind===k)?null:k;
    chips.forEach(function(c){c.setAttribute('aria-pressed',String(c.getAttribute('data-kind')===kind));});apply();
  });});
  var root=document.documentElement,btn=document.getElementById('theme'),bar=document.querySelector('.toolbar');
  function pad(){root.style.scrollPaddingTop=(bar.offsetHeight+16)+'px';}
  pad();addEventListener('resize',pad);
  try{var saved=localStorage.getItem('cpush-hub-theme');if(saved)root.setAttribute('data-theme',saved);}catch(e){}
  btn.addEventListener('click',function(){
    var cur=root.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
    var next=cur==='dark'?'light':'dark';root.setAttribute('data-theme',next);
    try{localStorage.setItem('cpush-hub-theme',next);}catch(e){}
  });
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    build()
