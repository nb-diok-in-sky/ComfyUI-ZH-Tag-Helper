# ComfyUI-ZH-Tag-Helper 中文标签助手

给 ComfyUI 提示词框用的中文 Danbooru 标签工具。纯前端，不加节点，不装 Python 依赖，运行时不联网。

## 功能

| 功能 | 怎么用 |
| --- | --- |
| **中文补全** | 在提示词框里打中文或英文（`长发`、`双马尾`、`long h`），光标处弹出候选。↑↓ 选择，Enter / Tab 插入，Esc 关闭，也可以鼠标点。中文输入法上屏后才搜索。 |
| **分类面板** | 点进提示词框，框旁边弹出分类面板：人物 / 服饰 / 表情动作 / 镜头 / 画面 / 画风 / 环境 / 场景 / 物品 / R18 / 角色 / 作品 / 其他，每个大类最前面是「全部」。点标签插到光标处，自动补逗号。点画布空白处或 Esc 收起，右下角可拉大小。 |
| **提示词上色** | 提示词框里，词库认得的标签按大类铺一层底色（人物蓝、服饰粉、表情动作绿、镜头黄、画面紫、画风靛蓝、环境青、场景橙、物品黄绿、R18 品红、角色蓝绿、作品灰、其他棕），分类面板左侧的色条就是图例。权重写法如 `(long hair:1.2)` 只给 `long hair` 上色，括号和 `:1.2` 是灰色。认不出的内容（句子、`<lora:...>`、没加进词库的触发词）不上色。侧边栏「画风图鉴」里可以关掉上色或调颜色深浅。 |
| **自定义词库** | 分类面板点「＋ 自定义词」：填英文标签、中文，选大类和子类（也可以新建子类，比如「LoRA 触发词」）。保存后补全、分类面板、上色立刻都认得这个词。「★ 我的词库」里修改或删除。存在 ComfyUI 的 `user/default/zh_tag_helper_custom.json`，更新插件不会丢。 |
| **违禁词标记** | 低龄相关标签照常收录、照常排序，但中文前带「🚫违禁词·」（绝对禁用）或「⚠违禁词·仅全年龄·」，补全和面板里标红 / 标橙，插入时弹提醒。 |
| **标签计数** | 提示词框左下角实时显示标签数；接到 KSampler 的正向 / 负向会按上限变色（正向 25 黄 / 30 红，负向 14 黄 / 15 红）。 |
| **画风图鉴窗口** | 左侧边栏「画风图鉴」打开大窗口：提示词分类 / 画师 / LoRA 画风三页。拖顶栏移动、拖右下角缩放，记住位置。 |

- 词库约 3.2 万条：通用标签 1.7 万、角色 1.2 万（按作品分组，如 原神 / 明日方舟 / Fate / hololive）、作品 3 千。
- 插入格式：下划线换空格，括号转义，例如 `artoria pendragon \(fate\)`。
- 可以在侧边栏「画风图鉴」里取消勾选「点进提示词框时，在旁边弹出分类面板」。

## 安装

```
cd ComfyUI/custom_nodes
git clone https://github.com/nb-diok-in-sky/ComfyUI-ZH-Tag-Helper.git
```

重启 ComfyUI，浏览器刷新。词库 `web/tag_categories.json` 已经生成好，不用额外下载。

**和 ComfyUI-Autocomplete-Plus 二选一**：两个同时开，打字时会出现两个补全框。本插件已经包含中文补全，建议停用 Autocomplete-Plus（把它的文件夹移出 `custom_nodes` 即可）。

可选（不在仓库里）：
- 画师页：把 [Illustrious-NoobAI-Style-Explorer](https://github.com/ThetaCursed/Illustrious-NoobAI-Style-Explorer) clone 到本插件的 `explorer/`，没有它时画师页是空的。
- LoRA 画风页：在 `lora_styles/` 放预览图和 `manifest.json`，格式 `[{"style": "画风名", "thumb": "文件名.webp"}]`。

## 词库数据格式

`web/tag_categories.json`：`groups[].subs[].tags[]`，每个标签是

```
[英文标签, 中文, Danbooru 图片数, 违禁级别, 其他别名（仅供搜索）]
```

违禁级别：`2` = 🚫 绝对禁用（正向提示词任何时候都不能用），`1` = ⚠ 仅全年龄（正向里有 nsfw / explicit / sensitive 时不能用），`0` = 可用。
让 AI 帮忙写提示词时，可以直接读这个字段过滤。

自定义词 `user/default/zh_tag_helper_custom.json`：`[{"tag": "my_lora_trigger", "zh": "我的画风", "group": "画风", "sub": "LoRA 触发词"}]`。改的是内置词时，原有的违禁级别保持不变。

## 重新生成词库

```
python tools/fetch_sources.py           # 下载原始数据到 tools/sources/（可加 --proxy http://127.0.0.1:7890）
python tools/build_zh_tags.py           # 合并中文翻译、标违禁词 -> tools/build/
python tools/build_tag_categories.py    # 分类 -> web/tag_categories.json
```

- 翻译表里没有中文的词，手工翻译在 `tools/zh_extra.tsv`。
- 违禁词规则在 `tools/build_zh_tags.py`，分类规则在 `tools/build_tag_categories.py`。

## 数据来源

标签与热度来自 newtextdoc1111/danbooru-tag-csv（MIT），中文翻译来自 ffdkj 的 Danbooru 中英对照表（MIT），分类参考 Danbooru wiki 的 Tag group 页面。详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## 许可证

MIT © nb-diok-in-sky
