# TTL 资源工具箱

游戏 UI 资源处理工具，支持 PNG 九宫格转换。套件标识为 `ttl-resources`。

## PNG 九宫格转换

按用户指定的边角尺寸保留四角与透明度，压缩中间拉伸区域，生成可用于 Cocos2d-x Scale9Sprite 的普通 PNG，并输出 `capInsets` 切片参数。

附上 PNG 图片后，可以直接说：

> 把这张 PNG 转成九宫格，左右、上下各保留 20 像素。

> 把这张 PNG 的中间区域压缩到 1×1 像素，左右、上下各保留 20 像素。

默认中间区域宽高分别等于横向、纵向边角尺寸；中间区域尺寸不是最终图片尺寸。默认输出 `原名_s9.png`，保留原图。转换不会生成 Android `.9.png` 标记，也不会自动识别边角尺寸。

需要 Python 3.9+ 和 Pillow 9.1+。安装套件不会自动安装 Python 依赖；缺失时助手会先说明并征得同意。安装方法见[仓库说明](../../README.md)，详细参数见[技能说明](skills/png-to-scale9sprite/SKILL.md)。

## 维护

套件名称、简介、详情、推荐提示词及版本在 [metadata.json](metadata.json) 中维护。在仓库根目录运行 `npm run generate` 和 `npm run check`，同步两个客户端的配置。技能的 Codex 展示信息在其 `agents/openai.yaml` 中维护。
