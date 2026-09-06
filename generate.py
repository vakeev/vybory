#!/usr/bin/env python3
"""Generate regions/*.html and index.html from candidates.xlsx.

Region slug -> name mapping is read from the existing region pages.
"""
import glob
import html
import os
import re

from openpyxl import load_workbook

REPO = "candidates.xlsx"
REPO_SHEET = "Кандидаты по округам"
CONTACT_COLS = ["ВКонтакте", "Telegram", "запрещённая сеть", "Одноклассники", "MAX", "Сайт", "Дзен"]


def make_link(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if "://" in url:
        href = url
        disp = re.sub(r"^https?://", "", url)
    else:
        href = "https://" + url
        disp = url
    disp = disp.rstrip("/")
    return f'<a href="{html.escape(href, quote=True)}" target="_blank" rel="noopener">{html.escape(disp)}</a>'


def contacts_span(cells) -> str:
    links = []
    for cell in cells:
        if not cell:
            continue
        for part in str(cell).split(";"):
            link = make_link(part)
            if link:
                links.append(link)
    if not links:
        return ""
    return ' <span class="contacts"> — ' + ", ".join(links) + "</span>"


slug = {}
for path in glob.glob("regions/*.html"):
    name = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = re.search(r"<h1>(.*?)</h1>", line)
            if m:
                name = m.group(1).strip()
                break
    if name:
        slug[name] = os.path.basename(path)

wb = load_workbook(REPO)
ws = wb[REPO_SHEET]
headers = [c.value for c in ws[1]]
col = {h: i for i, h in enumerate(headers)}

by_region = {}
for row in ws.iter_rows(min_row=2, values_only=True):
    if not row[col["Кандидат"]]:
        continue
    by_region.setdefault(row[col["Регион"]], []).append(row)


def page(region: str, rows) -> str:
    title = html.escape(region)
    items = []
    for r in rows:
        name = html.escape(r[col["Кандидат"]] or "")
        party = html.escape(r[col["Партия"]] or "")
        contacts = contacts_span([r[col[c]] for c in CONTACT_COLS])
        items.append(f'  <li><span class="name">{name}</span> <span class="party">({party})</span>{contacts}</li>')
    return (
        "<!DOCTYPE html>\n"
        '<html lang="ru">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{title} — Выборы</title>\n"
        '<link rel="stylesheet" href="../styles.css">\n'
        "</head>\n"
        "<body>\n"
        '<nav class="breadcrumbs"><a href="../index.html">Оглавление</a><span class="sep">/</span><span>'
        f"{title}</span></nav>\n"
        f"<h1>{title}</h1>\n"
        "<ul>\n"
        + "\n".join(items)
        + "\n"
        "</ul>\n"
        "<footer>Статическая страница на GitHub Pages.</footer>\n"
        "</body>\n"
        "</html>\n"
    )


missing = []
for region, rows in by_region.items():
    if region not in slug:
        missing.append(region)
        continue
    with open("regions/" + slug[region], "w", encoding="utf-8") as f:
        f.write(page(region, rows))

nav = []
for region in sorted(by_region, key=lambda s: s.lower()):
    if region in slug:
        nav.append(f'<li><a href="regions/{slug[region]}">{html.escape(region)}</a></li>')

index = (
    "<!DOCTYPE html>\n"
    '<html lang="ru">\n'
    "<head>\n"
    '<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    "<title>Выборы — кандидаты по одномандатным округам</title>\n"
    '<link rel="stylesheet" href="styles.css">\n'
    "</head>\n"
    "<body>\n"
    "<h1>Кандидаты по одномандатным округам</h1>\n"
    '<nav class="menu"><ul>\n'
    + "\n".join(nav)
    + "\n"
    "</ul></nav>\n"
    "<footer>Статическая страница на GitHub Pages.</footer>\n"
    "</body>\n"
    "</html>\n"
)
with open("index.html", "w", encoding="utf-8") as f:
    f.write(index)

print(f"regions_generated={len(by_region)} nav={len(nav)}")
if missing:
    print("no slug for:", missing)