# Manimagine 2.0 — Kimi + Manim 最小可用演示

一个从自然语言到数学可视化视频的最小可用系统：
- 输入中文描述，调用 Kimi `kimi-k2-thinking` 生成 Manim CE 代码
- 自动提取单一 ```python 代码块，统一场景类 `GeneratedScene(MovingCameraScene)`
- 本地调用 `manim -qk` 渲染并输出到 `outputs/GeneratedScene.mp4`
- 提供命令行脚本与 FastAPI REST 接口

## 功能特性
- 自然语言 → Manim 代码 → 视频的流水线
- 统一代码约束，降低渲染报错率
- CLI 快速体验与 REST 服务集成
- 可扩展调参（tokens、temperature、质量等）

## 项目结构
```
manim_agent/
  __init__.py
  config.py          # 配置与默认参数
  kimi_client.py     # 调用 Moonshot Kimi
  manim_runner.py    # 代码提取与渲染
  pipeline.py        # 整体流水线
cli_generate.py      # 命令行入口
server.py            # FastAPI 服务
requirements.txt     # 依赖
提示词.md             # 系统提示词（需自行准备）
```

## 环境准备
1. 安装依赖：
```
pip install -r requirements.txt
```
2. 在项目根目录创建 `.env`：
```
MOONSHOT_API_KEY=你的_kimi_api_key
```
3. 在项目根目录放置 `提示词.md`（你的系统提示词）。

## 运行方式
- 命令行：
```
python cli_generate.py "演示单位圆上复平面指数 e^{it} 的几何意义"
```
- 启动服务：
```
uvicorn server:app --reload
```
- 调用接口：
```
curl -X POST "http://127.0.0.1:8000/generate-manim-video" \
  -H "Content-Type: application/json" \
  -d '{"description": "可视化极限 (1 + 1/n)^n 收敛到 e 的过程"}'
```
返回示例：
```
{"video_path": "outputs/GeneratedScene.mp4"}
```

## 关键配置
- 模型与地址：`MOONSHOT_BASE_URL=https://api.moonshot.cn/v1`，`MOONSHOT_MODEL=kimi-k2-thinking`
- 默认渲染质量：`-qk`（中等质量）
- 代码约束：单一 ```python 代码块；类名 `GeneratedScene` 且继承 `MovingCameraScene`
- `Text`/`MathTex`/`VGroup` 用法与 LaTeX 合法性需遵守提示词规范

## 测试
- 运行：
```
python -m unittest -q
```
- 覆盖：代码块提取、渲染调用（打桩）、端到端流水线

## 注意事项
- 请勿提交 `.env`，密钥只通过环境变量加载
- 真实渲染需本地 Manim 完整环境与有效 `MOONSHOT_API_KEY`

## 仓库
- GitHub：https://github.com/mtdxmtdx/Manimagine2.0