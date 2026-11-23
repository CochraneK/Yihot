import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOL_DIR = REPO_ROOT / "tools" / "stc-wechat-dashboard"
sys.path.insert(0, str(TOOL_DIR))

import build_dashboard  # noqa: E402


class TestStcDashboardBuild(unittest.TestCase):
    def test_inline_json_escapes_script_breakout_and_line_separators(self):
        payload = {
            "title": "</script><script>alert(1)</script><!--x-->\u2028\u2029",
        }
        rendered = build_dashboard.serialize_inline_json(payload)
        self.assertNotIn("</script>", rendered.lower())
        self.assertNotIn("<!--", rendered)
        self.assertNotIn("\u2028", rendered)
        self.assertNotIn("\u2029", rendered)
        self.assertEqual(json.loads(rendered), payload)

    def test_build_and_selftest_with_malicious_title_fixture(self):
        fixture = {
            "meta": {
                "total": 2,
                "year_min": 2024,
                "year_max": 2025,
                "theme_count": 2,
                "vocab_size": 120,
                "generated": "2025-01-02",
            },
            "yearly": [
                {"year": 2024, "count": 1, "total_char": 500, "avg_char": 500.0},
                {"year": 2025, "count": 1, "total_char": 600, "avg_char": 600.0},
            ],
            "themes": [
                {
                    "key": "protection",
                    "label": "儿童保护",
                    "color": "#DA291C",
                    "count": 1,
                    "pct": 50.0,
                    "by_year": {"2024": 1, "2025": 0},
                    "top_words": [{"word": "儿童", "n": 6}],
                },
                {
                    "key": "education",
                    "label": "儿童教育",
                    "color": "#009CA6",
                    "count": 1,
                    "pct": 50.0,
                    "by_year": {"2024": 0, "2025": 1},
                    "top_words": [{"word": "阅读", "n": 5}],
                },
            ],
            "overall_top_words": [{"word": "儿童", "n": 12}, {"word": "阅读", "n": 5}],
            "tfidf_year": {
                "2024": [{"word": "儿童", "score": 0.8, "n": 6}],
                "2025": [{"word": "阅读", "score": 0.9, "n": 5}],
            },
            "cooccurrence": [{"a": "protection", "b": "education", "n": 1}],
            "theme_keys": {"protection": "儿童保护", "education": "儿童教育"},
            "articles": [
                {
                    "id": "a1",
                    "date": "2024-01-01",
                    "year": 2024,
                    "title": "测试文章</script><script>throw new Error('xss')</script>",
                    "primary": "protection",
                    "themes": ["protection", "education"],
                },
                {
                    "id": "a2",
                    "date": "2025-01-02",
                    "year": 2025,
                    "title": "儿童保护年报发布",
                    "primary": "education",
                    "themes": ["education"],
                },
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            data_path = os.path.join(tmp, "data.json")
            out_path = os.path.join(tmp, "index.html")
            with open(data_path, "w", encoding="utf-8") as f:
                json.dump(fixture, f, ensure_ascii=False)
            build_proc = subprocess.run(
                [sys.executable, str(TOOL_DIR / "build_dashboard.py"), "--data", data_path, "--out", out_path, "--site"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(build_proc.returncode, 0, build_proc.stderr + build_proc.stdout)
            html = Path(out_path).read_text(encoding="utf-8")
            self.assertNotIn("alert(1)", html)
            self.assertNotIn("throw new Error('xss')</script>", html)
            smoke_proc = subprocess.run(
                ["node", str(TOOL_DIR / "selftest.js"), out_path],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(smoke_proc.returncode, 0, smoke_proc.stderr + smoke_proc.stdout)
            self.assertIn("SMOKE TEST PASSED", smoke_proc.stdout)


if __name__ == "__main__":
    unittest.main()
