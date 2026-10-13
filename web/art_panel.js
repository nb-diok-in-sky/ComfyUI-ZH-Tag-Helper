// 左侧边栏「画风图鉴」：
//  - 画师：本地版 Illustrious/NoobAI Style Explorer。它点卡片时会把画师名写进剪贴板，
//    这里拦截那一次写入，顺便插进最后点过的提示词框（名字本身已经带好 \( \) 转义）。
//  - LoRA 画风：AI styles dump 每个画风名的预览图，点击插入画风名。
//  - 提示词分类：中文词库按 大类 / 子类 浏览（tag_browser.js），点击插入。
import { app } from "../../scripts/app.js";
import { buildTagBrowser } from "./tag_browser.js";
import { insertIntoBox, isSidePanelEnabled, setSidePanelEnabled } from "./tag_side_panel.js";

const SAMPLERS = new Set(["KSampler", "KSamplerAdvanced"]);
let lastPromptNode = null;

function getLink(id) {
    const links = app.graph?.links;
    if (!links) return null;
    return typeof links.get === "function" ? links.get(id) : links[id];
}

function textWidget(node) {
    return node?.widgets?.find((w) => w.name === "text");
}

function isPositivePrompt(node) {
    for (const id of node.outputs?.[0]?.links ?? []) {
        const link = getLink(id);
        const target = link && app.graph.getNodeById(link.target_id);
        if (target && SAMPLERS.has(target.type) && target.inputs?.[link.target_slot]?.name === "positive") return true;
    }
    return false;
}

function targetNode() {
    if (lastPromptNode && app.graph.getNodeById(lastPromptNode.id) === lastPromptNode) return lastPromptNode;
    const prompts = (app.graph?._nodes ?? app.graph?.nodes ?? []).filter((n) => n.type === "CLIPTextEncode");
    return prompts.find(isPositivePrompt) ?? prompts[0] ?? null;
}

function toast(severity, summary, detail) {
    app.extensionManager?.toast?.add({ severity, summary, detail, life: 1800 });
}

function insertTag(tag) {
    const node = targetNode();
    const widget = textWidget(node);
    if (!widget?.element) {
        toast("warn", "没有找到提示词框", "先打开一个生图工作流");
        return;
    }
    // 插到这个框上次的光标位置（没点过的框光标在末尾）
    insertIntoBox(widget.element, tag);
    toast("success", `已插入到「${node.title || "提示词"}」光标处`, tag);
}

function hookExplorer(iframe) {
    const clip = iframe.contentWindow?.navigator?.clipboard;
    if (!clip) return;
    const original = clip.writeText.bind(clip);
    Object.defineProperty(clip, "writeText", {
        configurable: true,
        value: (text) => {
            insertTag(String(text).trim());
            return original(text).catch(() => {});
        },
    });
}

function el(tag, style, text) {
    const e = document.createElement(tag);
    if (style) Object.assign(e.style, style);
    if (text) e.textContent = text;
    return e;
}

async function buildLoraGrid(box) {
    let items;
    try {
        items = await (await fetch("/lora-styles/manifest.json")).json();
    } catch {
        box.textContent = "还没有 LoRA 画风预览图。";
        return;
    }
    box.appendChild(el("div", { padding: "6px 8px", fontSize: "12px", opacity: "0.75" },
        "AI styles dump 的画风预览（同一人物、同一种子，只换画风名）。点击插入画风名；记得在 LoRA 节点里打开这个 LoRA。"));
    const grid = el("div", { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: "8px", padding: "8px" });
    for (const it of items) {
        const card = el("div", { cursor: it.style ? "pointer" : "default", borderRadius: "6px", overflow: "hidden", background: "rgba(255,255,255,0.05)" });
        const img = el("img", { width: "100%", display: "block" });
        img.loading = "lazy";
        img.src = `/lora-styles/${encodeURIComponent(it.thumb)}`;
        card.appendChild(img);
        card.appendChild(el("div", { fontSize: "13px", padding: "4px 6px", wordBreak: "break-all" }, it.style || "（不写画风名·对照）"));
        if (it.style) card.addEventListener("click", () => insertTag(it.style));
        grid.appendChild(card);
    }
    box.appendChild(grid);
}

