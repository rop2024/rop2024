"""Shared design system for the profile panels (colors, fonts, text measuring, panel frame).

Pure standard library, so it runs on a stock GitHub Actions runner.
"""
from xml.sax.saxutils import escape as esc

from fonts_data import DISPLAY_B64, MONO_B64, DISPLAY_WIDTHS, MONO_ADVANCE

W = 900

BG, PANEL, LINE = "#0b0b10", "#14141c", "#30303d"
TXT, SOFT, MUT = "#ececf2", "#b4b4c2", "#858594"
CY, YE, PK, PU = "#00f0ff", "#fcee09", "#ff2a6d", "#b026ff"
TRACK = "#252532"


# ------------------------------------------------------------------ text measuring
def width(txt, size, ls=0.0):
    """Width of display-font (Rajdhani Bold) text."""
    return sum(DISPLAY_WIDTHS.get(c, DISPLAY_WIDTHS[" "]) for c in txt) * size + ls * len(txt)


def mw(txt, size, ls=0.0):
    """Width of mono-font (Cascadia Mono) text."""
    return len(txt) * (size * MONO_ADVANCE + ls)


def wrap(txt, size, maxw, ls=0.0):
    lines, cur = [], ""
    for w in txt.split(" "):
        t = (cur + " " + w).strip()
        if width(t, size, ls) > maxw and cur:
            lines.append(cur)
            cur = w
        else:
            cur = t
    lines.append(cur)
    return lines


def fit(txt, size, maxw, ls=0.0):
    while width(txt, size, ls) > maxw and size > 8:
        size -= 0.5
    return size


def trunc(txt, size, maxw, ls=0.0, mono=False):
    """Shorten txt with '...' so it fits maxw."""
    m = mw if mono else width
    if m(txt, size, ls) <= maxw:
        return txt
    while txt and m(txt + "...", size, ls) > maxw:
        txt = txt[:-1]
    return txt.rstrip() + "..."


def k(n):
    """1234 -> 1.2k"""
    n = int(n)
    return f"{n/1000:.1f}k".replace(".0k", "k") if n >= 10000 else f"{n:,}"


# ------------------------------------------------------------------ svg building blocks
FONT_CSS = (
    "@font-face{font-family:'CP Display';font-weight:400 900;src:url(data:font/woff2;base64,%s) format('woff2')}"
    "@font-face{font-family:'CP Mono';font-weight:400;src:url(data:font/woff2;base64,%s) format('woff2')}"
) % (DISPLAY_B64, MONO_B64)

BASE_CSS = """
.m{font-family:'CP Mono','Cascadia Mono','JetBrains Mono',Consolas,monospace}
.s{font-family:'Bahnschrift','CP Display','Rajdhani','Arial Narrow',sans-serif}
@keyframes sh{0%{transform:translateX(-320px)}100%{transform:translateX(920px)}}
.sh{animation:sh 5s linear infinite}
@keyframes bl{0%,100%{opacity:1}50%{opacity:.1}}
.bl{animation:bl 1.1s steps(1) infinite}
@keyframes pu{0%,100%{opacity:1}50%{opacity:.25}}
.pu{animation:pu 2s ease-in-out infinite}
"""


def panel(h, accent, body, extra_css="", defs="", framed=True, w=W):
    """Hero-style panel: gradient fill, accent bar, scanlines, shimmer, cut corner."""
    p = "16,12 %d,12 %d,%d %d,%d 16,%d" % (w - 16, w - 16, h - 28, w - 32, h - 12, h - 12)
    s = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d"><defs>'
         '<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#ffffff" fill-opacity="0.03"/></pattern>'
         '<linearGradient id="shim" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="%s" stop-opacity="0"/><stop offset="0.5" stop-color="%s"/><stop offset="1" stop-color="%s" stop-opacity="0"/></linearGradient>'
         '<linearGradient id="hg" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="#191923"/><stop offset="1" stop-color="#0e1720"/></linearGradient>'
         '<clipPath id="pc"><polygon points="%s"/></clipPath>%s<style>%s%s%s</style></defs>'
         '<rect width="%d" height="%d" fill="%s"/><rect width="%d" height="%d" fill="url(#scan)"/>') % (
         w, h, w, h, accent, accent, accent, p, defs, FONT_CSS, BASE_CSS, extra_css, w, h, BG, w, h)
    if framed:
        s += ('<polygon points="%s" fill="url(#hg)"/><polygon points="%s" fill="url(#scan)"/>'
              '<g clip-path="url(#pc)"><rect x="16" y="12" width="3" height="%d" fill="%s"/>'
              '<rect class="sh" x="0" y="12" width="300" height="2" fill="url(#shim)"/></g>'
              '<polygon points="%s" fill="none" stroke="%s"/>') % (p, p, h - 24, accent, p, LINE)
    return s + body + "</svg>"


def label(text, color, y=40):
    """Top-left section label + pulsing status dot."""
    return ('<text class="m" x="42" y="%d" font-size="10" letter-spacing="2" fill="%s">// %s</text>'
            '<circle class="pu" cx="854" cy="%d" r="3" fill="%s"/>'
            '<text class="m" x="844" y="%d" font-size="9" letter-spacing="1" fill="%s" text-anchor="end">SYS.OK</text>') % (
            y, color, esc(text.upper()), y - 4, color, y, MUT)


def stext(x, y, size, txt, fill, weight=900, ls=1.0, anchor="start", html=None):
    """Display-font text locked to its measured width (no overflow in any fallback font)."""
    tl = width(txt, size, ls)
    ax = {"start": x, "end": x - tl, "middle": x - tl / 2}[anchor]
    return ('<text class="s" x="%.1f" y="%.1f" font-size="%s" font-weight="%d" letter-spacing="%s" fill="%s" '
            'textLength="%.1f" lengthAdjust="spacingAndGlyphs">%s</text>') % (
            ax, y, size, weight, ls, fill, tl, html if html is not None else esc(txt))


def mtext(x, y, size, txt, fill, ls=0.0, anchor="start", extra=""):
    return ('<text class="m" x="%s" y="%s" font-size="%s" letter-spacing="%s" fill="%s" text-anchor="%s"%s>%s</text>') % (
            x, y, size, ls, fill, anchor, (" " + extra) if extra else "", esc(txt))


def pill(x, y, txt, color, size=11, h=26):
    w = int(mw(txt, size) + 24)
    return ('<rect x="%d" y="%d" width="%d" height="%d" fill="%s" stroke="%s" stroke-opacity=".45"/>'
            '<rect x="%d" y="%d" width="2" height="%d" fill="%s"/>'
            '<text class="m" x="%d" y="%d" font-size="%d" fill="%s">%s</text>') % (
            x, y, w, h, BG, color, x, y, h, color, x + 12, y + h // 2 + 4, size, color, esc(txt)), w


def pill_row(items, x, y, maxw, colors, size=11, gap=6, row_h=34):
    out, cx, cy = "", x, y
    for i, it in enumerate(items):
        s, w = pill(cx, cy, it, colors[i % len(colors)], size)
        if cx + w > x + maxw and cx != x:
            cx, cy = x, cy + row_h
            s, w = pill(cx, cy, it, colors[i % len(colors)], size)
        out += s
        cx += w + gap
    return out, cy + 26


def save(path, svg):
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
