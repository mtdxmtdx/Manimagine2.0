from .config import (
    MOONSHOT_API_KEY,
    MOONSHOT_BASE_URL,
    MOONSHOT_MODEL,
    PROMPT_FILE,
)


def load_system_prompt() -> str:
    base = PROMPT_FILE.read_text(encoding="utf-8")
    extra = (
        "\n在给出最终 Manim 社区版代码时，请务必遵守以下额外规则：\n"
        "1. 所有可运行的 Python 代码必须放在一个 ```python 代码块中。\n"
        "2. 场景类统一命名为 GeneratedScene，且继承自 MovingCameraScene。\n"
        "3. 不要在代码块外再重复粘贴一遍代码。\n"
        "4. 在给出代码之前，可以先给出“第 1 步详细提示词”“第 2 步代码”“第 3 步自查结果”的自然语言说明。\n"
    )
    return base + "\n" + extra


def call_kimi_for_manim(user_description: str) -> str:
    if not MOONSHOT_API_KEY:
        raise RuntimeError("未找到 MOONSHOT_API_KEY 环境变量，请在 .env 中配置你的 Kimi API key。")
    from openai import OpenAI

    client = OpenAI(api_key=MOONSHOT_API_KEY, base_url=MOONSHOT_BASE_URL)
    system_prompt = load_system_prompt()
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                "下面是用户的 Manim 动画需求，请按你任务说明的三步来完成：\n"
                f"{user_description}\n\n"
                "请记得：最终的可运行 Manim 代码必须只出现在一个 ```python 代码块中。"
            ),
        },
    ]
    completion = client.chat.completions.create(
        model=MOONSHOT_MODEL,
        messages=messages,
        max_tokens=4096,
        temperature=0.8,
    )
    message = completion.choices[0].message
    return message.content