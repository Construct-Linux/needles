#!/usr/bin/env python3
"""Lays the needles' gallery out in _site: the page, every view's PNG and .json, and views.json -
each view's size, group, the regions its comparison leaves out, and the commit that last changed
it. Run by .github/workflows/pages.yml; locally, `python3 site/build.py && python3 -m http.server
-d _site`."""

import json
import pathlib
import shutil
import struct
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"

# The surface a view is of, by its name: the shell's own views, the desktop and its wallpapers,
# libadwaita's widgets, Settings' panels; anything else is an app, by its id.
GROUPS = [("shell-", "Shell"), ("desktop", "Desktop"), ("gtk-", "GTK widgets"), ("panel-", "Settings")]


def group_of(name):
    for prefix, group in GROUPS:
        if name.startswith(prefix):
            return group
    return "Apps"


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"{path.name} is not a PNG")
    return struct.unpack(">II", head[16:24])


def last_commit(path):
    out = subprocess.run(["git", "log", "-1", "--format=%h%x00%cs%x00%s", "--", path.name],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    sha, date, subject = (out.split("\0") + ["", "", ""])[:3]
    return {"sha": sha, "date": date, "subject": subject}


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copy(ROOT / "site" / "index.html", OUT / "index.html")
    views = []
    for png in sorted(ROOT.glob("*.png")):
        w, h = png_size(png)
        meta = {}
        spec = png.with_suffix(".json")
        if spec.exists():
            meta = json.loads(spec.read_text())
            shutil.copy(spec, OUT / spec.name)
        shutil.copy(png, OUT / png.name)
        # The regions left out of the comparison: those written by hand (ignore) and the actors
        # the harness measured (the clock, Vitals), each once.
        regions, seen = [], set()
        for r in meta.get("ignore", []) + meta.get("actors", []):
            key = (r["x"], r["y"], r["w"], r["h"])
            if key not in seen:
                seen.add(key)
                regions.append(r)
        views.append({"name": png.stem, "group": group_of(png.stem), "w": w, "h": h,
                      "regions": regions, "commit": last_commit(png)})
    tip = subprocess.run(["git", "log", "-1", "--format=%h%x00%cs%x00%s"], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout.strip().split("\0")
    (OUT / "views.json").write_text(json.dumps({
        "repository": "Construct-Linux/needles",
        "commit": {"sha": tip[0], "date": tip[1], "subject": tip[2]},
        "views": views,
    }, indent=1))
    print(f"{len(views)} views in {OUT}")


if __name__ == "__main__":
    main()
