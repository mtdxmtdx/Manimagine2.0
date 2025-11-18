下面是一个\*\*可直接运行的最小 demo 项目结构\*\*，包含：



\* `requirements.txt`

\* 简单 CLI：`cli\_generate.py`

\* FastAPI 服务：`server.py`

\* Kimi 调用与 Manim 渲染核心：`manim\_agent/` 包

\* 以及你之前提到的 `提示词.md`（放在项目根目录）



你可以直接把这些文件创建出来，安装依赖后运行。



---



\## 一、项目结构



```text

manim-kimi-demo/

├── manim\_agent/

│   ├── \_\_init\_\_.py

│   ├── config.py

│   ├── kimi\_client.py

│   ├── manim\_runner.py

│   └── pipeline.py

├── cli\_generate.py

├── server.py

├── requirements.txt

└── 提示词.md        # 你已有的 prompt 文件，放这里

```



---



\## 二、requirements.txt



```txt

fastapi

uvicorn

openai>=1.51.0

manim

python-dotenv

pydantic>=2

```



> 说明：

>

> \* `openai`：用来调用兼容 OpenAI SDK 的 Moonshot Kimi 接口（`base\_url="https://api.moonshot.cn/v1"`）。

> \* `manim`：Manim Community Edition（会安装当前稳定版）。

> \* `python-dotenv`：方便用 `.env` 管理 `MOONSHOT\_API\_KEY`。

> \* `fastapi` + `uvicorn`：Web 服务。



在项目根目录执行：



```bash

pip install -r requirements.txt

```



然后在根目录创建 `.env`（\*\*不要提交到 Git\*\*）：



```bash

echo 'MOONSHOT\_API\_KEY=你的\_kimi\_api\_key' > .env

```



---



\## 三、manim\_agent/config.py



统一管理配置，比如 API Key、模型名等。



```python

\# manim\_agent/config.py

import os

from dotenv import load\_dotenv

from pathlib import Path



\# 加载 .env 中的环境变量

load\_dotenv()



\# Moonshot Kimi API 配置

MOONSHOT\_API\_KEY = os.getenv("MOONSHOT\_API\_KEY", "")

MOONSHOT\_BASE\_URL = "https://api.moonshot.cn/v1"

MOONSHOT\_MODEL = "kimi-k2-thinking"



if not MOONSHOT\_API\_KEY:

&nbsp;   raise RuntimeError(

&nbsp;       "未找到 MOONSHOT\_API\_KEY 环境变量，请在 .env 中配置你的 Kimi API key。"

&nbsp;   )



\# 项目路径

PROJECT\_ROOT = Path(\_\_file\_\_).resolve().parents\[1]

PROMPT\_FILE = PROJECT\_ROOT / "提示词.md"



\# 一些默认渲染参数（可视需要扩展）

DEFAULT\_QUALITY = "k"  # manim -qk 中的 k，对应 "medium quality"

DEFAULT\_SCENE\_NAME = "GeneratedScene"

```



---



\## 四、manim\_agent/kimi\_client.py



封装 Kimi（Moonshot）调用逻辑。



````python

\# manim\_agent/kimi\_client.py

from openai import OpenAI

from .config import MOONSHOT\_API\_KEY, MOONSHOT\_BASE\_URL, MOONSHOT\_MODEL, PROMPT\_FILE





def load\_system\_prompt() -> str:

&nbsp;   """读取提示词.md 并附加机器可读约束。"""

&nbsp;   base = PROMPT\_FILE.read\_text(encoding="utf-8")

&nbsp;   extra = """

在给出最终 Manim 社区版代码时，请务必遵守以下额外规则：

1\. 所有可运行的 Python 代码必须放在一个 ```python 代码块中。

2\. 场景类统一命名为 GeneratedScene，且继承自 MovingCameraScene。

3\. 不要在代码块外再重复粘贴一遍代码。

4\. 在给出代码之前，可以先给出“第 1 步详细提示词”“第 2 步代码”“第 3 步自查结果”的自然语言说明。

"""

