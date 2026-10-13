// 「提示词分类」页：tag_categories.json（由 tools\build_tag_categories.py 生成）按 大类 / 子类 浏览，
// 点卡片插入提示词。违禁词照常列出、照常排序，只是标红，卡片上的中文带「违禁词」标记。
const DATA_URL = new URL("./tag_categories.json", import.meta.url);
const PAGE = 300;
export const BAN_STYLE = {
    2: { color: "#ff6b6b", border: "1px solid #e03131", background: "rgba(224,49,49,0.12)" },
    1: { color: "#ffa94d", border: "1px solid #e8590c", background: "rgba(232,89,12,0.10)" },
};
export const BAN_TIP = {
    2: ["🚫 违禁词（绝对禁用）", "正向提示词里不准用，一般只写在负向里"],
    1: ["⚠ 违禁词（仅全年龄）", "正向里有 nsfw / explicit / sensitive 时不准用"],
};

function el(tag, style, text) {
    const e = document.createElement(tag);
    if (style) Object.assign(e.style, style);
    if (text) e.textContent = text;
    return e;
}

// 和 Autocomplete-Plus 插入时的写法一致：下划线换空格，括号转义。
export function toPrompt(tag) {
    const t = /[a-z0-9]/i.test(tag) ? tag.replace(/_/g, " ") : tag;
    return t.replace(/([()])/g, "\\$1");
}

function shortCount(n) {
    if (n >= 1e6) return (n / 1e6).toFixed(1) + "M";
    if (n >= 1e3) return Math.round(n / 1e3) + "k";
    return String(n);
}

let dataPromise = null;

// 补全和分类面板共用一份词库，只加载一次。
export function loadTags() {
    dataPromise ??= fetch(DATA_URL).then((r) => r.json()).catch((e) => {
        dataPromise = null;
        throw e;
    });
    return dataPromise;
}

