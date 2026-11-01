"""Refreshes the live panels: stats.svg, monkeytype.svg, activity.svg.

Runs in GitHub Actions (see .github/workflows/update-profile.yml) with the built-in
GITHUB_TOKEN. Standard library only.

    python scripts/build_dynamic.py            # live fetch, writes ../assets
    python scripts/build_dynamic.py --demo     # fake data, writes to ./demo for a preview
    python scripts/build_dynamic.py --empty    # "awaiting first sync" placeholders

If a source fails, the existing SVG for that panel is left untouched.
"""
import datetime as dt
import json
import os
import sys
import urllib.request

from cyber import *  # noqa: F401,F403

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets")

GH_LOGIN = os.environ.get("PROFILE_LOGIN") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "rop2024"
MT_USER = os.environ.get("MONKEYTYPE_USER", "__Rohit__")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
UA = "profile-readme-panels (+https://github.com/%s)" % GH_LOGIN


# ----------------------------------------------------------------------------- fetching
def http_json(url, data=None, headers=None):
    h = {"User-Agent": UA, "Accept": "application/json"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def gh_headers():
    return {"Authorization": "Bearer " + TOKEN} if TOKEN else {}


GQL = """
query($login:String!,$from:DateTime!,$to:DateTime!){
  user(login:$login){
    followers{totalCount}
    pullRequests{totalCount}
    issues{totalCount}
    repositories(ownerAffiliations:OWNER,isFork:false,privacy:PUBLIC,first:100){
      totalCount
      nodes{ stargazerCount languages(first:8,orderBy:{field:SIZE,direction:DESC}){edges{size node{name}}} }
    }
    contributionsCollection(from:$from,to:$to){
      totalCommitContributions
      contributionCalendar{ totalContributions weeks{ contributionDays{ date contributionCount } } }
    }
  }
}"""


def fetch_github():
    now = dt.datetime.now(dt.timezone.utc)
    body = json.dumps({"query": GQL, "variables": {
        "login": GH_LOGIN,
        "from": (now - dt.timedelta(days=364)).strftime("%Y-%m-%dT00:00:00Z"),
        "to": now.strftime("%Y-%m-%dT%H:%M:%SZ")}}).encode()
    res = http_json("https://api.github.com/graphql", body, dict(gh_headers(), **{"Content-Type": "application/json"}))
    u = res["data"]["user"]
    cc = u["contributionsCollection"]

    days = [d for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    days.sort(key=lambda d: d["date"])
    today = now.strftime("%Y-%m-%d")
    days = [d for d in days if d["date"] <= today]

    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] > 0 else 0
        longest = max(longest, run)
    cur = 0
    for i, d in enumerate(reversed(days)):
        if d["contributionCount"] > 0:
            cur += 1
        elif i == 0:          # today not committed yet: streak is still alive
            continue
        else:
            break

    langs = {}
    stars = 0
    for r in u["repositories"]["nodes"]:
        stars += r["stargazerCount"]
        for e in r["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:5]

    return {
        "commits": cc["totalCommitContributions"], "repos": u["repositories"]["totalCount"], "stars": stars,
        "prs": u["pullRequests"]["totalCount"], "issues": u["issues"]["totalCount"],
        "followers": u["followers"]["totalCount"], "contributions": cc["contributionCalendar"]["totalContributions"],
        "current_streak": cur, "longest_streak": longest,
        "active_days": sum(1 for d in days if d["contributionCount"] > 0),
        "languages": [(n, 100.0 * s / total) for n, s in top],
        "calendar": [d["contributionCount"] for d in days[-182:]],
        "updated": now.strftime("%Y-%m-%d %H:%M UTC"),
    }


def fetch_activity():
    ev = http_json("https://api.github.com/users/%s/events/public?per_page=100" % GH_LOGIN, headers=gh_headers())
    now = dt.datetime.now(dt.timezone.utc)
    rows = []
    for e in ev:
        t = dt.datetime.strptime(e["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
        repo = e["repo"]["name"].split("/")[-1]
        p = e.get("payload", {})
        if e["type"] == "PushEvent":
            commits = p.get("commits") or []
            msg = (commits[-1]["message"].splitlines()[0] if commits else "pushed to " + p.get("ref", "").split("/")[-1])
            sha = (commits[-1]["sha"] if commits else p.get("head", ""))[:7]
            rows.append({"repo": repo, "msg": msg, "sha": sha, "kind": "push", "when": t})
        elif e["type"] == "PullRequestEvent":
            pr = p.get("pull_request", {})
            rows.append({"repo": repo, "msg": "PR %s: %s" % (p.get("action", ""), pr.get("title", "")),
                         "sha": "#%s" % pr.get("number", ""), "kind": "pr", "when": t})
        elif e["type"] == "CreateEvent" and p.get("ref_type") == "repository":
            rows.append({"repo": repo, "msg": "created repository", "sha": "new", "kind": "new", "when": t})
    out = []
    for r in rows:
        if len(out) and out[-1]["repo"] == r["repo"] and out[-1]["kind"] == r["kind"] == "push" and out[-1]["msg"] == r["msg"]:
            continue
        r["ago"] = ago(now - r["when"])
        out.append(r)
    return {"rows": out[:6], "updated": now.strftime("%Y-%m-%d %H:%M UTC")}


def ago(delta):
    s = int(delta.total_seconds())
    if s < 3600:
        return "%dM AGO" % max(1, s // 60)
    if s < 86400:
        return "%dH AGO" % (s // 3600)
    return "%dD AGO" % (s // 86400)


def fetch_monkeytype():
    res = http_json("https://api.monkeytype.com/users/%s/profile" % MT_USER)
    d = res.get("data", res)
    modes = {}
    best_all = 0
    for m in ("15", "30", "60", "120"):
        entries = (d.get("personalBests", {}).get("time", {}) or {}).get(m) or []
        if entries:
            b = max(entries, key=lambda e: e.get("wpm", 0))
            modes[m] = (b.get("wpm", 0), b.get("acc", 0))
            best_all = max(best_all, b.get("wpm", 0))
    ts = d.get("typingStats", {}) or {}
    secs = int(ts.get("timeTyping", 0))
    return {
        "peak": best_all, "modes": modes,
        "tests": int(ts.get("completedTests", 0)),
        "time": "%dh %02dm" % (secs // 3600, (secs % 3600) // 60),
        "streak": int(d.get("streak", 0) or 0), "max_streak": int(d.get("maxStreak", 0) or 0),
        "updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


# ----------------------------------------------------------------------------- rendering
def readout(x, y, w, key, val, color):
    return (mtext(x, y, 9, key, MUT, ls=1) + mtext(x + w, y, 11, val, color, anchor="end")
            + '<line x1="%d" x2="%d" y1="%d" y2="%d" stroke="%s"/>' % (x, x + w, y + 8, y + 8, LINE))


def render_stats(d):
    empty = d is None
    g = lambda key, f=str: "--" if empty else f(d[key])
    b = label("05 / Data stats", YE)
    H = 396
    # tiles
    tiles = [("COMMITS / 12MO", g("commits", k), CY), ("PUBLIC REPOS", g("repos", k), PK), ("STARS EARNED", g("stars", k), YE),
             ("PULL REQUESTS", g("prs", k), PU), ("ISSUES", g("issues", k), CY), ("FOLLOWERS", g("followers", k), PK)]
    tw, th, gap = 124, 70, 8
    for i, (lab, val, col) in enumerate(tiles):
        x, y = 42 + (i % 3) * (tw + gap), 66 + (i // 3) * (th + gap)
        b += ('<rect x="%d" y="%d" width="%d" height="%d" fill="%s" stroke="%s"/><rect x="%d" y="%d" width="2" height="%d" fill="%s"/>') % (
            x, y, tw, th, BG, LINE, x, y, th, col)
        b += mtext(x + 14, y + 22, 8, lab, MUT, ls=1)
        b += stext(x + 14, y + 55, fit(val, 34, tw - 28, 1), val, col, ls=1)
    # streak readouts
    b += mtext(42, 246, 9, "// STREAK", MUT, ls=2)
    b += readout(42, 272, 388, "CURRENT STREAK", "--" if empty else "%d DAYS" % d["current_streak"], CY)
    b += readout(42, 298, 388, "LONGEST STREAK (12MO)", "--" if empty else "%d DAYS" % d["longest_streak"], YE)
    b += readout(42, 324, 388, "CONTRIBUTIONS (12MO)", "--" if empty else k(d["contributions"]), PK)
    # divider
    b += '<line x1="458" x2="458" y1="62" y2="%d" stroke="%s"/>' % (H - 36, LINE)
    # languages
    b += mtext(486, 76, 9, "// TOP LANGUAGES", MUT, ls=2)
    cols = [CY, PK, PU, YE, "#7a7a8c"]
    langs = [] if empty else d["languages"]
    for i in range(5):
        y = 104 + i * 25
        if i < len(langs):
            name, pct = langs[i]
            b += mtext(486, y, 11, name[:12], TXT)
            b += '<rect x="590" y="%d" width="206" height="6" fill="%s"/><rect x="590" y="%d" width="%.1f" height="6" fill="%s"/>' % (
                y - 7, TRACK, y - 7, max(2.0, 206 * pct / 100), cols[i])
            b += mtext(858, y, 10, "%.1f%%" % pct, SOFT, anchor="end")
        else:
            b += mtext(486, y, 11, "--", MUT)
            b += '<rect x="590" y="%d" width="206" height="6" fill="%s"/>' % (y - 7, TRACK)
    # heatmap
    b += mtext(486, 246, 9, "// ACTIVITY  LAST 26 WEEKS", MUT, ls=2)
    cal = [] if empty else d["calendar"]
    mx = max(cal) if cal else 0
    cell, pitch = 11, 13
    # calendar ends today; lay it into 7-row columns (oldest first)
    cells = [0] * (182 - len(cal)) + cal if cal else [None] * 182
    for idx, c in enumerate(cells):
        col, row = idx // 7, idx % 7
        x, y = 486 + col * pitch, 262 + row * pitch
        if c is None or mx == 0:
            fill, op = TRACK, 1
        elif c == 0:
            fill, op = TRACK, 1
        else:
            lvl = min(4, 1 + int(3.999 * c / mx))
            fill, op = CY, (0.28, 0.5, 0.75, 1.0)[lvl - 1]
        b += '<rect x="%d" y="%d" width="%d" height="%d" fill="%s" fill-opacity="%s"/>' % (x, y, cell, cell, fill, op)
    upd = "AWAITING FIRST SYNC" if empty else "UPDATED " + d["updated"]
    b += mtext(858, H - 22, 8, upd, MUT, ls=1, anchor="end")
    return panel(H, YE, b)


def render_monkeytype(d):
    empty = d is None
    H = 214
    b = label("06 / Typing profile", PK)
    # peak badge
    peak = "--" if empty else str(int(round(d["peak"])))
    b += ('<polygon points="42,66 138,66 138,148 124,164 42,164" fill="%s"/>' % PK
          + mtext(90, 84, 9, "PEAK", "#000", ls=2, anchor="middle")
          + stext(90, 134, 44, peak, "#000", ls=1, anchor="middle")
          + mtext(90, 154, 9, "WPM", "#000", ls=2, anchor="middle"))
    # mode tiles
    modes = [("15", "15 SEC"), ("30", "30 SEC"), ("60", "60 SEC"), ("120", "120 SEC")]
    tw, th = 120, 98
    for i, (m, lab) in enumerate(modes):
        x, y = 162 + i * (tw + 8), 66
        col = [CY, PU, YE, PK][i]
        wpm, acc = (None, None) if (empty or m not in d["modes"]) else d["modes"][m]
        b += ('<rect x="%d" y="%d" width="%d" height="%d" fill="%s" stroke="%s"/><rect x="%d" y="%d" width="2" height="%d" fill="%s"/>') % (
            x, y, tw, th, BG, LINE, x, y, th, col)
        b += mtext(x + 14, y + 22, 9, lab, MUT, ls=1.5)
        b += stext(x + 14, y + 62, 38, "--" if wpm is None else str(int(round(wpm))), col, ls=1)
        b += mtext(x + 14, y + 84, 9, "-- ACC" if acc is None else "%.1f%% ACC" % acc, SOFT, ls=.5)
    # right readouts
    b += readout(660 + 40, 82, 158, "TESTS", "--" if empty else k(d["tests"]), CY)
    b += readout(660 + 40, 114, 158, "TIME TYPING", "--" if empty else d["time"], YE)
    b += readout(660 + 40, 146, 158, "STREAK", "--" if empty else "%d DAYS" % d["streak"], PK)
    b += mtext(42, H - 24, 8, "monkeytype.com/profile/%s" % MT_USER, MUT, ls=1)
    b += mtext(858, H - 24, 8, "AWAITING FIRST SYNC" if empty else "UPDATED " + d["updated"], MUT, ls=1, anchor="end")
    return panel(H, PK, b)


def render_activity(d):
    empty = d is None or not d["rows"]
    rows = [] if empty else d["rows"]
    n = max(len(rows), 1)
    H = 124 + n * 40
    b = label("07 / Latest activity", CY)
    b += mtext(42, 66, 11, "$ git log --all --oneline -n %d" % len(rows) if rows else "$ git log --all --oneline", MUT)
    top = 96
    b += '<line x1="130" x2="130" y1="%d" y2="%d" stroke="%s"/>' % (top - 8, top + n * 40 - 22, LINE)
    kinds = {"push": CY, "pr": PU, "new": YE}
    if empty:
        b += mtext(150, top + 8, 12, "AWAITING FIRST SYNC", MUT, ls=2)
        b += '<circle cx="130" cy="%d" r="4" fill="%s"/>' % (top + 4, MUT)
    for i, r in enumerate(rows):
        y = top + i * 40
        col = kinds.get(r["kind"], CY)
        b += mtext(42, y + 8, 9, r["ago"], MUT, ls=1)
        b += '<circle class="%s" cx="130" cy="%d" r="4" fill="%s"/>' % ("pu" if i == 0 else "", y + 4, col)
        b += mtext(150, y + 8, 11, r["repo"], col, ls=.5)
        msg = trunc(r["msg"], 15, 520, .3)
        b += stext(150, y + 26, 15, msg, TXT, weight=500, ls=.3)
        b += mtext(858, y + 8, 10, r["sha"], MUT, anchor="end")
    upd = "AWAITING FIRST SYNC" if empty else "UPDATED " + d["updated"]
    b += mtext(858, H - 22, 8, upd, MUT, ls=1, anchor="end")
    return panel(H, CY, b)


# ----------------------------------------------------------------------------- demo data
DEMO_GH = {"commits": 412, "repos": 12, "stars": 7, "prs": 18, "issues": 3, "followers": 24, "contributions": 538,
           "current_streak": 9, "longest_streak": 31, "active_days": 141,
           "languages": [("JavaScript", 58.2), ("Python", 24.5), ("CSS", 9.8), ("HTML", 5.1), ("TypeScript", 2.4)],
           "calendar": [(i * 7 + (i % 5) * 3) % 9 if i % 11 else 0 for i in range(182)], "updated": "2026-11-01 12:00 UTC"}
DEMO_ACT = {"updated": "2026-11-01 12:00 UTC", "rows": [
    {"repo": "Promptly", "msg": "feat: streak calendar with monthly view", "sha": "a1b2c3d", "kind": "push", "ago": "2H AGO"},
    {"repo": "Tasklytics", "msg": "fix: drag and drop between groups on mobile", "sha": "9f8e7d6", "kind": "push", "ago": "5H AGO"},
    {"repo": "bookmark-clustering", "msg": "PR merged: resume interrupted categorization runs", "sha": "#14", "kind": "pr", "ago": "1D AGO"},
    {"repo": "Promptly", "msg": "chore: tidy editor word count and read time", "sha": "5c4b3a2", "kind": "push", "ago": "2D AGO"},
    {"repo": "profile", "msg": "created repository", "sha": "new", "kind": "new", "ago": "6D AGO"}]}
DEMO_MT = {"peak": 96, "modes": {"15": (101, 97.4), "30": (96, 96.9), "60": (92, 96.1), "120": (84, 95.2)},
           "tests": 3482, "time": "41h 12m", "streak": 4, "max_streak": 12, "updated": "2026-11-01 12:00 UTC"}


# ----------------------------------------------------------------------------- main
def main():
    mode = "live"
    if "--demo" in sys.argv:
        mode = "demo"
    elif "--empty" in sys.argv:
        mode = "empty"
    out = os.path.join(HERE, "..", "demo") if mode == "demo" else OUT
    os.makedirs(out, exist_ok=True)

    jobs = [("stats.svg", fetch_github, render_stats, DEMO_GH),
            ("activity.svg", fetch_activity, render_activity, DEMO_ACT),
            ("monkeytype.svg", fetch_monkeytype, render_monkeytype, DEMO_MT)]
    for fname, fetch, render, demo in jobs:
        path = os.path.join(out, fname)
        try:
            data = {"demo": demo, "empty": None}.get(mode) if mode != "live" else fetch()
        except Exception as e:  # keep the previous SVG if a source is down
            print("skip %s: %s" % (fname, e), file=sys.stderr)
            continue
        save(path, render(data))
        print("wrote", path)


if __name__ == "__main__":
    main()
