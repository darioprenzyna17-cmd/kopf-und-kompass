"""Kopf & Kompass — Story-Karten (1080x1920) im Archivkino-Look.
Zwei Typen:
  teaser  = weist auf den neuen Feed-Beitrag hin (Repost-Logik), mit Hook-Satz
  gedanke = eigenstaendiger kurzer Impuls, laedt zum Antworten ein
Rendert PNG; das Posten macht lib_meta.post_story.
"""
from pathlib import Path

import build_video_reel as bvr

OUT = bvr.HERE / "assets" / "stories"
OUT.mkdir(parents=True, exist_ok=True)
FILMBLACK, SHADOW, PAPER, META, PETROL, FB_RGB = (
    bvr.FILMBLACK, bvr.SHADOW, bvr.PAPER, bvr.META, bvr.PETROL, bvr.FB_RGB)


def _page(inner):
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{bvr._fonts_css()}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{width:1080px;height:1920px;position:relative;font-family:'Fraunces',serif;
  background:radial-gradient(90% 60% at 50% 44%,{SHADOW},{FILMBLACK} 72%);overflow:hidden;}}
.mark{{position:absolute;top:150px;left:0;right:0;text-align:center;font-weight:600;font-size:32px;
  letter-spacing:.30em;text-transform:uppercase;color:rgba(244,239,230,.82);}}
.mid{{position:absolute;left:0;right:0;top:50%;transform:translateY(-50%);text-align:center;padding:0 120px;}}
.label{{font-weight:600;font-size:32px;letter-spacing:.30em;text-transform:uppercase;color:{META};margin-bottom:44px;}}
.label .tick{{display:inline-block;width:24px;height:2px;background:{PETROL};vertical-align:middle;margin-right:16px;margin-bottom:6px;}}
.q div{{font-weight:470;font-size:82px;line-height:1.24;letter-spacing:.01em;color:{PAPER};}}
.q div.acc{{color:{PETROL};font-style:italic;}}
.foot{{position:absolute;left:0;right:0;bottom:220px;text-align:center;font-style:italic;font-weight:440;
  font-size:40px;color:{META};}}
.hair{{position:absolute;left:50%;transform:translateX(-50%);bottom:190px;width:150px;height:2px;background:{PETROL};}}
.handle{{position:absolute;left:0;right:0;bottom:120px;text-align:center;font-weight:500;font-size:30px;
  letter-spacing:.10em;color:#8A7C66;}}
</style></head><body>{inner}</body></html>"""


def _lines_html(text):
    out = []
    for ln in text.split("|"):
        ln = ln.strip()
        if ln.startswith("*"):
            out.append(f'<div class="acc">{ln[1:].strip()}</div>')
        else:
            out.append(f"<div>{ln}</div>")
    return "".join(out)


def story_gedanke(quote, out_png, foot="Antworte mit einem Wort."):
    inner = (f'<div class="mark">Kopf &amp; Kompass</div>'
             f'<div class="mid"><div class="q">{_lines_html(quote)}</div></div>'
             f'<div class="foot">{foot}</div><div class="hair"></div><div class="handle">@kopfundkompass</div>')
    bvr._shoot(_page(inner), str(out_png), transparent=False)
    return out_png


def story_teaser(hookline, out_png, label="Neu im Feed", foot="Ganzer Gedanke im Feed"):
    inner = (f'<div class="mark">Kopf &amp; Kompass</div>'
             f'<div class="mid"><div class="label"><span class="tick"></span>{label}</div>'
             f'<div class="q">{_lines_html(hookline)}</div></div>'
             f'<div class="foot">{foot}  &#8595;</div><div class="hair"></div><div class="handle">@kopfundkompass</div>')
    bvr._shoot(_page(inner), str(out_png), transparent=False)
    return out_png
