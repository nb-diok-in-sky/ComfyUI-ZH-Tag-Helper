// 「提示词分类」面板：按 大类 / 子类 浏览词库（tag_data.js），点卡片插入提示词。
// 违禁词照常列出、照常排序，只是标红，卡片上的中文带「违禁词」标记。
// 「＋ 自定义词」可以把自己的词（比如 LoRA 触发词）加进任意分类，「★ 我的词库」里修改或删除。
import { BAN_STYLE, BAN_TIP, GROUP_COLORS, customEntries, loadTags, normTag, onTagsChanged, saveCustomEntry, toPrompt } from "./tag_data.js";

const PAGE = 300;
const MINE = "★ 我的词库";

function el(tag, style, text) {
    const e = document.createElement(tag);
    if (style) Object.assign(e.style, style);
    if (text) e.textContent = text;
    return e;
}

function shortCount(n) {
    if (n >= 1e6) return (n / 1e6).toFixed(1) + "M";
    if (n >= 1e3) return Math.round(n / 1e3) + "k";
    return String(n);
}

// compact：输入框旁的小面板用，大类改成横排、卡片更窄。
export function buildTagBrowser(root, insert, toast, compact = false) {
    const bar = el("div", { display: "flex", gap: "8px", padding: compact ? "6px" : "0 8px 8px", alignItems: "center", flexShrink: "0" });
    const search = el("input", { flex: compact ? "1" : "0 0 280px", minWidth: "0", padding: "4px 8px", fontSize: "14px" });
    search.placeholder = compact ? "搜索中文或英文" : "搜索中文或英文，比如 长发 / long hair";
    const addBtn = el("button", { padding: "3px 8px", cursor: "pointer", flexShrink: "0" }, "＋ 自定义词");
    bar.append(search, addBtn);
    if (!compact) {
        bar.appendChild(el("div", { fontSize: "12px", opacity: "0.7" },
            "点卡片插入 · 数字是 Danbooru 图片数 · 红框 = 🚫绝对禁用，橙框 = ⚠仅全年龄"));
    }
    const form = el("div", { display: "none", flexWrap: "wrap", gap: "6px", padding: "6px 8px", alignItems: "center", flexShrink: "0",
        background: "rgba(255,255,255,0.04)", borderTop: "1px solid rgba(255,255,255,0.1)", fontSize: "13px" });
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
    root.append(bar, form, body);
    list.textContent = "正在加载词库……";

    let groups = [];
    let groupName = null;
    let subName = null;

    // ---------- 自定义词表单 ----------
    const fTag = el("input", { width: "160px", padding: "3px 6px" });
    fTag.placeholder = "英文标签，如 my_lora_trigger";
    const fZh = el("input", { width: "130px", padding: "3px 6px" });
    fZh.placeholder = "中文";
    const fGroup = el("select", { padding: "3px" });
    const fSub = el("select", { padding: "3px" });
    const fNewSub = el("input", { width: "110px", padding: "3px 6px", display: "none" });
    fNewSub.placeholder = "新子类名";
    const fHint = el("span", { fontSize: "12px", opacity: "0.7" });
    const fSave = el("button", { padding: "3px 10px", cursor: "pointer" }, "保存");
    const fCancel = el("button", { padding: "3px 10px", cursor: "pointer" }, "取消");
    form.append(fTag, fZh, fGroup, fSub, fNewSub, fSave, fCancel, fHint);

    function fillSubs(selected) {
        const g = groups.find((x) => x.name === fGroup.value);
        fSub.innerHTML = "";
        for (const s of g?.subs ?? []) fSub.appendChild(new Option(s.name, s.name));
        fSub.appendChild(new Option("＋ 新建子类…", ""));
        fSub.value = selected ?? g?.subs[0]?.name ?? "";
        fNewSub.style.display = fSub.value ? "none" : "";
    }
    fGroup.onchange = () => fillSubs();
    fSub.onchange = () => (fNewSub.style.display = fSub.value ? "none" : "");
    fTag.oninput = () => {
        const key = normTag(fTag.value);
        const hit = key && groups.flatMap((g) => g.subs.flatMap((s) => s.tags.map((t) => [g, s, t]))).find((x) => x[2][0] === key);
        fHint.textContent = !hit ? "" : hit[2][5] ? "已在我的词库里，保存会覆盖" : `词库里已有：${hit[0].name} / ${hit[1].name}，保存后改到你选的分类`;
    };

    function openForm(entry) {
        form.style.display = "flex";
        fTag.value = entry?.tag ?? "";
        fZh.value = entry?.zh ?? "";
        fGroup.innerHTML = "";
        for (const g of groups) fGroup.appendChild(new Option(g.name, g.name));
        fGroup.value = entry?.group ?? groupName ?? groups[0].name;
        fillSubs(entry?.sub ?? (subName && subName !== "全部" ? subName : undefined));
        fTag.oninput();
        fTag.focus();
    }
    addBtn.onclick = () => (form.style.display === "flex" ? (form.style.display = "none") : openForm());
    fCancel.onclick = () => (form.style.display = "none");
    fSave.onclick = async () => {
        const tag = normTag(fTag.value);
        const sub = (fSub.value || fNewSub.value).trim();
        if (!tag || !sub) {
            toast("warn", "还没填完", "英文标签和子类不能为空");
            return;
        }
        try {
            await saveCustomEntry({ tag, zh: fZh.value.trim(), group: fGroup.value, sub });
            form.style.display = "none";
            toast("success", "已加入我的词库", `${tag} → ${fGroup.value} / ${sub}`);
        } catch (e) {
            toast("error", "保存失败", String(e));
        }
    };

    // ---------- 列表 ----------
    function card(t, where, mine) {
        const [tag, zh, count, ban, , isCustom] = t;
        const c = el("div", { cursor: "pointer", borderRadius: "6px", padding: "4px 8px", lineHeight: "1.35",
            background: "rgba(255,255,255,0.05)", border: "1px solid transparent", ...BAN_STYLE[ban] });
        c.title = (ban ? BAN_TIP[ban][0] + "\n" : "") + toPrompt(tag);
        c.appendChild(el("div", { fontSize: "13px", wordBreak: "break-all" }, (isCustom ? "★ " : "") + (zh || tag)));
        const meta = el("div", { fontSize: "11px", opacity: "0.65", display: "flex", gap: "6px" });
        meta.appendChild(el("span", { flex: "1", wordBreak: "break-all" }, tag));
        if (count) meta.appendChild(el("span", { flexShrink: "0" }, shortCount(count)));
        c.appendChild(meta);
        if (where) c.appendChild(el("div", { fontSize: "11px", opacity: "0.5" }, where));
        if (mine) {
            const row = el("div", { display: "flex", gap: "4px", marginTop: "2px" });
            const edit = el("button", { fontSize: "11px", padding: "0 6px", cursor: "pointer" }, "修改");
            const del = el("button", { fontSize: "11px", padding: "0 6px", cursor: "pointer" }, "删除");
            edit.onclick = (e) => {
                e.stopPropagation();
                openForm(mine);
            };
            del.onclick = (e) => {
                e.stopPropagation();
                saveCustomEntry(mine, true).catch((err) => toast("error", "删除失败", String(err)));
            };
            row.append(edit, del);
            c.appendChild(row);
        }
        c.onclick = () => {
            insert(toPrompt(tag));
            if (ban) toast("warn", BAN_TIP[ban][0], BAN_TIP[ban][1]);
        };
        return c;
    }

    function fill(items, labelOf, mineOf) {
        list.innerHTML = "";
        let shown = 0;
        const more = el("button", { gridColumn: "1 / -1", padding: "6px", cursor: "pointer" });
        const page = () => {
            more.remove();
            for (const t of items.slice(shown, shown + PAGE)) list.appendChild(card(t, labelOf?.(t), mineOf?.(t)));
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
    let allSubs = new Map();
    function subsOf(g) {
        if (!allSubs.has(g)) {
            const tags = g.subs.flatMap((x) => x.tags).sort((a, b) => (b[5] ?? 0) - (a[5] ?? 0) || b[2] - a[2]);
            allSubs.set(g, [{ name: "全部", tags }, ...g.subs]);
        }
        return allSubs.get(g);
    }

    function markNav() {
        for (const b of nav.children) b.style.opacity = b._name === groupName ? "1" : "0.55";
    }

    function showMine() {
        groupName = MINE;
        subName = null;
        markNav();
        subBar.innerHTML = "";
        subBar.appendChild(el("div", { fontSize: "12px", opacity: "0.7" }, "自己加的词，补全和提示词上色也会认。点卡片插入，修改 / 删除在卡片下方。"));
        const where = new Map();
        const mine = new Map(customEntries().map((e) => [e.tag, e]));
        const items = [];
        for (const g of groups) {
            for (const s of g.subs) {
                for (const t of s.tags) {
                    if (!t[5]) continue;
                    items.push(t);
                    where.set(t, `${g.name} / ${s.name}`);
                }
            }
        }
        fill(items, (t) => where.get(t), (t) => mine.get(t[0]));
    }

    function pick(name, sName) {
        if (name === MINE) return showMine();
        const g = groups.find((x) => x.name === name) ?? groups[0];
        groupName = g.name;
        const subs = subsOf(g);
        const s = subs.find((x) => x.name === sName) ?? subs[0];
        subName = s.name;
        markNav();
        subBar.innerHTML = "";
        for (const x of subs) {
            const b = el("button", { padding: "2px 8px", cursor: "pointer", fontSize: "12px", opacity: x === s ? "1" : "0.55" },
                `${x.name} ${x.tags.length}`);
            b.onclick = () => pick(g.name, x.name);
            subBar.appendChild(b);
        }
        fill(s.tags);
    }

    function runSearch() {
        const q = search.value.trim().toLowerCase();
        if (!q) {
            if (groupName) pick(groupName, subName);
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

    // 大类按钮带上提示词底纹用的颜色
    function render(data) {
        groups = data.groups;
        allSubs = new Map();
        nav.innerHTML = "";
        for (const name of [...groups.map((g) => g.name), MINE]) {
            const color = GROUP_COLORS[name];
            const b = el("div", { padding: compact ? "4px 6px" : "8px 10px", cursor: "pointer", fontSize: compact ? "13px" : "14px",
                borderLeft: `3px solid ${color ? `rgb(${color})` : "transparent"}` }, name);
            b._name = name;
            b.onclick = () => {
                search.value = "";
                pick(name);
            };
            nav.appendChild(b);
        }
        if (search.value.trim()) runSearch();
        else pick(groupName ?? groups[0].name, subName);
    }

    const reload = () =>
        loadTags()
            .then(render)
            .catch(() => {
                list.textContent = "词库没有加载成功。先运行 tools\\build_tag_categories.py 生成 tag_categories.json。";
            });
    onTagsChanged(reload);
    reload();
}
