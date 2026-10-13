// 提示词上色：词库里认得的标签，在提示词框里按大类铺一层半透明底色；认不出的（自写句子、<lora:...>、没加进词库的触发词）不上色。
// 权重写法如 (long hair:1.2)：只有 long hair 上分类色，括号和 :1.2 铺灰色。
// 做法：文本框改成透明背景，在它下面放一个排版完全相同的 div，div 里文字透明、只显示底色。
// 开关和深浅在侧边栏「画风图鉴」里调，记在本机浏览器里。
import { app } from "../../scripts/app.js";
import { GROUP_COLORS, loadTags, normTag, onTagsChanged } from "./tag_data.js";

const SETTINGS_KEY = "local.tagHighlight";
const COPY = ["fontFamily", "fontSize", "fontWeight", "fontStyle", "lineHeight", "letterSpacing", "wordSpacing", "tabSize",
    "textIndent", "paddingTop", "paddingRight", "paddingBottom", "paddingLeft", "borderTopWidth", "borderRightWidth",
    "borderBottomWidth", "borderLeftWidth", "borderTopLeftRadius", "borderTopRightRadius", "borderBottomLeftRadius", "borderBottomRightRadius"];
// 一段 = 两个逗号之间：前导空白和括号 / 标签本体 / 权重和收尾括号（不吃掉转义的 \)）/ 尾随空白
const PART = /^(\s*[([{]*)(.*?)((?::\s*-?[\d.]+)?(?:(?<!\\)[)\]}])*\s*)$/s;

let lookup = new Map();
const boxes = new Map();
let settings = { on: true, alpha: 0.2 };
try {
    settings = { ...settings, ...JSON.parse(localStorage.getItem(SETTINGS_KEY)) };
} catch {}

export function getHighlightSettings() {
    return { ...settings };
}

// alpha：底色不透明度 0~1
export function setHighlightSettings(next) {
    settings = { ...settings, ...next };
    try {
        localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
    } catch {}
    for (const st of boxes.values()) st.text = null;
    scan();
}

function esc(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function span(text, background) {
    return text ? `<span style="background:${background};border-radius:3px">${esc(text)}</span>` : "";
}

function paint(text) {
    if (!settings.on) return esc(text) + "​";
    const syntax = `rgba(150,150,150,${(settings.alpha * 0.8).toFixed(2)})`;
    let html = "";
    for (const piece of text.split(/([,，\n])/)) {
        const m = piece.match(PART);
        const color = m && m[2] && lookup.get(normTag(m[2]));
        if (!color) {
            html += esc(piece);
            continue;
        }
        const [lead, core, trail] = [m[1], m[2], m[3]];
        const ws = lead.match(/^\s*/)[0];
        const tailWs = trail.match(/\s*$/)[0];
        html += esc(ws) + span(lead.slice(ws.length), syntax) + span(core, `rgba(${color},${settings.alpha})`)
            + span(trail.slice(0, trail.length - tailWs.length), syntax) + esc(tailWs);
    }
    // 末尾换行要多占一行，否则底色层比文本框矮
    return html + "​";
}

function attach(ta) {
    const box = ta.parentElement;
    if (!box) return;
    if (getComputedStyle(box).position === "static") box.style.position = "relative";
    const layer = document.createElement("div");
    Object.assign(layer.style, {
        position: "absolute", pointerEvents: "none", overflow: "hidden", boxSizing: "border-box", margin: "0",
        whiteSpace: "pre-wrap", overflowWrap: "break-word", wordBreak: "normal", color: "transparent",
        borderStyle: "solid", borderColor: "transparent", zIndex: "0",
    });
    // 原来的背景挪到底色层上，文本框本身变透明
    layer.style.background = getComputedStyle(ta).backgroundColor;
    ta.style.background = "transparent";
    if (getComputedStyle(ta).position === "static") ta.style.position = "relative";
    ta.style.zIndex = "1";
    box.insertBefore(layer, ta);
    const state = { layer, text: null, ro: new ResizeObserver(() => sync(ta)) };
    state.ro.observe(ta);
    ta.addEventListener("input", () => update(ta));
    ta.addEventListener("scroll", () => (layer.scrollTop = ta.scrollTop));
    boxes.set(ta, state);
    sync(ta);
}

// 底色层和文本框一样大、一样的内边距；文本框有滚动条时右边多留出滚动条宽度，换行位置才一致。
function sync(ta) {
    const st = boxes.get(ta);
    const s = getComputedStyle(ta);
    for (const p of COPY) st.layer.style[p] = s[p];
    const bar = ta.offsetWidth - ta.clientWidth - ta.clientLeft * 2;
    st.layer.style.paddingRight = `calc(${s.paddingRight} + ${Math.max(0, bar)}px)`;
    Object.assign(st.layer.style, {
        left: ta.offsetLeft + "px", top: ta.offsetTop + "px", width: ta.offsetWidth + "px", height: ta.offsetHeight + "px",
    });
    st.text = null;
    update(ta);
}

function update(ta) {
    const st = boxes.get(ta);
    if (!st || st.text === ta.value) return;
    st.text = ta.value;
    st.layer.innerHTML = paint(ta.value);
    st.layer.scrollTop = ta.scrollTop;
}

// 新出现的提示词框挂上底色层；加载工作流等不触发 input 的改动也靠这里补刷新。
function scan() {
    for (const ta of document.querySelectorAll("textarea.comfy-multiline-input")) {
        if (boxes.has(ta)) update(ta);
        else attach(ta);
    }
    for (const [ta, st] of boxes) {
        if (ta.isConnected) continue;
        st.ro.disconnect();
        st.layer.remove();
        boxes.delete(ta);
    }
}

function rebuild(data) {
    lookup = new Map();
    for (const g of data.groups) {
        const color = GROUP_COLORS[g.name] ?? GROUP_COLORS.其他;
        for (const s of g.subs) for (const t of s.tags) lookup.set(t[0].toLowerCase(), color);
    }
    for (const st of boxes.values()) st.text = null;
    scan();
}

app.registerExtension({
    name: "local.TagHighlight",
    setup() {
        const reload = () => loadTags().then(rebuild).catch(() => {});
        onTagsChanged(reload);
        reload();
        setInterval(scan, 700);
    },
});
