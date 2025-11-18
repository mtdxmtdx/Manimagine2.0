import os
from pathlib import Path
from unittest import mock, TestCase


class TestPipeline(TestCase):
    def setUp(self):
        os.environ.setdefault("MOONSHOT_API_KEY", "test_key")

    def test_extract_python_code(self):
        from manim_agent.manim_runner import extract_python_code

        text = (
            "说明\n```python\nfrom manim import *\nclass GeneratedScene(MovingCameraScene):\n"
            "    def construct(self):\n        pass\n```\n结束"
        )
        code = extract_python_code(text)
        self.assertIn("GeneratedScene", code)

    def _mock_run(self, args, check=True, cwd=None):
        if args and args[0] == "manim":
            media_root = Path(cwd) / "media" / "videos" / "generated_scene" / "1080p60"
            media_root.mkdir(parents=True, exist_ok=True)
            (media_root / "GeneratedScene.mp4").write_bytes(b"mp4")
        return mock.Mock()

    def test_run_manim_mocked(self):
        from manim_agent.manim_runner import run_manim

        code = "from manim import *\nclass GeneratedScene(MovingCameraScene):\n    def construct(self):\n        pass\n"
        with mock.patch("subprocess.run", side_effect=self._mock_run):
            final_path = run_manim(code)
        self.assertTrue(final_path.exists())
        self.assertTrue(str(final_path).endswith("GeneratedScene.mp4"))

    def test_generate_video_from_description(self):
        from manim_agent import pipeline

        sample_reply = (
            "步骤\n```python\nfrom manim import *\nclass GeneratedScene(MovingCameraScene):\n"
            "    def construct(self):\n        pass\n```\n"
        )

        with mock.patch("manim_agent.pipeline.call_kimi_for_manim", return_value=sample_reply):
            with mock.patch("subprocess.run", side_effect=self._mock_run):
                path = pipeline.generate_video_from_description("测试")
        self.assertTrue(path.exists())
