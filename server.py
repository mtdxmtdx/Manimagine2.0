from fastapi import FastAPI
from pydantic import BaseModel
from manim_agent.pipeline import generate_video_from_description


app = FastAPI(title="Kimi + Manim Demo")


class GenerateRequest(BaseModel):
    description: str


class GenerateResponse(BaseModel):
    video_path: str


@app.post("/generate-manim-video", response_model=GenerateResponse)
def generate_manim_video(req: GenerateRequest):
    video_path = generate_video_from_description(req.description)
    return GenerateResponse(video_path=str(video_path))