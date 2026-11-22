# Bài dự thi – 70 năm Ngày truyền thống Trường Sĩ quan Pháo binh

Trang web đọc bài dự thi, tạo tự động từ file Word. Địa chỉ trên Vercel: https://baiduthi-70nam-sqpb.vercel.app

```
baiduthi-70nam-sqpb/
├─ tai-lieu/      ← chép file Word (.doc/.docx) vào đây (không đưa lên git)
├─ cong-cu/
│  ├─ taoweb.py   ← chương trình chuyển Word → trang web (sửa tiêu đề ở phần CẤU HÌNH)
│  ├─ mau.html    ← giao diện (màu sắc, cỡ chữ)
│  └─ logo.jpg
├─ public/        ← trang web đã tạo – Vercel đăng đúng thư mục này
└─ vercel.json
```

## Cài một lần

1. [Python 3](https://www.python.org/downloads/) – trên Windows nhớ tích **Add python to PATH**.
2. [Pandoc](https://pandoc.org/installing.html).
3. [Git](https://git-scm.com/downloads).
4. Mở thư mục này trong VS Code → `Ctrl+Shift+P` → **Tasks: Run Task** → **Cài thư viện (chạy 1 lần)**.

File `.doc` đời cũ cần thêm LibreOffice; hoặc mở bằng Word → *Lưu thành* `.docx`.

## Kết nối Vercel (một lần)

```bash
git init
git add .
git commit -m "Trang bài dự thi"
git branch -M main
git remote add origin https://github.com/<tài-khoản>/baiduthi-70nam-sqpb.git
git push -u origin main
```

Trên vercel.com: **Add New → Project** → chọn repo `baiduthi-70nam-sqpb` → giữ **Project Name** đúng như vậy → **Deploy**.
(Có thể dùng nút *Source Control* bên trái VS Code thay cho các lệnh git.)

## Mỗi lần thay file Word

1. Chép file Word mới vào `tai-lieu/` (công cụ tự lấy file mới nhất).
2. `Ctrl+Shift+B` → trang mới được tạo vào `public/` trong vài giây.
3. Xem thử: **Tasks: Run Task → Xem thử trên máy**, mở http://localhost:8000
4. Đưa lên:
   ```bash
   git add -A
   git commit -m "Cập nhật bài dự thi"
   git push
   ```
   Vercel tự đăng bản mới sau khoảng 1 phút. Địa chỉ không đổi nên **mã QR giữ nguyên**.

## Yêu cầu với file Word

- Mỗi câu hỏi là một đoạn riêng, bắt đầu bằng `Câu 1:` hoặc `Câu hỏi 1:` (dấu `:` hay `.` đều được).
- Ảnh nền/logo chìm lặp lại nhiều lần và trang bìa được tự động bỏ.
