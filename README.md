# 山南的AI工具市场

分享日常工作中实用的 AI 技能，支持通过 WorkBuddy 和 Codex 的套件 / marketplace 安装。

当前提供 [TTL 资源工具箱](plugins/ttl-resources/README.md)：游戏 UI 资源处理工具，支持 PNG 九宫格转换。

## 安装与使用

在客户端的套件 / marketplace 管理中添加仓库地址：

```text
https://github.com/shannan1989/ai-marketplace
```

安装并启用 `ttl-resources`。Codex 中的套件展示名称为「TTL 资源工具箱」；WorkBuddy 中可通过 `ttl-resources` 和中文简介识别它。

使用 Codex CLI 时，也可以运行：

```bash
codex plugin marketplace add https://github.com/shannan1989/ai-marketplace
codex plugin add ttl-resources@shannan-skill-market
```

在聊天中附上 PNG 图片，然后说：

> 把这张 PNG 转成九宫格，左右、上下各保留 20 像素。

该技能需要 Python 3.9+ 和 Pillow 9.1+。安装套件不会自动安装 Python 依赖；缺少依赖时，助手会说明需要安装的内容。转换结果默认为图片旁的 `原名_s9.png`，保留原图。

## 维护文案与新增技能

展示文案从源配置生成，请优先修改以下文件：

| 文件 | 维护内容 |
| --- | --- |
| `marketplace.metadata.json` | 市场显示名、简介、发布者及仓库地址 |
| `plugins/<套件>/metadata.json` | 套件显示名、版本、简介、详情、分类、关键词及推荐提示词 |
| `plugins/<套件>/skills/<技能>/agents/openai.yaml` | Codex 技能显示名、短简介及默认提示词 |
| `plugins/<套件>/skills/<技能>/SKILL.md` | 技能触发说明和执行指导 |

`name` 和目录名是安装及调用使用的稳定标识；调整文案时保留 `shannan-ai-marketplace`、`ttl-resources`、`png-to-scale9sprite`。

修改后在仓库根目录运行：

```bash
npm ci
npm run generate
npm run check
```

`generate` 分别生成两个客户端的 marketplace 和插件 manifest；`check` 只校验输入和生成结果是否一致，不写文件。新增套件时，参照现有的 `metadata.json`，将技能放入其 `skills/` 目录。发布套件更新时在 metadata 中递增版本号，并一并提交源配置、技能文件和生成结果。

WorkBuddy 的套件标识保留英文名，中文套件名写入简介；Codex 使用 `interface.displayName` 展示中文名。`SKILL.md` 的触发说明不会被拼接成套件简介。隐私政策、服务条款及图标等字段在有实际内容后再按客户端支持情况添加。

使用远程仓库时，需要先发布这些修改，再在客户端刷新市场并更新套件；已有会话仍显示旧信息时，可新建会话或重启客户端后查看。
