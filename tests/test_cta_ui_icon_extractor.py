import importlib.util
import struct
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "extract-cta-ui-icons.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("cta_ui_icon_extractor", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def pvr(pixel_type: int, width: int, height: int, pixels: bytes) -> bytes:
    header = struct.pack(
        "<13I", 52, height, width, 0, 0x8000 | pixel_type, len(pixels),
        32 if pixel_type == 0x12 else 16, 0xFF, 0xFF00, 0xFF0000, 0xFF000000,
        0x21525650, 1,
    )
    return header + pixels


class UiIconExtractorTests(unittest.TestCase):
    def test_job_indicators_use_distinct_he_job_frames_not_awakening_resources(self):
        self.assertEqual(("UI1", "HE_JobFighter.png"), MODULE.JOBS["brawler"])
        self.assertEqual(10, len(set(MODULE.JOBS.values())))
        self.assertFalse(any("Rs_HeJob" in frame for _, frame in MODULE.JOBS.values()))

    def test_decodes_rgba8888_and_crops_a_trimmed_frame(self):
        pixels = bytes((
            255, 0, 0, 255, 0, 255, 0, 255,
            0, 0, 255, 255, 255, 255, 255, 255,
        ))
        atlas = MODULE.decode_pvr(pvr(0x12, 2, 2, pixels))
        icon = MODULE.crop(atlas, {
            "frame": "{{1,0},{1,2}}", "rotated": False,
            "sourceColorRect": "{{1,0},{1,2}}", "sourceSize": "{2,2}",
        })
        self.assertEqual((2, 2), (icon.width, icon.height))
        self.assertEqual(bytes((0, 0, 0, 0, 0, 255, 0, 255)), icon.rgba[:8])
        self.assertTrue(MODULE.png(icon).startswith(b"\x89PNG\r\n\x1a\n"))

    def test_decodes_rgba4444_using_pvr_channel_masks(self):
        atlas = MODULE.decode_pvr(pvr(0x10, 1, 1, struct.pack("<H", 0x123F)))
        self.assertEqual(bytes((0x11, 0x22, 0x33, 0xFF)), atlas.rgba)

    def test_rejects_frames_outside_the_atlas(self):
        atlas = MODULE.Image(1, 1, bytes((0, 0, 0, 0)))
        with self.assertRaisesRegex(ValueError, "outside"):
            MODULE.crop(atlas, {
                "frame": "{{1,0},{1,1}}", "rotated": False,
                "sourceColorRect": "{{0,0},{1,1}}", "sourceSize": "{1,1}",
            })


if __name__ == "__main__":
    unittest.main()
