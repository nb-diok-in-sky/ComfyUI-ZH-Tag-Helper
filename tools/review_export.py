# Split web/tag_categories.json into small review lists for an AI (or a person) to check, one subcategory at a time.
#   tools/review/todo/NNN_大类_子类[_k].tsv   tag, 中文, 图片数, 当前分类   (at most --size tags each, most popular first)
#   tools/review/categories.txt               every valid 大类/子类 with its size
# Reviewers write corrections to tools/review/done/<same file name>; check them with review_check.py.
# See docs/AI_REVIEW_GUIDE.md.  Usage: python tools/review_export.py [--size 200] [--with-names]
import argparse
import json
import os
import re

TOOLS = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(TOOLS, "..", "web", "tag_categories.json")
REVIEW = os.path.join(TOOLS, "review")
# Character and series names are sorted by the series in their Chinese name; skipped unless --with-names.
NAME_GROUPS = {"角色", "作品"}


def safe(name):
    return re.sub(r"[^\w]+", "-", name).strip("-")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=200)
    ap.add_argument("--with-names", action="store_true", help="also export 角色 / 作品")
    args = ap.parse_args()
    data = json.load(open(DATA, encoding="utf-8"))
    todo = os.path.join(REVIEW, "todo")
    os.makedirs(todo, exist_ok=True)
    os.makedirs(os.path.join(REVIEW, "done"), exist_ok=True)
    for old in os.listdir(todo):
        os.remove(os.path.join(todo, old))
    n = 0
    with open(os.path.join(REVIEW, "categories.txt"), "w", encoding="utf-8") as cats:
        for g in data["groups"]:
            for s in g["subs"]:
                cats.write(f"{g['name']}/{s['name']}\t{len(s['tags'])}\n")
                if g["name"] in NAME_GROUPS and not args.with_names:
                    continue
                for k in range(0, len(s["tags"]), args.size):
                    n += 1
                    part = "" if len(s["tags"]) <= args.size else f"_{k // args.size + 1}"
                    path = os.path.join(todo, f"{n:03d}_{safe(g['name'])}_{safe(s['name'])}{part}.tsv")
                    with open(path, "w", encoding="utf-8") as f:
                        f.write("# tag\t中文\t图片数\t当前分类\n")
                        for t in s["tags"][k:k + args.size]:
                            f.write(f"{t[0]}\t{t[1]}\t{t[2]}\t{g['name']}/{s['name']}\n")
    print(f"{n} lists in {todo}")


main()