// 大窗口：挂在 body 上，只建一次，关掉只是隐藏（图鉴不用重新加载）。
// 拖顶栏移动、拖右下角缩放，位置和大小记在本机浏览器里；「全屏」几乎铺满，「还原」回到靠右的默认大小。
const GEOMETRY_KEY = "local.artPanel.geometry";
let win = null;

function defaultGeometry() {
    const width = Math.min(960, innerWidth * 0.6);
    const height = Math.min(680, innerHeight * 0.8);
    return { left: innerWidth - width - 16, top: 60, width, height };
}

function fullGeometry() {
    return { left: innerWidth * 0.02, top: innerHeight * 0.03, width: innerWidth * 0.96, height: innerHeight * 0.95 };
}

function applyGeometry(root, g) {
    const width = Math.min(g.width, innerWidth - 16);
    const height = Math.min(g.height, innerHeight - 16);
    Object.assign(root.style, {
        width: width + "px", height: height + "px",
        left: Math.min(Math.max(0, g.left), innerWidth - width) + "px",
        top: Math.min(Math.max(0, g.top), innerHeight - height) + "px",
    });
}

function saveGeometry(root) {
    const r = root.getBoundingClientRect();
    try {
        localStorage.setItem(GEOMETRY_KEY, JSON.stringify({ left: r.left, top: r.top, width: r.width, height: r.height }));
    } catch {}
}

function savedGeometry() {
    try {
        return JSON.parse(localStorage.getItem(GEOMETRY_KEY)) ?? defaultGeometry();
    } catch {
        return defaultGeometry();
    }
}

// 拖动时鼠标会被画师页的 iframe 吃掉，拖动期间先关掉它的鼠标事件。
function makeDraggable(root, handle) {
    handle.style.cursor = "move";
    handle.addEventListener("mousedown", (e) => {
        if (e.target !== handle) return;
        e.preventDefault();
        const r = root.getBoundingClientRect();
        const dx = e.clientX - r.left;
        const dy = e.clientY - r.top;
        const frames = [...root.querySelectorAll("iframe")];
        frames.forEach((f) => (f.style.pointerEvents = "none"));
        const move = (m) => applyGeometry(root, { left: m.clientX - dx, top: m.clientY - dy, width: r.width, height: r.height });
        const up = () => {
            frames.forEach((f) => (f.style.pointerEvents = ""));
            removeEventListener("mousemove", move);
            removeEventListener("mouseup", up);
            saveGeometry(root);
        };
        addEventListener("mousemove", move);
        addEventListener("mouseup", up);
    });
    // 右下角原生缩放把手松手后记下大小
    root.addEventListener("mouseup", (e) => {
        if (e.target === root) saveGeometry(root);
    });
}

