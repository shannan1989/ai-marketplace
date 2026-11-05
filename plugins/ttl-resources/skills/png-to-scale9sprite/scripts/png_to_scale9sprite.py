#!/usr/bin/env python3
"""保留四角、分区缩放 PNG，生成 Cocos Scale9Sprite 使用的图片。"""

import argparse
import io
import json
from pathlib import Path
import re

from PIL import Image, UnidentifiedImageError


def parse_corner(value):
    """解析 20 或 20x30 格式的对称边角尺寸。"""
    if not re.fullmatch(r"[0-9]+(?:[xX][0-9]+)?", value):
        raise argparse.ArgumentTypeError("边角须为非负整数或 宽x高，例如 20、20x30")
    parts = re.split("[xX]", value)
    return int(parts[0]), int(parts[-1])


def resize_scale9(source, corner, center_width=None, center_height=None):
    """按九宫格缩放，返回 RGBA 图片及实际中间尺寸，不修改原图。"""
    # 1. 校验边角，并将默认值和 -1 转换为实际中间尺寸。
    corner_x, corner_y = corner
    if corner_x < 0 or corner_y < 0:
        raise ValueError("边角尺寸不能为负数")
    source_width, source_height = source.size
    inner_width = source_width - corner_x * 2
    inner_height = source_height - corner_y * 2
    if inner_width <= 0 or inner_height <= 0:
        raise ValueError("原图宽高必须分别大于对应边角尺寸的 2 倍")
    width = corner_x if center_width is None else center_width
    height = corner_y if center_height is None else center_height
    width = inner_width if width == -1 else width
    height = inner_height if height == -1 else height
    if width <= 0 or height <= 0:
        raise ValueError("中间尺寸须为正整数或 -1；边角为 0 时必须指定该方向的中间尺寸")

    # 2. 分别复制或缩放九个区域；直接粘贴 RGBA，避免重复混合透明度。
    rgba = source.convert("RGBA")
    target = Image.new("RGBA", (corner_x * 2 + width, corner_y * 2 + height))
    src_x = (0, corner_x, source_width - corner_x, source_width)
    src_y = (0, corner_y, source_height - corner_y, source_height)
    dst_x = (0, corner_x, corner_x + width, target.width)
    dst_y = (0, corner_y, corner_y + height, target.height)
    for row in range(3):
        for column in range(3):
            size = (dst_x[column + 1] - dst_x[column], dst_y[row + 1] - dst_y[row])
            if 0 in size:
                continue
            region = rgba.crop((src_x[column], src_y[row], src_x[column + 1], src_y[row + 1]))
            if region.size != size:
                region = region.resize(size, Image.Resampling.NEAREST)
            target.paste(region, (dst_x[column], dst_y[row]))
    return target, (width, height)


def convert_file(input_path, corner, center_width=None, center_height=None, output_path=None, force=False):
    """读取 PNG 并写入新文件，拒绝覆盖原图，默认不覆盖已有结果。"""
    source_path = Path(input_path).expanduser()
    target_path = Path(output_path).expanduser() if output_path else source_path.with_name(source_path.stem + "_s9.png")
    if source_path.resolve() == target_path.resolve():
        raise ValueError("输出不能覆盖原图")
    if target_path.suffix.lower() != ".png":
        raise ValueError("输出文件扩展名须为 .png")
    if target_path.exists() and source_path.exists() and source_path.samefile(target_path):
        raise ValueError("输出不能与原图指向同一个文件")
    if target_path.exists() and not force:
        raise FileExistsError("输出文件已存在；确认覆盖后可使用 --force")
    with Image.open(source_path) as source:
        if source.format != "PNG":
            raise ValueError("输入必须为 PNG 图片")
        if getattr(source, "is_animated", False):
            raise ValueError("不支持动态 PNG，请先选择需要转换的静态帧")
        target, center = resize_scale9(source, corner, center_width, center_height)
        buffer = io.BytesIO()
        options = {key: source.info[key] for key in ("icc_profile", "dpi") if key in source.info}
        target.save(buffer, format="PNG", **options)
        with target_path.open("wb" if force else "xb") as output:
            output.write(buffer.getvalue())
        return {
            "output": str(target_path.resolve()),
            "source_size": list(source.size),
            "output_size": list(target.size),
            "cap_insets": dict(zip(("x", "y", "width", "height"), (*corner, *center))),
        }


def main():
    """提供与 PHP 相同的四个位置参数，以及输出和覆盖选项。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="输入 PNG 路径")
    parser.add_argument("corner", type=parse_corner, help="保留边角：20 或 20x30")
    parser.add_argument("width", nargs="?", type=int, help="中间宽，默认横向边角；-1 保持原宽")
    parser.add_argument("height", nargs="?", type=int, help="中间高，默认纵向边角；-1 保持原高")
    parser.add_argument("--output", type=Path, help="输出路径，默认 原名_s9.png")
    parser.add_argument("--force", action="store_true", help="覆盖已有结果，不允许覆盖原图")
    args = parser.parse_args()
    try:
        result = convert_file(args.input, args.corner, args.width, args.height, args.output, args.force)
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError) as error:
        parser.exit(1, f"转换失败：{error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
