#!/usr/bin/env python3
"""
TẠO TRANG WEB ĐỌC BÀI DỰ THI TỪ FILE WORD
=========================================
Cách dùng (trong VS Code): Ctrl+Shift+B  -> chọn "Tạo trang web"
Hoặc:  python cong-cu/taoweb.py  [file-word]   (mặc định lấy file Word mới nhất trong tai-lieu/)
Kết quả ghi vào thư mục public/ – Vercel phục vụ đúng thư mục này.

Cần có: Python 3, Pandoc, thư viện Pillow (pip install pillow).
Chỉ khi đầu vào là .doc (Word 97-2003) mới cần thêm LibreOffice.

Công cụ tự nhận:
  - Các câu hỏi: đoạn bắt đầu bằng "Câu 1:", "Câu hỏi 2.", "CÂU 3 -" ...
  - Ảnh nền/hình mờ lặp lại nhiều lần (logo chìm) -> tự bỏ.
  - Trang bìa (phần trước đoạn văn dài đầu tiên) -> tự bỏ.
Chỉ cần sửa phần CẤU HÌNH bên dưới nếu đổi tiêu đề.
"""

# ======================= CẤU HÌNH =======================
URL_TRANG   = "https://baiduthi-70nam-sqpb.vercel.app"   # địa chỉ trang trên Vercel – mã QR trỏ tới đây
TIEU_DE_NHO = "Bài dự thi tìm hiểu"
TIEU_DE     = "70 năm Ngày truyền thống Trường Sĩ quan Pháo binh"
MOC_THOI_GIAN = "18/02/1957 – 18/02/2027"
CHAN_TRANG  = "Bài dự thi tìm hiểu 70 năm Ngày truyền thống Trường Sĩ quan Pháo binh"
LOGO        = "logo.jpg"   # ảnh logo đặt cạnh file này; để "" nếu không dùng
ANH_TOI_DA  = 1400         # cạnh dài tối đa của ảnh (px) – nhỏ hơn = trang nhẹ hơn
CHAT_LUONG_ANH = 78        # chất lượng JPEG 1–95
SO_LAN_LAP_LA_HINH_NEN = 3 # ảnh xuất hiện từ ngần này lần trở lên coi là hình nền, bỏ đi
# ========================================================

import hashlib, html, os, re, shutil, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont

# Windows: in tiếng Việt ra Terminal không bị lỗi mã hóa
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def newest_word():
    d = os.path.join(ROOT, "tai-lieu")
    files = [os.path.join(d, f) for f in os.listdir(d)
             if f.lower().endswith((".doc", ".docx")) and not f.startswith("~$")]
    if not files:
        sys.exit("Chưa có file Word. Hãy chép file .doc/.docx vào thư mục tai-lieu/ rồi chạy lại.")
    return max(files, key=os.path.getmtime)


def to_docx(src, tmp):
    if src.lower().endswith(".docx"):
        return src
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        for p in (r"C:\Program Files\LibreOffice\program\soffice.exe",
                  "/Applications/LibreOffice.app/Contents/MacOS/soffice"):
            if os.path.exists(p):
                soffice = p
    if not soffice:
        sys.exit("File .doc cần LibreOffice để chuyển đổi. Hoặc mở bằng Word -> Lưu thành .docx rồi chạy lại.")
    subprocess.run([soffice, "--headless", "--convert-to", "docx", "--outdir", tmp, src],
                   check=True, capture_output=True)
    return os.path.join(tmp, os.path.splitext(os.path.basename(src))[0] + ".docx")


def _font(names, size):
    dirs = [os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts"),
            "/System/Library/Fonts/Supplemental", "/Library/Fonts",
            "/usr/share/fonts/truetype/liberation", "/usr/share/fonts/truetype/dejavu"]
    for n in names:
        for d in dirs:
            if os.path.exists(os.path.join(d, n)):
                return ImageFont.truetype(os.path.join(d, n), size)
    return ImageFont.load_default()


