# needles

How CONSTRUCT must look, view by view: the screenshots its test harness
([os](https://github.com/Construct-Linux/os), `task test:usb`) took once someone looked at
them and approved them. openQA, which openSUSE, Fedora and GNOME test their images with, calls
them needles.

**See them:** https://needles.constructlinux.org/ - every view, by surface, at the size a
2x screen shows it or at 1:1 to judge its sharpness, with the regions the comparison leaves out
(site/, published on every push to main).

Every run compares its screenshots with these. A view that changed beyond the tolerance fails
the run, and its difference is drawn. When the change is the one meant, `task needles:propose`
opens a pull request here with the views that changed. GitHub shows each image's difference -
2-up, swipe, onion skin - and merging it approves the new look. A release is made from a build
whose run matched `main`.

## What is here

| File | What it is |
|---|---|
| `<view>.png` | the view at the harness's 2880x1800, a 15" laptop's panel at 200%: `desktop*`, `shell-*` (the shell's own views), `gtk-*` (libadwaita's widgets), `panel-*` (Settings' panels), an app by its id (`org.gnome.Nautilus`) |
| `<view>.json` | written by the harness (os `cmd/image/needles.go`), every field required: `group` (the call that shot it: shell, desktop, app, gtk, settings, type, installer), `about` (what it validates) and `rules` (THEMING.md's ids), `scheme` and `screen` (physical size, scale, the stage's logical size), `approved` (the build and os commit it was approved from, the share that changed, or new), `lf` (its look-and-feel checks), `noise` (edge pixels, palette colours), and the regions left out of the comparison, each with why: `ignore`, written by hand, and `actors`, which the harness measured (the clock, Vitals' readings) |
| `tolerance.json` | the comparison's tolerance: a pixel differs past `channel` of 255, a view fails past `share` of its compared area |
| `site/` | the gallery: `build.py` lays it out - and refuses a view whose .json lacks a field - and `.github/workflows/pages.yml` publishes it |

Every view leaves out the top bar's clock and Vitals' readings, which change from one run to the
next (`cmd/image/needles.go` in os).

## The tolerance

A pixel differs when a colour channel moves more than 24 of 255: antialiasing and the VM's
software rendering stay under it, a colour the theme changed does not. A view fails when more
than 0.2% of its compared area differs: a few glyphs that moved fail it, noise does not.

## Approving a change

1. Run the harness with `NEEDLES` naming a checkout of this repository (os' `.env`):
   `task test:usb`. It writes `_output/test/look.json` and `look.html`: each view against its
   needle, and the difference.
2. `task needles:propose` opens the pull request: branch `look/<build>`, only the views that
   changed or are new, the share of each that differs.
3. Review the images on GitHub and merge. The next run compares with them.

## License

The screenshots show the brand's artwork (CC BY-SA 4.0, github.com/Construct-Linux/brand), GNOME
and the apps the image ships, each under its own license.
