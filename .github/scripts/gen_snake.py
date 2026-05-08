#!/usr/bin/env python3
"""Generate animated snake contribution SVG. Used in GitHub Actions."""
import json, subprocess, sys, os

def fetch(username, token):
    q = '{ user(login:"%s") { contributionsCollection { contributionCalendar { weeks { contributionDays { date contributionCount } } } } } }' % username
    r = subprocess.run([
        "curl", "-s", "-X", "POST",
        "-H", "Authorization: token %s" % token,
        "-H", "Content-Type: application/json",
        "https://api.github.com/graphql",
        "-d", json.dumps({"query": q})
    ], capture_output=True, text=True, timeout=30)
    data = json.loads(r.stdout)
    weeks = data['data']['user']['contributionsCollection']['contributionCalendar']['weeks']
    return [[d['contributionCount'] for d in w['contributionDays']] for w in weeks]

def cell_color(c, dark=True):
    if dark:
        return ["#161b22","#0e4429","#006d32","#26a641","#39d353"][min(c,4)] if c > 0 else "#161b22"
    else:
        return ["#ebedf0","#9be9a8","#40c463","#30a14e","#216e39"][min(c,4)] if c > 0 else "#ebedf0"

def snake_path(cols):
    path = []
    for x in range(cols):
        if x % 2 == 0:
            for y in range(7): path.append((x, y))
        else:
            for y in range(6, -1, -1): path.append((x, y))
    return path

def gen(grid, dark=True):
    cs, cg = 10, 3
    ct = cs + cg
    lw, mh = 36, 20
    cols = len(grid)

    rects = []
    for x, week in enumerate(grid):
        for y, c in enumerate(week):
            rx, ry = lw + x*ct, mh + y*ct
            rects.append('<rect x="%d" y="%d" width="%d" height="%d" rx="2" fill="%s"/>' % (rx, ry, cs, cs, cell_color(c, dark)))

    path = snake_path(cols)
    snake_len = min(30, len(path))
    tail = len(path) - snake_len

    def draw_snake(offset_x):
        parts = []
        for i in range(snake_len):
            idx = tail + i
            if 0 <= idx < len(path):
                gx, gy = path[idx]
                t = i / max(snake_len - 1, 1)
                if t < 0.3:   color = "#0e4429"
                elif t < 0.6: color = "#006d32"
                elif t < 0.85: color = "#26a641"
                else:          color = "#39d353"
                rx = lw + gx*ct + offset_x
                ry = mh + gy*ct
                sz = cs + 2 if i >= snake_len - 2 else cs
                off = -1 if i >= snake_len - 2 else 0
                parts.append('<rect x="%d" y="%d" width="%d" height="%d" rx="2" fill="%s"/>' % (rx+off, ry+off, sz, sz, color))
        return parts

    gw = cols * ct
    snake1 = draw_snake(0)
    snake2 = draw_snake(gw)

    bg = "#0d1117" if dark else "#ffffff"
    w = lw + cols*ct + 10
    h = mh + 7*ct + 10
    duration = max(cols * 0.3, 16)

    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">
<rect width="100%%" height="100%%" fill="%s" rx="4"/>
<style>
.snake-group{animation:slither %ds linear infinite}
@keyframes slither{0%%{transform:translateX(0)}100%%{transform:translateX(-%dpx)}}
</style>
%s
<g class="snake-group">
%s
%s
</g>
</svg>''' % (w, h, w, h, bg, duration, gw, "\n".join(rects), "\n".join(snake1), "\n".join(snake2))

if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else "liuyunss"
    token = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("GITHUB_TOKEN", "")

    grid = fetch(username, token)
    print("Fetched %d weeks" % len(grid))

    os.makedirs("dist", exist_ok=True)
    for theme, dark in [("dark", True), ("light", False)]:
        svg = gen(grid, dark)
        path = "dist/snake-%s.svg" % theme
        with open(path, "w") as f:
            f.write(svg)
        print("%s: %d bytes" % (path, len(svg)))
