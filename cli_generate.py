import argparse
from manim_agent.pipeline import generate_video_from_description


def main():
    parser = argparse.ArgumentParser(
        description="使用 Kimi + Manim 从自然语言生成数学可视化视频"
    )
    parser.add_argument(
        "description",
        type=str,
        help="要可视化的自然语言描述，例如：'可视化傅里叶级数收敛过程'",
    )
    args = parser.parse_args()
    print(">>> 正在调用 Kimi 生成 Manim 代码并渲染视频，请稍候...")
    video_path = generate_video_from_description(args.description)
    print(f">>> 完成！视频已输出到：{video_path}")


if __name__ == "__main__":
    main()