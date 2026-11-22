"""Tạo mã QR (chế độ byte, phiên bản 1–40) bằng Python thuần, không cần thư viện ngoài.
Dùng:  m = make_qr("https://...", "H")  -> ma trận True/False (True = ô đen)."""

_ECC_PER_BLOCK = {
    "L": (-1, 7, 10, 15, 20, 26, 18, 20, 24, 30, 18, 20, 24, 26, 30, 22, 24, 28, 30, 28, 28, 28, 28, 30, 30, 26, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30),
    "M": (-1, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26, 30, 22, 22, 24, 24, 28, 28, 26, 26, 26, 26, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28),
    "Q": (-1, 13, 22, 18, 26, 18, 24, 18, 22, 20, 24, 28, 26, 24, 20, 30, 24, 28, 28, 26, 30, 28, 30, 30, 30, 30, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30),
    "H": (-1, 17, 28, 22, 16, 22, 28, 26, 26, 24, 28, 24, 28, 22, 24, 24, 30, 28, 28, 26, 28, 30, 24, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30),
}
_NUM_BLOCKS = {
    "L": (-1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 4, 4, 4, 4, 4, 6, 6, 6, 6, 7, 8, 8, 9, 9, 10, 12, 12, 12, 13, 14, 15, 16, 17, 18, 19, 19, 20, 21, 22, 24, 25),
    "M": (-1, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5, 5, 8, 9, 9, 10, 10, 11, 13, 14, 16, 17, 17, 18, 20, 21, 23, 25, 26, 28, 29, 31, 33, 35, 37, 38, 40, 43, 45, 47, 49),
    "Q": (-1, 1, 1, 2, 2, 4, 4, 6, 6, 8, 8, 8, 10, 12, 16, 12, 17, 16, 18, 21, 20, 23, 23, 25, 27, 29, 34, 34, 35, 38, 40, 43, 45, 48, 51, 53, 56, 59, 62, 65, 68),
    "H": (-1, 1, 1, 2, 4, 4, 4, 5, 6, 8, 8, 11, 11, 16, 16, 18, 16, 19, 21, 25, 25, 25, 34, 30, 32, 35, 37, 40, 42, 45, 48, 51, 54, 57, 60, 63, 66, 70, 74, 77, 81),
}
_FORMAT = {"L": 1, "M": 0, "Q": 3, "H": 2}


def _raw_modules(v):
    r = (16 * v + 128) * v + 64
    if v >= 2:
        n = v // 7 + 2
        r -= (25 * n - 10) * n - 55
        if v >= 7:
            r -= 36
    return r


def _data_codewords(v, e):
    return _raw_modules(v) // 8 - _ECC_PER_BLOCK[e][v] * _NUM_BLOCKS[e][v]


def _gf_mul(x, y):
    z = 0
    for i in reversed(range(8)):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z


def _rs_divisor(deg):
    res = [0] * (deg - 1) + [1]
    root = 1
    for _ in range(deg):
        for j in range(deg):
            res[j] = _gf_mul(res[j], root)
            if j + 1 < deg:
                res[j] ^= res[j + 1]
        root = _gf_mul(root, 2)
    return res


def _rs_remainder(data, div):
    res = [0] * len(div)
    for b in data:
        f = b ^ res.pop(0)
        res.append(0)
        for i, c in enumerate(div):
            res[i] ^= _gf_mul(c, f)
    return res