function buildWindow() {
    const root = el("div", {
        position: "fixed", zIndex: "2000", display: "none", flexDirection: "column",
        background: "var(--comfy-menu-bg, #202020)", borderRadius: "8px",
        boxShadow: "0 0 30px rgba(0,0,0,0.6)", overflow: "hidden",
        resize: "both", minWidth: "480px", minHeight: "320px",
    });
    const bar = el("div", { display: "flex", gap: "6px", padding: "8px", alignItems: "center", flexShrink: "0" });
    const views = {};
    const tabs = {};
    let tagsBuilt = false;
    const show = (key) => {
        if (key === "tags" && !tagsBuilt) {
            tagsBuilt = true;
            buildTagBrowser(views.tags, insertTag, toast);
        }
        for (const k in views) {
            views[k].style.display = k === key ? (k === "tags" ? "flex" : "block") : "none";
            tabs[k].style.opacity = k === key ? "1" : "0.5";
        }
    };
    for (const [key, label] of [["artist", "画师"], ["lora", "LoRA 画风"], ["tags", "提示词分类"]]) {
        const b = el("button", { padding: "4px 14px", cursor: "pointer", fontSize: "14px" }, label);
        b.onclick = () => show(key);
        tabs[key] = b;
        bar.appendChild(b);
    }
    bar.appendChild(el("div", { fontSize: "12px", opacity: "0.7", marginLeft: "8px", pointerEvents: "none" },
        "点卡片 = 插到最后点过的提示词框的光标处 · 拖这里移动，拖右下角缩放"));
    const size = el("button", { marginLeft: "auto", padding: "4px 12px", cursor: "pointer" }, "⤢ 全屏");
    size.onclick = () => {
        const full = size.textContent === "⤢ 全屏";
        applyGeometry(root, full ? fullGeometry() : defaultGeometry());
        size.textContent = full ? "⤡ 还原" : "⤢ 全屏";
        saveGeometry(root);
    };
    const close = el("button", { padding: "4px 12px", cursor: "pointer" }, "✕ 关闭");
    close.onclick = () => (root.style.display = "none");
    bar.appendChild(size);
    bar.appendChild(close);
    root.appendChild(bar);

    const iframe = el("iframe", { border: "0", width: "100%", height: "100%" });
    iframe.src = "/artist-explorer/index_local.html";
    iframe.addEventListener("load", () => hookExplorer(iframe));
    views.artist = el("div", { flex: "1", minHeight: "0" });
    views.artist.appendChild(iframe);
    views.lora = el("div", { flex: "1", minHeight: "0", overflowY: "auto", display: "none" });
    buildLoraGrid(views.lora);
    views.tags = el("div", { flex: "1", minHeight: "0", display: "none", flexDirection: "column" });
    root.appendChild(views.artist);
    root.appendChild(views.lora);
    root.appendChild(views.tags);
    makeDraggable(root, bar);
    document.body.appendChild(root);
    show("artist");
    return { root, show };
}

function openWindow(key) {
    win ??= buildWindow();
    win.root.style.display = "flex";
    applyGeometry(win.root, savedGeometry());
    win.show(key);
}

function render(container) {
    container.innerHTML = "";
    const box = el("div", { padding: "12px", display: "flex", flexDirection: "column", gap: "8px" });
    for (const [key, label] of [["artist", "打开画风图鉴"], ["tags", "打开提示词分类"]]) {
        const btn = el("button", { padding: "8px", cursor: "pointer", fontSize: "14px" }, label);
        btn.onclick = () => openWindow(key);
        box.appendChild(btn);
    }
    box.appendChild(el("div", { fontSize: "12px", opacity: "0.7" }, "大窗口可以拖顶栏移动、拖右下角缩放，会记住上次的位置和大小。"));
    const label = el("label", { display: "flex", gap: "6px", alignItems: "center", fontSize: "13px", cursor: "pointer", marginTop: "8px" });
    const check = el("input");
    check.type = "checkbox";
    check.checked = isSidePanelEnabled();
    check.onchange = () => setSidePanelEnabled(check.checked);
    label.append(check, "点进提示词框时，在旁边弹出分类面板");
    box.appendChild(label);
    container.appendChild(box);
}

app.registerExtension({
    name: "local.ArtStylePanel",
    setup() {
        document.addEventListener("focusin", (e) => {
            if (!(e.target instanceof HTMLTextAreaElement)) return;
            const nodes = app.graph?._nodes ?? app.graph?.nodes ?? [];
            const node = nodes.find((n) => n.type === "CLIPTextEncode" && textWidget(n)?.element === e.target);
            if (node) lastPromptNode = node;
        }, true);
        app.extensionManager?.registerSidebarTab?.({
            id: "local-art-style-panel",
            icon: "pi pi-palette",
            title: "画风图鉴",
            tooltip: "画风图鉴：画师 / LoRA 画风 / 提示词分类，点击插入提示词",
            type: "custom",
            render,
        });
    },
});
