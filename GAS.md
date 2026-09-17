# GAS.md — Guideline CMS nguyenthevan.com

> Đọc file này TOÀN BỘ trước khi sửa bất cứ file nào trong `gas/`, `scripts/build.py`,
> `templates/*.html`, hoặc `data/*.json`. Đây là nguồn quyết định CHỐT — không tự suy đoán
> khác. Theo playbook `~/.claude/skills/free-cms-static-site-pipeline/`.

Exec URL hiện tại (đã deploy từ trước bởi khách hàng):
`https://script.google.com/macros/s/AKfycbz3TiD7SLNTdJ05Xuhd_90GcieZr1yuGGfpB4SYNb17kkAKB0SkOJO3pJ3Lqfu6X69P/exec`

## I. Đăng nhập

1. Luồng: gửi OTP → xác nhận → vào trang Admin. Không mật khẩu, không dựa vào session Google
   (user thật không cùng Workspace domain với chủ script).
2. Chỉ email đã có trong Sheet `Users` mới được gửi OTP.
3. Chủ script (người deploy) LUÔN hợp lệ/luôn có quyền `root` cao nhất — KHÔNG lưu trong Sheet,
   KHÔNG hiện trong UI quản lý người dùng. `requestOtp` phải tự cho phép ngoại lệ với chính
   email này (`ownerEmail_()`), song song với việc tra Sheet — nếu không sẽ tự khoá chủ script
   ra khỏi hệ thống ngay từ đầu.
4. Phân quyền: **3 cấp, không có `viewer`**: `root` (chủ script, ngầm định) > `admin` (hiển thị
   UI: "Admin") > `editor` (hiển thị UI: "Editor"). `ROLE_RANK = {editor:1, admin:2, root:3}`.
   - `editor`: CRUD Bài viết + CRUD Danh mục bài viết + xem tab Podcast (placeholder tĩnh).
   - `admin`: mọi quyền của `editor` + Quản lý người dùng (thêm/sửa/xoá `admin`/`editor` qua
     CMS — KHÔNG bao giờ đụng được dòng `root`).
   - `root`: toàn quyền, chỉ sửa được bằng tay trong Sheet `Users` (thực ra không cần dòng nào
     trong Sheet — ngầm định qua `ownerEmail_()`).
5. Mã OTP sống 10 phút, cooldown 60 giây/email, tối đa 5 lần nhập sai rồi phải xin mã mới. Token
   phiên đăng nhập sống 30 ngày, lưu `localStorage`.
6. Server luôn tự kiểm tra quyền (`requireRole_`) ở MỌI hành động — không tin việc ẩn nút/menu
   trên giao diện là đủ để bảo mật.

## II. Đối với Bài viết

