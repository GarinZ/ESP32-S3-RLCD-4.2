#!/usr/bin/env python3
"""Fetch Waveshare ESP32-S3-RLCD-4.2 docs and export as clean Markdown.

Re-run to refresh the exported docs after upstream changes.
"""
import os
import re
import sys
import urllib.request
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from markdownify import markdownify as md

BASE = "https://docs.waveshare.net"
DOC_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(DOC_DIR, "assets")

# page path -> output filename (order matters for the TOC)
PAGES = [
    ("/ESP32-S3-RLCD-4.2", "01-overview.md"),
    ("/ESP32-S3-RLCD-4.2/Resources-And-Documents", "02-resources-and-documents.md"),
    ("/ESP32-S3-RLCD-4.2/Arduino", "03-arduino.md"),
    ("/ESP32-S3-RLCD-4.2/ESP-IDF", "04-esp-idf.md"),
    ("/ESP32-S3-RLCD-4.2/XiaoZhi_AI", "05-xiaozhi-ai.md"),
    ("/ESP32-S3-RLCD-4.2/FAQ", "06-faq.md"),
    ("/ESP32-S3-RLCD-4.2/Technical-Support", "07-technical-support.md"),
]

LINK_MAP = {p: f for p, f in PAGES}
# longest prefix first so /.../Arduino isn't captured by /.../
SORTED_PATHS = sorted(LINK_MAP, key=len, reverse=True)


