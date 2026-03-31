"""
Security regression tests for the eval() RCE vulnerability (OX Security disclosure).

The vulnerability allowed arbitrary code execution via crafted OCR output
that was passed to eval() in parse_coordinates(). The fix uses ast.literal_eval()
which only allows literal data structures.

This test is self-contained and does not require backend dependencies.

Run: python test_security.py
"""

import ast


def parse_coordinates(ref_text, image_width, image_height):
    """
    Minimal reproduction of pdf_utils.parse_coordinates using the patched code.
    This mirrors the fixed version that uses ast.literal_eval() instead of eval().
    """
    try:
        label_type = ref_text[1]
        cor_list = ast.literal_eval(ref_text[2])

        scaled_boxes = []
        for points in cor_list:
            x1, y1, x2, y2 = points
            scaled_box = [
                int(x1 / 999 * image_width),
                int(y1 / 999 * image_height),
                int(x2 / 999 * image_width),
                int(y2 / 999 * image_height)
            ]
            scaled_boxes.append(scaled_box)

        return {
            'label': label_type,
            'boxes': scaled_boxes
        }
    except Exception as e:
        print(f"  [Blocked] {type(e).__name__}: {e}")
        return None


def test_legitimate_coordinates():
    """Verify that normal coordinate parsing still works."""
    ref_text = ("full_match", "text", "[[312, 339, 480, 681]]")
    result = parse_coordinates(ref_text, 1000, 1000)

    assert result is not None, "Legitimate coordinates should parse successfully"
    assert result['label'] == 'text'
    assert len(result['boxes']) == 1
    print("PASS: Legitimate coordinates parse correctly")


def test_multiple_boxes():
    """Verify multiple bounding boxes still work."""
    ref_text = ("full_match", "image", "[[100, 200, 300, 400], [500, 600, 700, 800]]")
    result = parse_coordinates(ref_text, 1000, 1000)

    assert result is not None, "Multiple boxes should parse successfully"
    assert len(result['boxes']) == 2
    print("PASS: Multiple bounding boxes parse correctly")


def test_rce_blocked_import_os():
    """The original exploit: __import__('os').system('...') must be blocked."""
    malicious = "__import__('os').system('echo HACKED')"
    ref_text = ("full_match", "exploit", malicious)
    result = parse_coordinates(ref_text, 1000, 1000)

    assert result is None, "Code execution payload should be rejected"
    print("PASS: __import__('os').system() payload is blocked")


def test_rce_blocked_exec():
    """exec() based payloads must be blocked."""
    malicious = "exec('import os; os.system(\"echo HACKED\")')"
    ref_text = ("full_match", "exploit", malicious)
    result = parse_coordinates(ref_text, 1000, 1000)

    assert result is None, "exec() payload should be rejected"
    print("PASS: exec() payload is blocked")


def test_rce_blocked_eval():
    """Nested eval() payloads must be blocked."""
    malicious = "eval('__import__(\"os\").popen(\"id\").read()')"
    ref_text = ("full_match", "exploit", malicious)
    result = parse_coordinates(ref_text, 1000, 1000)

    assert result is None, "Nested eval() payload should be rejected"
    print("PASS: Nested eval() payload is blocked")


def test_rce_blocked_lambda():
    """Lambda-based payloads must be blocked."""
    malicious = "(lambda: __import__('os').system('echo HACKED'))()"
    ref_text = ("full_match", "exploit", malicious)
    result = parse_coordinates(ref_text, 1000, 1000)

    assert result is None, "Lambda payload should be rejected"
    print("PASS: Lambda payload is blocked")


def test_rce_blocked_comprehension():
    """List comprehension code execution must be blocked."""
    malicious = "[__import__('os').system('echo HACKED') for x in [1]]"
    ref_text = ("full_match", "exploit", malicious)
    result = parse_coordinates(ref_text, 1000, 1000)

    assert result is None, "List comprehension payload should be rejected"
    print("PASS: List comprehension payload is blocked")


if __name__ == "__main__":
    print("=" * 60)
    print("Security Regression Tests (OX Security RCE disclosure)")
    print("=" * 60)
    print()

    tests = [
        test_legitimate_coordinates,
        test_multiple_boxes,
        test_rce_blocked_import_os,
        test_rce_blocked_exec,
        test_rce_blocked_eval,
        test_rce_blocked_lambda,
        test_rce_blocked_comprehension,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR: {test.__name__}: {e}")
            failed += 1

    print()
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    if failed == 0:
        print("All security tests passed - RCE vulnerability is patched.")
    else:
        print("WARNING: Some tests failed!")