&nbsp;   return base + "\\n" + extra





client = OpenAI(

&nbsp;   api\_key=MOONSHOT\_API\_KEY,

&nbsp;   base\_url=MOONSHOT\_BASE\_URL,

)





def call\_kimi\_for\_manim(user\_description: str) -> str:

&nbsp;   """

&nbsp;   调用 kimi-k2-thinking，根据自然语言生成完整回复（含解释和 python 代码块）。

&nbsp;   返回的是 message.content（字符串）。

&nbsp;   """

&nbsp;   system\_prompt = load\_system\_prompt()

&nbsp;   messages = \[

&nbsp;       {"role": "system", "content": system\_prompt},

&nbsp;       {

&nbsp;           "role": "user",

&nbsp;           "content": (

&nbsp;               "下面是用户的 Manim 动画需求，请按你任务说明的三步来完成：\\n"

&nbsp;               f"{user\_description}\\n\\n"

&nbsp;               "请记得：最终的可运行 Manim 代码必须只出现在一个 ```python 代码块中。"

&nbsp;           ),

&nbsp;       },

&nbsp;   ]



&nbsp;   completion = client.chat.completions.create(

&nbsp;       model=MOONSHOT\_MODEL,

&nbsp;       messages=messages,

&nbsp;       max\_tokens=4096,

&nbsp;       temperature=0.8,

&nbsp;   )



&nbsp;   message = completion.choices\[0].message

&nbsp;   return message.content

````



---



\## 五、manim\_agent/manim\_runner.py



负责从文本里抽取代码，并调用 Manim 渲染。



````python

\# manim\_agent/manim\_runner.py

import re

import subprocess

import tempfile

from pathlib import Path

from typing import Optional



from .config import DEFAULT\_SCENE\_NAME, DEFAULT\_QUALITY





CODE\_BLOCK\_RE = re.compile(

&nbsp;   r"```python\\s\*(?P<code>.\*?)```",

&nbsp;   re.DOTALL | re.IGNORECASE,

)





def extract\_python\_code(full\_text: str) -> str:

&nbsp;   """从模型的完整回复中提取第一个 ```python 代码块。"""

&nbsp;   m = CODE\_BLOCK\_RE.search(full\_text)

&nbsp;   if not m:

&nbsp;       raise ValueError("未在模型输出中找到 ```python 代码块，请检查提示词或输出。")

&nbsp;   return m.group("code").strip()





def run\_manim(code: str, scene\_name: str = DEFAULT\_SCENE\_NAME) -> Path:

&nbsp;   """

&nbsp;   将代码写入临时文件，调用 manim 渲染，返回生成的视频文件路径。

&nbsp;   使用 -q{DEFAULT\_QUALITY} 设置质量。

&nbsp;   """

&nbsp;   with tempfile.TemporaryDirectory() as tmpdir:

&nbsp;       work\_dir = Path(tmpdir)

&nbsp;       script\_path = work\_dir / "generated\_scene.py"

&nbsp;       script\_path.write\_text(code, encoding="utf-8")



&nbsp;       # 可选：先做语法检查

&nbsp;       subprocess.run(

&nbsp;           \["python", "-m", "py\_compile", str(script\_path)],

&nbsp;           check=True,

&nbsp;       )



&nbsp;       # 调用 manim 渲染

&nbsp;       # manim -qk generated\_scene.py GeneratedScene

&nbsp;       subprocess.run(

&nbsp;           \["manim", f"-q{DEFAULT\_QUALITY}", str(script\_path), scene\_name],

&nbsp;           check=True,

&nbsp;           cwd=work\_dir,

&nbsp;       )



&nbsp;       # Manim 默认输出路径大致是：media/videos/generated\_scene/1080p60/GeneratedScene.mp4

&nbsp;       media\_dir = work\_dir / "media" / "videos"

&nbsp;       video\_path: Optional\[Path] = None

&nbsp;       for f in media\_dir.rglob(f"{scene\_name}.mp4"):

&nbsp;           video\_path = f