def make_qr_files(outdir, logo_path):
    """Tạo public/qr.png (mã QR có logo) và public/qr-in-an.png (thẻ để in)."""
    sys.path.insert(0, HERE)
    from qr import qr_image
    qr = qr_image(URL_TRANG, scale=24, border=4, ecl="H")   # mức H: vẫn quét được khi có logo giữa
    if logo_path and os.path.exists(logo_path):
        s = qr.width // 5
        lg = Image.open(logo_path).convert("RGB").resize((s, s))
        pad = Image.new("RGB", (s + 16, s + 16), "white"); pad.paste(lg, (8, 8))
        qr.paste(pad, ((qr.width - pad.width) // 2, (qr.height - pad.height) // 2))
    qr.save(os.path.join(outdir, "qr.png"))

    W, H = 1200, 1500
    card = Image.new("RGB", (W, H), "#faf7f2"); d = ImageDraw.Draw(card)
    d.rectangle([0, 0, W, 300], fill="#a3141b")
    serif = ["timesbd.ttf", "Times New Roman Bold.ttf", "LiberationSerif-Bold.ttf", "DejaVuSerif-Bold.ttf"]
    sans = ["arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"]
    def center(y, text, font, fill, maxw=W - 80):
        while d.textlength(text, font=font) > maxw and getattr(font, "size", 0) > 20:
            font = font.font_variant(size=font.size - 2)
        d.text(((W - d.textlength(text, font=font)) / 2, y), text, font=font, fill=fill)
    center(55, TIEU_DE_NHO.upper(), _font(sans, 40), "#ffd98a")
    words = TIEU_DE.split(); half = (len(words) + 1) // 2
    center(120, " ".join(words[:half]), _font(serif, 64), "white")
    center(195, " ".join(words[half:]), _font(serif, 64), "white")
    card.paste(qr.resize((860, 860), Image.NEAREST), ((W - 860) // 2, 350))
    center(1250, "Quét mã QR để đọc toàn bộ bài dự thi", _font(serif, 50), "#1d1b19")
    center(1330, URL_TRANG.replace("https://", ""), _font(sans, 34), "#a3141b")
    card.save(os.path.join(outdir, "qr-in-an.png"), dpi=(300, 300))


def find_pandoc():
    p = shutil.which("pandoc")
    if p:
        return p
    for c in (os.path.join(os.environ.get("LOCALAPPDATA", ""), "Pandoc", "pandoc.exe"),
              os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Pandoc", "pandoc.exe"),
              "/opt/homebrew/bin/pandoc", "/usr/local/bin/pandoc"):
        if c and os.path.exists(c):
            return c
    sys.exit("\nLỖI: Không tìm thấy Pandoc.\n"
             "  1. Tải và cài Pandoc: https://pandoc.org/installing.html (Windows: file .msi)\n"
             "  2. Đóng hẳn VS Code rồi mở lại, sau đó bấm Ctrl+Shift+B lần nữa.\n"
             "  Kiểm tra: gõ  pandoc --version  trong Terminal phải ra số phiên bản.")


def docx_to_html(docx, tmp):
    media = os.path.join(tmp, "m")
    out = subprocess.run([find_pandoc(), docx, "-t", "html5", "--wrap=none", f"--extract-media={media}"],
                         check=True, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    return out


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def build(src, outdir):
    t0 = time.time()
    tmp = tempfile.mkdtemp()
    body = docx_to_html(to_docx(src, tmp), tmp)

    img_re = re.compile(r'<img\s+src="([^"]+)"\s*(?:style="([^"]*)")?[^>]*?/?>', re.S)

    # 1) hình nền: cùng nội dung ảnh xuất hiện nhiều lần
    def digest(p):
        with open(p, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    srcs = [m.group(1) for m in img_re.finditer(body)]
    hashes = {s: digest(s) for s in set(srcs) if os.path.exists(s)}
    count = {}
    for s in srcs:
        h = hashes.get(s)
        count[h] = count.get(h, 0) + 1
    watermark = {s for s, h in hashes.items() if count[h] >= SO_LAN_LAP_LA_HINH_NEN}

    # 2) bỏ trang bìa: bắt đầu từ đoạn văn dài đầu tiên hoặc câu hỏi đầu tiên
    q_re = re.compile(r'<p>((?:\s|<[^>]+>)*)C[âÂ]U(?:\s+H[ỏỎ]I)?\s*(\d+)\s*[:.\-–)]\s*(.*?)</p>', re.S | re.I)
    starts = [m.start() for m in re.finditer(r"<p>", body)
              if len(strip_tags(body[m.start():body.find("</p>", m.start())])) >= 200]
    first_q = q_re.search(body)
    cut = min([x for x in [starts[0] if starts else None, first_q.start() if first_q else None] if x is not None] or [0])
    body = body[cut:]

    # 3) ảnh: nén song song, ghi kích thước để trang không bị giật khi ảnh tải
    os.makedirs(os.path.join(outdir, "img"), exist_ok=True)
    jobs = {}
    def compress(path):
        name = "a" + hashes[path][:10] + ".jpg"
        im = Image.open(path)
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA"); bg = Image.new("RGB", im.size, "white")
            bg.paste(im, mask=im.split()[-1]); im = bg
        else:
            im = im.convert("RGB")
        im.thumbnail((ANH_TOI_DA, ANH_TOI_DA))
        im.save(os.path.join(outdir, "img", name), "JPEG", quality=CHAT_LUONG_ANH, optimize=True, progressive=True)
        return name, im.size
    todo = sorted({m.group(1) for m in img_re.finditer(body)} & set(hashes) - watermark)
    with ThreadPoolExecutor() as ex:
        for s, r in zip(todo, ex.map(compress, todo)):
            jobs[s] = r

    def img_sub(m):
        s, style = m.group(1), m.group(2) or ""
        if s not in jobs:
            return ""
        name, (w, h) = jobs[s]
        wi = re.search(r"width:([\d.]+)in", style)
        maxw = min(int(float(wi.group(1)) * 110), w) if wi else w
        return f'<img src="img/{name}" width="{w}" height="{h}" loading="lazy" decoding="async" alt="" style="width:min(100%,{maxw}px)">'
    body = img_re.sub(img_sub, body)

    # 4) câu hỏi -> mục có id, tiêu đề nổi bật
    questions = []
    def q_sub(m):
        n, text = m.group(2), strip_tags(m.group(3))
        questions.append((n, text))
        return (f'</section>\n<section class="q" id="cau-{n}">\n'
                f'<h2 class="qtitle"><span class="qnum">Câu {n}</span> {html.escape(text)}</h2>')
    body = q_re.sub(q_sub, body)

    # 5) nhãn "Trả lời"
    body = re.sub(r'<p>(?:\s|<(?:strong|em)>)*Trả lời(?:\s|</?(?:strong|em)>)*:?(?:\s|</?(?:strong|em)>)*',
                  '<p><span class="ans">Trả lời:</span> ', body, flags=re.I)
    body = re.sub(r"<table[^>]*>", '<div class="tw"><table>', body).replace("</table>", "</table></div>")
    body = re.sub(r"<p>\s*</p>", "", body)

    # 6) logo
    logo_html, icon = "", ""
    lp = os.path.join(HERE, LOGO) if LOGO else ""
    if lp and os.path.exists(lp):
        im = Image.open(lp).convert("RGB"); im.thumbnail((300, 300))
        im.save(os.path.join(outdir, "img", "logo.jpg"), quality=85)
        logo_html = '<img class="logo" src="img/logo.jpg" width="110" height="110" alt="Logo">'
        icon = '<link rel="icon" href="img/logo.jpg">'

    make_qr_files(outdir, lp)

    pills = "".join(f'<a href="#cau-{n}">Câu {n}</a>' for n, _ in questions)
    toc = "".join(f'<li><a href="#cau-{n}"><b>Câu {n}</b><span>{html.escape(t)}</span></a></li>'
                  for n, t in questions)
    tpl = open(os.path.join(HERE, "mau.html"), encoding="utf-8").read()
    page = (tpl.replace("{{TIEU_DE_NHO}}", html.escape(TIEU_DE_NHO))
               .replace("{{TIEU_DE}}", html.escape(TIEU_DE))
               .replace("{{MOC_THOI_GIAN}}", html.escape(MOC_THOI_GIAN))
               .replace("{{CHAN_TRANG}}", html.escape(CHAN_TRANG))
               .replace("{{LOGO}}", logo_html).replace("{{ICON}}", icon)
               .replace("{{NUT_CAU}}", pills).replace("{{MUC_LUC}}", toc)
               .replace("{{NOI_DUNG}}", body)
               .replace("{{URL_TRANG}}", html.escape(URL_TRANG)))
    open(os.path.join(outdir, "index.html"), "w", encoding="utf-8").write(page)
    shutil.rmtree(tmp, ignore_errors=True)

    size = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(outdir) for f in fs)
    print(f"Xong trong {time.time()-t0:.1f} giây -> public/")
    print(f"  {len(questions)} câu hỏi: " + ", ".join(n for n, _ in questions))
    print(f"  Mã QR -> {URL_TRANG}  (public/qr.png, public/qr-in-an.png)")
    print(f"  {len(jobs)} ảnh, bỏ {len(watermark)} hình nền, dung lượng {size/1e6:.1f} MB")
    if not questions:
        print("  CẢNH BÁO: không tìm thấy câu hỏi nào. Đoạn câu hỏi phải bắt đầu bằng 'Câu 1:' hoặc 'Câu hỏi 1:'.")


if __name__ == "__main__":
    src = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else newest_word()
    out = os.path.join(ROOT, "public")
    print("Đang xử lý:", os.path.basename(src))
    if os.path.isdir(out):
        shutil.rmtree(out)
    build(src, out)
