// 词库：内置的 tag_categories.json + 用户自定义词，补全、分类面板、提示词上色共用一份。
// 自定义词存在 ComfyUI 的用户数据目录（user/default/zh_tag_helper_custom.json），更新插件不会丢。
// 自定义词可以是新词（比如 LoRA 触发词），也可以改内置词的中文和分类；内置词原有的违禁级别保持不变。
import { api } from "../../scripts/api.js";

const DATA_URL = new URL("./tag_categories.json", import.meta.url);
const CUSTOM_FILE = "zh_tag_helper_custom.json";
const CHANGED = "zh-tag-helper-changed";

// 每个大类一种颜色（r,g,b），分类面板和提示词底纹都用它。
export const GROUP_COLORS = {
    人物: "77,171,247",
    服饰: "247,131,172",
    表情动作: "105,219,124",
    镜头: "255,212,59",
    画面: "177,151,252",
    画风: "92,124,250",
    环境: "56,217,169",
    场景: "255,169,77",
    物品: "169,227,75",
    R18: "230,73,128",
    角色: "34,184,207",
    作品: "173,181,189",
    其他: "192,148,108",
};

export const BAN_STYLE = {
    2: { color: "#ff6b6b", border: "1px solid #e03131", background: "rgba(224,49,49,0.12)" },
    1: { color: "#ffa94d", border: "1px solid #e8590c", background: "rgba(232,89,12,0.10)" },
};
export const BAN_TIP = {
    2: ["🚫 违禁词（绝对禁用）", "正向提示词里不准用，一般只写在负向里"],
    1: ["⚠ 违禁词（仅全年龄）", "正向里有 nsfw / explicit / sensitive 时不准用"],
};

// 插入格式：下划线换空格，括号转义。
export function toPrompt(tag) {
    const t = /[a-z0-9]/i.test(tag) ? tag.replace(/_/g, " ") : tag;
    return t.replace(/([()])/g, "\\$1");
}

// 提示词里的写法 -> 词库里的键：去掉括号转义，空格换下划线，小写。
export function normTag(text) {
    return text.trim().replace(/\\([()])/g, "$1").replace(/\s+/g, "_").toLowerCase();
}

let basePromise = null;
let custom = [];
let merged = null;

function loadBase() {
    // no-cache：更新插件后别拿到浏览器里的旧词库（没变时服务器回 304，不会重新下载）
    basePromise ??= fetch(DATA_URL, { cache: "no-cache" }).then((r) => r.json()).catch((e) => {
        basePromise = null;
        throw e;
    });
    return basePromise;
}

async function loadCustom() {
    try {
        const r = await api.getUserData(CUSTOM_FILE);
        return r.ok ? await r.json() : [];
    } catch {
        return [];
    }
}

// tags 每项：[英文, 中文, 图片数, 违禁级别, 搜索别名, 是否自定义]；自定义词排在所属子类最前面。
function merge(base, entries) {
    const byTag = new Map(entries.map((e) => [e.tag, e]));
    const builtin = new Map();
    const groups = base.groups.map((g) => ({
        name: g.name,
        subs: g.subs.map((s) => ({
            name: s.name,
            tags: s.tags.filter((t) => {
                if (!byTag.has(t[0])) return true;
                builtin.set(t[0], t);
                return false;
            }),
        })),
    }));
    for (const e of [...entries].reverse()) {
        const g = groups.find((x) => x.name === e.group) ?? groups.find((x) => x.name === "其他");
        let s = g.subs.find((x) => x.name === e.sub);
        if (!s) {
            s = { name: e.sub, tags: [] };
            g.subs.push(s);
        }
        const b = builtin.get(e.tag);
        s.tags.unshift([e.tag, e.zh, b?.[2] ?? 0, b?.[3] ?? 0, b?.[4] ?? "", 1]);
    }
    return { groups };
}

export function loadTags() {
    merged ??= Promise.all([loadBase(), loadCustom()]).then(([base, entries]) => {
        custom = entries;
        return merge(base, entries);
    });
    return merged;
}

export function customEntries() {
    return custom;
}

// 新增或修改一个自定义词（按英文标签去重），存盘后通知各处刷新。
export async function saveCustomEntry(entry, remove = false) {
    await loadTags();
    const list = custom.filter((e) => e.tag !== entry.tag);
    if (!remove) list.unshift(entry);
    await api.storeUserData(CUSTOM_FILE, list, { overwrite: true, stringify: true, throwOnError: true });
    custom = list;
    merged = loadBase().then((base) => merge(base, list));
    window.dispatchEvent(new Event(CHANGED));
}

export function onTagsChanged(callback) {
    window.addEventListener(CHANGED, callback);
}
