// 点进提示词框时，在框旁边弹出「提示词分类」小面板，点标签插到光标处。
// 面板上按鼠标不会抢走提示词框的焦点；点画布或别处自动收起，Esc 也能关。
// 可以在侧边栏「画风图鉴」里关掉自动弹出。
import { app } from "../../scripts/app.js";
import { buildTagBrowser } from "./tag_browser.js";

const ENABLED_KEY = "local.tagSidePanel.enabled";
const SIZE_KEY = "local.tagSidePanel.size";

function load(key, fallback) {
    try {
        return JSON.parse(localStorage.getItem(key)) ?? fallback;
    } catch {
        return fallback;
    }
}

function save(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch {}
}

export function isSidePanelEnabled() {
    return load(ENABLED_KEY, true);
}

export function setSidePanelEnabled(on) {
    save(ENABLED_KEY, on);
    if (!on) hide();
}

let panel = null;
let target = null;
let timer = null;
// ComfyUI 在按下鼠标时会让提示词框失焦，记住这次按下是不是在面板里，免得面板被收起。
let pressInPanel = false;

function toast(severity, summary, detail) {
    app.extensionManager?.toast?.add({ severity, summary, detail, life: 1800 });
}

function isPromptBox(e) {
    return e instanceof HTMLTextAreaElement && e.classList.contains("comfy-multiline-input") && !e.readOnly;
}

// 插到光标处，前后补好逗号。
// 大窗口也用它：插到这个提示词框上次的光标位置。refocus 为 true 时把焦点还给提示词框。
export function insertIntoBox(ta, tag, refocus = false) {
    const v = ta.value;
    const start = ta.selectionStart ?? v.length;
    const before = v.slice(0, start).replace(/\s+$/, "");
    const after = v.slice(ta.selectionEnd ?? start).replace(/^[\s,，]+/, "");
    const head = before ? before + (/[,，]$/.test(before) ? " " : ", ") : "";
    const text = head + tag + ", ";
    ta.value = text + after;
    if (refocus) ta.focus({ preventScroll: true });
    ta.setSelectionRange(text.length, text.length);
    const nodes = app.graph?._nodes ?? app.graph?.nodes ?? [];
    for (const n of nodes) {
        const w = n.widgets?.find((x) => x.element === ta);
        if (w) w.value = ta.value;
    }
    ta.dispatchEvent(new Event("input", { bubbles: true }));
    app.graph?.setDirtyCanvas(true, true);
}

function insertAtCursor(tag) {
    if (!target?.isConnected) return;
    // 正在面板的搜索框或表单里打字时，焦点留在那里
    const searching = document.activeElement instanceof HTMLInputElement && panel.contains(document.activeElement);
    insertIntoBox(target, tag, !searching);
}

function build() {
    const size = load(SIZE_KEY, { w: 460, h: 480 });
    const root = document.createElement("div");
    Object.assign(root.style, {
        position: "fixed", zIndex: "1500", display: "none", flexDirection: "column",
        width: size.w + "px", height: size.h + "px", minWidth: "300px", minHeight: "240px",
        resize: "both", overflow: "hidden", borderRadius: "8px",
        background: "var(--comfy-menu-bg, #202020)", boxShadow: "0 0 20px rgba(0,0,0,0.6)",
    });
    const head = document.createElement("div");
    Object.assign(head.style, { display: "flex", alignItems: "center", padding: "4px 8px", fontSize: "12px", opacity: "0.8", flexShrink: "0" });
    head.textContent = "提示词分类 · 点击插到光标处 · 右下角可拉大小";
    const close = document.createElement("button");
    Object.assign(close.style, { marginLeft: "auto", cursor: "pointer", padding: "0 8px" });
    close.textContent = "✕";
    close.onclick = hide;
    head.appendChild(close);
    const box = document.createElement("div");
    Object.assign(box.style, { flex: "1", minHeight: "0", display: "flex", flexDirection: "column" });
    root.append(head, box);
    buildTagBrowser(box, insertAtCursor, toast, true);
    // 只有搜索框和自定义词表单需要焦点，其余地方按下鼠标时保住提示词框的光标。
    // e.target === root 时是右下角的缩放把手，不能拦。
    root.addEventListener("mousedown", (e) => {
        if (e.target !== root && !(e.target instanceof HTMLInputElement || e.target instanceof HTMLSelectElement)) e.preventDefault();
    });
    root.addEventListener("mouseup", () => save(SIZE_KEY, { w: root.offsetWidth, h: root.offsetHeight }));
    document.body.appendChild(root);
    return root;
}

function place() {
    if (!target?.isConnected) return hide();
    const r = target.getBoundingClientRect();
    if (!r.width || !r.height) return hide();
    const w = panel.offsetWidth;
    const h = panel.offsetHeight;
    let left = r.right + 8;
    if (left + w > innerWidth - 8) left = r.left - w - 8;
    if (left < 8) left = Math.max(8, innerWidth - w - 8);
    const top = Math.min(Math.max(8, r.top), Math.max(8, innerHeight - h - 8));
    panel.style.left = left + "px";
    panel.style.top = top + "px";
}

function show(ta) {
    panel ??= build();
    target = ta;
    panel.style.display = "flex";
    place();
    clearInterval(timer);
    // 画布平移缩放时提示词框会动，跟着走
    timer = setInterval(place, 250);
}

function hide() {
    clearInterval(timer);
    if (panel) panel.style.display = "none";
}

app.registerExtension({
    name: "local.TagSidePanel",
    setup() {
        addEventListener("pointerdown", (e) => {
            pressInPanel = !!panel?.contains(e.target);
            // 点了面板里的分类按钮后提示词框已经失焦，再点别处时直接收起
            if (!pressInPanel && e.target !== target) hide();
        }, true);
        document.addEventListener("focusin", (e) => {
            if (isPromptBox(e.target)) {
                if (isSidePanelEnabled()) show(e.target);
            } else if (!panel?.contains(e.target)) {
                hide();
            }
        }, true);
        document.addEventListener("focusout", (e) => {
            if (e.target !== target && !panel?.contains(e.target)) return;
            setTimeout(() => {
                const a = document.activeElement;
                if (a !== target && !panel?.contains(a) && !pressInPanel) hide();
            }, 0);
        }, true);
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape" && panel?.style.display === "flex") hide();
        }, true);
    },
});
