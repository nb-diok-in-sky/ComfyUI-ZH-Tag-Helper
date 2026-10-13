// 提示词标签计数：按逗号（中英文）切分，只数非空段。
// 接到 KSampler / KSamplerAdvanced 的 positive / negative 时按上限变色，其他情况只显示个数。
import { app } from "../../scripts/app.js";

const LIMITS = {
    positive: { warn: 25, max: 30, label: "正向" },
    negative: { warn: 14, max: 15, label: "负向" },
};
const SAMPLERS = new Set(["KSampler", "KSamplerAdvanced"]);

function countTags(text) {
    return text.split(/[,，]/).filter((s) => s.trim() !== "").length;
}

function getLink(id) {
    const links = app.graph?.links;
    if (!links) return null;
    return typeof links.get === "function" ? links.get(id) : links[id];
}

function promptRole(node) {
    for (const id of node.outputs?.[0]?.links ?? []) {
        const link = getLink(id);
        if (!link) continue;
        const target = app.graph.getNodeById(link.target_id);
        if (!target || !SAMPLERS.has(target.type)) continue;
        const name = target.inputs?.[link.target_slot]?.name;
        if (name === "positive" || name === "negative") return name;
    }
    return null;
}

function attach(node) {
    const widget = node.widgets?.find((w) => w.name === "text");
    const textarea = widget?.element;
    const container = textarea?.parentElement;
    if (!container || container.querySelector(".tag-counter-badge")) return;

    container.style.position = "relative";
    const badge = document.createElement("div");
    badge.className = "tag-counter-badge";
    Object.assign(badge.style, {
        position: "absolute",
        left: "8px",
        bottom: "6px",
        padding: "1px 6px",
        borderRadius: "4px",
        fontSize: "11px",
        fontFamily: "monospace",
        pointerEvents: "none",
        zIndex: "10",
    });
    container.appendChild(badge);

    let last = null;
    const update = () => {
        if (!badge.isConnected) {
            clearInterval(timer);
            return;
        }
        const text = textarea.value ?? "";
        const role = promptRole(node);
        const key = text + "|" + role;
        if (key === last) return;
        last = key;

        const n = countTags(text);
        const limit = role && LIMITS[role];
        let color = "rgba(255,255,255,0.45)";
        let bg = "rgba(0,0,0,0.35)";
        let msg = `标签 ${n}`;
        if (limit) {
            msg = `${limit.label} 标签 ${n} / ${limit.max}`;
            if (n > limit.max) {
                color = "#fff";
                bg = "rgba(220,40,40,0.9)";
                msg += "  超出上限！";
            } else if (n >= limit.warn) {
                color = "#111";
                bg = "rgba(240,190,40,0.95)";
                msg += "  快到上限了";
            }
        }
        badge.textContent = msg;
        badge.style.color = color;
        badge.style.background = bg;
    };

    textarea.addEventListener("input", update);
    // 加载工作流、改连线时不会触发 input，用轻量轮询兜底
    const timer = setInterval(update, 500);
    update();
}

app.registerExtension({
    name: "local.TagCounter",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "CLIPTextEncode") return;
        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = onNodeCreated?.apply(this, arguments);
            setTimeout(() => attach(this), 150);
            return r;
        };
    },
});
