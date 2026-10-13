// 提示词补全：在提示词框里打中文或英文，光标处弹出候选，↑↓ 选择，Enter / Tab 插入，Esc 关闭，也可以用鼠标点。
// 词库就是 tag_categories.json（和分类面板共用），违禁词同样标红并在插入时提醒。
// 中文输入法组字期间不搜索，上屏（compositionend）后再搜。
import { app } from "../../scripts/app.js";
import { BAN_STYLE, BAN_TIP, loadTags, toPrompt } from "./tag_browser.js";

const LIMIT = 30;
const MARKS = /^(🚫违禁词·|⚠违禁词·仅全年龄·)/;

let index = null;
let box = null;
let target = null;
let hits = [];
let active = 0;
let tokenStart = 0;

function el(tag, style, text) {
    const e = document.createElement(tag);
    if (style) Object.assign(e.style, style);
    if (text) e.textContent = text;
    return e;
}

function shortCount(n) {
    return n >= 1e6 ? (n / 1e6).toFixed(1) + "M" : n >= 1e3 ? Math.round(n / 1e3) + "k" : String(n);
}

function toast(severity, summary, detail) {
    app.extensionManager?.toast?.add({ severity, summary, detail, life: 1800 });
}

function isPromptBox(e) {
    return e instanceof HTMLTextAreaElement && e.classList.contains("comfy-multiline-input") && !e.readOnly;
}

function buildIndex(data) {
    const out = [];
    for (const g of data.groups) {
        for (const s of g.subs) {
            for (const t of s.tags) out.push({ t, zh: t[1].replace(MARKS, "").toLowerCase(), alias: t[4] ?? "" });
        }
    }
    return out;
}

