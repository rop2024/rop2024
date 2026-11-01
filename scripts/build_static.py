"""Builds the hand-written panels: project cards, section headers, contact terminal, footer.

Edit the PROJECTS list / CONTACT block below, then run:  python scripts/build_static.py
"""
import os

from cyber import *  # noqa: F401,F403

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
os.makedirs(OUT, exist_ok=True)

# ----------------------------------------------------------------------------- content
PROJECTS = [
    {
        "tag": "PROJECT / 01", "name": "PROMPTLY", "kind": "REFLECTIVE WRITING PLATFORM", "color": CY,
        "desc": "A calm writing space built around deliberate pauses: daily prompts, streak tracking "
                "and a distraction-free editor.",
        "tech": ["React", "Node.js", "MongoDB"],
        "url": "https://github.com/rop2024/Promptly", "file": "project-1.svg",
    },
    {
        "tag": "PROJECT / 02", "name": "TASKLYTICS", "kind": "TASK + PRODUCTIVITY APP", "color": PK,
        "desc": "Full-stack task manager with color-coded groups, drag-and-drop, a calendar view "
                "and productivity analytics.",
        "tech": ["React", "Express", "MongoDB"],
        "url": "https://github.com/rop2024/Tasklytics", "file": "project-2.svg",
    },
    {
        "tag": "PROJECT / 03", "name": "BOOKMARK CLUSTERING", "kind": "AI BOOKMARK ORGANIZER", "color": PU,
        "desc": "Turns a messy browser bookmark export into organized folders, using Gemini to "
                "categorize and tag every link.",
        "tech": ["Python", "Streamlit", "Gemini"],
        "url": "https://github.com/rop2024/bookmark-clustering", "file": "project-3.svg",
    },
]

# Email is left out on purpose: a public README is scraped. Put one here to show it in the terminal.
EMAIL = ""

CONTACT = [
    ("github", "github.com/rop2024"),
    ("linkedin", "linkedin.com/in/rohitpandey08"),
    ("artstation", "artstation.com/rohit_pandey_0"),
    ("discord", "discord.com/users/1387348547308883968"),
    ("monkeytype", "monkeytype.com/profile/__Rohit__"),
]


# ----------------------------------------------------------------------------- panels
def project_card(p):
    cw, ch = 300, 322
    c = p["color"]
    x0, cwid = 36, 228
    b = mtext(x0, 44, 9, p["tag"], MUT, ls=2)
    b += '<circle class="pu" cx="%d" cy="41" r="3" fill="%s"/>' % (x0 + cwid - 3, c)
    y = 80
    size = fit(p["name"], 30, cwid, 1.5)
    b += stext(x0, y, size, p["name"], c, ls=1.5)
    y += 20
    b += mtext(x0, y, 9, p["kind"], SOFT, ls=1)
    y += 14
    b += '<line x1="%d" x2="%d" y1="%d" y2="%d" stroke="%s"/>' % (x0, x0 + cwid, y, y, LINE)
    y += 26
    for ln in wrap(p["desc"], 14, cwid - 6, .3)[:5]:
        b += stext(x0, y, 14, ln, SOFT, weight=500, ls=.3)
        y += 21
    row, _ = pill_row(p["tech"], x0, ch - 106, cwid, [c], size=10, gap=6, row_h=32)
    b += row
    by = ch - 62
    b += ('<rect x="%d" y="%d" width="118" height="24" fill="%s" stroke="%s" stroke-opacity=".7"/>'
          '<rect x="%d" y="%d" width="2" height="24" fill="%s"/>') % (x0, by, BG, c, x0, by, c)
    b += mtext(x0 + 14, by + 16, 10, "VIEW REPO", c, ls=1.5)
    b += '<text class="m bl" x="%d" y="%d" font-size="11" fill="%s" text-anchor="end">&gt;</text>' % (x0 + 106, by + 16, c)
    return panel(ch, c, b, w=cw)


