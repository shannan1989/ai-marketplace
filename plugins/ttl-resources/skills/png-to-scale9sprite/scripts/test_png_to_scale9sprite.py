"""九宫格转换的像素、参数和文件保护回归测试。"""

import argparse
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from png_to_scale9sprite import convert_file, parse_corner, resize_scale9


class Scale9Tests(unittest.TestCase):
    def setUp(self):
        """创建每个像素不同且包含透明度的非正方形测试图。"""
        self.source = Image.new("RGBA", (13, 17))
        self.source.putdata([(x * 17, y * 13, (x + y) * 7, (x * 19 + y * 11) % 256)
                             for y in range(17) for x in range(13)])

    def test_corner_formats(self):
        """边角支持等宽及宽高独立格式，拒绝其他输入。"""
        self.assertEqual(parse_corner("2"), (2, 2))
        self.assertEqual(parse_corner("2X3"), (2, 3))
        for value in ("-1", "2.5", "2x3x4", "", "ax3"):
            with self.assertRaises(argparse.ArgumentTypeError):
                parse_corner(value)

    def test_default_and_custom_sizes(self):
        """默认中间尺寸等于边角，自定义尺寸独立生效。"""
        target, center = resize_scale9(self.source, (2, 3))
        self.assertEqual(center, (2, 3))
        self.assertEqual(target.size, (6, 9))
        target, center = resize_scale9(self.source, (2, 3), 1, 2)
        self.assertEqual(center, (1, 2))
        self.assertEqual(target.size, (5, 8))

    def test_corners_preserve_exact_pixels(self):
        """四角位置改变但像素和半透明颜色不变。"""
        target, _ = resize_scale9(self.source, (2, 3), 1, 2)
        for sx, sy, tx, ty in ((0, 0, 0, 0), (11, 0, 3, 0), (0, 14, 0, 5), (11, 14, 3, 5)):
            self.assertEqual(self.source.crop((sx, sy, sx + 2, sy + 3)).tobytes(),
                             target.crop((tx, ty, tx + 2, ty + 3)).tobytes())

    def test_nine_regions_do_not_mix(self):
        """九个区域的颜色独立，透明度不经遮罩重复混合。"""
        source = Image.new("RGBA", (12, 18))
        xs, ys = (0, 2, 10, 12), (0, 3, 15, 18)
        for row in range(3):
            for col in range(3):
                source.paste((row * 70, col * 70, 100, (row * 3 + col) * 31),
                             (xs[col], ys[row], xs[col + 1], ys[row + 1]))
        target, _ = resize_scale9(source, (2, 3), 1, 2)
        for row, y in enumerate((0, 3, 5)):
            for col, x in enumerate((0, 2, 3)):
                self.assertEqual(target.getpixel((x, y)), (row * 70, col * 70, 100, (row * 3 + col) * 31))

    def test_keep_original_size(self):
        """-1 保留原尺寸，逐像素往返不变。"""
        target, center = resize_scale9(self.source, (2, 3), -1, -1)
        self.assertEqual(center, (9, 11))
        self.assertEqual(target.tobytes(), self.source.tobytes())

    def test_zero_corners(self):
        """支持只横向或只纵向切片，以及无边角的整图缩放。"""
        for corner, width, height, size in (((0, 3), -1, 2, (13, 8)),
                                            ((2, 0), 1, -1, (5, 17)),
                                            ((0, 0), 3, 4, (3, 4))):
            target, _ = resize_scale9(self.source, corner, width, height)
            self.assertEqual(target.size, size)

    def test_invalid_dimensions(self):
        """拒绝无中心区域、负边角和非法目标尺寸。"""
        for corner, width, height in (((7, 3), 1, 1), ((2, 9), 1, 1), ((-1, 2), 1, 1),
                                      ((0, 3), None, None), ((2, 3), 0, 1), ((2, 3), -2, 1)):
            with self.assertRaises(ValueError):
                resize_scale9(self.source, corner, width, height)

    def test_file_output_and_overwrite_guards(self):
        """默认输出新文件，保留原图，只有显式授权才能覆盖结果。"""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "原始 图片.PNG"
            self.source.save(source)
            original = source.read_bytes()
            result = convert_file(source, (2, 3), 1, 2)
            target = Path(result["output"])
            self.assertEqual(target.name, "原始 图片_s9.png")
            self.assertEqual(result["cap_insets"], {"x": 2, "y": 3, "width": 1, "height": 2})
            with Image.open(target) as image:
                self.assertEqual(image.mode, "RGBA")
                self.assertEqual(image.size, (5, 8))
            with self.assertRaises(FileExistsError):
                convert_file(source, (2, 3))
            convert_file(source, (2, 3), force=True)
            with self.assertRaises(ValueError):
                convert_file(source, (2, 3), output_path=source, force=True)
            self.assertEqual(source.read_bytes(), original)

    def test_palette_transparency(self):
        """索引 PNG 的透明像素转换后仍然透明。"""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "palette.png"
            palette = Image.new("P", (9, 9), 1)
            palette.putpalette([255, 0, 0, 0, 255, 0] + [0] * 762)
            palette.putpixel((0, 0), 0)
            palette.save(source, transparency=0)
            result = convert_file(source, (2, 2), 1, 1)
            with Image.open(result["output"]) as target:
                self.assertEqual(target.getpixel((0, 0)), (255, 0, 0, 0))
                self.assertEqual(target.getpixel((1, 1)), (0, 255, 0, 255))

    def test_cli(self):
        """命令行支持 -1、中英文路径，并在无效参数时返回失败。"""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "test 图.png"
            self.source.save(source)
            command = [sys.executable, str(Path(__file__).with_name("png_to_scale9sprite.py")), str(source), "2x3", "-1", "2"]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(source.with_name("test 图_s9.png").exists())
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("已存在", result.stderr)


if __name__ == "__main__":
    unittest.main()
