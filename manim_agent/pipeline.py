from pathlib import Path

from .kimi_client import call_kimi_for_manim
from .manim_runner import extract_python_code, run_manim


def generate_video_from_description(description: str) -> Path:
    full_text = call_kimi_for_manim(description)
    code = extract_python_code(full_text)
    video_path = run_manim(code)
    return video_path