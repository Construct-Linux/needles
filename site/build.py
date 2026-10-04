#!/usr/bin/env python3
"""Lays the needles' gallery out in _site: the page, every view's PNG and .json, the view's previous
approved PNG (prev/<view>.png, for the before and after), and views.json - each view's metadata as
the harness wrote it (os cmd/image needles.go: group, what it validates, its rules, its scheme and
screen, how it was approved, its look-and-feel checks and noise), with the commits that approved it.
Run by .github/workflows/pages.yml; locally, `python3 site/build.py && python3 -m http.server -d
_site`.

A view whose .json lacks a field the gallery shows is an error, not a gap: the harness writes every
field (needles.go), so a missing one is a needle made some other way."""

import json
import pathlib
import shutil
import struct
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"

# What each group validates, in the order the gallery shows them. The group is the harness's: the
# call that shot the view, written in its .json - not a guess from the name.
GROUPS = {
    "shell": ("The shell",
              "GNOME Shell's own surfaces: the top bar, the dock, its menus, the overview, the lock "
              "screen. Dark in both schemes - the shell does not follow the light one - so its "
              "views are dark; shell-overview-light is the card over the light wallpaper."),
    "desktop": ("The desktop",
                "The shell's bars over each of the brand's wallpapers, and over a flat one: that the "
                "bars keep their edge over any of them (E2). The *-light views are the light "
                "wallpaper under the dark shell, not the light scheme."),
    "app": ("Apps",
            "Every app the image ships, as it opens, in the dark scheme: the window, its header bar "
            "and its accent."),
    "gtk": ("GTK and libadwaita",
            "libadwaita's widgets the apps do not show by themselves - popover, tooltip, dialog, "
            "banner, a destructive confirmation, focus, hover, pressed - in the dark and the light "
            "scheme."),
    "settings": ("Settings",
                 "Settings' panels, the app every person opens: rows, switches, the selected "
                 "sidebar item, and the light scheme's window."),
    "type": ("Type", "The type at the UI's sizes as GTK draws it: Adwaita Sans and Adwaita Mono, "
                     "regular and bold, on dark and on light."),
    "installer": ("The installer", "The graphical installer, the first thing a person sees."),
}

REQUIRED = ["group", "about", "rules", "scheme", "screen", "approved", "lf", "noise"]


def png_size(data):
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", data[16:24])


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def commits_of(name):
    """The commits that changed name, newest first: hash, date, subject."""
    out = git("log", "--format=%h%x00%cs%x00%s", "--", name).decode().strip()
    return [dict(zip(("sha", "date", "subject"), line.split("\0"))) for line in out.splitlines() if line]


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "prev").mkdir(parents=True)
    shutil.copy(ROOT / "site" / "index.html", OUT / "index.html")
    tolerance = json.loads((ROOT / "tolerance.json").read_text())
    views, problems = [], []
    for png in sorted(ROOT.glob("*.png")):
        spec_file = png.with_suffix(".json")
        if not spec_file.exists():
            problems.append(f"{png.stem}: no {spec_file.name}")
            continue
        spec = json.loads(spec_file.read_text())
        missing = [k for k in REQUIRED if k not in spec]
        if missing:
            problems.append(f"{png.stem}: {spec_file.name} lacks {', '.join(missing)}")
            continue
        if spec["group"] not in GROUPS:
            problems.append(f"{png.stem}: group {spec['group']!r} is not one of {', '.join(GROUPS)}")
            continue
        size = png_size(png.read_bytes()[:24])
        if size != (spec["screen"]["w"], spec["screen"]["h"]):
            problems.append(f"{png.stem}: the PNG is {size}, its screen {spec['screen']['w']}x{spec['screen']['h']}")
            continue
        shutil.copy(png, OUT / png.name)
        shutil.copy(spec_file, OUT / spec_file.name)
        history = commits_of(png.name)
        # The needle before this one, for the before and after: the PNG as the previous commit that
        # changed it left it, when it was the same size.
        prev = None
        if len(history) > 1:
            old = git("show", f"{history[1]['sha']}:{png.name}")
            if png_size(old[:24]) == size:
                (OUT / "prev" / png.name).write_bytes(old)
                prev = history[1]
        regions, seen = [], set()
        for r in spec.get("ignore", []) + spec.get("actors", []):
            key = (r["x"], r["y"], r["w"], r["h"])
            if key not in seen:
                seen.add(key)
                regions.append(r)
        views.append({**{k: spec[k] for k in REQUIRED}, "name": png.stem, "regions": regions,
                      "commit": history[0] if history else None, "prev": prev})
    if problems:
        raise SystemExit("the needles are not all as the harness writes them:\n  " + "\n  ".join(problems))
    tip = git("log", "-1", "--format=%h%x00%cs%x00%s").decode().strip().split("\0")
    (OUT / "views.json").write_text(json.dumps({
        "repository": "Construct-Linux/needles",
        "commit": dict(zip(("sha", "date", "subject"), tip)),
        "tolerance": tolerance,
        "groups": [{"key": k, "title": t, "about": a} for k, (t, a) in GROUPS.items()],
        "views": views,
    }, indent=1))
    print(f"{len(views)} views in {OUT}")


if __name__ == "__main__":
    main()
