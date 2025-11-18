import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from .config import DEFAULT_SCENE_NAME, DEFAULT_QUALITY


CODE_BLOCK_RE = re.compile(r"```python\s*(?P<code>.*?)```", re.DOTALL | re.IGNORECASE)


def extract_python_code(full_text: str) -> str:
    m = CODE_BLOCK_RE.search(full_text)
    if not m:
        raise ValueError("未在模型输出中找到 ```python 代码块，请检查提示词或输出。")
    return m.group("code").strip()


def run_manim(code: str, scene_name: str = DEFAULT_SCENE_NAME) -> Path:
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)
        script_path = work_dir / "generated_scene.py"
        script_path.write_text(code, encoding="utf-8")

        subprocess.run(["python", "-m", "py_compile", str(script_path)], check=True)

        subprocess.run([
            "manim",
            f"-q{DEFAULT_QUALITY}",
            str(script_path),
            scene_name,
        ], check=True, cwd=work_dir)

        media_dir = work_dir / "media" / "videos"
        video_path: Optional[Path] = None
        for f in media_dir.rglob(f"{scene_name}.mp4"):
            video_path = f
            break
        if video_path is None:
            raise FileNotFoundError("未找到渲染输出的 mp4 文件，请检查 manim 配置。")

        output_dir = Path.cwd() / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        final_path = output_dir / video_path.name
        final_path.write_bytes(video_path.read_bytes())
        return final_path