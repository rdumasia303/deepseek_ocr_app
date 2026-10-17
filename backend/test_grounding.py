"""Grounding parser regressions. Run from the repository root with:

    python -m unittest discover -s backend -p test_grounding.py

Requires the backend dependencies, but does not load a model or use a GPU.
"""

import unittest
from unittest.mock import patch

from main import clean_grounding_text, parse_detections


def detection(label, coordinates):
    return f"<|ref|>{label}<|/ref|><|det|>{coordinates}<|/det|>"


class GroundingTests(unittest.TestCase):
    def test_separate_labels_keep_all_boxes_in_order(self):
        text = detection("cat", "[[0, 100, 200, 300], [400, 500, 600, 700]]")
        text += detection("dog", "[[700, 800, 900, 999]]")
        self.assertEqual(parse_detections(text, 999, 1998), [
            {"label": "cat", "box": [0, 200, 200, 600]},
            {"label": "cat", "box": [400, 1000, 600, 1400]},
            {"label": "dog", "box": [700, 1600, 900, 1998]},
        ])

    def test_clean_text_keeps_labels_and_intervening_content(self):
        text = "<|grounding|>Before\n" + detection("cat", "[[0, 1, 2, 3]]")
        text += "\nA [bracketed] paragraph.\n" + detection("dog", "[[4, 5, 6, 7]]") + "\nAfter"
        self.assertEqual(
            clean_grounding_text(text),
            "Before\ncat\nA [bracketed] paragraph.\ndog\nAfter",
        )

    def test_flat_and_nested_single_boxes_still_work(self):
        for coordinates in ["[100, 200, 300, 400]", "[[100, 200, 300, 400]]"]:
            with self.subTest(coordinates=coordinates):
                self.assertEqual(parse_detections(detection("total", coordinates), 999, 999), [
                    {"label": "total", "box": [100, 200, 300, 400]},
                ])

    def test_multiline_lists_and_unicode_labels(self):
        text = detection("猫", "[\n [0, 0, 100, 100],\n [200, 200, 300, 300]\n]")
        text += "\n" + detection("犬", "[400, 400, 500, 500]")
        self.assertEqual(parse_detections(text, 999, 999), [
            {"label": "猫", "box": [0, 0, 100, 100]},
            {"label": "猫", "box": [200, 200, 300, 300]},
            {"label": "犬", "box": [400, 400, 500, 500]},
        ])
        self.assertEqual(clean_grounding_text(text), "猫\n犬")

    def test_invalid_coordinates_do_not_discard_later_detections(self):
        text = detection("bad", "[not valid]") + "\n" + detection("good", "[[1, 2, 3, 4]]")
        self.assertEqual(parse_detections(text, 999, 999), [
            {"label": "good", "box": [1, 2, 3, 4]},
        ])

    def test_coordinate_expressions_are_not_executed(self):
        text = detection("bad", "[__import__('os').system('unexpected')]")
        text += detection("good", "[[1, 2, 3, 4]]")
        with patch("os.system") as system:
            boxes = parse_detections(text, 999, 999)
        system.assert_not_called()
        self.assertEqual(boxes, [{"label": "good", "box": [1, 2, 3, 4]}])

    def test_empty_detections_and_plain_text(self):
        for text in ["", "Plain OCR text", detection("empty", "[]")]:
            with self.subTest(text=text):
                self.assertEqual(parse_detections(text, 999, 999), [])
        self.assertEqual(clean_grounding_text("Plain OCR text"), "Plain OCR text")
        self.assertEqual(clean_grounding_text(detection("empty", "[]")), "empty")


if __name__ == "__main__":
    unittest.main()
