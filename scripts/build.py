#!/usr/bin/env python3
"""
Build script: đọc data/*.json (nguồn CMS), sinh lại các trang tĩnh trong html/.

Quy ước quan trọng (PHẢI khớp với gas/Code.js — đổi 1 bên phải đổi bên kia):
  - data/posts.json là mảng đã sắp MỚI NHẤT TRƯỚC (bài mới `unshift` ở đầu mảng khi CMS lưu).
  - data/categories.json sắp theo field "order" tăng dần.

Chạy: python3 scripts/build.py   (từ thư mục gốc epic/)
Idempotent: chạy 2 lần liên tiếp không được tự sinh thêm diff.
"""
import json
import re
import html as htmlmod
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML_DIR = ROOT / "html"
DATA_DIR = ROOT / "data"
TEMPLATES_DIR = ROOT / "templates"
MANIFEST_PATH = DATA_DIR / ".build-manifest.json"

# Trang KHÔNG do build.py sinh ra — không bao giờ được patch nav/footer/pills nếu không có
# đúng class/id mong đợi, và tuyệt đối không nằm trong danh sách xoá mồ côi.
NAV_DROPDOWN_RE = re.compile(r'(<ul class="nav-dropdown">\n)(.*?)(\n\s*</ul>)', re.S)
FOOTER_NAV_RE = re.compile(
    r'(<nav class="footer-nav" aria-label="Liên kết footer">\n)(.*?)(\n\s*</nav>)', re.S
)
CATEGORY_PILLS_RE = re.compile(
    r'(<ul class="category-pills"([^>]*)>\n)(.*?)(\n\s*</ul>)', re.S
)
ARTICLE_LIST_RE = re.compile(
    r'(<div class="article-list"([^>]*)>\n)(.*?)(\n\s*</div>)', re.S
)
PAGINATION_HIDDEN_RE = re.compile(r'(<div class="pagination" id="pagination")( hidden)?(>)')


def load_json(path, default):
    if not path.exists():
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def esc(s):
    return htmlmod.escape(str(s or ""), quote=True)


def load_categories():
    cats = load_json(DATA_DIR / "categories.json", [])
    return sorted(cats, key=lambda c: c.get("order", 0))


def load_posts_index():
    return load_json(DATA_DIR / "posts.json", [])


def load_post_detail(slug):
    return load_json(DATA_DIR / "posts" / (slug + ".json"), None)


# ================= Render các khối dùng chung (nav-dropdown / footer-nav / category-pills) =====

def render_nav_dropdown(categories):
    lines = [
        '          <li><a href="{0}.html">{1}</a></li>'.format(c["slug"], esc(c["name"]))
        for c in categories
    ]
    return "\n".join(lines)


def render_footer_nav(categories):
    lines = ['            <a href="index.html">Gần đây</a>']
    for c in categories:
        lines.append('            <a href="{0}.html">{1}</a>'.format(c["slug"], esc(c["name"])))
    lines.append('            <a href="about.html">Về tôi</a>')
    lines.append('            <a href="membership.html">Thành viên</a>')
    lines.append('            <a href="#newsletterForm" class="is-bold">Bản tin miễn phí</a>')
    return "\n".join(lines)


def render_category_pills(categories, mode, current_slug=None):
    """mode: 'home' (trang chủ, không có Tất cả/is-active) hoặc 'other' (mọi trang khác,
    có 'Tất cả' đầu tiên; is-active nếu slug khớp current_slug)."""
    lines = []
    if mode != "home":
        lines.append('      <li><a href="index.html">Tất cả</a></li>')
    for c in categories:
        active = ' class="is-active"' if c["slug"] == current_slug else ""
        lines.append(
            '      <li><a href="{0}.html"{2}>{1}</a></li>'.format(c["slug"], esc(c["name"]), active)
        )
    return "\n".join(lines)


def render_article_item(post, categories_by_slug):
    cat = categories_by_slug.get(post["category"])
    cat_name = esc(cat["name"]) if cat else ""
    excerpt = esc(post.get("description", "")).rstrip()
    if excerpt and not excerpt.endswith(("…", "&hellip;")):
        excerpt = excerpt + " &hellip;"
    return (
        '      <article class="article-item">\n'
        '        <a class="article-category" href="{slug_cat}.html">{cat_name}</a>\n'
        '        <h2><a href="{slug}.html">{title}</a></h2>\n'
        '        <p class="excerpt">{excerpt}</p>\n'
        '        <a href="{slug}.html" class="read-more">Đọc tiếp</a>\n'
        '      </article>'
    ).format(
        slug_cat=post["category"], cat_name=cat_name, slug=post["slug"],
        title=esc(post["title"]), excerpt=excerpt,
    )


