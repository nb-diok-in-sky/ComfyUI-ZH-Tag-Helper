# Download the raw sources the word list is built from into tools/sources/ (not part of the repo):
#   danbooru_tags.csv    tags + post counts      newtextdoc1111/danbooru-tag-csv (HuggingFace, MIT)
#   tag_zh.sqlite        Chinese translations    ffdkj/ffdkj-Danbooru_Tag-Chinese-English-Translation-Table (GitHub, MIT)
#   danbooru_groups/     "Tag group:" wiki pages used for categories (danbooru.donmai.us)
# Build-time only; the plugin itself never touches the network. Existing files are kept, delete one to refresh it.
# Usage: python tools/fetch_sources.py [--proxy http://127.0.0.1:17890]
# Then:  python tools/build_zh_tags.py && python tools/build_tag_categories.py
import argparse
import json
import os
import re
import time
import urllib.parse
import urllib.request

SOURCES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sources")
GROUPS = os.path.join(SOURCES, "danbooru_groups")
FILES = {
    "danbooru_tags.csv": "https://huggingface.co/datasets/newtextdoc1111/danbooru-tag-csv/resolve/main/danbooru_tags.csv",
    "tag_zh.sqlite": "https://raw.githubusercontent.com/ffdkj/ffdkj-Danbooru_Tag-Chinese-English-Translation-Table/main/tag.sqlite",
}
LINK = re.compile(r"\[\[((?:tag group|list of)[^\]|#]+)", re.I)
HEADERS = {"User-Agent": "ComfyUI-ZH-Tag-Helper/1.0"}


def norm(title):
    return title.strip().lower().replace(" ", "_")


def download(name, url):
    path = os.path.join(SOURCES, name)
    if os.path.exists(path):
        return
    print("download", name)
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=120) as r:
        data = r.read()
    with open(path, "wb") as f:
        f.write(data)


def fetch_page(title):
    path = os.path.join(GROUPS, re.sub(r"[^\w\-]", "_", title) + ".json")
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    url = "https://danbooru.donmai.us/wiki_pages/" + urllib.parse.quote(title) + ".json"
    try:
        data = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30))
    except Exception as e:
        # Not cached, so a rerun retries it (Danbooru answers 503 when rate limited).
        print("skip", title, e)
        return {"title": title, "body": ""}
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    time.sleep(0.4)
    return data


def fetch_groups():
    seen = set()
    queue = [norm(t) for t in LINK.findall(fetch_page("tag_groups")["body"])]
    depth = {t: 0 for t in queue}
    while queue:
        t = queue.pop(0)
        if t in seen:
            continue
        seen.add(t)
        body = fetch_page(t)["body"]
        if depth[t] < 1:
            for sub in LINK.findall(body):
                s = norm(sub)
                if s not in depth:
                    depth[s] = depth[t] + 1
                    queue.append(s)
    print(f"{len(seen)} wiki pages in {GROUPS}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proxy", help="e.g. http://127.0.0.1:17890")
    args = ap.parse_args()
    if args.proxy:
        urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({"http": args.proxy, "https": args.proxy})))
    os.makedirs(GROUPS, exist_ok=True)
    for name, url in FILES.items():
        download(name, url)
    fetch_groups()


main()