def make_qr(text, ecl="M"):
    data = text.encode("utf-8")
    for ver in range(1, 41):
        ccbits = 8 if ver < 10 else 16
        if 4 + ccbits + 8 * len(data) <= _data_codewords(ver, ecl) * 8:
            break
    else:
        raise ValueError("Nội dung quá dài cho mã QR")

    # dòng bit dữ liệu
    bits = []
    def put(val, n):
        bits.extend((val >> i) & 1 for i in reversed(range(n)))
    put(4, 4); put(len(data), ccbits)
    for b in data:
        put(b, 8)
    cap = _data_codewords(ver, ecl) * 8
    put(0, min(4, cap - len(bits)))
    put(0, (-len(bits)) % 8)
    pad = 0xEC
    while len(bits) < cap:
        put(pad, 8); pad ^= 0xEC ^ 0x11
    words = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]

    # mã sửa lỗi + xen kẽ khối
    nb, ecc_len = _NUM_BLOCKS[ecl][ver], _ECC_PER_BLOCK[ecl][ver]
    raw = _raw_modules(ver) // 8
    nshort, short_len = nb - raw % nb, raw // nb
    div = _rs_divisor(ecc_len)
    blocks, k = [], 0
    for i in range(nb):
        dat = words[k:k + short_len - ecc_len + (0 if i < nshort else 1)]
        k += len(dat)
        ecc = _rs_remainder(dat, div)
        if i < nshort:
            dat.append(0)
        blocks.append(dat + ecc)
    final = []
    for i in range(len(blocks[0])):
        for j, blk in enumerate(blocks):
            if i != short_len - ecc_len or j >= nshort:
                final.append(blk[i])

    size = ver * 4 + 17
    mod = [[False] * size for _ in range(size)]
    fn = [[False] * size for _ in range(size)]
    def setf(x, y, d):
        mod[y][x] = d; fn[y][x] = True

    for i in range(size):
        setf(6, i, i % 2 == 0); setf(i, 6, i % 2 == 0)
    for cx, cy in ((3, 3), (size - 4, 3), (3, size - 4)):
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                x, y = cx + dx, cy + dy
                if 0 <= x < size and 0 <= y < size:
                    setf(x, y, max(abs(dx), abs(dy)) not in (2, 4))
    if ver > 1:
        n = ver // 7 + 2
        step = (ver * 8 + n * 3 + 5) // (n * 4 - 4) * 2
        pos = [6] + sorted(size - 7 - i * step for i in range(n - 1))
        for i, a in enumerate(pos):
            for j, b in enumerate(pos):
                if (i == 0 and j == 0) or (i == 0 and j == n - 1) or (i == n - 1 and j == 0):
                    continue
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        setf(a + dx, b + dy, max(abs(dx), abs(dy)) != 1)

    def draw_format(mask):
        d = _FORMAT[ecl] << 3 | mask
        r = d
        for _ in range(10):
            r = (r << 1) ^ ((r >> 9) * 0x537)
        bits_ = (d << 10 | r) ^ 0x5412
        g = lambda i: (bits_ >> i) & 1 == 1
        for i in range(6):
            setf(8, i, g(i))
        setf(8, 7, g(6)); setf(8, 8, g(7)); setf(7, 8, g(8))
        for i in range(9, 15):
            setf(14 - i, 8, g(i))
        for i in range(8):
            setf(size - 1 - i, 8, g(i))
        for i in range(8, 15):
            setf(8, size - 15 + i, g(i))
        setf(8, size - 8, True)

    draw_format(0)
    if ver >= 7:
        r = ver
        for _ in range(12):
            r = (r << 1) ^ ((r >> 11) * 0x1F25)
        vb = ver << 12 | r
        for i in range(18):
            bit = (vb >> i) & 1 == 1
            a, b = size - 11 + i % 3, i // 3
            setf(a, b, bit); setf(b, a, bit)

    i = 0
    right = size - 1
    while right >= 1:
        if right == 6:
            right = 5
        for vert in range(size):
            for j in range(2):
                x = right - j
                up = ((right + 1) & 2) == 0
                y = size - 1 - vert if up else vert
                if not fn[y][x] and i < len(final) * 8:
                    mod[y][x] = (final[i >> 3] >> (7 - (i & 7))) & 1 == 1
                    i += 1
        right -= 2

    masks = [
        lambda x, y: (x + y) % 2 == 0, lambda x, y: y % 2 == 0, lambda x, y: x % 3 == 0,
        lambda x, y: (x + y) % 3 == 0, lambda x, y: (x // 3 + y // 2) % 2 == 0,
        lambda x, y: x * y % 2 + x * y % 3 == 0, lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0,
        lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0,
    ]
    def apply(m):
        f = masks[m]
        for y in range(size):
            for x in range(size):
                if not fn[y][x] and f(x, y):
                    mod[y][x] = not mod[y][x]

    def penalty():
        p = 0
        lines = mod + [list(c) for c in zip(*mod)]
        for row in lines:
            run, prev = 0, None
            for c in row:
                if c == prev:
                    run += 1
                else:
                    if run >= 5: p += run - 2
                    run, prev = 1, c
            if run >= 5: p += run - 2
            s = "".join("1" if c else "0" for c in row)
            p += 40 * (s.count("10111010000") + s.count("00001011101"))
        for y in range(size - 1):
            for x in range(size - 1):
                c = mod[y][x]
                if c == mod[y][x + 1] == mod[y + 1][x] == mod[y + 1][x + 1]:
                    p += 3
        dark = sum(map(sum, mod))
        p += abs(dark * 20 - size * size * 10) // (size * size) * 10
        return p

    best, best_p = 0, None
    for m in range(8):
        apply(m); draw_format(m)
        pv = penalty()
        if best_p is None or pv < best_p:
            best, best_p = m, pv
        apply(m)
    apply(best); draw_format(best)
    return mod


def qr_image(text, scale=20, border=4, ecl="H"):
    from PIL import Image
    m = make_qr(text, ecl)
    n = len(m)
    im = Image.new("1", (n + 2 * border, n + 2 * border), 1)
    px = im.load()
    for y in range(n):
        for x in range(n):
            if m[y][x]:
                px[x + border, y + border] = 0
    return im.resize((im.width * scale, im.height * scale), Image.NEAREST).convert("RGB")
