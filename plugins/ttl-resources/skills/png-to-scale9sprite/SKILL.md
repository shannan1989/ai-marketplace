---
name: png-to-scale9sprite
description: 将 PNG 转换为适用于 Cocos2d-x Scale9Sprite 的九宫格图片，保留四角和透明度，支持设置边角及中间拉伸区域尺寸。用于“PNG 转九宫格”“转成 Scale9Sprite 图片”“压缩九宫格中间区域”等请求。独立于具体项目，不生成 Android .9.png 标记，也不自动识别拉伸边界。
---

# PNG 转 Scale9Sprite 九宫格

将 PNG 按九宫格分区缩放，输出可用于 `Scale9Sprite` 的普通 PNG 及对应的 `capInsets`。不依赖业务项目、游戏工程或 Cocos2d-x 运行环境。

使用随技能分发的 `scripts/png_to_scale9sprite.py`，运行环境为 Python 3.9+、Pillow 9.1+，不依赖 PHP / GD。选择已安装 Pillow 的 Python；依赖缺失时说明要求，安装前征得用户同意。

## 参数与效果

- 必须有输入 PNG 和保留边角尺寸。`20` 表示左右各保留 20 像素、上下各保留 20 像素；`20x30` 表示左右各 20、上下各 30。
- 未提供边角尺寸时，先问用户需要保留多少像素；可以查看图片帮助建议，但不能把推测当成已确认的裁切参数。
- 中间区域宽高可选，默认分别等于横纵边角尺寸；`-1` 表示该方向保留原始中间尺寸。这两个参数不是最终图片尺寸。
- 最终尺寸为 `(左右边角 * 2 + 中间宽) × (上下边角 * 2 + 中间高)`。四角像素不变，上下边只横向缩放，左右边只纵向缩放，中间双向缩放。
- 边角某一方向允许为 0，但该方向的中间尺寸必须另外指定为正数或 `-1`；原图扣除边角后必须仍有正尺寸的中间区域。
- 使用最近邻缩放，保留 RGBA 颜色和透明度，不进行调色板量化或平滑插值。
- 默认在输入图片旁输出 `原名_s9.png`，保留原文件。输出已存在时先询问是否覆盖；只有获得授权才传 `--force`，即使覆盖也不允许输出路径等于原图。

## 执行

从当前 `SKILL.md` 的位置确定技能安装目录，用脚本绝对路径执行，可在任意工作目录运行。下例的 `SKILL_DIR` 替换为实际安装目录；不要假设技能位于当前仓库的 `.agents/skills/` 下。路径包含空格时必须加引号。

```bash
SKILL_DIR="/安装位置/png-to-scale9sprite"
python3 "$SKILL_DIR/scripts/png_to_scale9sprite.py" "/path/panel.png" 20
python3 "$SKILL_DIR/scripts/png_to_scale9sprite.py" "/path/panel.png" 20x30 1 1
python3 "$SKILL_DIR/scripts/png_to_scale9sprite.py" "/path/panel.png" 20x30 -1 1 --output "/path/panel_s9.png"
```

第一例中间尺寸为 `20×20`、输出 `60×60`；第二例输出 `41×61`。转换脚本会输出原图尺寸、结果尺寸和 Cocos `capInsets`。

读取或写入用户提供的目录仍遵循当前权限。若目标目录不可写，申请所需权限，或与用户确认其他输出位置，不悄悄改变目标路径。

## 检查与交付

1. 核对参数、输出尺寸及边角范围；报错时修正参数，不裁掉原图内容或忽略解码错误。
2. 使用图像查看工具检查结果是否符合预期，特别是边角和透明区域；透明图预览不清楚时，可在临时位置合成棋盘格预览，不能改交付图片的透明背景。
3. 提供结果图片的绝对路径链接，说明边角尺寸、输出尺寸和 `capInsets`。不要只给脚本命令而不处理用户已提供且参数齐全的图片。

输出是普通 PNG，不会嵌入 Android `.9.png` 标记或自动写入九宫格元数据。Cocos 使用时需要正确的 `capInsets`，中间尺寸不等于边角尺寸时尤其不能依赖默认等分切片：

```cpp
auto sprite = ui::Scale9Sprite::create(Rect(cornerX, cornerY, centerWidth, centerHeight), filename);
```

用户只要求转换图片时，不修改业务代码、资源图集或工程配置。分发时保留整个 `png-to-scale9sprite/` 目录，确保脚本随技能一起提供；`scripts/test_png_to_scale9sprite.py` 可用于验证转换行为。
