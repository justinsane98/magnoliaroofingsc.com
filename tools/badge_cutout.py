"""Cut a badge out of a white background (pure Python PNG I/O). Usage: cutout.py in.png out.png"""
import struct, sys, zlib
from collections import deque


def read_png(path):
    data = open(path, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos, idat, w = 8, b"", None
    while pos < len(data):
        ln, typ = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, bd, ct, _, _, il = struct.unpack(">IIBBBBB", body)
            assert bd == 8 and ct in (2, 6) and il == 0, (bd, ct, il)
            ch = 4 if ct == 6 else 3
        elif typ == b"IDAT":
            idat += body
        pos += 12 + ln
    raw, stride, out, prev = zlib.decompress(idat), w * ch, [], bytearray(w * ch)
    i = 0
    for _ in range(h):
        f = raw[i]; line = bytearray(raw[i + 1:i + 1 + stride]); i += 1 + stride
        for x in range(stride):
            a = line[x - ch] if x >= ch else 0
            b = prev[x]
            c = prev[x - ch] if x >= ch else 0
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + b) & 255
            elif f == 3: line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c; pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        out.append([list(line[x * ch:x * ch + ch]) + ([255] if ch == 3 else []) for x in range(w)])
        prev = line
    return w, h, out


def write_png(path, w, h, px):
    raw = b"".join(b"\x00" + bytes(v for p in row for v in p) for row in px)
    def chunk(t, b): return struct.pack(">I", len(b)) + t + b + struct.pack(">I", zlib.crc32(t + b) & 0xffffffff)
    open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


w, h, px = read_png(sys.argv[1])
light = lambda p: min(p[0], p[1], p[2]) >= 228  # near-white background
bg = [[False] * w for _ in range(h)]
q = deque((x, y) for x in range(w) for y in (0, h - 1)) + deque((x, y) for y in range(h) for x in (0, w - 1))
while q:
    x, y = q.popleft()
    if 0 <= x < w and 0 <= y < h and not bg[y][x] and light(px[y][x]):
        bg[y][x] = True
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

out = [[list(p) for p in row] for row in px]
for y in range(h):
    for x in range(w):
        if bg[y][x]:
            out[y][x] = [0, 0, 0, 0]
        elif any(0 <= x + dx < w and 0 <= y + dy < h and bg[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            # edge pixel: un-matte from white so there's no white fringe
            r, g, b, _ = px[y][x]
            a = max(1, 255 - min(r, g, b)) / 255
            a = min(1.0, a * 1.25)
            out[y][x] = [max(0, min(255, round((c - (1 - a) * 255) / a))) for c in (r, g, b)] + [round(a * 255)]

# keep only the largest opaque component (drops stray specks), then crop to it
seen = [[False] * w for _ in range(h)]; best = []
for y0 in range(h):
    for x0 in range(w):
        if out[y0][x0][3] and not seen[y0][x0]:
            comp, q = [], deque([(x0, y0)]); seen[y0][x0] = True
            while q:
                x, y = q.popleft(); comp.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and out[ny][nx][3]:
                        seen[ny][nx] = True; q.append((nx, ny))
            if len(comp) > len(best): best = comp
keep = set(best)
xs, ys = [p[0] for p in best], [p[1] for p in best]
x0, x1, y0, y1 = max(0, min(xs) - 1), min(w - 1, max(xs) + 1), max(0, min(ys) - 1), min(h - 1, max(ys) + 1)
crop = [[(out[y][x] if (x, y) in keep else [0, 0, 0, 0]) for x in range(x0, x1 + 1)] for y in range(y0, y1 + 1)]
write_png(sys.argv[2], x1 - x0 + 1, y1 - y0 + 1, crop)
print("bbox", x0, y0, x1, y1, "->", x1 - x0 + 1, "x", y1 - y0 + 1, "pixels kept", len(best))
