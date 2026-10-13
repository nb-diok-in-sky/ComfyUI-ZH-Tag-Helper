# Check the corrections in tools/review/done/*.tsv before a maintainer reviews and merges them.
# Each line: tag<TAB>操作<TAB>新值<TAB>理由, 操作 is 分类 (新值 = 大类/子类), 翻译 (新值 = 中文) or 违禁 (新值 = 疑似漏标/疑似误标).
# Prints problems first, then the valid suggestions grouped by 操作, and writes them to tools/review/merged_suggestions.tsv.
# Usage: python tools/review_check.py
import glob
import json
import os
import re

TOOLS = os.path.dirname(os.path.abspath(__file__))
REVIEW = os.path.join(TOOLS, "review")
data = json.load(open(os.path.join(TOOLS, "..", "web", "tag_categories.json"), encoding="utf-8"))
where = {t[0]: (f"{g['name']}/{s['name']}", t[1]) for g in data["groups"] for s in g["subs"] for t in s["tags"]}
valid = {f"{g['name']}/{s['name']}" for g in data["groups"] for s in g["subs"]}
SEPARATORS = re.compile(r"[;；/,，|]")

problems, good = [], []
for path in sorted(glob.glob(os.path.join(REVIEW, "done", "*.tsv"))):
    name = os.path.basename(path)
    for no, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.rstrip("\n")
        if not line.strip() or line.startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) < 3:
            problems.append(f"{name}:{no} 列数不够（要用 Tab 分隔 4 列）: {line}")
            continue
        tag, op, value = cols[0].strip(), cols[1].strip(), cols[2].strip()
        reason = cols[3].strip() if len(cols) > 3 else ""
        if tag not in where:
            problems.append(f"{name}:{no} 词库里没有这个标签: {tag}")
        elif op == "分类" and value not in valid:
            problems.append(f"{name}:{no} 分类名不存在: {value}（{tag}）")
        elif op == "分类" and value == where[tag][0]:
            problems.append(f"{name}:{no} 新分类和当前分类一样: {tag}")
        elif op == "翻译" and (not value or SEPARATORS.search(value)):
            problems.append(f"{name}:{no} 翻译为空或含 ; / , 等分隔符: {tag} -> {value}")
        elif op == "翻译" and value == where[tag][1]:
            problems.append(f"{name}:{no} 新翻译和当前翻译一样: {tag}")
        elif op not in ("分类", "翻译", "违禁"):
            problems.append(f"{name}:{no} 操作只能是 分类 / 翻译 / 违禁: {op}")
        else:
            good.append((op, tag, where[tag][1], where[tag][0], value, reason, name))

for p in problems:
    print("✗", p)
out = os.path.join(REVIEW, "merged_suggestions.tsv")
with open(out, "w", encoding="utf-8") as f:
    f.write("# 操作\ttag\t当前中文\t当前分类\t建议\t理由\t来源\n")
    for op in ("违禁", "分类", "翻译"):
        rows = [g for g in good if g[0] == op]
        print(f"\n== {op} {len(rows)} 条")
        for r in rows:
            print(f"  {r[1]}  {r[2]}  [{r[3]}] -> {r[4]}  {r[5]}")
            f.write("\t".join(r) + "\n")
print(f"\n{len(problems)} 个问题，{len(good)} 条建议 -> {out}")
