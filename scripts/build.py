"""Inline the computed map data into the page template and write a standalone index.html.

Usage: python scripts/build.py scripts/template.html data/mapdata.js index.html
"""
import sys

tpl, data, out = sys.argv[1:4]
html = open(tpl, encoding="utf-8").read().replace("/*DATA*/", open(data, encoding="utf-8").read())
head = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n')
html = head + html.replace('<canvas id="map"', '</head><body>\n<canvas id="map"', 1) + "\n</body></html>"
open(out, "w", encoding="utf-8").write(html)
print(f"wrote {out} ({len(html) / 1e6:.1f} MB)")