1. Field trên giao diện (KHÔNG có ảnh bìa/cover — chốt rõ với khách: "bài viết không có cover
   luôn"):
   - Tiêu đề
   - Slug: tự sinh từ tiêu đề (bỏ dấu, gạch ngang), BẤT BIẾN sau khi đã Lưu lần đầu (mục III).
   - Danh mục: `<select>` load từ `data/categories.json`, bắt buộc chọn 1. Server validate danh
     mục gửi lên phải tồn tại trong danh sách hiện tại, không tin `<select>` phía client.
   - Mô tả: dùng làm `meta description` + `og:description` + đoạn trích (excerpt) trong danh
     sách bài viết.
   - "Dành cho: lớp …" — field text ngắn, TUỲ CHỌN (khớp `.post-audience` đã có sẵn trên site
     thật). Để trống thì KHÔNG render dòng này trong trang (khác hẳn placeholder tĩnh "lớp …"
     từng có ở 1 số bài migrate — sau migrate field này để trống thật, không giữ "…").
   - Nội dung: TinyMCE. **CÓ chèn ảnh trong content** (khách xác nhận rõ: "bài viết được thêm
     ảnh như bình thường") — bắt buộc nút chèn ảnh nhanh (`quickimage`, mở thẳng file picker,
     KHÔNG dùng dialog "Image" mặc định của TinyMCE — xem gas-backend-patterns.md mục 4). Cần
     caption/alt tự động đồng bộ theo tiêu đề (mục 4b cùng file).
2. Field KHÔNG có ô nhập — server tự suy lúc Lưu:
   - `seo_title` / `breadcrumb` / `og:title` = luôn theo `title` hiện tại.
   - `date` = ngày Lưu lần đầu; bài đã có thì GIỮ NGUYÊN ngày gốc.
3. Danh sách trong Admin tải qua GAS đọc GitHub Contents API mỗi lần mở (`boot()`) — luôn mới
   nhất, chấp nhận tốn thêm 1 API call/lần mở (số bài ít, không đáng lo quota).
4. Ảnh nội dung: nén/resize phía client (canvas) trước khi upload — cạnh dài tối đa 1600px,
   JPEG chất lượng ~0.85. Không chặn thao tác khi đang upload. Ảnh RIÊNG theo từng bài (tên đặt
   tất định theo slug: `<slug>-content-<N>.jpg`) — xoá bài xoá kèm được đúng ảnh của bài đó, an
   toàn (không dùng chung).

## III. Đối với sửa Bài viết

- Slug/URL công khai bất biến sau khi đã lưu lần đầu — chặn CẢ server (`throw` nếu đổi) LẪN
  client (disable input slug khi mở bản ghi đã tồn tại để sửa).
- Site nguyenthevan.com có MỌI trang nằm PHẲNG ở gốc `html/` (không có thư mục con lồng nhau) —
  vì vậy đường dẫn ảnh trong content luôn là `assets/images/posts/<file>` (1 tầng, không có vấn
  đề "độ sâu tương đối" khác nhau giữa các trang).
- Form soạn bài dùng lại DOM cho cả "tạo mới" và "sửa": nhớ RESET `disabled = false` cho input
  slug khi mở form tạo mới (trạng thái khoá từ lần sửa trước dễ dính lại nếu không set lại
  tường minh).

## IV. Đối với xoá Bài viết

- Xoá ĐỦ: `data/posts/<slug>.json` + gỡ khỏi `data/posts.json` + mọi ảnh nội dung của bài đó
  (`<slug>-content-*.jpg`, an toàn vì ảnh riêng 1-1 theo bài — mục II.4).
- Bắt buộc có bước xác nhận (modal Huỷ/Xoá) trước khi xoá thật — Contents API không có "thùng
  rác", không thể hoàn tác.

## Đối với Danh mục bài viết (song song với mục II-IV, cùng nguyên tắc)

- Field: Tên danh mục, Slug (tự sinh, BẤT BIẾN sau khi Lưu lần đầu — đổi tên thật thì xoá tạo
  lại danh mục mới, không rename tại chỗ), Mô tả (dùng làm hero intro của trang danh mục + meta
  description), Thứ tự hiển thị (`order` — quyết định thứ tự trong menu "Bài viết", footer, và
  category-pills trên toàn site).
- Lưu trên GitHub: `data/categories.json` — TOÀN BỘ danh mục trong 1 file (ít bản ghi, không
  tách index/detail).
- Xoá danh mục: CHẶN nếu còn bài viết thuộc danh mục đó (đếm trong `data/posts.json`) — throw
  lỗi rõ ràng yêu cầu chuyển bài sang danh mục khác trước. Không xoá kéo theo bài viết.
- Thêm/xoá/đổi `order` một danh mục → CI build lại patch `nav-dropdown`, `footer-nav`,
  `category-pills` trên TOÀN BỘ trang tĩnh của site (không chỉ trang danh mục) — xem
  `scripts/build.py`.

## V. Đối với form công khai (Liên hệ...)

Không áp dụng cho dự án này. Site có sẵn form newsletter riêng (`#newsletterForm`, xử lý bằng
`assets/js/main.js` hiện có) — không thuộc phạm vi CMS này, CMS này không có `doPost` public
nào.

## VI. Đối với form công khai loại 2 (Đặt xe/Đơn hàng...)

Không áp dụng cho dự án này.

## VII. UX chung (mọi Lưu/Xoá/Đổi trạng thái trong Admin)

- 2 modal riêng biệt (không `alert()`/`confirm()` native, không toast tự ẩn): XÁC NHẬN
  (Huỷ/Xoá) trước khi xử lý, THÔNG BÁO kết quả (1 nút Đóng) sau khi xử lý xong.
- Mọi nút async: disable + spinner trong lúc chờ, tự phục hồi kể cả khi lỗi (`finally`).
- Sau Lưu/Xoá thành công: danh sách trong Admin tự cập nhật ngay, không đợi F5.
- Chuyển tab trong Admin chỉ là hiệu ứng giao diện — không tải lại toàn trang.
- Đăng nhập lần đầu: 1 lượt gọi `boot()` duy nhất lấy hết dữ liệu cần.
- Lần vào Admin sau: hiện ngay từ cache `localStorage` (stale-while-revalidate), rồi mới âm
  thầm làm mới.
- Phiên bản client (`CLIENT_BUILD`) **băm MD5 tự động từ nội dung `app.html` + `js.html`**
  (`clientBuild_()` trong `Code.js`, đúng pattern xevip) — KHÔNG dùng hằng số gõ tay. Sửa
  `app.html`/`js.html` là mọi key `localStorage` liên quan tự đổi theo, cache cũ tự bị dọn.
  Không cần bump tay, không được thêm lại hằng số gõ tay (xem `gas/README.md`).

## VIII. Kiến trúc lưu trữ

- **Google Sheet "nguyenthevan CMS Data"** (tự tạo lần đầu chạy, lưu ID vào
  `SPREADSHEET_ID`) — CHỈ 1 sheet:
  - `Users`: cột `email`, `role` (giá trị hợp lệ: `admin`, `editor` — dòng `root` KHÔNG BAO GIỜ
    xuất hiện ở đây).
- **GitHub (repo `tranquanghuy-rightsvn/epicacademic`, nhánh `master`, qua Contents API)**:
  - `data/categories.json` — toàn bộ danh mục: `[{slug, name, description, order}]`.
  - `data/posts.json` — index nhẹ mọi bài, **mảng đã sắp mới nhất TRƯỚC** (bài mới `unshift` ở
    đầu mảng — quy ước này dùng chung giữa `Code.js` VÀ `scripts/build.py`, đổi 1 bên phải đổi
    bên kia): `[{slug, title, category, description, audience, date, updated_at}]`.
  - `data/posts/<slug>.json` — nội dung đầy đủ 1 bài (thêm `content_html`).
  - `html/assets/images/posts/<slug>-content-<N>.jpg` — ảnh nội dung bài viết, ghi THẲNG vào vị
    trí site thật.
- File "danh sách tổng" (`data/posts.json`, `data/categories.json`) LUÔN ghi SAU CÙNG trong 1
  thao tác Lưu/Xoá — đây là file CI theo dõi để trigger build (`.github/workflows/build.yml`).
- Độ trễ thực tế từ lúc Lưu tới lúc thấy trên site thật: build CI (~1-2 phút) + **thời gian
  deploy hosting** — CHƯA XÁC ĐỊNH được vì nền tảng hosting của site hiện chưa rõ (xem mục
  "Việc còn thiếu" bên dưới).

## IX. Checklist bug thường gặp ở dự án này

Chưa có bug nào gặp — đây là lần đầu triển khai CMS cho dự án này. Cập nhật mục này khi gặp bug
thật trong quá trình vận hành (không copy bug của dự án khác vào đây).

## X. Script Properties

- `GITHUB_TOKEN` — Personal Access Token quyền ghi repo `epicacademic` (fine-grained: Contents
  = Read and write). BẮT BUỘC, tự điền tay, không có mặc định.
- `GITHUB_OWNER` = `tranquanghuy-rightsvn`
- `GITHUB_REPO` = `epicacademic`
- `GITHUB_BRANCH` = `master`
- `SPREADSHEET_ID` — KHÔNG cần tự điền, code tự tạo Sheet lần đầu chạy và tự lưu lại.

## Việc còn thiếu ngoài phạm vi đã triển khai (cần khách xác nhận)

- **Nền tảng hosting site tĩnh chưa rõ** (không thấy `vercel.json`/`wrangler.toml` trong repo) —
  `.github/workflows/build.yml` chỉ build lại `html/` từ `data/` và commit, KHÔNG có bước deploy
  tự động. Cần biết site đang deploy qua đâu để nối bước deploy sau khi CI build xong, nếu không
  mỗi lần CMS lưu bài chỉ cập nhật `html/` trong repo mà site thật KHÔNG tự cập nhật theo.
- `robots.txt`/`sitemap.xml` hiện CHƯA tồn tại trên site — không tự tạo vì ngoài phạm vi yêu cầu
  ban đầu (chỉ được yêu cầu dựng CMS). Khi có, nhớ áp mục 6b của `static-site-build.md` cho
  `/admin/` (chặn bot bằng meta+header, KHÔNG khai `Disallow` trong `robots.txt`).
