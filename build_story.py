"""Kopf & Kompass — Story-Karten (1080x1920) im Marken-Look.
Zwei Typen:
  teaser  = weist auf den neuen Feed-Beitrag hin (Repost-Logik)
  gedanke = eigenstaendige Gedanken-Story (kurzer Impuls, lädt zum Antworten ein)
Rendert PNG; das Posten macht scheduler.py / lib_meta.post_story.
"""
from pathlib import Path

import build_video_reel as bvr

OUT = bvr.HERE / "assets" / "stories"
OUT.mkdir(parents=True, exist_ok=True)
BG, INK, ACC, BG_RGB = bvr.BG, bvr.INK, bvr.ACC, bvr.BG_RGB


def _page(inner):
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{bvr._fonts_css()}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{width:1080px;height:1920px;position:relative;font-family:'Quote',serif;background:{BG};overflow:hidden;}}
.glow{{position:absolute;left:50%;top:44%;transform:translate(-50%,-50%);width:1300px;height:1300px;background:radial-gradient(circle,rgba(216,181,127,.12),rgba({BG_RGB},0) 62%);}}
.mark{{position:absolute;top:150px;left:0;right:0;text-align:center;font-family:'Sans';font-weight:700;font-size:34px;letter-spacing:8px;text-transform:uppercase;color:rgba(244,239,230,.9);}}
.mid{{position:absolute;left:0;right:0;top:50%;transform:translateY(-50%);text-align:center;padding:0 110px;}}
.label{{font-family:'Sans';font-weight:600;font-size:40px;letter-spacing:4px;text-transform:uppercase;color:{ACC};margin-bottom:44px;}}
.q div{{font-weight:600;font-size:88px;line-height:1.16;letter-spacing:-.5px;color:{INK};}}
.q div.acc{{color:{ACC};font-style:italic;}}
.foot{{position:absolute;left:0;right:0;bottom:180px;text-align:center;font-family:'Sans';font-weight:500;font-size:40px;color:rgba(244,239,230,.75);}}
.handle{{position:absolute;left:0;right:0;bottom:110px;text-align:center;font-family:'Sans';font-weight:500;font-size:32px;letter-spacing:.5px;color:rgba(244,239,230,.5);}}
</style></head><body><div class="glow"></div>{inner}</body></html>"""


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
    """quote: Zeilen mit | trennen, Zeile mit * -> Amber-Akzent."""
    inner = (f'<div class="mark">Kopf &amp; Kompass</div>'
             f'<div class="mid"><div class="q">{_lines_html(quote)}</div></div>'
             f'<div class="foot">{foot}</div><div class="handle">@kopfundkompass</div>')
    bvr._shoot(_page(inner), str(out_png), transparent=False)
    return out_png


def story_teaser(hookline, out_png, label="Neu im Feed", foot="Ganzer Gedanke im Feed"):
    inner = (f'<div class="mark">Kopf &amp; Kompass</div>'
             f'<div class="mid"><div class="label">{label}</div>'
             f'<div class="q">{_lines_html(hookline)}</div></div>'
             f'<div class="foot">{foot}  &#8595;</div><div class="handle">@kopfundkompass</div>')
    bvr._shoot(_page(inner), str(out_png), transparent=False)
    return out_png