&nbsp;           break



&nbsp;       if video\_path is None:

&nbsp;           raise FileNotFoundError("未找到渲染输出的 mp4 文件，请检查 manim 配置。")



&nbsp;       # 把结果复制到项目根目录下的 outputs 目录

&nbsp;       output\_dir = Path.cwd() / "outputs"

&nbsp;       output\_dir.mkdir(parents=True, exist\_ok=True)

&nbsp;       final\_path = output\_dir / video\_path.name

&nbsp;       final\_path.write\_bytes(video\_path.read\_bytes())

&nbsp;       return final\_path

````



---



\## 六、manim\_agent/pipeline.py



把“调用 Kimi → 提取代码 → 渲染视频”拼成一条流水线。



```python

\# manim\_agent/pipeline.py

from pathlib import Path



from .kimi\_client import call\_kimi\_for\_manim

from .manim\_runner import extract\_python\_code, run\_manim





def generate\_video\_from\_description(description: str) -> Path:

&nbsp;   """

&nbsp;   整体流水线：

&nbsp;   1. 调用 kimi-k2-thinking 获取完整回复

&nbsp;   2. 提取 python 代码块

&nbsp;   3. 调用 manim 渲染

&nbsp;   4. 返回输出视频路径

&nbsp;   """

&nbsp;   full\_text = call\_kimi\_for\_manim(description)

&nbsp;   code = extract\_python\_code(full\_text)

&nbsp;   video\_path = run\_manim(code)

&nbsp;   return video\_path

```



---



\## 七、cli\_generate.py（命令行脚本）



```python

\# cli\_generate.py

import argparse

from manim\_agent.pipeline import generate\_video\_from\_description





def main():

&nbsp;   parser = argparse.ArgumentParser(

&nbsp;       description="使用 Kimi + Manim 从自然语言生成数学可视化视频"

&nbsp;   )

&nbsp;   parser.add\_argument(

&nbsp;       "description",

&nbsp;       type=str,

&nbsp;       help="要可视化的自然语言描述，例如：'可视化傅里叶级数收敛过程'",

&nbsp;   )

&nbsp;   args = parser.parse\_args()



&nbsp;   print(">>> 正在调用 Kimi 生成 Manim 代码并渲染视频，请稍候...")

&nbsp;   video\_path = generate\_video\_from\_description(args.description)

&nbsp;   print(f">>> 完成！视频已输出到：{video\_path}")





if \_\_name\_\_ == "\_\_main\_\_":

&nbsp;   main()

```



使用示例：



```bash

python cli\_generate.py "演示单位圆上复平面指数 e^{it} 的几何意义"

```



---



\## 八、server.py（FastAPI 服务）



```python

\# server.py

from fastapi import FastAPI

from pydantic import BaseModel

from manim\_agent.pipeline import generate\_video\_from\_description



app = FastAPI(title="Kimi + Manim Demo")





class GenerateRequest(BaseModel):

&nbsp;   description: str





class GenerateResponse(BaseModel):

&nbsp;   video\_path: str





@app.post("/generate-manim-video", response\_model=GenerateResponse)

def generate\_manim\_video(req: GenerateRequest):

&nbsp;   """

&nbsp;   输入自然语言描述，输出渲染后视频在服务器上的路径。

&nbsp;   实际部署时可以配合 nginx / 静态文件服务把 outputs 暴露出去。

&nbsp;   """

&nbsp;   video\_path = generate\_video\_from\_description(req.description)

&nbsp;   return GenerateResponse(video\_path=str(video\_path))

```



启动服务：



```bash

uvicorn server:app --reload

```



发送请求（示例）：



```bash

curl -X POST "http://127.0.0.1:8000/generate-manim-video" \\

&nbsp; -H "Content-Type: application/json" \\

&nbsp; -d '{"description": "可视化极限 (1 + 1/n)^n 收敛到 e 的过程"}'

```



返回类似：



```json

{

&nbsp; "video\_path": "outputs/GeneratedScene.mp4"

}

```



---





