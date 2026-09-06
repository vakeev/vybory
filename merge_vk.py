#!/usr/bin/env python3
"""Merge VK contacts from «508 аккаунтов Степану.xlsx» into candidates.xlsx.

Rules:
- match by (ФИО, Партия), names normalized (ё->е, whitespace collapsed)
- fill column «ВКонтакте» only where empty
- rows that already have a value in «ВКонтакте» are left unchanged
"""
import re

from openpyxl import load_workbook

LOCAL = "508 аккаунтов Степану.xlsx"
REPO = "candidates.xlsx"
LOCAL_SHEET = "Зелёные кандидаты"
REPO_SHEET = "Кандидаты по округам"


def norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = s.replace("ё", "е").replace("Ё", "е")
    return re.sub(r"\s+", " ", s)


wb = load_workbook(REPO)
ws = wb[REPO_SHEET]
headers = [c.value for c in ws[1]]
col = {h: i for i, h in enumerate(headers, start=1)}

idx = {}
for row in ws.iter_rows(min_row=2):
    name = row[col["Кандидат"] - 1].value
    party = row[col["Партия"] - 1].value
    if not name:
        continue
    idx.setdefault((norm(name), party), []).append(row)

lwb = load_workbook(LOCAL)
lws = lwb[LOCAL_SHEET]
lheaders = [c.value for c in lws[1]]
lcol = {h: i for i, h in enumerate(lheaders, start=1)}

added = 0
appended = 0
kept = 0
not_found = []
for row in lws.iter_rows(min_row=2):
    name = row[lcol["ФИО"] - 1].value
    party = row[lcol["Партия"] - 1].value
    vk = row[lcol["VK 1"] - 1].value
    if not name:
        continue
    hits = idx.get((norm(name), party), [])
    if not hits:
        not_found.append(name)
        continue
    r = hits[0]
    cell = r[col["ВКонтакте"] - 1]
    cur = cell.value
    if cur:
        if vk and vk.strip() and vk not in cur:
            cell.value = f"{cur}; {vk}"
            appended += 1
        else:
            kept += 1
    else:
        cell.value = vk
        added += 1

wb.save(REPO)
print(f"added={added} appended={appended} kept={kept} not_found={len(not_found)}")