def section_header(fname, text, color):
    save(os.path.join(OUT, fname), panel(64, color, label(text, color, y=42)))


def contact_terminal():
    lines = []  # (html, delay)
    P = "rop2024@profile"
    lines.append('<tspan fill="%s">%s</tspan><tspan fill="%s">:~$</tspan> <tspan fill="%s">contact --open</tspan>' % (PK, P, MUT, TXT))
    lines.append('<tspan fill="%s">[ok]</tspan> <tspan fill="%s">channel open // full-stack roles + ML / AI roles</tspan>' % (CY, SOFT))
    lines.append('<tspan fill="%s">[ok]</tspan> <tspan fill="%s">location // Ranchi, India</tspan>' % (CY, SOFT))
    lines.append("")
    rows = list(CONTACT)
    if EMAIL:
        rows.insert(0, ("email", EMAIL))
    cols = [CY, PK, PU, YE, CY, PK]
    for i, (key, val) in enumerate(rows):
        lines.append('<tspan fill="%s">%s</tspan><tspan fill="%s"> -&gt; </tspan><tspan fill="%s">%s</tspan>' % (
            cols[i % len(cols)], esc(key.ljust(11)).replace(" ", " "), MUT, TXT, esc(val)))
    lines.append("")
    lines.append('<tspan fill="%s">%s</tspan><tspan fill="%s">:~$</tspan> <tspan class="bl" fill="%s">_</tspan>' % (PK, P, MUT, CY))

    x0, y0, lh = 56, 92, 24
    n = len(lines)
    cycle = 16.0
    css = ""
    body = ('<circle cx="48" cy="38" r="4" fill="%s"/><circle cx="64" cy="38" r="4" fill="%s"/><circle cx="80" cy="38" r="4" fill="%s"/>'
            '<line x1="32" x2="868" y1="56" y2="56" stroke="%s"/>'
            '<circle class="pu" cx="854" cy="36" r="3" fill="%s"/>') % (PK, YE, CY, LINE, CY)
    body += mtext(450, 42, 10, "09 / CONTACT  //  rop2024@profile: ~", MUT, ls=1.5, anchor="middle")
    for i, html in enumerate(lines):
        if not html:
            continue
        t0 = 0.5 + 0.42 * i
        a = round(t0 / cycle * 100, 3)
        css += "@keyframes l%d{0%%{opacity:0}%s%%{opacity:1}97%%{opacity:1}100%%{opacity:0}}.l%d{opacity:0;animation:l%d %ss infinite steps(1)}\n" % (i, a, i, i, cycle)
        body += '<text class="m l%d" x="%d" y="%d" font-size="13" fill="%s" xml:space="preserve">%s</text>' % (i, x0, y0 + i * lh, TXT, html)
    h = y0 + n * lh + 30
    svg = panel(h, CY, body, extra_css=css)
    save(os.path.join(OUT, "contact.svg"), svg)


def footer():
    b = ('<line x1="42" x2="858" y1="26" y2="26" stroke="%s"/>' % LINE
         + mtext(42, 54, 9, "ROP2024 / PERSONAL KNOWLEDGE BASE", MUT, ls=1)
         + mtext(858, 54, 9, "PROFILE_V2.0", MUT, ls=1, anchor="end")
         + '<text class="m" x="450" y="54" font-size="9" letter-spacing="2" fill="%s" text-anchor="middle">// END OF TRANSMISSION<tspan class="bl"> _</tspan></text>' % CY)
    save(os.path.join(OUT, "footer.svg"), panel(80, CY, b, framed=False))


if __name__ == "__main__":
    for p in PROJECTS:
        save(os.path.join(OUT, p["file"]), project_card(p))
    section_header("projects-header.svg", "02 / Projects", PK)
    section_header("links-header.svg", "08 / Find me online", CY)
    contact_terminal()
    footer()
    print("static panels written to", os.path.abspath(OUT))