// compact：输入框旁的小面板用，大类改成横排、卡片更窄。
export function buildTagBrowser(root, insert, toast, compact = false) {
    const bar = el("div", { display: "flex", gap: "8px", padding: compact ? "6px" : "0 8px 8px", alignItems: "center", flexShrink: "0" });
    const search = el("input", { flex: compact ? "1" : "0 0 280px", minWidth: "0", padding: "4px 8px", fontSize: "14px" });
    search.placeholder = compact ? "搜索中文或英文" : "搜索中文或英文，比如 长发 / long hair";
    bar.appendChild(search);
    if (!compact) {
        bar.appendChild(el("div", { fontSize: "12px", opacity: "0.7" },
            "点卡片插入 · 数字是 Danbooru 图片数 · 红框 = 🚫绝对禁用，橙框 = ⚠仅全年龄"));
    }
    const body = el("div", { flex: "1", minHeight: "0", display: "flex", flexDirection: compact ? "column" : "row" });
    const nav = el("div", compact
        ? { display: "flex", flexWrap: "wrap", flexShrink: "0", padding: "0 4px", borderBottom: "1px solid rgba(255,255,255,0.1)" }
        : { width: "120px", flexShrink: "0", overflowY: "auto", borderRight: "1px solid rgba(255,255,255,0.1)" });
    const main = el("div", { flex: "1", minWidth: "0", minHeight: "0", display: "flex", flexDirection: "column" });
    const subBar = el("div", { display: "flex", flexWrap: "wrap", gap: "4px", padding: "6px 8px", flexShrink: "0", maxHeight: "30%", overflowY: "auto" });
    const list = el("div", { flex: "1", overflowY: "auto", padding: compact ? "6px" : "8px", alignContent: "start",
        display: "grid", gridTemplateColumns: `repeat(auto-fill, minmax(${compact ? 120 : 170}px, 1fr))`, gap: compact ? "4px" : "6px" });
    main.append(subBar, list);
    body.append(nav, main);
    root.append(bar, body);
    list.textContent = "正在加载词库……";

    let groups = [];
    let group = null;
    let sub = null;

    function card(t, where) {
        const [tag, zh, count, ban] = t;
        const c = el("div", { cursor: "pointer", borderRadius: "6px", padding: "4px 8px", lineHeight: "1.35",
            background: "rgba(255,255,255,0.05)", border: "1px solid transparent", ...BAN_STYLE[ban] });
        c.title = (ban ? BAN_TIP[ban][0] + "\n" : "") + toPrompt(tag);
        c.appendChild(el("div", { fontSize: "13px", wordBreak: "break-all" }, zh || tag));
        const meta = el("div", { fontSize: "11px", opacity: "0.65", display: "flex", gap: "6px" });
        meta.appendChild(el("span", { flex: "1", wordBreak: "break-all" }, tag));
        meta.appendChild(el("span", { flexShrink: "0" }, shortCount(count)));
        c.appendChild(meta);
        if (where) c.appendChild(el("div", { fontSize: "11px", opacity: "0.5" }, where));
        c.onclick = () => {
            insert(toPrompt(tag));
            if (ban) toast("warn", BAN_TIP[ban][0], BAN_TIP[ban][1]);
        };
        return c;
    }

    function fill(items, labelOf) {
        list.innerHTML = "";
        let shown = 0;
        const more = el("button", { gridColumn: "1 / -1", padding: "6px", cursor: "pointer" });
        const page = () => {
            more.remove();
            for (const t of items.slice(shown, shown + PAGE)) list.appendChild(card(t, labelOf?.(t)));
            shown += PAGE;
            if (shown < items.length) {
                more.textContent = `再显示 ${Math.min(PAGE, items.length - shown)} 个（共 ${items.length}）`;
                list.appendChild(more);
            }
        };
        more.onclick = page;
        if (!items.length) list.textContent = "没有找到。";
        else page();
        list.scrollTop = 0;
    }

    // 每个大类最前面加一个「全部」，按图片数排序；不放进 g.subs，免得搜索时重复。
    const allSubs = new Map();
    function subsOf(g) {
        if (!allSubs.has(g)) {
            const tags = g.subs.flatMap((x) => x.tags).sort((a, b) => b[2] - a[2]);
            allSubs.set(g, [{ name: "全部", tags }, ...g.subs]);
        }
        return allSubs.get(g);
    }

    function pick(g, s) {
        group = g;
        sub = s ?? subsOf(g)[0];
        for (const b of nav.children) b.style.opacity = b._group === group ? "1" : "0.55";
        subBar.innerHTML = "";
        for (const x of subsOf(group)) {
            const b = el("button", { padding: "2px 8px", cursor: "pointer", fontSize: "12px", opacity: x === sub ? "1" : "0.55" },
                `${x.name} ${x.tags.length}`);
            b.onclick = () => pick(group, x);
            subBar.appendChild(b);
        }
        fill(sub.tags);
    }

    function runSearch() {
        const q = search.value.trim().toLowerCase();
        if (!q) {
            if (group) pick(group, sub);
            return;
        }
        const key = q.replace(/\s+/g, "_");
        const hits = [];
        const where = new Map();
        for (const g of groups) {
            for (const s of g.subs) {
                for (const t of s.tags) {
                    if (t[0].includes(key) || t[1].toLowerCase().includes(q)) {
                        hits.push(t);
                        where.set(t, `${g.name} / ${s.name}`);
                    }
                }
            }
        }
        hits.sort((a, b) => b[2] - a[2]);
        subBar.innerHTML = "";
        subBar.appendChild(el("div", { fontSize: "12px", opacity: "0.7" }, `搜索「${q}」：${hits.length} 个`));
        fill(hits, (t) => where.get(t));
    }

    let timer = null;
    const later = () => {
        clearTimeout(timer);
        timer = setTimeout(runSearch, 200);
    };
    search.addEventListener("input", later);
    // 中文输入法上屏时有的浏览器不再补发 input
    search.addEventListener("compositionend", later);

    loadTags()
        .then((data) => {
            groups = data.groups;
            for (const g of groups) {
                const b = el("div", { padding: compact ? "4px 6px" : "8px 10px", cursor: "pointer", fontSize: compact ? "13px" : "14px" }, g.name);
                b._group = g;
                b.onclick = () => {
                    search.value = "";
                    pick(g);
                };
                nav.appendChild(b);
            }
            pick(groups[0]);
        })
        .catch(() => {
            list.textContent = "词库没有加载成功。先运行 tools\\build_tag_categories.py 生成 tag_categories.json。";
        });
}