// 光标前到上一个逗号 / 换行之间的文字，去掉开头的空格和权重括号。
function currentToken(ta) {
    const end = ta.selectionStart;
    if (end !== ta.selectionEnd) return null;
    const before = ta.value.slice(0, end);
    const cut = Math.max(before.lastIndexOf(","), before.lastIndexOf("，"), before.lastIndexOf("\n")) + 1;
    const lead = before.slice(cut).match(/^[\s([{]*/)[0].length;
    tokenStart = cut + lead;
    const text = before.slice(tokenStart);
    if (!text.trim() || /^[\x00-\x7f]$/.test(text) || text.includes(":") || text.startsWith("<")) return null;
    return text.toLowerCase();
}

function search(q) {
    const key = q.trim().replace(/\s+/g, "_");
    const scored = [];
    for (const it of index) {
        const tag = it.t[0];
        let s;
        if (tag.startsWith(key)) s = 0;
        else if (it.zh.startsWith(q)) s = 1;
        else if (tag.includes("_" + key)) s = 2;
        else if (tag.includes(key) || it.zh.includes(q)) s = 3;
        else if (it.alias.includes(q)) s = 4;
        else continue;
        scored.push([s, it.t]);
    }
    scored.sort((a, b) => a[0] - b[0] || b[1][2] - a[1][2]);
    return scored.slice(0, LIMIT).map((x) => x[1]);
}

// 用一个隐藏的镜像 div 量出光标位置；节点缩放时提示词框带 transform，按实际显示尺寸换算。
function caretPoint(ta) {
    const s = getComputedStyle(ta);
    const m = el("div", { position: "absolute", visibility: "hidden", top: "0", left: "-9999px", whiteSpace: "pre-wrap", wordWrap: "break-word" });
    for (const p of ["boxSizing", "width", "paddingTop", "paddingRight", "paddingBottom", "paddingLeft", "borderTopWidth", "borderRightWidth",
        "borderBottomWidth", "borderLeftWidth", "fontFamily", "fontSize", "fontWeight", "fontStyle", "lineHeight", "letterSpacing", "wordSpacing", "tabSize"]) {
        m.style[p] = s[p];
    }
    m.textContent = ta.value.slice(0, ta.selectionStart);
    const mark = el("span", null, "​");
    m.appendChild(mark);
    document.body.appendChild(m);
    const r = ta.getBoundingClientRect();
    const scale = r.width / ta.offsetWidth || 1;
    const line = (parseFloat(s.lineHeight) || parseFloat(s.fontSize) * 1.3) * scale;
    const x = r.left + (mark.offsetLeft - ta.scrollLeft) * scale;
    const y = r.top + (mark.offsetTop - ta.scrollTop) * scale + line;
    m.remove();
    return { x, y, line };
}

function buildBox() {
    const b = el("div", {
        position: "fixed", zIndex: "2100", display: "none", minWidth: "260px", maxWidth: "420px", maxHeight: "320px", overflowY: "auto",
        background: "var(--comfy-menu-bg, #202020)", border: "1px solid rgba(255,255,255,0.15)", borderRadius: "6px",
        boxShadow: "0 4px 16px rgba(0,0,0,0.5)", fontSize: "13px",
    });
    // 点候选时不让提示词框失焦
    b.addEventListener("mousedown", (e) => e.preventDefault());
    document.body.appendChild(b);
    return b;
}

function render() {
    box.innerHTML = "";
    hits.forEach((t, i) => {
        const [tag, zh, count, ban] = t;
        const row = el("div", { display: "flex", gap: "8px", padding: "3px 8px", cursor: "pointer", alignItems: "baseline",
            background: i === active ? "rgba(255,255,255,0.12)" : "", color: BAN_STYLE[ban]?.color ?? "" });
        if (ban) row.title = BAN_TIP[ban][0];
        row.appendChild(el("span", { flexShrink: "0" }, zh || tag));
        row.appendChild(el("span", { flex: "1", opacity: "0.6", fontSize: "12px", wordBreak: "break-all" }, tag));
        row.appendChild(el("span", { opacity: "0.5", fontSize: "11px" }, shortCount(count)));
        row.onmouseenter = () => {
            active = i;
            for (const [j, c] of [...box.children].entries()) c.style.background = j === i ? "rgba(255,255,255,0.12)" : "";
        };
        row.onclick = () => accept(i);
        box.appendChild(row);
    });
    box.children[active]?.scrollIntoView({ block: "nearest" });
}

function close() {
    hits = [];
    if (box) box.style.display = "none";
}

function update(ta) {
    if (!index) return;
    const q = currentToken(ta);
    hits = q ? search(q) : [];
    if (!hits.length) return close();
    target = ta;
    active = 0;
    box ??= buildBox();
    render();
    box.style.display = "block";
    const p = caretPoint(ta);
    const h = box.offsetHeight;
    box.style.left = Math.max(4, Math.min(p.x, innerWidth - box.offsetWidth - 4)) + "px";
    box.style.top = Math.max(4, p.y + h > innerHeight - 4 ? p.y - p.line - h : p.y) + "px";
}

function accept(i) {
    const t = hits[i];
    const ta = target;
    if (!t || !ta?.isConnected) return close();
    const end = ta.selectionStart;
    const after = ta.value.slice(end);
    const text = ta.value.slice(0, tokenStart) + toPrompt(t[0]) + (/^\s*[,，]/.test(after) ? "" : ", ");
    ta.value = text + after;
    ta.setSelectionRange(text.length, text.length);
    for (const n of app.graph?._nodes ?? app.graph?.nodes ?? []) {
        const w = n.widgets?.find((x) => x.element === ta);
        if (w) w.value = ta.value;
    }
    close();
    ta.dispatchEvent(new Event("input", { bubbles: true }));
    app.graph?.setDirtyCanvas(true, true);
    if (t[3]) toast("warn", BAN_TIP[t[3]][0], BAN_TIP[t[3]][1]);
}

app.registerExtension({
    name: "local.ZhTagAutocomplete",
    setup() {
        loadTags().then((data) => (index = buildIndex(data))).catch(() => {});
        document.addEventListener("input", (e) => {
            if (isPromptBox(e.target) && !e.isComposing) update(e.target);
        }, true);
        document.addEventListener("compositionend", (e) => {
            // 等上屏的字写进 textarea
            if (isPromptBox(e.target)) setTimeout(() => update(e.target), 0);
        }, true);
        document.addEventListener("keydown", (e) => {
            if (!hits.length || e.target !== target || e.isComposing) return;
            const keys = { ArrowDown: 1, ArrowUp: -1 };
            if (e.key in keys) {
                active = (active + keys[e.key] + hits.length) % hits.length;
                render();
            } else if ((e.key === "Enter" || e.key === "Tab") && !e.ctrlKey && !e.shiftKey && !e.altKey) {
                accept(active);
            } else if (e.key === "Escape") {
                close();
            } else {
                return;
            }
            e.preventDefault();
            e.stopImmediatePropagation();
        }, true);
        document.addEventListener("focusout", (e) => {
            if (e.target === target) setTimeout(() => document.activeElement !== target && close(), 0);
        }, true);
        // 鼠标挪了光标位置，旧候选就不对了
        document.addEventListener("click", (e) => {
            if (e.target === target) close();
        }, true);
    },
});