_DATA_URI_COUNTER = 0


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def download(url):
    """Download a binary asset, return local relative path or None."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        path = urlparse(url).path
        stem, ext = os.path.splitext(os.path.basename(path))
        if ext.lower() not in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"):
            ext = ".bin"
        stem = re.sub(r"[^a-zA-Z0-9._-]", "-", stem)[:100]
        fname = f"{stem}{ext}"
        dest = os.path.join(ASSET_DIR, fname)
        if not os.path.exists(dest):
            with open(dest, "wb") as f:
                f.write(data)
        return f"assets/{fname}"
    except Exception as e:  # noqa: BLE001
        print(f"    !! asset failed {url}: {e}", file=sys.stderr)
        return None


def convert_table(table, soup, idx, tables):
    """Convert a bs4 <table> to GFM markdown, register placeholder."""
    rows = []
    header = []
    thead = table.find("thead")
    if thead:
        for th in thead.find_all(["th", "td"]):
            header.append(th.get_text(" ", strip=True))
    # colspan aware (simple): pad headers
    body_rows = table.find("tbody") or table
    for tr in body_rows.find_all("tr"):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
        if cells:
            rows.append(cells)
    ncol = max([len(header)] + [len(r) for r in rows]) if rows else len(header)
    if ncol == 0:
        return
    header = (header + [""] * ncol)[:ncol]
    lines = ["| " + " | ".join(header) + " |",
             "| " + " | ".join(["---"] * ncol) + " |"]
    for r in rows:
        r = (r + [""] * ncol)[:ncol]
        lines.append("| " + " | ".join(r) + " |")
    token = f"@@TABLE{idx}@@"
    tables.append("\n".join(lines))
    table.replace_with(soup.new_string(f"\n\n{token}\n\n"))


def convert_admonitions(article, soup):
    for ad in article.find_all("div", class_="theme-admonition"):
        heading = ad.find("div", class_="admonitionHeading_Gvgb")
        title = heading.get_text(" ", strip=True) if heading else ""
        content = ad.find("div", class_="admonitionContent_BuS1")
        inner = content.decode_contents() if content else ad.decode_contents()
        if title:
            inner = f"<p><strong>{title}</strong></p>" + inner
        block = soup.new_tag("blockquote")
        # parse inner html into the blockquote
        block.append(BeautifulSoup(inner, "html.parser"))
        ad.replace_with(block)


def convert_iframes(article, soup):
    for iframe in article.find_all("iframe"):
        src = iframe.get("src") or ""
        bvid = re.search(r"bvid=([A-Za-z0-9]+)", src)
        if bvid:
            url = f"https://www.bilibili.com/video/{bvid.group(1)}"
        else:
            url = urljoin(BASE, src) if src else ""
        note = soup.new_tag("p")
        note.append(soup.new_string("视频教程："))
        a = soup.new_tag("a", href=url)
        a.string = url
        note.append(a)
        iframe.replace_with(note)


def fix_headings(article):
    # remove hash-link self anchors that Docusaurus injects into headings
    for a in article.find_all("a", class_="hash-link"):
        a.decompose()


def save_data_uri(img):
    """Decode a data: URI image to a file, return local rel path or None."""
    import base64
    global _DATA_URI_COUNTER
    _DATA_URI_COUNTER += 1
    src = img.get("src") or ""
    m = re.match(r"data:(image/[a-zA-Z0-9.+-]+);base64,(.*)", src, re.S)
    if not m:
        return None
    mime, b64 = m.group(1), m.group(2)
    ext = "." + mime.split("/")[-1].replace("jpeg", "jpg")
    if ext not in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"):
        ext = ".bin"
    alt = re.sub(r"[^a-zA-Z0-9._-]", "-", img.get("alt") or "").strip("-")[:60]
    stem = alt or "icon"
    fname = f"{stem}-{_DATA_URI_COUNTER}{ext}"
    dest = os.path.join(ASSET_DIR, fname)
    try:
        if not os.path.exists(dest):
            with open(dest, "wb") as f:
                f.write(base64.b64decode(b64))
        return f"assets/{fname}"
    except Exception as e:  # noqa: BLE001
        print(f"    !! data uri failed: {e}", file=sys.stderr)
        return None


def fix_img_srcs(article):
    n = 0
    for img in article.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if not src:
            continue
        if src.startswith("data:"):
            rel = save_data_uri(img)
            if rel:
                img["src"] = rel
                n += 1
            continue
        abs_url = urljoin(BASE, src)
        if abs_url.startswith(BASE + "/assets/") or abs_url.startswith(BASE + "/img/"):
            rel = download(abs_url)
            if rel:
                img["src"] = rel
                n += 1
        else:
            img["src"] = abs_url
    return n


def fix_links(article):
    for a in article.find_all("a"):
        href = a.get("href")
        if not href:
            continue
        path, _, anchor = href.partition("#")
        for p in SORTED_PATHS:
            if path == p or path == p.rstrip("/"):
                a["href"] = LINK_MAP[p] + (f"#{anchor}" if anchor else "")
                break
        else:
            if href.startswith("/") and not href.startswith("//"):
                a["href"] = urljoin(BASE, href)


def process(page_path, out_file):
    url = BASE + page_path
    print(f"== {out_file}  <-  {url}")
    html = fetch(url)
    soup = BeautifulSoup(html, "html5lib")

    article = soup.find("div", class_="theme-doc-markdown")
    if article is None:
        print("    !! no article found", file=sys.stderr)
        return

    # title from first h1, then drop it (we add our own header line)
    title_el = article.find("h1")
    title = title_el.get_text(strip=True) if title_el else page_path.strip("/")
    if title_el:
        title_el.decompose()

    fix_headings(article)
    convert_admonitions(article, soup)
    convert_iframes(article, soup)

    tables = []
    for i, tbl in enumerate(article.find_all("table")):
        convert_table(tbl, soup, i, tables)

    n_img = fix_img_srcs(article)
    fix_links(article)

    body = md(str(article), heading_style="ATX", bullets="-")
    for i, t in enumerate(tables):
        body = body.replace(f"@@TABLE{i}@@", f"\n\n{t}\n\n")
    # collapse blank lines
    body = re.sub(r"\n{3,}", "\n\n", body).strip()

    header = f"# {title}\n\n> 来源: {url}\n\n"
    with open(os.path.join(DOC_DIR, out_file), "w", encoding="utf-8") as f:
        f.write(header + body + "\n")
    print(f"    wrote {out_file}  ({n_img} images, {len(tables)} tables)")


def main():
    os.makedirs(ASSET_DIR, exist_ok=True)
    for p, f in PAGES:
        try:
            process(p, f)
        except Exception as e:  # noqa: BLE001
            print(f"    !! FAILED {p}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
