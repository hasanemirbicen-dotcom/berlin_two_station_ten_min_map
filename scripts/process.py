import json, math, sys, heapq
from collections import defaultdict

SRC, OUT = sys.argv[1], sys.argv[2]
S, W, N, E = 52.492, 13.305, 52.536, 13.440
LAT0 = (S + N) / 2
KX = 111320 * math.cos(math.radians(LAT0))
KY = 110540
def P(lat, lon):
    return ((lon - W) * KX, (N - lat) * KY)

WIDTH, HEIGHT = P(S, E)
SPEED = 5000 / 60          # m per minute at 5 km/h
LIMIT = 10 * SPEED         # 833 m

STATIONS = [
    {"id": "alex", "name": "Alexanderplatz", "lat": 52.52153, "lon": 13.41131},
    {"id": "zoo", "name": "Zoologischer Garten", "lat": 52.50687, "lon": 13.33263},
]

data = json.load(open(SRC, encoding="utf-8"))["elements"]

WALK = {"footway","path","pedestrian","residential","living_street","service","tertiary","secondary",
        "primary","unclassified","steps","cycleway","track","trunk","primary_link","secondary_link",
        "tertiary_link","trunk_link","corridor","platform","bridleway"}
MAJOR = {"primary","secondary","trunk","primary_link","secondary_link","trunk_link","motorway","motorway_link"}
MID = {"tertiary","tertiary_link","residential","unclassified","living_street","pedestrian"}

def simplify(pts, tol=2.5):
    if len(pts) < 3: return pts
    out = [pts[0]]
    for p in pts[1:-1]:
        q = out[-1]
        if abs(p[0]-q[0]) + abs(p[1]-q[1]) >= tol: out.append(p)
    out.append(pts[-1])
    return out

def flat(pts):
    r = []
    for x, y in pts: r += [round(x), round(y)]
    return r

bg = {"major": [], "mid": [], "minor": [], "rail": [], "waterline": [], "water": [], "green": []}
graph = defaultdict(list)
coord = {}

def stitch(ways):
    ways = [list(w) for w in ways if len(w) > 1]
    rings = []
    while ways:
        ring = ways.pop(0)
        changed = True
        while ring[0] != ring[-1] and changed:
            changed = False
            for i, w in enumerate(ways):
                if w[0] == ring[-1]: ring += w[1:]
                elif w[-1] == ring[-1]: ring += w[::-1][1:]
                elif w[-1] == ring[0]: ring = w[:-1] + ring
                elif w[0] == ring[0]: ring = w[::-1][:-1] + ring
                else: continue
                ways.pop(i); changed = True; break
        rings.append(ring)
    return rings

for el in data:
    t = el.get("tags", {})
    if el["type"] == "way":
        g = el.get("geometry")
        if not g: continue
        pts = [P(p["lat"], p["lon"]) for p in g]
        hw = t.get("highway")
        if hw:
            if hw in MAJOR: bg["major"].append(flat(simplify(pts)))
            elif hw in MID: bg["mid"].append(flat(simplify(pts)))
            elif hw not in ("proposed", "construction", "abandoned", "razed"): bg["minor"].append(flat(simplify(pts)))
            ok = hw in WALK
            if t.get("foot") in ("no", "private") or (t.get("access") in ("private", "no") and t.get("foot") not in ("yes", "designated", "permissive")):
                ok = False
            if ok:
                nodes = el["nodes"]
                for i, nid in enumerate(nodes): coord[nid] = pts[i]
                for a, b in zip(nodes, nodes[1:]):
                    pa, pb = coord[a], coord[b]
                    L = math.hypot(pa[0]-pb[0], pa[1]-pb[1])
                    graph[a].append((b, L)); graph[b].append((a, L))
        elif t.get("railway") in ("rail", "light_rail"):
            bg["rail"].append(flat(simplify(pts)))
        elif t.get("waterway") in ("river", "canal") and t.get("area") != "yes":
            bg["waterline"].append(flat(simplify(pts)))
        elif t.get("natural") == "water" or t.get("waterway") == "riverbank":
            if len(pts) > 3: bg["water"].append(flat(simplify(pts)))
        elif t.get("leisure") in ("park", "garden") or t.get("landuse") in ("grass","forest","cemetery","recreation_ground") or t.get("natural") == "wood":
            if len(pts) > 3: bg["green"].append(flat(simplify(pts)))
    elif el["type"] == "relation":
        members = [m for m in el.get("members", []) if m.get("geometry")]
        key = "water" if t.get("natural") == "water" else "green"
        ways = [[(round(P(p["lat"],p["lon"])[0],1), round(P(p["lat"],p["lon"])[1],1)) for p in m["geometry"]] for m in members]
        for ring in stitch(ways):
            if len(ring) > 3: bg[key].append(flat(simplify(ring)))

print("graph nodes", len(graph))

result = {"w": round(WIDTH), "h": round(HEIGHT), "limit": round(LIMIT), "speed": SPEED, "stations": [], "bg": bg}
for st in STATIONS:
    sx, sy = P(st["lat"], st["lon"])
    dist = {}
    pq = []
    for nid in graph:
        x, y = coord[nid]
        d = math.hypot(x - sx, y - sy)
        if d < 70:
            dist[nid] = d; pq.append((d, nid))
    heapq.heapify(pq)
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, 1e18) or d > LIMIT: continue
        for v, L in graph[u]:
            nd = d + L
            if nd < dist.get(v, 1e18):
                dist[v] = nd; heapq.heappush(pq, (nd, v))
    segs = []
    seen = set()
    total = 0.0
    for u, du in dist.items():
        for v, L in graph[u]:
            key = (min(u, v), max(u, v))
            if key in seen: continue
            seen.add(key)
            dv = dist.get(v, 1e18)
            if min(du, dv) >= LIMIT: continue
            dv = min(dv, du + L)
            du2 = min(du, dv + L)
            a, b = coord[u], coord[v]
            segs += [round(a[0],1), round(a[1],1), round(b[0],1), round(b[1],1), round(du2,1), round(dv,1)]
            # reached length
            ra = max(0, min(L, LIMIT - du2)); rb = max(0, min(L, LIMIT - dv))
            total += min(L, ra + rb)
    print(st["name"], "segments", len(segs)//6, "km", round(total/1000, 2))
    result["stations"].append({"id": st["id"], "name": st["name"], "x": round(sx,1), "y": round(sy,1),
                               "km": round(total/1000, 1), "segs": segs})

LAND = [("Fernsehturm", 52.52080, 13.40940), ("Museum Island", 52.51690, 13.40100), ("Brandenburg Gate", 52.51627, 13.37770),
        ("Tiergarten", 52.51300, 13.35700), ("Victory Column", 52.51450, 13.35010), ("Kurfürstendamm", 52.50280, 13.32300),
        ("Hackescher Markt", 52.52290, 13.40240), ("Berlin Zoo", 52.50850, 13.33700), ("Rotes Rathaus", 52.51850, 13.40830)]
result["labels"] = [{"t": n, "x": round(P(a, b)[0]), "y": round(P(a, b)[1])} for n, a, b in LAND]

with open(OUT, "w", encoding="utf-8") as f:
    f.write("window.MAPDATA=")
    json.dump(result, f, separators=(",", ":"), ensure_ascii=False)
    f.write(";")
import os
print("size", os.path.getsize(OUT))