def render_article_list(posts, categories_by_slug, empty_message):
    if not posts:
        return '      <p class="intro">{0}</p>'.format(esc(empty_message))
    return "\n".join(render_article_item(p, categories_by_slug) for p in posts)


# ================= Patch các trang tĩnh đã có sẵn (không tự sinh lại toàn trang) ================

def patch_shared_blocks(text, categories, page_kind, current_slug=None):
    """Áp cho MỌI trang .html ở gốc html/ có chứa các khối này — nav-dropdown, footer-nav,
    category-pills (nếu có). page_kind: 'home' | 'category' | 'other'."""
    if NAV_DROPDOWN_RE.search(text):
        text = NAV_DROPDOWN_RE.sub(
            lambda m: m.group(1) + render_nav_dropdown(categories) + m.group(3), text, count=1
        )
    if FOOTER_NAV_RE.search(text):
        text = FOOTER_NAV_RE.sub(
            lambda m: m.group(1) + render_footer_nav(categories) + m.group(3), text, count=1
        )
    if CATEGORY_PILLS_RE.search(text):
        mode = "home" if page_kind == "home" else "other"
        pills = render_category_pills(categories, mode, current_slug)
        text = CATEGORY_PILLS_RE.sub(
            lambda m: m.group(1) + pills + m.group(4), text, count=1
        )
    return text


def patch_index(text, categories, posts, categories_by_slug):
    text = patch_shared_blocks(text, categories, "home")
    article_html = render_article_list(posts, categories_by_slug, "Bài đầu tiên sắp lên.")
    text = ARTICLE_LIST_RE.sub(
        lambda m: m.group(1) + article_html + m.group(4), text, count=1
    )
    hidden_attr = "" if len(posts) > 5 else " hidden"
    text = PAGINATION_HIDDEN_RE.sub(lambda m: m.group(1) + hidden_attr + m.group(3), text, count=1)
    return text


# ================= Render trang danh mục / bài viết từ template ================================

def render_template(name, mapping):
    raw = (TEMPLATES_DIR / name).read_text(encoding="utf-8")
    for key, value in mapping.items():
        raw = raw.replace("{{" + key + "}}", value)
    return raw


def build_category_page(cat, categories, posts_for_cat, categories_by_slug):
    article_html = render_article_list(posts_for_cat, categories_by_slug, "Bài đầu tiên sắp lên.")
    out = render_template("category.html", {
        "NAME": esc(cat["name"]),
        "SLUG": cat["slug"],
        "DESCRIPTION": esc(cat["description"]),
        "ARTICLE_LIST": article_html,
        "NAV_DROPDOWN": render_nav_dropdown(categories),
        "FOOTER_NAV": render_footer_nav(categories),
        "CATEGORY_PILLS": render_category_pills(categories, "other", cat["slug"]),
    })
    return out


def build_post_page(post, detail, categories):
    audience = (detail.get("audience") or "").strip()
    audience_line = (
        '      <p class="post-audience">Dành cho: {0}</p>'.format(esc(audience))
        if audience else ""
    )
    out = render_template("post.html", {
        "TITLE": esc(detail["title"]),
        "SLUG": detail["slug"],
        "DESCRIPTION": esc(detail["description"]),
        "CATEGORY_NAME": esc(next(
            (c["name"] for c in categories if c["slug"] == detail["category"]), ""
        )),
        "AUDIENCE_LINE": audience_line,
        "INTRO": detail.get("intro", ""),
        "CONTENT_HTML": detail.get("content_html", ""),
        "NAV_DROPDOWN": render_nav_dropdown(categories),
        "FOOTER_NAV": render_footer_nav(categories),
        "CATEGORY_PILLS": render_category_pills(categories, "other", None),
    })
    # AUDIENCE_LINE rỗng để lại 1 dòng trống - dọn cho sạch diff.
    if not audience_line:
        out = out.replace("\n\n      <p class=\"intro\">", "\n      <p class=\"intro\">")
    return out


# ================= search-index.js =================

STATIC_SEARCH_PAGES = [
    {
        "type": "Trang",
        "title": "Về blog này, và về mình",
        "url": "ve-blog-va-nguoi-viet.html",
        "tags": ["giới thiệu", "tác giả"],
    },
]


