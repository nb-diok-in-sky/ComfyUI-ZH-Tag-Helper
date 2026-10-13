# Step 1 of the word list build: tools/build/danbooru_tags_zh.csv (tag, category, post count, aliases).
# Adds Chinese aliases (from ffdkj Danbooru zh translation table, tag_zh.sqlite) to every tag of
# danbooru_tags.csv; zh_extra.tsv (hand-written) fills missing translations and overrides wrong ones.
# Youth-coded tags keep their Chinese but every Chinese alias is prefixed with a 违禁词 marker:
# BAN for the loli/shota family (never use), WARN for the rest (SFW-only), so people and AI see it.
# Usage: python tools/build_zh_tags.py   (sources from tools/fetch_sources.py; step 2 is build_tag_categories.py)
import csv
import os
import re
import sqlite3

TOOLS = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(TOOLS, "sources/danbooru_tags.csv")
DB = os.path.join(TOOLS, "sources/tag_zh.sqlite")
EXTRA_TSV = os.path.join(TOOLS, "zh_extra.tsv")
OUT = os.path.join(TOOLS, "build/danbooru_tags_zh.csv")

HAN = re.compile(r"[一-鿿]")
BANNED_TOKENS = {"loli", "shota", "child", "children", "kid", "kids", "toddler", "teen", "teenage", "teenager",
                 "school", "schoolgirl", "schoolboy", "elementary", "kindergarten", "randoseru", "younger"}
BANNED_EXACT = {"young", "petite", "flat_chest", "tiny", "cheerleader", "serafuku", "aged_down"}
ALLOW = {"school_of_fish"}
BAN_TOKENS = {"loli", "shota"}
BAN_EXACT = {"aged_down", "kodomo_doushi", "mesugaki", "cub", "toddlercon", "osana_reimu"}
# Word-initial loli/shota, also run together (lolidom, lolicon, shotadom); not lolita fashion or hololive.
LOLI_SHOTA = re.compile(r"(^|[_-])(loli(?!ta)|shota)")
# Character tags are only checked for these, e.g. shigure_ui_(vtuber)_(young).
CHARACTER_BAN_TOKENS = {"loli", "shota", "young", "child"}
BAN = "🚫违禁词·"
WARN = "⚠违禁词·仅全年龄·"
# Hand-written aliases where the machine translation is ambiguous for everyday Chinese.
EXTRA = {
    "sex_from_behind": ["后入（泛指，各种姿势）"],
    "doggystyle": ["后入·狗爬式（四肢着地）"],
}


def tokens(tag):
    return set(re.split(r"[_()\-:]+", tag))


def banned(tag, cat):
    # Returns BAN, WARN or None. Series names are left alone unless listed in BAN_EXACT.
    if tag in BAN_EXACT:
        return BAN
    if cat == "4":
        return BAN if tokens(tag) & CHARACTER_BAN_TOKENS else None
    if cat != "0" or tag in ALLOW:
        return None
    if tag in BAN_EXACT or tokens(tag) & BAN_TOKENS or LOLI_SHOTA.search(tag):
        return BAN
    if tag in BANNED_EXACT or tokens(tag) & BANNED_TOKENS:
        return WARN
    return None


def zh_aliases(cn):
    out = []
    for part in re.split(r"[、/;；,，|]", cn):
        p = part.strip()
        if not p:
            continue
        out.append(p)
        short = re.sub(r"[（(].*?[）)]", "", p).strip()
        if short and short != p:
            out.append(short)
    return out


zh = {n: c for n, c in sqlite3.connect(DB).execute("select name, cn_name from tags") if c}
for line in open(EXTRA_TSV, encoding="utf-8"):
    if line.startswith("#") or "\t" not in line:
        continue
    t, c = line.rstrip("\n").split("\t", 1)
    zh[t] = c
rows = []
for r in csv.reader(open(BASE, encoding="utf-8")):
    if len(r) < 3 or not r[2].isdigit():
        continue
    tag, cat, cnt = r[0], r[1], r[2]
    aliases = [a for a in (r[3].split(",") if len(r) > 3 and r[3] else []) if a]
    if tag in zh:
        # The translation goes first (it becomes the display name), even if the base list already has it further down.
        first = zh_aliases(zh[tag])
        aliases = first + [a for a in aliases if a not in first]
    aliases = EXTRA.get(tag, []) + aliases
    mark = banned(tag, cat)
    if mark:
        aliases = [mark + a if HAN.search(a) else a for a in aliases]
    rows.append([tag, cat, cnt, ",".join(aliases)])

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8", newline="") as f:
    csv.writer(f).writerows(rows)
print(f"wrote {len(rows)} tags -> {OUT}")
