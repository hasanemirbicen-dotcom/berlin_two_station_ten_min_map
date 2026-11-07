import urllib.request, urllib.parse, json, sys, os

OUT = sys.argv[1]
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
S, W, N, E = 52.492, 13.305, 52.536, 13.440
bbox = f"{S},{W},{N},{E}"
q = f"""
[out:json][timeout:180];
(
  way["highway"]({bbox});
  way["natural"="water"]({bbox});
  way["waterway"~"riverbank|river|canal"]({bbox});
  relation["natural"="water"]({bbox});
  way["leisure"~"park|garden"]({bbox});
  relation["leisure"="park"]({bbox});
  way["landuse"~"grass|forest|cemetery|recreation_ground"]({bbox});
  way["natural"="wood"]({bbox});
  way["railway"~"rail|light_rail"]["tunnel"!="yes"]({bbox});
);
out geom;
"""
data = urllib.parse.urlencode({"data": q}).encode()
req = urllib.request.Request("https://overpass-api.de/api/interpreter", data=data,
                             headers={"User-Agent": "30daymapchallenge-isochrone/1.0"})
with urllib.request.urlopen(req, timeout=300) as r:
    raw = r.read()
with open(OUT, "wb") as f:
    f.write(raw)
print(len(raw))
