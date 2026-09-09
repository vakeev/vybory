#!/usr/bin/env python3
"""Merge VK contacts from a source workbook into candidates.xlsx.

Reads «Зелёные кандидаты» sheet of the given source file (default:
kandidaty_zelenye_vk_obedinennye_bez_giperssylok_plus_72.xlsx).

Rules:
- only rows whose party is in ALLOWED_PARTIES are processed
- match by (ФИО, Партия), names normalized (ё->е, whitespace collapsed)
- fill column «ВКонтакте» with VK 1 and VK 2 values:
  - empty cell -> filled
  - existing cell -> append missing values with "; " (no duplicates)
- «https://HYPERLINK is not implemented. linkLocation=<url>» artifacts are
  unwrapped to the real <url> (both in source and existing cells)
- candidates from source that are missing in candidates.xlsx are appended as
  new rows; extra округ fields come from NEW_CANDIDATE_EXTRA (keyed by
  (ФИО, Партия)) because the source sheet has no округ columns
"""
import re
import sys

from openpyxl import load_workbook

DEFAULT_SOURCE = "kandidaty_zelenye_vk_obedinennye_bez_giperssylok_plus_72.xlsx"
REPO = "candidates.xlsx"
SOURCE_SHEET = "Зелёные кандидаты"
REPO_SHEET = "Кандидаты по округам"

ALLOWED_PARTIES = {"Единая Россия", "КПРФ", "ЛДПР", "Справедливая Россия", "Новые люди"}

# Cell fill rule: a filled VK cell is included only if it is green; red/other
# solid fills are skipped. Unfilled cells are always included (old sources).
GREEN = "FF00FF00"

# Округ fields for candidates not present in candidates.xlsx (source sheet has
# no округ columns, so they are supplied here manually).
NEW_CANDIDATE_EXTRA = {
    ("Мотрюков Владимир Анатольевич", "Новые люди"): {
        "№ округа": "160",
        "Округ": "Округ № 160 (Тольяттинский)",
        "Территория округа": "Округ включает Центральный и Автозаводский районы города Тольятти, а также основную часть пригородного Ставропольского района.",
    },
}

JUNK = re.compile(r"https://HYPERLINK is not implemented\. linkLocation=(.+)$")


def norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = s.replace("ё", "е").replace("Ё", "е")
    return re.sub(r"\s+", " ", s)


def unwrap(v):
    """Unwrap HYPERLINK artifact to the real URL, else return value as-is."""
    if not v:
        return ""
    m = JUNK.match(str(v).strip())
    return m.group(1).strip() if m else str(v).strip()


def vk_value(rec, scol, sheaders):
    vals = []
    for sh in ("VK 1", "VK 2 (если другой)", "VK 2"):
        if sh in scol:
            cell = rec[scol[sh] - 1]
            u = unwrap(cell.value)
            if not u:
                continue
            fill = cell.fill
            if fill and fill.patternType == "solid" and str(fill.fgColor.rgb) != GREEN:
                continue
            vals.append(u)
    return "; ".join(dict.fromkeys(vals))


def main():
    source = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SOURCE

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

    swb = load_workbook(source)
    sws = swb[SOURCE_SHEET] if SOURCE_SHEET in swb.sheetnames else swb[swb.sheetnames[0]]
    sheaders = [c.value for c in sws[1]]
    scol = {h: i for i, h in enumerate(sheaders, start=1)}

    added = appended = kept = cleaned = added_new = skipped_party = 0
    no_extra = []

    for rec in sws.iter_rows(min_row=2):
        name = rec[scol["ФИО"] - 1].value if "ФИО" in scol else None
        party = rec[scol["Партия"] - 1].value if "Партия" in scol else None
        if not name:
            continue
        if party not in ALLOWED_PARTIES:
            skipped_party += 1
            continue

        vk = vk_value(rec, scol, sheaders)
        hits = idx.get((norm(name), party), [])

        if not hits:
            row = [None] * len(headers)
            row[col["Кандидат"] - 1] = name
            row[col["Партия"] - 1] = party
            if "Регион" in scol and "Регион" in col:
                row[col["Регион"] - 1] = rec[scol["Регион"] - 1].value
            if "ВКонтакте" in col:
                row[col["ВКонтакте"] - 1] = vk or None
            extra = NEW_CANDIDATE_EXTRA.get((name, party))
            if extra:
                for rh, rv in extra.items():
                    if rh in col:
                        row[col[rh] - 1] = rv
            else:
                no_extra.append((name, party))
            ws.append(row)
            added_new += 1
            continue

        r = hits[0]
        cell = r[col["ВКонтакте"] - 1]
        raw = cell.value
        is_junk = raw is not None and "HYPERLINK" in str(raw)
        cur = unwrap(raw)
        merged = merge_value(cur, vk)
        if is_junk or (merged and merged != cur):
            cell.value = merged or None
            if is_junk:
                cleaned += 1
            elif cur:
                appended += 1
            else:
                added += 1
        else:
            kept += 1

    wb.save(REPO)
    print(
        f"added={added} appended={appended} kept={kept} cleaned={cleaned} "
        f"added_new={added_new} skipped_party={skipped_party} no_extra={len(no_extra)}"
    )
    for n, p in no_extra:
        print("  new candidate WITHOUT округ data:", n, p)


def merge_value(cur, new_val) -> str:
    parts = [p for p in (cur.split(";") if cur else []) if p.strip()]
    if new_val:
        for v in new_val.split(";"):
            v = v.strip()
            if v and v not in parts:
                parts.append(v)
    return "; ".join(parts)


if __name__ == "__main__":
    main()