def build_search_index(categories, posts, categories_by_slug):
    entries = []
    for c in categories:
        entries.append({
            "type": "Chủ đề",
            "title": c["name"],
            "url": c["slug"] + ".html",
            "tags": [c["name"].lower(), "chủ đề"],
        })
    for p in posts:
        cat = categories_by_slug.get(p["category"])
        entries.append({
            "type": "Bài viết",
            "title": p["title"],
            "url": p["slug"] + ".html",
            "pillar": cat["name"] if cat else "",
            "tags": [cat["name"].lower()] if cat else [],
        })
    entries.extend(STATIC_SEARCH_PAGES)

    lines = [
        "// Danh sách nội dung có thể tìm kiếm: các chủ đề và bài viết thật.",
        "// File này do scripts/build.py tự sinh từ data/categories.json + data/posts.json - không sửa tay.",
        "window.SITE_SEARCH_INDEX = [",
    ]
    for i, e in enumerate(entries):
        comma = "," if i < len(entries) - 1 else ""
        parts = ['type: "{0}"'.format(e["type"]), 'title: "{0}"'.format(js_str(e["title"])),
                  'url: "{0}"'.format(e["url"])]
        if "pillar" in e:
            parts.append('pillar: "{0}"'.format(js_str(e["pillar"])))
        tags = ", ".join('"{0}"'.format(js_str(t)) for t in e["tags"])
        parts.append("tags: [{0}]".format(tags))
        lines.append("  {\n    " + ",\n    ".join(parts) + "\n  }" + comma)
    lines.append("];")
    return "\n".join(lines) + "\n"


def js_str(s):
    return str(s or "").replace("\\", "\\\\").replace('"', '\\"')


# ================= Xoá file mồ côi (chỉ trong manifest do build.py quản lý) =====================

def load_manifest():
    return set(load_json(MANIFEST_PATH, []))


def save_manifest(names):
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(names), f, ensure_ascii=False, indent=2)
        f.write("\n")


# ================= Main =================

def main():
    categories = load_categories()
    categories_by_slug = {c["slug"]: c for c in categories}
    posts_index = load_posts_index()  # đã sắp mới nhất trước

    print("Danh mục: {0}".format(", ".join(c["slug"] for c in categories)))
    print("Bài viết: {0}".format(", ".join(p["slug"] for p in posts_index)))

    new_manifest = set()

    # 1) Trang danh mục
    for cat in categories:
        posts_for_cat = [p for p in posts_index if p["category"] == cat["slug"]]
        out = build_category_page(cat, categories, posts_for_cat, categories_by_slug)
        fname = cat["slug"] + ".html"
        (HTML_DIR / fname).write_text(out, encoding="utf-8")
        new_manifest.add(fname)
        print("  ghi  " + fname)

    # 2) Trang bài viết
    for p in posts_index:
        detail = load_post_detail(p["slug"])
        if not detail:
            print("  CẢNH BÁO: thiếu data/posts/{0}.json - bỏ qua".format(p["slug"]))
            continue
        out = build_post_page(p, detail, categories)
        fname = p["slug"] + ".html"
        (HTML_DIR / fname).write_text(out, encoding="utf-8")
        new_manifest.add(fname)
        print("  ghi  " + fname)

    # 3) Patch trang chủ (2 vùng: articleList + categoryPills, + pagination hidden)
    index_path = HTML_DIR / "index.html"
    index_text = index_path.read_text(encoding="utf-8")
    index_text = patch_index(index_text, categories, posts_index, categories_by_slug)
    index_path.write_text(index_text, encoding="utf-8")
    print("  patch index.html")

    # 4) Patch nav-dropdown/footer-nav/category-pills trên MỌI trang .html khác ở gốc html/
    #    (không đụng file trong html/admin/, không đụng lại index.html/trang danh mục vừa ghi ở
    #    trên - chúng đã đúng ngay từ lúc render template).
    generated = new_manifest | {"index.html"}
    for path in sorted(HTML_DIR.glob("*.html")):
        if path.name in generated:
            continue
        text = path.read_text(encoding="utf-8")
        original = text
        page_kind = "category" if path.stem in categories_by_slug else "other"
        current_slug = path.stem if page_kind == "category" else None
        text = patch_shared_blocks(text, categories, page_kind, current_slug)
        if text != original:
            path.write_text(text, encoding="utf-8")
            print("  patch " + path.name)

    # 5) search-index.js
    search_js = build_search_index(categories, posts_index, categories_by_slug)
    search_path = HTML_DIR / "assets" / "js" / "search-index.js"
    search_path.write_text(search_js, encoding="utf-8")
    print("  ghi  assets/js/search-index.js")

    # 6) Xoá file mồ côi (chỉ trong phạm vi manifest cũ do CHÍNH build.py từng tạo)
    old_manifest = load_manifest()
    orphans = old_manifest - new_manifest
    for fname in orphans:
        fpath = HTML_DIR / fname
        if fpath.exists():
            fpath.unlink()
            print("  xoá  " + fname)
    save_manifest(new_manifest)

    print("Xong.")


if __name__ == "__main__":
    main()
